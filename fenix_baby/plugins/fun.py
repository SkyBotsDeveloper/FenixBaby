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
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸŽ² <b>á´…Éªá´„á´‡ É¢á´€á´á´‡</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ Roll 4-6 to WIN!
â•‘ Roll 1-3 and LOSE!
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ’µ <b>Min Bet:</b> <code>$50</code>
â•‘ ðŸ“ <b>Usage:</b> <code>/dice [amount]</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
        return await update.message.reply_text(dice_help, parse_mode=ParseMode.HTML)
    
    try: bet = int(context.args[0])
    except: return await update.message.reply_text(Templates.error_box("Invalid bet amount"), parse_mode=ParseMode.HTML)
    
    if bet < 50: return await update.message.reply_text(Templates.warning_box("Min bet is $50"), parse_mode=ParseMode.HTML)
    if user['balance'] < bet: return await update.message.reply_text(Templates.error_box("Not enough money!"), parse_mode=ParseMode.HTML)
    
    # Send the native Dice
    msg = await context.bot.send_dice(chat_id, emoji='ðŸŽ²')
    result = msg.dice.value # 1-6
    
    # Wait for animation
    await asyncio.sleep(3)
    
    dice_faces = {1: "âš€", 2: "âš", 3: "âš‚", 4: "âšƒ", 5: "âš„", 6: "âš…"}
    dice_face = dice_faces.get(result, "ðŸŽ²")
    
    if result > 3: # 4, 5, 6 Wins
        win_amt = bet 
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": win_amt}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸŽ‰ <b>Êá´á´œ á´¡á´É´!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ 
â•‘   {dice_face} <b>Result:</b> {result}
â•‘ 
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ’° <b>Won:</b> <code>+{format_money(win_amt)}</code>
â•‘ ðŸ‘› <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
    else: # 1, 2, 3 Loses
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -bet}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸ’€ <b>Êá´á´œ ÊŸá´sá´›!</b>  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ 
â•‘   {dice_face} <b>Result:</b> {result}
â•‘ 
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ“‰ <b>Lost:</b> <code>-{format_money(bet)}</code>
â•‘ ðŸ‘› <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸŽ² á´˜ÊŸá´€Ê á´€É¢á´€ÉªÉ´", callback_data="game_dice_info"),
            InlineKeyboardButton("ðŸŽ° sÊŸá´á´›s", callback_data="game_slots_info"),
        ],
        [
            InlineKeyboardButton("ðŸ’° Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
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
    msg = await context.bot.send_dice(chat_id, emoji='ðŸŽ°')
    value = msg.dice.value 
    
    await asyncio.sleep(2) # Wait for spin
    
    # Winning logic based on Telegram API values
    if value == 64: # 777
        prize = bet * 10
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸŽ°âœ¨ <b>á´Šá´€á´„á´‹á´˜á´á´›!</b> âœ¨ðŸŽ°  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘                           
â•‘     ðŸ”” ðŸ”” ðŸ””     
â•‘     <b>7  7  7</b>      
â•‘                           
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸŽ‰ <b>Won:</b> <code>+{format_money(prize)}</code>
â•‘ ðŸ‘› <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
    elif value in [1, 22, 43]: # 3 matching fruits
        prize = bet * 3
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸŽ° <b>á´¡ÉªÉ´É´á´‡Ê€!</b> ðŸŽ°  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘                           
â•‘     ðŸ’ ðŸ’ ðŸ’     
â•‘                           
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ’° <b>Won:</b> <code>+{format_money(prize)}</code>
â•‘ ðŸ‘› <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""
    else:
        updated_user = users_collection.find_one({"user_id": user["user_id"]})
        
        result_text = f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  ðŸŽ° <b>É´á´ ÊŸá´œá´„á´‹!</b> ðŸŽ°  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘                           
â•‘     ðŸ‹ ðŸ’ ðŸ‡     
â•‘                           
â• â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â•£
â•‘ ðŸ“‰ <b>Lost:</b> <code>-{format_money(bet)}</code>
â•‘ ðŸ‘› <b>Balance:</b> <code>{format_money(updated_user['balance'])}</code>
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸŽ° sá´˜ÉªÉ´ á´€É¢á´€ÉªÉ´", callback_data="game_slots_info"),
            InlineKeyboardButton("ðŸŽ² á´…Éªá´„á´‡", callback_data="game_dice_info"),
        ],
        [
            InlineKeyboardButton("ðŸ’° Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸ  á´á´‡É´á´œ", callback_data="return_start"),
        ]
    ])

    await update.message.reply_text(result_text, reply_to_message_id=msg.message_id, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def catch_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guide for /catch command."""
    guide_text = """
ðŸ“– <b>Êœá´á´¡ á´›á´ á´„á´€á´›á´„Êœ á´¡á´€ÉªÒ“á´œs</b>

1. Stay active in groups! Waifus appear randomly after several messages.
2. When a waifu appears, look at her image/name.
3. Use <code>/catch [name]</code> to guess and claim her!
4. If you guess right, she's yours! ðŸŽ‰

âœ¨ <b>á´›Éªá´˜:</b> Be the fastest to type the name correctly!
    """
    await update.message.reply_text(guide_text, parse_mode=ParseMode.HTML)

