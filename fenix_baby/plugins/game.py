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
    "P1 ne P2 ko thappad maar ke bhaga diya! ðŸ’€",
    "P1 ne P2 ko chappal se maara! ðŸ©´ðŸ’¥",
    "P1 ne P2 ko uda diya! ðŸ”«ðŸ’¨",
    "P1 ne P2 ka game khatam kar diya! â˜ ï¸",
    "P1 ne P2 ko dharti mein gada diya! ðŸª¦",
    "P1 ne P2 ka kaam tamaam kar diya! ðŸ’€",
    "P1 ne P2 ko seedha swarg bhej diya! ðŸ˜‡",
    "P1 ne P2 ko dhool chata di! ðŸ’¨",
]

ROB_NARRATIVES = [
    "P1 ne P2 ki jeb kaati! ðŸ’°",
    "P1 ne P2 ka wallet chura liya! ðŸ‘›",
    "P1 ne P2 ko loot liya bhai! ðŸ¤‘",
    "P1 ne P2 ka paisa gayab kar diya! ðŸ’¸",
    "P1 ne P2 ko kangaal bana diya! ðŸ“‰",
    "P1 ne P2 ki tijori khali kar di! ðŸ¦",
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
            await update.effective_message.reply_text(error if error else "âš ï¸ <b>Usage:</b> <code>/kill @user</code>", parse_mode=ParseMode.HTML)
        return

    if target['user_id'] == OWNER_ID: return await update.effective_message.reply_text("ðŸ‘‘ <b>Immortal God!</b> Master is the source of all life. You cannot kill him.", parse_mode=ParseMode.HTML)
    
    # Protection check moved up to be the absolute first check after basic existence
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.effective_message.reply_text(f"ðŸ›¡ï¸ <b>Blocked!</b> Target is under protection for <code>{format_time(rem)}</code>. No one can touch them!", parse_mode=ParseMode.HTML)

    if attacker['user_id'] != OWNER_ID:
        if attacker['status'] == 'dead': return await update.effective_message.reply_text("ðŸ’€ You are dead.", parse_mode=ParseMode.HTML)
    
    if target['status'] == 'dead': return await update.effective_message.reply_text("âš°ï¸ Already dead.", parse_mode=ParseMode.HTML)
    if target['user_id'] == attacker['user_id']: return await update.effective_message.reply_text("ðŸ¤” No.", parse_mode=ParseMode.HTML)

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
        flex_burn_text = f"\nðŸ”¥ <b>Burned:</b> {len(flex_items)} Flex Items destroyed!"

    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "dead", "death_time": datetime.utcnow()}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"kills": 1, "balance": final_reward}})

    narration = await get_narrative("kill", get_mention(attacker), get_mention(target))
    buff_text = f" <i>(+{int(buff*100)}% {best_w['name']})</i>" if best_w else ""

    kill_result = f"ðŸ”ª <b>á´‹ÉªÊŸÊŸá´‡á´…!</b> {narration} ðŸ’° <b>+{format_money(final_reward)}</b>"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ›¡ï¸ Ê™á´œÊ á´˜Ê€á´á´›á´‡á´„á´›Éªá´É´", callback_data="game_protect_info"),
            InlineKeyboardButton("ðŸ’€ á´‹ÉªÊŸÊŸ á´€É¢á´€ÉªÉ´", callback_data="game_kill_info"),
        ],
        [
            InlineKeyboardButton("ðŸ’° á´Ê Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
        ]
    ])

    await update.effective_message.reply_text(kill_result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    attacker = ensure_user_exists(update.effective_user)
    if not attacker: return
    if attacker['user_id'] == OWNER_ID:
        return await update.effective_message.reply_text("Master, everything already belongs to you. No need to rob! ðŸ‘‘")

    if not context.args: return await update.effective_message.reply_text("âš ï¸ <b>Usage:</b> <code>/rob [amount] @user</code>", parse_mode=ParseMode.HTML)
    
    try: amount = int(context.args[0])
    except: return await update.effective_message.reply_text("âš ï¸ Invalid Amount", parse_mode=ParseMode.HTML)
    target_arg = context.args[1] if len(context.args) > 1 else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.effective_message.reply_text(error or "âš ï¸ Tag victim", parse_mode=ParseMode.HTML)

    if target['user_id'] == OWNER_ID: return await update.effective_message.reply_text("ðŸ‘‘ <b>Immortal God!</b> Master's wealth is infinite and his protection is absolute.", parse_mode=ParseMode.HTML)
    if attacker['status'] == 'dead': return await update.effective_message.reply_text("ðŸ’€ Dead.", parse_mode=ParseMode.HTML)
    if target['user_id'] == attacker['user_id']: return await update.effective_message.reply_text("ðŸ¤¦â€â™‚ï¸ No.", parse_mode=ParseMode.HTML)
    
    # Protection check moved up to be the absolute first check after basic existence
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.effective_message.reply_text(f"ðŸ›¡ï¸ <b>Shielded!</b> Safe for <code>{format_time(rem)}</code>. No one can rob them!", parse_mode=ParseMode.HTML)

    if target['balance'] < amount: return await update.effective_message.reply_text("ðŸ“‰ Too poor.", parse_mode=ParseMode.HTML)

    # --- FAIR PLAY: MAX 1 ARMOR BLOCK ---
    armors = [i for i in target.get('inventory', []) if i['type'] == 'armor']
    best_a = max(armors, key=lambda x: x['buff']) if armors else None
    block_chance = best_a['buff'] if best_a else 0

    if random.random() < block_chance:
        return await update.effective_message.reply_text(f"ðŸ›¡ï¸ <b>BLOCKED!</b> {get_mention(target)} used {best_a['name']} to stop you!", parse_mode=ParseMode.HTML)

    # Execute
    users_collection.update_one({"user_id": target["user_id"]}, {"$inc": {"balance": -amount}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"balance": amount}})
    
    narration = await get_narrative("rob", get_mention(attacker), get_mention(target))
    header_title = "É¢Ê€á´€á´ á´‡ Ê€á´Ê™Ê™á´‡Ê€Ê" if target['status'] == 'dead' else "Ê€á´Ê™Ê™á´‡Ê€Ê á´„á´á´á´˜ÊŸá´‡á´›á´‡"
    header_emoji = "ðŸ§Ÿ" if target['status'] == 'dead' else "ðŸ’°"

    rob_result = f"ðŸ’° <b>sá´›á´ÊŸá´‡É´!</b> {narration} ðŸ’¸ <b>+{format_money(amount)}</b>"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ’° Ê€á´Ê™ á´€É¢á´€ÉªÉ´", callback_data="game_rob_info"),
            InlineKeyboardButton("ðŸ”ª á´‹ÉªÊŸÊŸ", callback_data="game_kill_info"),
        ],
        [
            InlineKeyboardButton("ðŸ’° á´Ê Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
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
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ›¡ï¸ <b>á´˜Ê€á´á´›á´‡á´„á´›Éªá´É´ sÊœÉªá´‡ÊŸá´…</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ Keep safe from kills & robs!
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ“¦ <b>1 Day:</b> <code>{format_money(PROTECT_1D_COST)}</code>
â•‘ ðŸ“¦ <b>2 Days:</b> <code>{format_money(PROTECT_2D_COST)}</code>
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ“ <b>Usage:</b>
â•‘ <code>/protect 1d</code> - Self
â•‘ <code>/protect 1d @user</code> - Partner
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
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
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ›¡ï¸ <b>á´€ÊŸÊ€á´‡á´€á´…Ê sá´€Ò“á´‡!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ â° <b>Time Left:</b> <code>{format_time(rem)}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•""", parse_mode=ParseMode.HTML)
    
    if sender['balance'] < cost: return await update.effective_message.reply_text(Templates.error_box(f"Need {format_money(cost)}"), parse_mode=ParseMode.HTML)

    users_collection.update_one({"user_id": sender["user_id"]}, {"$inc": {"balance": -cost}})
    expiry_dt = datetime.utcnow() + timedelta(days=days)
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"protection_expiry": expiry_dt}})
    
    partner_id = target.get("partner_id")
    partner_bonus = ""
    if partner_id:
        users_collection.update_one({"user_id": partner_id}, {"$set": {"protection_expiry": expiry_dt}})
        partner_bonus = "\nâ•‘ ðŸ’ž <b>Partner Also Protected!</b>"

    if is_self:
        result = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ›¡ï¸ <b>sÊœÉªá´‡ÊŸá´… á´€á´„á´›Éªá´ á´‡!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ ðŸ”’ You are protected!
â•‘ â° <b>Duration:</b> <code>{days} day(s)</code>{partner_bonus}
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
    else:
        result = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ›¡ï¸ <b>É¢á´œá´€Ê€á´…Éªá´€É´!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ ðŸ”’ Protected {get_mention(target)}
â•‘ â° <b>Duration:</b> <code>{days} day(s)</code>{partner_bonus}
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ’° Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
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
        return await update.effective_message.reply_text(f"âœ¨ <b>Ê€á´‡á´ Éªá´ á´‡á´…!</b>\n\nðŸ’– {target_text} are back by Master's grace! ðŸ‘‘", parse_mode=ParseMode.HTML)

    if reviver['balance'] < REVIVE_COST: 
        return await update.effective_message.reply_text(Templates.error_box(f"Need {format_money(REVIVE_COST)}"), parse_mode=ParseMode.HTML)

    users_collection.update_one({"user_id": reviver["user_id"]}, {"$inc": {"balance": -REVIVE_COST}})
    users_collection.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": REVIVE_COST}})
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "alive", "death_time": None}})
    
    is_self = target['user_id'] == reviver['user_id']
    target_text = "You" if is_self else get_mention(target)

    result = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ’– <b>Ê€á´‡á´ Éªá´ á´‡á´…!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ âœ¨ {target_text} are back!
â•‘ ðŸ’µ <b>Cost:</b> <code>{format_money(REVIVE_COST)}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ›¡ï¸ Ê™á´œÊ á´˜Ê€á´á´›á´‡á´„á´›Éªá´É´", callback_data="game_protect_info"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
        ]
    ])
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

