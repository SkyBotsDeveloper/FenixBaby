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

import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden, BadRequest
from fenix_baby.utils import SUDO_USERS
from fenix_baby.database import users_collection, groups_collection

logger = logging.getLogger(__name__)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS: return
    
    args = context.args
    reply = update.message.reply_to_message
    
    if not args and not reply:
        return await update.message.reply_text(
            "📢 <b>Broadcast Manager</b>\n\n"
            "<b>Usage:</b>\n"
            "‣ /broadcast -user (Reply to msg)\n"
            "‣ /broadcast -group (Reply to msg)\n\n"
            "<b>Flags:</b>\n"
            "‣ -clean : Copy msg (Use for Buttons)",
            parse_mode=ParseMode.HTML
        )
    
    target_type = "user" if "-user" in args else "group" if "-group" in args else None
    if not target_type:
        return await update.message.reply_text("⚠️ Missing flag: <code>-user</code> or <code>-group</code>", parse_mode=ParseMode.HTML)

    is_clean = "-clean" in args
    
    msg_text = None
    if not reply:
        clean_args = [a for a in args if a not in ["-user", "-group", "-clean"]]
        if not clean_args: return await update.message.reply_text("⚠️ Give me a message or reply to one.", parse_mode=ParseMode.HTML)
        msg_text = " ".join(clean_args)

    status_msg = await update.message.reply_text(f"⏳ <b>Broadcasting to {target_type}s...</b>", parse_mode=ParseMode.HTML)
    
    count = 0
    failed = 0
    targets = list(users_collection.find({})) if target_type == "user" else list(groups_collection.find({}))
    total_targets = len(targets)
    
    for doc in targets:
        cid = doc.get("user_id") if target_type == "user" else doc.get("chat_id")
        if not cid: continue
        try:
            if reply:
                if is_clean: await reply.copy(cid)
                else: await reply.forward(cid)
            else:
                await context.bot.send_message(chat_id=cid, text=msg_text, parse_mode=ParseMode.HTML)
            
            count += 1
            if count % 20 == 0: await asyncio.sleep(1)
        except (Forbidden, BadRequest) as e:
            failed += 1
            err_msg = str(e).lower()
            if "chat not found" in err_msg or "bot was blocked" in err_msg or "user is deactivated" in err_msg or isinstance(e, Forbidden):
                if target_type == "user": users_collection.delete_one({"user_id": cid})
                else: groups_collection.delete_one({"chat_id": cid})
            else:
                logger.error(f"Broadcast API error for {cid}: {e}")
        except Exception as e: 
            failed += 1
            logger.error(f"Broadcast unexpected error for {cid}: {e}")
        
    final_text = (
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📊 <b>Statistics:</b>\n"
        f"‣ Total Targets: {total_targets}\n"
        f"‣ Successfully Sent: {count}\n"
        f"‣ Failed/Blocked: {failed}\n"
        f"‣ Target Type: {target_type.title()}"
    )
    try:
        await status_msg.edit_text(final_text, parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text(final_text, parse_mode=ParseMode.HTML)

