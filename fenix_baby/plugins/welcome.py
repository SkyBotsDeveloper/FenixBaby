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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from fenix_baby.config import BOT_NAME, SUPPORT_GROUP, WELCOME_IMG_URL
from fenix_baby.database import groups_collection
from fenix_baby.utils import ensure_user_exists, get_mention


async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable or disable welcome messages in groups."""
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text(
            "🍼 <b>This command works in groups only.</b>",
            parse_mode=ParseMode.HTML,
        )

    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text(
            "❌ <b>Admins only.</b>",
            parse_mode=ParseMode.HTML,
        )

    if not args:
        return await update.message.reply_text(
            "⚠️ <b>Usage:</b> <code>/welcome on</code> or <code>/welcome off</code>",
            parse_mode=ParseMode.HTML,
        )

    state = args[0].lower()
    if state in ["on", "enable", "yes"]:
        groups_collection.update_one(
            {"chat_id": chat.id},
            {"$set": {"welcome_enabled": True}},
            upsert=True,
        )
        await update.message.reply_text(
            "✅ <b>Welcome messages enabled.</b>",
            parse_mode=ParseMode.HTML,
        )
    elif state in ["off", "disable", "no"]:
        groups_collection.update_one(
            {"chat_id": chat.id},
            {"$set": {"welcome_enabled": False}},
            upsert=True,
        )
        await update.message.reply_text(
            "❌ <b>Welcome messages disabled.</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            "⚠️ Invalid option. Use <code>on</code> or <code>off</code>.",
            parse_mode=ParseMode.HTML,
        )


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            adder = update.message.from_user
            ensure_user_exists(adder)

            groups_collection.update_one(
                {"chat_id": chat.id},
                {"$set": {"welcome_enabled": True, "title": chat.title}},
                upsert=True,
            )

            text = (
                f"🌸 <b>Thanks for adding {BOT_NAME}!</b>\n\n"
                f"💫 Added by: {get_mention(adder)}\n"
                f"📢 Group: <b>{chat.title}</b>\n\n"
                f"🎁 <b>First claim bonus:</b>\n"
                f"Use <code>/claim</code> quickly to grab 2,000 coins.\n"
                f"<i>Only the first person gets it.</i>"
            )
            keyboard = None
            if SUPPORT_GROUP:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP)]]
                )

            try:
                await update.message.reply_photo(
                    WELCOME_IMG_URL,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception:
                await update.message.reply_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            continue

        ensure_user_exists(member)
        group_data = groups_collection.find_one({"chat_id": chat.id})

        if group_data and group_data.get("welcome_enabled"):
            greeting = random.choice(["Hello", "Hey", "Welcome", "Glad you're here"])
            text = (
                f"💞 <b>{greeting}, {get_mention(member)}!</b>\n\n"
                f"Welcome to <b>{chat.title}</b> 🌸\n"
                "Don't forget to /register."
            )
            try:
                await update.message.reply_photo(
                    WELCOME_IMG_URL,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await update.message.reply_text(text, parse_mode=ParseMode.HTML)
