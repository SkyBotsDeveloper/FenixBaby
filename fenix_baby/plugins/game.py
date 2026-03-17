# Copyright (c) 2025 Telegram:- @llFenixxll <llFenixxll>
# Location: Patna, Bihar 
#
# All rights reserved.
#
# This code is the intellectual property of @llFenixxll.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Contact: https://t.me/llFenixxll

import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.config import PROTECT_1D_COST, PROTECT_2D_COST, REVIVE_COST, AUTO_REVIVE_HOURS, OWNER_ID
from fenix_baby.utils import ensure_user_exists, resolve_target, is_protected, get_active_protection, format_time, format_money, get_mention, check_auto_revive
from fenix_baby.database import users_collection
from fenix_baby.services.ai_client import ask_ai_raw
from fenix_baby.ui.components import Templates, Buttons

KILL_NARRATIVES = [
    "P1 ne P2 ko thappad maar ke bhaga diya! 💀",
    "P1 ne P2 ko chappal se maara! 🩴💥",
    "P1 ne P2 ko uda diya! 🔫💨",
    "P1 ne P2 ka game khatam kar diya! ☠️",
    "P1 ne P2 ko dharti mein gada diya! 🪦",
    "P1 ne P2 ka kaam tamaam kar diya! 💀",
    "P1 ne P2 ko seedha swarg bhej diya! 😇",
    "P1 ne P2 ko dhool chata di! 💨",
]

ROB_NARRATIVES = [
    "P1 ne P2 ki jeb kaati! 💰",
    "P1 ne P2 ka wallet chura liya! 👛",
    "P1 ne P2 ko loot liya bhai! 🤑",
    "P1 ne P2 ka paisa gayab kar diya! 💸",
    "P1 ne P2 ko kangaal bana diya! 📉",
    "P1 ne P2 ki tijori khali kar di! 🏦",
]

