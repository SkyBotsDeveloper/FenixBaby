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
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from fenix_baby.database import groups_collection
from fenix_baby.utils import get_mention, ensure_user_exists
from fenix_baby.config import WELCOME_IMG_URL, BOT_NAME, START_IMG_URL, SUPPORT_GROUP

async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/Disable Welcomes."""
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("ðŸ¼ <b>á´›ÊœÉªs á´„ÏƒÏ»Ï»á´§Î·á´… á´¡Ïƒê›á´‹s ÉªÎ· É¢ê›á´˜ ÏƒÎ·ÊŸÊ Ê™á´§Ê™Ê!</b>", parse_mode=ParseMode.HTML)
    
    member = await chat.get_member(user.id)
    if member.status not in ['administrator', 'creator']:
        return await update.message.reply_text("âŒ <b>á´§á´…Ï»ÉªÎ· ÏƒÎ·ÊŸÊ!</b>", parse_mode=ParseMode.HTML)

    if not args:
        return await update.message.reply_text("âš ï¸ <b>Usage:</b> <code>/welcome on</code> or <code>off</code>", parse_mode=ParseMode.HTML)
    
    state = args[0].lower()
    if state in ['on', 'enable', 'yes']:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": True}}, upsert=True)
        await update.message.reply_text("âœ… <b>á´¡Ñ”ÊŸá´„ÏƒÏ»Ñ” Ï»Ñ”ssá´§É¢Ñ” Ñ”Î·á´§Ê™ÊŸÑ”á´…!</b>", parse_mode=ParseMode.HTML)
    elif state in ['off', 'disable', 'no']:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": False}}, upsert=True)
        await update.message.reply_text("âŒ <b>á´¡Ñ”ÊŸá´„ÏƒÏ»Ñ” Ï»Ñ”ssá´§É¢Ñ” á´…Éªsá´§Ê™ÊŸÑ”á´…!</b>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("âš ï¸ Invalid option. Use <code>on</code> or <code>off</code>.", parse_mode=ParseMode.HTML)

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    for member in update.message.new_chat_members:
        # --- ðŸ¤– BOT ADDED TO GROUP ---
        if member.id == context.bot.id:
            adder = update.message.from_user
            ensure_user_exists(adder)
            
            groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": True, "title": chat.title}}, upsert=True)
            
            txt = (
                f"ðŸŒ¸á´›Êœá´§Î·x Ò“Ïƒê› á´§á´…á´…ÉªÎ·É¢<b>ðŸ’« {get_mention(adder)}!</b>\n\n"
                f"ðŸ“¢ Ò“Ïƒê› á´§á´…á´…ÉªÎ·É¢ <b>{chat.title}</b>! âœ¨\n\n"
                f"ðŸŽ <b>Ò’Éªê›sá´› á´›ÉªÏ»Ñ” Ê™ÏƒÎ·Ï…s:</b>\n"
                f"Type <code>/claim</code> fast to get 2,000 Coins!\n"
                f"(Only the first person gets it!)"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ’¬ sÏ…á´˜á´˜Ïƒê›á´›", url=SUPPORT_GROUP)]]) if SUPPORT_GROUP else None
            
            # Use Welcome Image (gyi5iu.jpg) for this interaction
            try: await update.message.reply_photo(WELCOME_IMG_URL, caption=txt, parse_mode=ParseMode.HTML, reply_markup=kb)
            except: await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

        # --- ðŸ‘¤ USER JOINED GROUP ---
        else:
            ensure_user_exists(member)
            group_data = groups_collection.find_one({"chat_id": chat.id})
            
            if group_data and group_data.get("welcome_enabled"):
                greetings = ["ÊœÑ”ÊŸÊŸÏƒ", "ÊœÉªÉªÉª", "á´¡Ñ”ÊŸá´„ÏƒÏ»Ñ”", "É¢ê›ÏƒÏ…á´˜ Ï»Ñ” sá´¡á´§É¢á´§á´› Êœá´§Éª"]
                greet = random.choice(greetings)
                txt = f"ðŸ’ž <b>{greet} {get_mention(member)}!</b>\n\ná´¡Ñ”ÊŸá´„ÏƒÏ»Ñ” á´›Ïƒ <b>{chat.title}</b> ðŸŒ¸\nDon't forget to /register!"
                try: await update.message.reply_photo(WELCOME_IMG_URL, caption=txt, parse_mode=ParseMode.HTML)
                except: await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

