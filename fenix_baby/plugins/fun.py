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
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.utils import ensure_user_exists, get_mention, format_money
from fenix_baby.database import users_collection
from fenix_baby.ui.components import Templates, Buttons

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Real Telegram Dice with enhanced UI."""
    user = ensure_user_exists(update.effective_user)
    chat_id = update.effective_chat.id
    
    if not context.args: 
        dice_help = """
╔═══════════════════════╗
║  🎲 <b>dice game</b>  ║
╠═══════════════════════╣
║ Roll 4-6 to WIN!
║ Roll 1-3 and LOSE!
╠───────────────────────╣
║ 💵 <b>Min Bet:</b> <code>$50</code>
║ 📝 <b>Usage:</b> <code>/dice [amount]</code>
╚═══════════════════════╝"""
        return await update.message.reply_text(dice_help, parse_mode=ParseMode.HTML)
    
    try: bet = int(context.args[0])
    except: return await update.message.reply_text(Templates.error_box("Invalid bet amount"), parse_mode=ParseMode.HTML)
    
    if bet < 50: return await update.message.reply_text(Templates.warning_box("Min bet is $50"), parse_mode=ParseMode.HTML)
    if user['balance'] < bet: return await update.message.reply_text(Templates.error_box("Not enough money!"), parse_mode=ParseMode.HTML)
    
    # Send the native Dice
    msg = await context.bot.send_dice(chat_id, emoji='🎲')
    result = msg.dice.value # 1-6
    
    # Wait for animation
    await asyncio.sleep(3)
    
    dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    dice_face = dice_faces.get(result, "🎲")
    
    if result > 3: # 4, 5, 6 Wins
        win_amt = bet 
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": win_amt}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
╔═══════════════════════╗
║  🎉 <b>you won!</b>  ║
╠═══════════════════════╣
║ 
║   {dice_face} <b>Result:</b> {result}
║ 
╠───────────────────────╣
║ 💰 <b>Won:</b> <code>+{format_money(win_amt)}</code>
║ 👛 <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
╚═══════════════════════╝"""
    else: # 1, 2, 3 Loses
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -bet}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
╔═══════════════════════╗
║  💀 <b>you lost!</b>  ║
╠═══════════════════════╣
║ 
║   {dice_face} <b>Result:</b> {result}
║ 
╠───────────────────────╣
║ 📉 <b>Lost:</b> <code>-{format_money(bet)}</code>
║ 👛 <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
╚═══════════════════════╝"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎲 play again", callback_data="game_dice_info"),
            InlineKeyboardButton("🎰 slots", callback_data="game_slots_info"),
        ],
        [
            InlineKeyboardButton("💰 balance", callback_data="quick_bal"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])

    await update.message.reply_text(result_text, reply_to_message_id=msg.message_id, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Real Telegram Slots with enhanced UI."""
    user = ensure_user_exists(update.effective_user)
    chat_id = update.effective_chat.id
    bet = 100 # Fixed bet
    
    if user['balance'] < bet: 
        return await update.message.reply_text(Templates.error_box("Need $100 to spin!"), parse_mode=ParseMode.HTML)
    
    users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -bet}})
    
    # Send native Slot Machine
    msg = await context.bot.send_dice(chat_id, emoji='🎰')
    value = msg.dice.value 
    
    await asyncio.sleep(2) # Wait for spin
    
    # Winning logic based on Telegram API values
    if value == 64: # 777
        prize = bet * 10
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
╔═══════════════════════════╗
║  🎰✨ <b>jackpot!</b> ✨🎰  ║
╠═══════════════════════════╣
║                           
║     🔔 🔔 🔔     
║     <b>7  7  7</b>      
║                           
╠───────────────────────────╣
║ 🎉 <b>Won:</b> <code>+{format_money(prize)}</code>
║ 👛 <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
╚═══════════════════════════╝"""
    elif value in [1, 22, 43]: # 3 matching fruits
        prize = bet * 3
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
╔═══════════════════════════╗
║  🎰 <b>winner!</b> 🎰  ║
╠═══════════════════════════╣
║                           
║     🍒 🍒 🍒     
║                           
╠───────────────────────────╣
║ 💰 <b>Won:</b> <code>+{format_money(prize)}</code>
║ 👛 <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
╚═══════════════════════════╝"""
    else:
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
╔═══════════════════════════╗
║  🎰 <b>no luck!</b> 🎰  ║
╠═══════════════════════════╣
║                           
║     🍋 🍒 🍇     
║                           
╠───────────────────────────╣
║ 📉 <b>Lost:</b> <code>-{format_money(bet)}</code>
║ 👛 <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
╚═══════════════════════════╝"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎰 spin again", callback_data="game_slots_info"),
            InlineKeyboardButton("🎲 dice", callback_data="game_dice_info"),
        ],
        [
            InlineKeyboardButton("💰 balance", callback_data="quick_bal"),
            InlineKeyboardButton("🏠 menu", callback_data="return_start"),
        ]
    ])

    await update.message.reply_text(result_text, reply_to_message_id=msg.message_id, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def catch_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guide for /catch command."""
    guide_text = """
📖 <b>how to catch waifus</b>

1. Stay active in groups! Waifus appear randomly after several messages.
2. When a waifu appears, look at her image/name.
3. Use <code>/catch [name]</code> to guess and claim her!
4. If you guess right, she's yours! 🎉

✨ <b>tip:</b> Be the fastest to type the name correctly!
    """
    await update.message.reply_text(guide_text, parse_mode=ParseMode.HTML)