async def get_narrative(action_type, attacker_mention, target_mention):
    if action_type == 'kill':
        prompt = "Generate a funny 1-line kill message in Hinglish. Use P1 for killer and P2 for victim. Make it dramatic and funny. Example: 'P1 ne P2 ko seedha swarg bhej diya!'"
        fallback = KILL_NARRATIVES
    elif action_type == 'rob':
        prompt = "Generate a funny 1-line robbery message in Hinglish. Use P1 for thief and P2 for victim. Make it dramatic. Example: 'P1 ne P2 ki jeb kaati!'"
        fallback = ROB_NARRATIVES
    else:
        return "P1 -> P2"
    
    res = await ask_ai_raw("Game Narrator - generate funny Hinglish game messages", prompt, 50)
    
    if res and "P1" in res and "P2" in res:
        text = res
    else:
        import random
        text = random.choice(fallback)
    
    return text.replace("P1", attacker_mention).replace("P2", target_mention)

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    attacker = ensure_user_exists(update.effective_user)
    if attacker['user_id'] == OWNER_ID:
        # Owner can't be killed, but can kill. However, respect protection if target is protected even from owner?
        # User said "no one can rob them till there protection time get out". Usually owner is exception but let's be strict if asked.
        pass

    target, error = await resolve_target(update, context)
    
    if not target or not update or not update.effective_message:
        if update and update.effective_message:
            await update.effective_message.reply_text(error if error else "⚠️ <b>Usage:</b> <code>/kill @user</code>", parse_mode=ParseMode.HTML)
        return

    if target['user_id'] == OWNER_ID: return await update.effective_message.reply_text("👑 <b>Immortal God!</b> Master is the source of all life. You cannot kill him.", parse_mode=ParseMode.HTML)
    
    # Protection check moved up to be the absolute first check after basic existence
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.effective_message.reply_text(f"🛡️ <b>Blocked!</b> Target is under protection for <code>{format_time(rem)}</code>. No one can touch them!", parse_mode=ParseMode.HTML)

    if attacker['user_id'] != OWNER_ID:
        if attacker['status'] == 'dead': return await update.effective_message.reply_text("💀 You are dead.", parse_mode=ParseMode.HTML)
    
    if target['status'] == 'dead': return await update.effective_message.reply_text("⚰️ Already dead.", parse_mode=ParseMode.HTML)
    if target['user_id'] == attacker['user_id']: return await update.effective_message.reply_text("🤔 No.", parse_mode=ParseMode.HTML)

    # --- FAIR PLAY: MAX 1 WEAPON BUFF ---
    base_reward = random.randint(100, 200)
    weapons = [i for i in attacker.get('inventory', []) if i['type'] == 'weapon']
    best_w = max(weapons, key=lambda x: x['buff']) if weapons else None
    buff = best_w['buff'] if best_w else 0
    final_reward = int(base_reward * (1 + buff))
    
    # --- BURN FLEX ITEMS ---
    flex_burn_text = ""
    target_inv = target.get('inventory', [])
    # Filter out Flex items to delete
    flex_items = [i for i in target_inv if i['type'] == 'flex']
    if flex_items:
        users_collection.update_one({"user_id": target["user_id"]}, {"$pull": {"inventory": {"type": "flex"}}})
        flex_burn_text = f"\n🔥 <b>Burned:</b> {len(flex_items)} Flex Items destroyed!"

    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "dead", "death_time": datetime.utcnow()}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"kills": 1, "balance": final_reward}})

    narration = await get_narrative("kill", get_mention(attacker), get_mention(target))
    buff_text = f" <i>(+{int(buff*100)}% {best_w['name']})</i>" if best_w else ""

    kill_result = f"🔪 <b>killed!</b> {narration} 💰 <b>+{format_money(final_reward)}</b>"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛡️ buy protection", callback_data="game_protect_info"),
            InlineKeyboardButton("💀 kill again", callback_data="game_kill_info"),
        ],
        [
            InlineKeyboardButton("💰 my balance", callback_data="quick_bal"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])

    await update.effective_message.reply_text(kill_result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    attacker = ensure_user_exists(update.effective_user)
    if not attacker: return
    if attacker['user_id'] == OWNER_ID:
        return await update.effective_message.reply_text("Master, everything already belongs to you. No need to rob! 👑")

    if not context.args: return await update.effective_message.reply_text("⚠️ <b>Usage:</b> <code>/rob [amount] @user</code>", parse_mode=ParseMode.HTML)
    
    try: amount = int(context.args[0])
    except: return await update.effective_message.reply_text("⚠️ Invalid Amount", parse_mode=ParseMode.HTML)
    target_arg = context.args[1] if len(context.args) > 1 else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.effective_message.reply_text(error or "⚠️ Tag victim", parse_mode=ParseMode.HTML)

    if target['user_id'] == OWNER_ID: return await update.effective_message.reply_text("👑 <b>Immortal God!</b> Master's wealth is infinite and his protection is absolute.", parse_mode=ParseMode.HTML)
    if attacker['status'] == 'dead': return await update.effective_message.reply_text("💀 Dead.", parse_mode=ParseMode.HTML)
    if target['user_id'] == attacker['user_id']: return await update.effective_message.reply_text("🤦‍♂️ No.", parse_mode=ParseMode.HTML)
    
    # Protection check moved up to be the absolute first check after basic existence
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.effective_message.reply_text(f"🛡️ <b>Shielded!</b> Safe for <code>{format_time(rem)}</code>. No one can rob them!", parse_mode=ParseMode.HTML)

    if target['balance'] < amount: return await update.effective_message.reply_text("📉 Too poor.", parse_mode=ParseMode.HTML)

    # --- FAIR PLAY: MAX 1 ARMOR BLOCK ---
    armors = [i for i in target.get('inventory', []) if i['type'] == 'armor']
    best_a = max(armors, key=lambda x: x['buff']) if armors else None
    block_chance = best_a['buff'] if best_a else 0

    if random.random() < block_chance:
        return await update.effective_message.reply_text(f"🛡️ <b>BLOCKED!</b> {get_mention(target)} used {best_a['name']} to stop you!", parse_mode=ParseMode.HTML)

    # Execute
    users_collection.update_one({"user_id": target["user_id"]}, {"$inc": {"balance": -amount}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"balance": amount}})
    
    narration = await get_narrative("rob", get_mention(attacker), get_mention(target))
    header_title = "grave robbery" if target['status'] == 'dead' else "robbery complete"
    header_emoji = "🧟" if target['status'] == 'dead' else "💰"

    rob_result = f"💰 <b>stolen!</b> {narration} 💸 <b>+{format_money(amount)}</b>"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 rob again", callback_data="game_rob_info"),
            InlineKeyboardButton("🔪 kill", callback_data="game_kill_info"),
        ],
        [
            InlineKeyboardButton("💰 my balance", callback_data="quick_bal"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])

    await update.effective_message.reply_text(rob_result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    sender = ensure_user_exists(update.effective_user)
    if not sender: return
    if not context.args:
        protect_help = f"""
╔═══════════════════════╗
║  🛡️ <b>protection shield</b>  ║
╠═══════════════════════╣
║ Keep safe from kills & robs!
╠───────────────────────╣
║ 📦 <b>1 Day:</b> <code>{format_money(PROTECT_1D_COST)}</code>
║ 📦 <b>2 Days:</b> <code>{format_money(PROTECT_2D_COST)}</code>
╠───────────────────────╣
║ 📝 <b>Usage:</b>
║ <code>/protect 1d</code> - Self
║ <code>/protect 1d @user</code> - Partner
╚═══════════════════════╝"""
        return await update.effective_message.reply_text(protect_help, parse_mode=ParseMode.HTML)

    dur = context.args[0].lower()
    if dur == '1d': cost, days = PROTECT_1D_COST, 1
    elif dur == '2d': cost, days = PROTECT_2D_COST, 2
    else: return await update.effective_message.reply_text(Templates.warning_box("Use 1d or 2d only!"), parse_mode=ParseMode.HTML)

    target_arg = context.args[1] if len(context.args) > 1 else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    if not target: target = sender
    is_self = target['user_id'] == sender['user_id']
    
    # Couple Check
    if not is_self and sender.get("partner_id") != target["user_id"]:
         return await update.effective_message.reply_text(Templates.error_box("Couples only!"), parse_mode=ParseMode.HTML)

    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.effective_message.reply_text(f"""
╔═══════════════════════╗
║  🛡️ <b>already safe!</b>  ║
╠═══════════════════════╣
║ ⏰ <b>Time Left:</b> <code>{format_time(rem)}</code>
╚═══════════════════════╝""", parse_mode=ParseMode.HTML)
    
    if sender['balance'] < cost: return await update.effective_message.reply_text(Templates.error_box(f"Need {format_money(cost)}"), parse_mode=ParseMode.HTML)

    users_collection.update_one({"user_id": sender["user_id"]}, {"$inc": {"balance": -cost}})
    expiry_dt = datetime.utcnow() + timedelta(days=days)
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"protection_expiry": expiry_dt}})
    
    partner_id = target.get("partner_id")
    partner_bonus = ""
    if partner_id:
        users_collection.update_one({"user_id": partner_id}, {"$set": {"protection_expiry": expiry_dt}})
        partner_bonus = "\n║ 💞 <b>Partner Also Protected!</b>"

    if is_self:
        result = f"""
╔═══════════════════════╗
║  🛡️ <b>shield active!</b>  ║
╠═══════════════════════╣
║ 🔒 You are protected!
║ ⏰ <b>Duration:</b> <code>{days} day(s)</code>{partner_bonus}
╚═══════════════════════╝"""
    else:
        result = f"""
╔═══════════════════════╗
║  🛡️ <b>guardian!</b>  ║
╠═══════════════════════╣
║ 🔒 Protected {get_mention(target)}
║ ⏰ <b>Duration:</b> <code>{days} day(s)</code>{partner_bonus}
╚═══════════════════════╝"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 balance", callback_data="quick_bal"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    reviver = ensure_user_exists(update.effective_user)
    if not reviver: return
    target, _ = await resolve_target(update, context)
    if not target: target = reviver
    
    if target['status'] == 'alive': 
        return await update.effective_message.reply_text(Templates.success_box("Already alive!"), parse_mode=ParseMode.HTML)

    # Owner bypasses cost and check
    if reviver['user_id'] == OWNER_ID:
        users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "alive", "death_time": None}})
        target_text = "You" if target['user_id'] == reviver['user_id'] else get_mention(target)
        return await update.effective_message.reply_text(f"✨ <b>revived!</b>\n\n💖 {target_text} are back by Master's grace! 👑", parse_mode=ParseMode.HTML)

    if reviver['balance'] < REVIVE_COST: 
        return await update.effective_message.reply_text(Templates.error_box(f"Need {format_money(REVIVE_COST)}"), parse_mode=ParseMode.HTML)

    users_collection.update_one({"user_id": reviver["user_id"]}, {"$inc": {"balance": -REVIVE_COST}})
    users_collection.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": REVIVE_COST}})
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "alive", "death_time": None}})
    
    is_self = target['user_id'] == reviver['user_id']
    target_text = "You" if is_self else get_mention(target)

    result = f"""
╔═══════════════════════╗
║  💖 <b>revived!</b>  ║
╠═══════════════════════╣
║ ✨ {target_text} are back!
║ 💵 <b>Cost:</b> <code>{format_money(REVIVE_COST)}</code>
╚═══════════════════════╝"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛡️ buy protection", callback_data="game_protect_info"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

