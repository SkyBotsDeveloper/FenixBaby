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

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.utils import ensure_user_exists, format_money
from fenix_baby.database import users_collection

from fenix_baby.config import OWNER_ID, REGISTER_BONUS

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    
    now = datetime.utcnow()
    last = user.get("last_daily")
    
    if last:
        # Check if 24 hours have passed
        if isinstance(last, str):
            last = datetime.fromisoformat(last)
            
        if (now - last) < timedelta(hours=24):
            rem = timedelta(hours=24) - (now - last)
            hours, remainder = divmod(int(rem.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            return await update.message.reply_text(f"â³ <b>Cooldown!</b>\n\nBabu thoda sabar karo! ðŸ˜Š\nWait <code>{hours}h {minutes}m</code> more.", parse_mode=ParseMode.HTML)
    
    streak = user.get("daily_streak", 0)
    # If more than 48 hours, reset streak
    if last and (now - last) > timedelta(hours=48):
        streak = 0
    
    streak += 1
    reward = 500 + (streak * 100) # Incremental reward
    if reward > 5000: reward = 5000 # Cap it
    
    bonus = 10000 if streak % 7 == 0 else 0
    total = reward + bonus
    
    users_collection.update_one(
        {"user_id": user['user_id']},
        {
            "$set": {"last_daily": now, "daily_streak": streak},
            "$inc": {"balance": total}
        }
    )
    
    msg = (
        f"ðŸ“… <b>ðƒðšð¢ð¥ð² ð‘ðžð°ðšð«ð: Day {streak}</b>\n\n"
        f"ðŸ’° <b>Received:</b> <code>{format_money(reward)}</code>\n"
    )
    if bonus:
        msg += f"ðŸŽ‰ <b>Weekly Bonus:</b> <code>{format_money(bonus)}</code>\n"
    
    msg += f"\nâœ¨ Come back tomorrow for more!"
    
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

