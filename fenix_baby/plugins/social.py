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
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from fenix_baby.utils import ensure_user_exists, resolve_target, get_mention, format_money, stylize_text
from fenix_baby.database import users_collection
from fenix_baby.config import DIVORCE_COST, BOT_NAME

def get_progress_bar(percent):
    filled = int(percent / 10)
    bar = "â–ˆ" * filled + "â–’" * (10 - filled)
    return bar

def get_love_comment(percent):
    if percent < 30: return "ðŸ’” Terrible!"
    if percent < 60: return "ðŸ¤” Hmm..."
    if percent < 90: return "ðŸ’– Good!"
    return "ðŸ”¥ Soulmates!"

async def couple_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matches users in group."""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == ChatType.PRIVATE: return await update.effective_message.reply_text("âŒ Group Only!", parse_mode=ParseMode.HTML)

    user1 = ensure_user_exists(user)
    
    # Check for specific target
    target_arg = context.args[0] if context.args else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    
    if target:
        user2 = target
        from fenix_baby.config import OWNER_ID
        if int(user2['user_id']) == int(OWNER_ID):
             return await update.effective_message.reply_text("ðŸ‘‘ <b>Blasphemy!</b> You cannot match with the Creator. His heart belongs to the code.", parse_mode=ParseMode.HTML)
    else:
        try:
            # Random Match in Group
            pipeline = [{"$match": {"seen_groups": chat.id, "user_id": {"$ne": user.id}}}, {"$sample": {"size": 1}}]
            results = list(users_collection.aggregate(pipeline))
            if not results: return await update.effective_message.reply_text("ðŸ˜” No one else found here.", parse_mode=ParseMode.HTML)
            user2 = results[0]
        except:
             return await update.effective_message.reply_text("âš ï¸ DB Error", parse_mode=ParseMode.HTML)

    percent = random.randint(0, 100)
    await update.effective_message.reply_text(
        f"ðŸ’˜ <b>Match:</b> {get_mention(user1)} x {get_mention(user2)}\n"
        f"ðŸ“Š <b>{percent}%</b> <code>{get_progress_bar(percent)}</code>\n"
        f"ðŸ’­ <i>{get_love_comment(percent)}</i>",
        parse_mode=ParseMode.HTML
    )

async def propose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = ensure_user_exists(update.effective_user)
    if sender.get("partner_id"): return await update.effective_message.reply_text("âŒ Married!", parse_mode=ParseMode.HTML)
    
    target_arg = context.args[0] if context.args else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    
    if not target: return await update.effective_message.reply_text(error or "âš ï¸ <b>Usage:</b> <code>/propose @user</code>", parse_mode=ParseMode.HTML)
    
    # Owner Protection
    from fenix_baby.config import OWNER_ID
    if int(target['user_id']) == int(OWNER_ID):
        return await update.effective_message.reply_text("ðŸ‘‘ <b>Impossible!</b> The Creator is already married to his work and the universe. You cannot propose to a God.", parse_mode=ParseMode.HTML)
    
    if target['user_id'] == sender['user_id']: return await update.effective_message.reply_text("ðŸ¥² No.", parse_mode=ParseMode.HTML)
    if target.get('partner_id'): return await update.effective_message.reply_text("ðŸ’” Taken.", parse_mode=ParseMode.HTML)

    s_id, t_id = sender['user_id'], target['user_id']
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ’ Accept", callback_data=f"marry_y|{s_id}|{t_id}"), InlineKeyboardButton("ðŸ—‘ï¸ Reject", callback_data=f"marry_n|{s_id}|{t_id}")]])
    
    msg = await update.effective_message.reply_text(f"ðŸ’˜ <b>Proposal!</b>\n{get_mention(sender)} ðŸ’ {get_mention(target)}", reply_markup=kb, parse_mode=ParseMode.HTML)
    
    async def delete():
        await asyncio.sleep(30)
        try: await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text="âŒ Expired.", parse_mode=ParseMode.HTML)
        except: pass
    asyncio.create_task(delete())

async def marry_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_arg = context.args[0] if context.args else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    
    # Check for Owner Target
    from fenix_baby.config import OWNER_ID
    if target and int(target['user_id']) == int(OWNER_ID):
        return await update.effective_message.reply_text("ðŸ‘‘ <b>The Creator is beyond status.</b> His only partnership is with his code.", parse_mode=ParseMode.HTML)
    
    user = target if target else ensure_user_exists(update.effective_user)
    
    pid = user.get("partner_id")
    pname = "None"
    if pid:
        p = users_collection.find_one({"user_id": pid})
        pname = get_mention(p) if p else str(pid)
    
    await update.effective_message.reply_text(f"ðŸ“Š <b>Status:</b>\nðŸ‘¤ {get_mention(user)}\nðŸ’ {pname}", parse_mode=ParseMode.HTML)

async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    if not user.get("partner_id"): return await update.effective_message.reply_text("ðŸ¤·â€â™‚ï¸ Single.", parse_mode=ParseMode.HTML)
    if user['balance'] < DIVORCE_COST: return await update.effective_message.reply_text(f"âŒ Cost: {format_money(DIVORCE_COST)}", parse_mode=ParseMode.HTML)

    pid = user["partner_id"]
    users_collection.update_one({"user_id": user["user_id"]}, {"$set": {"partner_id": None}, "$inc": {"balance": -DIVORCE_COST}})
    users_collection.update_one({"user_id": pid}, {"$set": {"partner_id": None}})
    await update.effective_message.reply_text(f"ðŸ’” <b>Divorced!</b> Paid {format_money(DIVORCE_COST)}.", parse_mode=ParseMode.HTML)

async def proposal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    action, p_id, t_id = data[0], int(data[1]), int(data[2])
    
    if query.from_user.id != t_id: return await query.answer("âŒ Not for you!", show_alert=True)

    if action == "marry_y":
        users_collection.update_one({"user_id": p_id}, {"$set": {"partner_id": t_id}})
        users_collection.update_one({"user_id": t_id}, {"$set": {"partner_id": p_id}})
        await query.message.edit_text(f"ðŸ’ <b>Married!</b>\n<a href='tg://user?id={p_id}'>P1</a> â¤ï¸ <a href='tg://user?id={t_id}'>P2</a>", parse_mode=ParseMode.HTML)
    elif action == "marry_n":
        await query.message.edit_text("âŒ <b>Rejected!</b> Better luck next time. ðŸ’”", parse_mode=ParseMode.HTML)

