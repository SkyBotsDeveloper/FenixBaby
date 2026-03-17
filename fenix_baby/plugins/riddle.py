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

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from fenix_baby.services.ai_client import ask_ai_raw
from fenix_baby.database import riddles_collection, users_collection
from fenix_baby.utils import format_money, ensure_user_exists, get_mention
from fenix_baby.config import RIDDLE_REWARD

async def riddle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new AI riddle."""
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE: return await update.message.reply_text("âŒ Group Only!", parse_mode=ParseMode.HTML)

    # Check active riddle
    if riddles_collection.find_one({"chat_id": chat.id}):
        return await update.message.reply_text("âš ï¸ A riddle is already active! Guess it.", parse_mode=ParseMode.HTML)

    msg = await update.message.reply_text("ðŸ§  <b>Generating AI Riddle...</b>", parse_mode=ParseMode.HTML)

    # Generate
    prompt = "Generate a short, hard riddle. Format: 'Riddle: [Question] | Answer: [OneWordAnswer]'. Do not add anything else."
    response = await ask_ai_raw(
        system_prompt="You are a riddle master. Return concise riddles exactly in the requested format.",
        user_input=prompt,
    )
    
    if not response or "|" not in response:
        return await msg.edit_text("âš ï¸ AI Brain Freeze. Try again.", parse_mode=ParseMode.HTML)

    try:
        parts = response.split("|")
        question = parts[0].replace("Riddle:", "").strip()
        answer = parts[1].replace("Answer:", "").strip().lower()
    except:
        return await msg.edit_text("âš ï¸ AI Error.", parse_mode=ParseMode.HTML)

    # Save
    riddles_collection.insert_one({"chat_id": chat.id, "answer": answer})

    await msg.edit_text(
        f"ðŸ§© <b>ð€ðˆ ð‘ð¢ððð¥ðž ð‚ð¡ðšð¥ð¥ðžð§ð ðž!</b>\n\n"
        f"<i>{question}</i>\n\n"
        f"ðŸ’¡ <b>Reward:</b> <code>{format_money(RIDDLE_REWARD)}</code>\n"
        f"ðŸ‘‡ <i>Reply with your answer!</i>",
        parse_mode=ParseMode.HTML
    )

async def check_riddle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks user messages for the answer."""
    if not update.message or not update.message.text: return
    chat = update.effective_chat
    text = update.message.text.strip().lower()

    riddle = riddles_collection.find_one({"chat_id": chat.id})
    if not riddle: return

    if text == riddle['answer']:
        user = update.effective_user
        ensure_user_exists(user)
        
        # Winner
        users_collection.update_one({"user_id": user.id}, {"$inc": {"balance": RIDDLE_REWARD}})
        riddles_collection.delete_one({"chat_id": chat.id})
        
        await update.message.reply_text(
            f"ðŸŽ‰ <b>ð‚ð¨ð«ð«ðžðœð­!</b>\n\n"
            f"ðŸ‘¤ <b>Winner:</b> {get_mention(user)}\n"
            f"ðŸ’° <b>Won:</b> <code>{format_money(RIDDLE_REWARD)}</code>\n"
            f"ðŸ”‘ <b>Answer:</b> <i>{riddle['answer'].title()}</i>",
            parse_mode=ParseMode.HTML
        )

