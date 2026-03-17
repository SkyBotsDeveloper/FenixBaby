# Copyright (c) 2025 Telegram:- @llFenixxll <llFenixxll>
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.database import users_collection
from fenix_baby.utils import ensure_user_exists, get_mention, format_money, resolve_target
from fenix_baby.config import OWNER_ID

# Duel Storage
active_duels = {}

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_message: return
    sender = ensure_user_exists(update.effective_user)
    
    if not context.args:
        return await update.message.reply_text("⚔️ <b>Duel Arena</b>\n\nUsage: /duel [bet] @user\nExample: /duel 1000 @llFenixxll", parse_mode=ParseMode.HTML)
    
    try: bet = int(context.args[0])
    except: return await update.message.reply_text("❌ Invalid bet amount.")
    
    if bet < 100: return await update.message.reply_text("❌ Minimum bet is 100.")
    if sender['balance'] < bet: return await update.message.reply_text("📉 You don't have enough balance!")

    target_user, error = await resolve_target(update, context, specific_arg=context.args[1] if len(context.args) > 1 else None)
    if not target_user: return await update.message.reply_text(error or "❌ Tag someone to duel!")
    if int(target_user['user_id']) == int(OWNER_ID): return await update.message.reply_text("👑 You cannot challenge the Owner. He is the master of this realm!")
    if target_user['user_id'] == sender['user_id']: return await update.message.reply_text("🤔 Dueling yourself?")
    if target_user['balance'] < bet: return await update.message.reply_text("📉 Target doesn't have enough balance!")

    duel_id = f"{sender['user_id']}_{target_user['user_id']}"
    active_duels[duel_id] = {
        "bet": bet, 
        "expiry": datetime.utcnow() + timedelta(minutes=2),
        "target_id": target_user['user_id']
    }
    
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚔️ Accept Duel", callback_data=f"duel_acc|{sender['user_id']}|{bet}"),
        InlineKeyboardButton("🏳️ Decline", callback_data=f"duel_dec|{sender['user_id']}")
    ]])
    
    await update.message.reply_text(
        f"⚔️ <b>DUEL CHALLENGE!</b>\n\n"
        f"👤 {get_mention(sender)} challenged {get_mention(target_user)}!\n"
        f"💰 <b>Bet:</b> {format_money(bet)}\n\n"
        f"<i>Click below to fight!</i>",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )

async def duel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith("duel_"): return
    
    data = query.data.split("|")
    action = data[0]
    challenger_id = int(data[1])
    
    if action == "duel_acc":
        bet = int(data[2])
        defender = ensure_user_exists(query.from_user)
        challenger = users_collection.find_one({"user_id": challenger_id})
        
        duel_id = f"{challenger_id}_{defender['user_id']}"
        if duel_id not in active_duels:
            return await query.answer("❌ This duel invitation has expired or is invalid.", show_alert=True)
        
        duel_data = active_duels[duel_id]
        if datetime.utcnow() > duel_data["expiry"]:
            del active_duels[duel_id]
            return await query.answer("❌ This duel invitation has expired.", show_alert=True)

        if not challenger or challenger['balance'] < bet:
            return await query.answer("❌ Challenger no longer has enough balance!", show_alert=True)
        if defender['balance'] < bet:
            return await query.answer("❌ You don't have enough balance!", show_alert=True)
            
        # Fight logic
        winner = random.choice([challenger, defender])
        loser = defender if winner['user_id'] == challenger['user_id'] else challenger
        
        users_collection.update_one({"user_id": winner['user_id']}, {"$inc": {"balance": bet}})
        users_collection.update_one({"user_id": loser['user_id']}, {"$inc": {"balance": -bet}})
        
        # Clear duel
        del active_duels[duel_id]

        await query.message.edit_text(
            f"⚔️ <b>DUEL RESULTS</b> ⚔️\n\n"
            f"🏆 <b>Winner:</b> {get_mention(winner)}\n"
            f"💀 <b>Loser:</b> {get_mention(loser)}\n"
            f"💰 <b>Prize:</b> {format_money(bet)}",
            parse_mode=ParseMode.HTML
        )
    elif action == "duel_dec":
        defender = query.from_user
        # Find the active duel to delete it
        duel_to_del = None
        for d_id, d_data in active_duels.items():
            if d_id.startswith(f"{challenger_id}_") and d_data.get("target_id") == defender.id:
                duel_to_del = d_id
                break
        
        if not duel_to_del:
            return await query.answer("❌ No active duel found for you to decline.", show_alert=True)

        del active_duels[duel_to_del]
        await query.message.edit_text(f"🏳️ Duel declined by {get_mention(defender)}.", parse_mode=ParseMode.HTML)

async def lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    cost = 500
    if user['balance'] < cost: return await update.message.reply_text("📉 Lottery ticket costs 500 coins!")
    
    users_collection.update_one({"user_id": user['user_id']}, {"$inc": {"balance": -cost}})
    
    if random.random() < 0.1: # 10% win rate
        win = random.randint(2000, 10000)
        users_collection.update_one({"user_id": user['user_id']}, {"$inc": {"balance": win}})
        await update.message.reply_text(f"🎰 <b>JACKPOT!</b>\n\nYou won <b>{format_money(win)}</b> from the lottery! 🎉", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("🎰 You bought a ticket but didn't win anything this time. Better luck next time! 🍀")

