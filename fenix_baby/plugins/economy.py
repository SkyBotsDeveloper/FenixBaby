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

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from fenix_baby.config import REGISTER_BONUS, OWNER_ID, TAX_RATE, CLAIM_BONUS, MARRIED_TAX_RATE, SHOP_ITEMS, MIN_CLAIM_MEMBERS
from fenix_baby.services.ai_client import ask_ai_raw
from fenix_baby.utils import ensure_user_exists, get_mention, format_money, resolve_target, log_to_channel, stylize_text, track_group
from fenix_baby.database import users_collection, groups_collection

# --- INVENTORY CALLBACK ---
async def inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    data = query.data.split("|")
    item_id = data[1]
    
    item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
    if not item: 
        await query.answer("âŒ Item data not found.", show_alert=True)
        return

    rarity_text = "Common"
    if item['price'] > 100000: rarity_text = "Rare"
    if item['price'] > 1000000: rarity_text = "Legendary"
    if item['price'] > 100000000: rarity_text = "Godly"

    text = (
        f"ðŸ’Ž ð…ð¥ðžð± ðˆð­ðžð¦: {item['name']}\n"
        f"ðŸ’° ð•ðšð¥ð®ðž: {format_money(item['price'])}\n"
        f"ðŸŒŸ ð‘ðšð«ð¢ð­ð²: {rarity_text}\n"
        f"ðŸ›¡ï¸ ð’ð­ðšð­ð®ð¬: Safe (Unless you die!)"
    )
    await query.answer(text, show_alert=True)

