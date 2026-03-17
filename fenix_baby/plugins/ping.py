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

import time
import psutil
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError
from fenix_baby.config import START_TIME, BOT_NAME

def get_readable_time(seconds: int) -> str:
    count = 0
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        time_list.pop()

    time_list.reverse()
    return ":".join(time_list)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks API Latency and System Stats."""
    if not update.message: return
    
    try:
        start_time = time.time()
        # Send initial message (Plain text is faster/safer)
        msg = await update.message.reply_text("âš¡ á´„ÊœÑ”á´„á´‹ÉªÎ·É¢...", quote=True)
        end_time = time.time()
        
        # Calculate Latency
        latency = round((end_time - start_time) * 1000)
        
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("ðŸ“¡ sÊsá´›Ñ”Ï» sá´›á´§á´›s", callback_data="sys_stats")
        ]])
        
        await msg.edit_text(
            f"ðŸ“ <b>á´˜ÏƒÎ·É¢!</b>\n\n"
            f"ðŸ“¶ <b>ÊŸá´§á´›Ñ”Î·á´„Ê:</b> <code>{latency}ms</code>\n"
            f"ðŸ¤– <b>sá´›á´§á´›Ï…s:</b> ðŸŸ¢ ÏƒÎ·ÊŸÉªÎ·Ñ”\n"
            f"<i>á´„ÊŸÉªá´„á´‹ Ê™Ñ”ÊŸÏƒá´¡ Ò“Ïƒê› sÑ”ê›á´ Ñ”ê› sá´›á´§á´›s!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
    except TelegramError:
        # If bot can't send message to group (Restricted), fail silently or log it
        print(f"âš ï¸ á´˜ÉªÎ·É¢ Ò’á´§ÉªÊŸÑ”á´… ÉªÎ· á´„Êœá´§á´› {update.effective_chat.id} (Permissions?)")
    except Exception as e:
        print(f"âŒ á´˜ÉªÎ·É¢ á´„ê›Éªá´›Éªá´„á´§ÊŸ Ð„ê›ê›Ïƒê›: {e}")

async def ping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data != "sys_stats": return
    
    try:
        uptime = get_readable_time(int(time.time() - START_TIME))
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        # Check LOCAL disk usage (Current Folder)
        disk = psutil.disk_usage(os.getcwd()).percent
        
        # Popups do NOT support HTML, must be plain text
        text = (
            f"ðŸ’ž {BOT_NAME} sá´›á´§á´›s ðŸ“Š\n\n"
            f"â° Ï…á´˜á´›ÉªÏ»Ñ”: {uptime}\n"
            f"ðŸ§  êšá´§Ï»: {ram}%\n"
            f"âš™ï¸ á´„á´˜Ï…: {cpu}%\n"
            f"ðŸ’¾ á´…Éªsá´‹: {disk}%"
        )
        
        await query.answer(text, show_alert=True)
    except Exception as e:
        await query.answer("âŒ Error fetching stats", show_alert=True)