# --- COMMANDS ---

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registers a new user (PM Only)."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or not update.effective_message:
        return
    
    # --- FIX: PM ONLY CHECK ---
    if chat.type != ChatType.PRIVATE:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("ðŸš€ Register Here", url=f"https://t.me/{context.bot.username}?start=register")]])
        return await update.effective_message.reply_text(
            "âŒ <b>Fenix Baby!</b> You cannot register in a group!\n"
            "<i>Go to my PM to create your wallet securely.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )

    if users_collection.find_one({"user_id": user.id}): 
        return await update.effective_message.reply_text(f"âœ¨ <b>Ara?</b> {get_mention(user)}, you are already registered!", parse_mode=ParseMode.HTML)
    
    ensure_user_exists(user)
    users_collection.update_one({"user_id": user.id}, {"$set": {"balance": REGISTER_BONUS}})
    
    await update.effective_message.reply_text(
        f"ðŸŽ‰ <b>Yayy!</b> {get_mention(user)} Registered!\n"
        f"ðŸŽ <b>Welcome Bonus:</b> <code>+{format_money(REGISTER_BONUS)}</code>\n"
        f"â„¹ï¸ <i>Use /help to learn how to play!</i>", 
        parse_mode=ParseMode.HTML
    )

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """One-time bonus for groups (Group Only)."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not update.effective_message:
        return
    
    # --- FIX: GROUP ONLY CHECK ---
    if chat.type == ChatType.PRIVATE:
        return await update.effective_message.reply_text("âš ï¸ <b>Fenix Baby!</b> This command is for Group Bonuses only.", parse_mode=ParseMode.HTML)
    
    ensure_user_exists(user)
    
    # Ensure group exists in DB (Fixes 'Not Working' issue)
    track_group(chat, user)
    
    group_doc = groups_collection.find_one({"chat_id": chat.id})
    
    if group_doc and group_doc.get("claimed"): 
        return await update.effective_message.reply_text("âŒ <b>Too late!</b> This group bonus has already been claimed.", parse_mode=ParseMode.HTML)
    
    # Check Member Count
    try: 
        count = await context.bot.get_chat_member_count(chat.id)
    except: 
        return await update.effective_message.reply_text("âš ï¸ I need <b>Admin Rights</b> to verify member count!", parse_mode=ParseMode.HTML)

    if count < MIN_CLAIM_MEMBERS:
        # Generate Roast
        roast = await ask_ai_raw(
            "You are a savage but funny Hinglish roaster.",
            f"Roast {user.first_name} for claiming in a group with only {count} members. Needs {MIN_CLAIM_MEMBERS}.",
        )
        final_roast = roast if roast else "Itna sannaata kyu hai bhai? ðŸ˜‚"
        
        return await update.effective_message.reply_text(
            f"âŒ <b>Claim Failed!</b>\n\n"
            f"ðŸ“‰ <b>Members:</b> {count}/{MIN_CLAIM_MEMBERS}\n"
            f"ðŸ”¥ <b>Roast:</b> <i>{stylize_text(final_roast)}</i>", 
            parse_mode=ParseMode.HTML
        )
    
    # Process Claim
    users_collection.update_one({"user_id": user.id}, {"$inc": {"balance": CLAIM_BONUS}})
    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"claimed": True}})
    
    await update.effective_message.reply_text(
        f"ðŸ’Ž <b>ð‚ð¥ðšð¢ð¦ ð’ð®ðœðœðžð¬ð¬ðŸð®ð¥!</b>\n\n"
        f"ðŸ‘¤ <b>Claimer:</b> {get_mention(user)}\n"
        f"ðŸ’° <b>Reward:</b> <code>+{format_money(CLAIM_BONUS)}</code>\n"
        f"ðŸ† <i>Congratulations! You were the fastest.</i>", 
        parse_mode=ParseMode.HTML
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    target, error = await resolve_target(update, context)
    if not target and error == "No target": target = ensure_user_exists(update.effective_user)
    if not target:
        if update.effective_message:
            await update.effective_message.reply_text(error or "âš ï¸ Error", parse_mode=ParseMode.HTML)
        return

    if target['user_id'] == OWNER_ID:
        return await update.effective_message.reply_text("ðŸ‘‘ <b>Immortal God!</b> Master owns everything.", parse_mode=ParseMode.HTML)

    rank = users_collection.count_documents({"balance": {"$gt": target["balance"]}}) + 1
    status = "ðŸ’– Alive" if target['status'] == 'alive' else "ðŸ’€ Dead"
    
    inventory = target.get('inventory', [])
    weapons = [i for i in inventory if i['type'] == 'weapon']
    armors = [i for i in inventory if i['type'] == 'armor']
    flex_items = [i for i in inventory if i['type'] == 'flex']
    
    best_w = max(weapons, key=lambda x: x['buff']) if weapons else None
    best_a = max(armors, key=lambda x: x['buff']) if armors else None
    
    w_text = f"{best_w['name']} (+{int(best_w['buff']*100)}%)" if best_w else "None"
    a_text = f"{best_a['name']} ({int(best_a['buff']*100)}% Block)" if best_a else "None"
    
    kb = []
    row = []
    for item in flex_items:
        row.append(InlineKeyboardButton(item['name'], callback_data=f"inv_view|{item['id']}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    reply_markup = InlineKeyboardMarkup(kb) if kb else None

    msg = (
        f"ðŸ‘¤ {get_mention(target)} | ðŸ‘› <b>{format_money(target['balance'])}</b>\n"
        f"ðŸ† #{rank} | â¤ï¸ {status} | âš”ï¸ {target['kills']}\n"
        f"ðŸ—¡ï¸ {w_text} / {a_text}"
    )
    
    if flex_items: msg += f"\nðŸ’Ž Flex: {len(flex_items)} items"
    
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_message:
        return
    rich = users_collection.find().sort("balance", -1).limit(10)
    kills = users_collection.find().sort("kills", -1).limit(10)

    def get_badge(i): return ["ðŸ¥‡","ðŸ¥ˆ","ðŸ¥‰"][i-1] if i<=3 else f"<code>{i}.</code>"

    msg = "ðŸ† <b>ð†ð‹ðŽðð€ð‹ ð‹ð„ð€ðƒð„ð‘ððŽð€ð‘ðƒ</b> ðŸ†\n\n"
    msg += "ðŸ’° <b>ð“ð¨ð© ðŸðŸŽ ð‘ð¢ðœð¡ðžð¬ð­:</b>\n"
    for i, d in enumerate(rich, 1): 
        msg += f"{get_badge(i)} {get_mention(d)} Â» <b>{format_money(d['balance'])}</b>\n"
    
    msg += "\nðŸ©¸ <b>ð“ð¨ð© ðŸðŸŽ ðŠð¢ð¥ð¥ðžð«ð¬:</b>\n"
    for i, d in enumerate(kills, 1): 
        msg += f"{get_badge(i)} {get_mention(d)} Â» <b>{d.get('kills',0)} Kills</b>\n"

    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update or not update.effective_user or not update.effective_message:
        return
    sender = ensure_user_exists(update.effective_user)
    if not sender: return
    args = context.args
    if not args: return await update.effective_message.reply_text("âš ï¸ <b>Usage:</b> <code>/give 100 @user</code>", parse_mode=ParseMode.HTML)

    amount = None
    target_str = None
    for arg in args:
        if arg.isdigit() and amount is None: amount = int(arg)
        else: target_str = arg
    
    if amount is None: return await update.effective_message.reply_text("âš ï¸ <b>Error:</b> Amount must be a number.", parse_mode=ParseMode.HTML)

    target, error = await resolve_target(update, context, specific_arg=target_str)
    
    if not target: return await update.effective_message.reply_text(error or "âš ï¸ <b>Tag someone to give coins.</b>", parse_mode=ParseMode.HTML)

    if amount <= 0: return await update.effective_message.reply_text("âš ï¸ Don't be cheeky!", parse_mode=ParseMode.HTML)
    if sender['balance'] < amount: return await update.effective_message.reply_text(f"ðŸ“‰ <b>Poor!</b> You only have <code>{format_money(sender['balance'])}</code>", parse_mode=ParseMode.HTML)
    if sender['user_id'] == target['user_id']: return await update.effective_message.reply_text("ðŸ¤” Sending money to yourself?", parse_mode=ParseMode.HTML)

    current_tax = TAX_RATE
    tax_type = "Standard"
    
    if sender.get("partner_id") == target["user_id"]:
        current_tax = MARRIED_TAX_RATE
        tax_type = "Couple (5%)"

    tax = int(amount * current_tax)
    final_amt = amount - tax
    
    users_collection.update_one({"user_id": sender["user_id"]}, {"$inc": {"balance": -amount}})
    users_collection.update_one({"user_id": target["user_id"]}, {"$inc": {"balance": final_amt}})
    users_collection.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": tax}})

    msg = (
        f"ðŸ’¸ <b>ð“ð«ðšð§ð¬ðŸðžð« ð‚ð¨ð¦ð©ð¥ðžð­ðž!</b>\n"
        f"ðŸ‘¤ <b>From:</b> {get_mention(sender)}\n"
        f"ðŸ‘¤ <b>To:</b> {get_mention(target)}\n"
        f"ðŸ’° <b>Sent:</b> <code>{format_money(final_amt)}</code>\n"
        f"ðŸ¦ <b>Tax:</b> <code>{format_money(tax)}</code> ({tax_type})"
    )
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    await log_to_channel(context.bot, "transfer", {
        "user": f"{get_mention(sender)} (`{sender['user_id']}`)",
        "action": f"Transferred {format_money(amount)} to {get_mention(target)} (Tax: {tax_type})",
        "chat": "Economy System"
    })

