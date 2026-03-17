import random
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.utils import ensure_user_exists, get_mention, format_money
from fenix_baby.database import users_collection, db
from fenix_baby.ui.components import Templates, Buttons, back_button

heists_collection = db["heists"]

HEIST_COST = 500
HEIST_COOLDOWN = 300
HEIST_MIN_PLAYERS = 1
HEIST_MAX_PLAYERS = 5
HEIST_DURATION = 60

TARGETS = [
    {"name": "🏪 Convenience Store", "difficulty": 1, "base_reward": 1000, "success_rate": 0.8},
    {"name": "🏦 Local Bank", "difficulty": 2, "base_reward": 5000, "success_rate": 0.6},
    {"name": "💎 Jewelry Store", "difficulty": 3, "base_reward": 10000, "success_rate": 0.5},
    {"name": "🏛️ Central Bank", "difficulty": 4, "base_reward": 25000, "success_rate": 0.35},
    {"name": "🎰 Casino Vault", "difficulty": 5, "base_reward": 50000, "success_rate": 0.25},
]

ROLES = [
    {"id": "hacker", "name": "💻 Hacker", "bonus": 0.15, "desc": "Disables security (+15% success)"},
    {"id": "driver", "name": "🚗 Driver", "bonus": 0.10, "desc": "Fast getaway (+10% success)"},
    {"id": "muscle", "name": "💪 Muscle", "bonus": 0.20, "desc": "Intimidation (+20% success)"},
    {"id": "insider", "name": "🕵️ Insider", "bonus": 0.25, "desc": "Inside info (+25% success)"},
]

SUCCESS_MESSAGES = [
    "The crew executed the heist flawlessly! 🎉",
    "Perfect execution! The guards didn't see it coming! 💰",
    "Like taking candy from a baby! Clean getaway! 🚗💨",
    "The vault was no match for this crew! 🔓",
]

FAIL_MESSAGES = [
    "Alarm triggered! The crew barely escaped! 🚨",
    "Security was too tight! Had to abort! 🛑",
    "Someone tripped the laser! Mission failed! ❌",
    "The cops showed up early! Everyone scattered! 🚔",
]

async def heist_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    chat_id = update.effective_chat.id
    
    active_heist = heists_collection.find_one({
        "chat_id": chat_id,
        "status": "planning",
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if active_heist:
        return await show_active_heist(update, context, active_heist)
    
    text = Templates.info_card(
        "🏦 HEIST PLANNING",
        f"""┃ 💰 Entry Fee: <code>${HEIST_COST}</code>
┃ 👥 Players: {HEIST_MIN_PLAYERS}-{HEIST_MAX_PLAYERS}
┃ ⏱️ Planning: {HEIST_DURATION}s
┃
┃ <i>Choose a target and recruit</i>
┃ <i>your crew for the big score!</i>""",
        "Bigger risks = Bigger rewards!"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{t['name']} (${t['base_reward']:,})", callback_data=f"heist_start_{i}")]
        for i, t in enumerate(TARGETS)
    ] + [[Buttons.back("menu_games")]])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception as e:
            if "Message is not modified" in str(e): return
            try: await update.callback_query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except: pass
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def show_active_heist(update: Update, context: ContextTypes.DEFAULT_TYPE, heist: dict):
    target = TARGETS[heist["target_idx"]]
    crew = heist.get("crew", [])
    time_left = (heist["expires_at"] - datetime.utcnow()).seconds
    
    crew_text = "\n".join([f"┃ • {m['name']} ({m['role']})" for m in crew]) or "┃ <i>No members yet...</i>"
    
    total_bonus = sum(next((r["bonus"] for r in ROLES if r["id"] == m.get("role_id", "")), 0) for m in crew)
    success_chance = min(0.95, target["success_rate"] + total_bonus)
    
    text = Templates.info_card(
        f"🏦 HEIST: {target['name']}",
        f"""┃ 💎 Reward: <code>${target['base_reward']:,}</code>
┃ 📊 Success: <code>{int(success_chance*100)}%</code>
┃ ⏱️ Time: <code>{time_left}s</code>
┃
┃ <b>CREW ({len(crew)}/{HEIST_MAX_PLAYERS}):</b>
{crew_text}""",
        f"Entry: ${HEIST_COST}"
    )
    
    keyboard = []
    if len(crew) < HEIST_MAX_PLAYERS:
        keyboard.append([InlineKeyboardButton("🎭 join crew", callback_data=f"heist_join_{heist['_id']}")])
    
    if len(crew) >= HEIST_MIN_PLAYERS:
        keyboard.append([InlineKeyboardButton("🚀 start heist", callback_data=f"heist_execute_{heist['_id']}")])
    
    keyboard.append([Buttons.back("menu_games")])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            if "Message is not modified" in str(e): return
            try: await update.callback_query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
            except: pass
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def heist_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_idx = int(query.data.split("_")[-1])
    target = TARGETS[target_idx]
    user = ensure_user_exists(query.from_user)
    chat_id = update.effective_chat.id
    
    existing = heists_collection.find_one({
        "chat_id": chat_id,
        "status": "planning",
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if existing:
        return await query.answer("⚠️ A heist is already being planned!", show_alert=True)
    
    if user["balance"] < HEIST_COST:
        return await query.answer(f"❌ Need ${HEIST_COST} to start!", show_alert=True)
    
    users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -HEIST_COST}})
    
    heist = {
        "chat_id": chat_id,
        "target_idx": target_idx,
        "status": "planning",
        "leader_id": user["user_id"],
        "crew": [{
            "user_id": user["user_id"],
            "name": get_mention(user),
            "role": "👑 Leader",
            "role_id": "leader"
        }],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=HEIST_DURATION)
    }
    
    result = heists_collection.insert_one(heist)
    heist["_id"] = result.inserted_id
    
    await show_active_heist(update, context, heist)

async def heist_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = ensure_user_exists(query.from_user)
    
    try:
        heist_id = ObjectId(query.data.split("_")[-1])
    except:
        return await query.answer("❌ Invalid heist!", show_alert=True)
    
    heist = heists_collection.find_one({"_id": heist_id, "status": "planning"})
    
    if not heist:
        return await query.answer("❌ Heist expired or started!", show_alert=True)
    
    if any(m["user_id"] == user["user_id"] for m in heist.get("crew", [])):
        return await query.answer("⚠️ Already in crew!", show_alert=True)
    
    if len(heist.get("crew", [])) >= HEIST_MAX_PLAYERS:
        return await query.answer("❌ Crew is full!", show_alert=True)
    
    if user["balance"] < HEIST_COST:
        return await query.answer(f"❌ Need ${HEIST_COST}!", show_alert=True)
    
    role = random.choice(ROLES)
    
    users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -HEIST_COST}})
    
    heists_collection.update_one(
        {"_id": heist_id},
        {"$push": {"crew": {
            "user_id": user["user_id"],
            "name": get_mention(user),
            "role": role["name"],
            "role_id": role["id"]
        }}}
    )
    
    await query.answer(f"✅ Joined as {role['name']}!")
    
    heist = heists_collection.find_one({"_id": heist_id})
    await show_active_heist(update, context, heist)

async def heist_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        heist_id = ObjectId(query.data.split("_")[-1])
    except:
        return await query.answer("❌ Invalid heist!", show_alert=True)
    
    heist = heists_collection.find_one({"_id": heist_id, "status": "planning"})
    
    if not heist:
        return await query.answer("❌ Heist not found!", show_alert=True)
    
    if query.from_user.id != heist["leader_id"]:
        return await query.answer("❌ Only the leader can start!", show_alert=True)
    
    heists_collection.update_one({"_id": heist_id}, {"$set": {"status": "executing"}})
    
    target = TARGETS[heist["target_idx"]]
    crew = heist.get("crew", [])
    
    total_bonus = sum(next((r["bonus"] for r in ROLES if r["id"] == m.get("role_id", "")), 0) for m in crew)
    crew_bonus = len(crew) * 0.05
    success_chance = min(0.95, target["success_rate"] + total_bonus + crew_bonus)
    
    try:
        await query.edit_message_text(
            f"""
╔{'═'*22}╗
║  🏦 <b>HEIST IN PROGRESS</b>
╠{'═'*22}╣
║  🎯 Target: {target['name']}
║  👥 Crew: {len(crew)} members
║  
║  ⏳ <i>Executing plan...</i>
╚{'═'*22}╝""",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        if "Message is not modified" in str(e): pass
        else:
            try:
                await query.edit_message_caption(
                    caption=f"""
╔{'═'*22}╗
║  🏦 <b>HEIST IN PROGRESS</b>
╠{'═'*22}╣
║  🎯 Target: {target['name']}
║  👥 Crew: {len(crew)} members
║  
║  ⏳ <i>Executing plan...</i>
╚{'═'*22}╝""",
                    parse_mode=ParseMode.HTML
                )
            except: pass
    
    await asyncio.sleep(3)
    
    success = random.random() < success_chance
    
    if success:
        base_reward = target["base_reward"]
        bonus_mult = 1 + (len(crew) - 1) * 0.1
        total_reward = int(base_reward * bonus_mult)
        per_player = total_reward // len(crew)
        
        for member in crew:
            users_collection.update_one(
                {"user_id": member["user_id"]},
                {"$inc": {"balance": per_player, "heists_won": 1}}
            )
        
        crew_names = "\n".join([f"║  • {m['name']}: +${per_player:,}" for m in crew])
        
        result_text = f"""
╔{'═'*22}╗
║  🎉 <b>HEIST SUCCESS!</b>
╠{'═'*22}╣
║  🎯 {target['name']}
║  💰 Total: <code>${total_reward:,}</code>
║
║  <b>PAYOUTS:</b>
{crew_names}
╠{'═'*22}╣
║  <i>{random.choice(SUCCESS_MESSAGES)}</i>
╚{'═'*22}╝"""
    else:
        for member in crew:
            users_collection.update_one(
                {"user_id": member["user_id"]},
                {"$inc": {"heists_lost": 1}}
            )
        
        result_text = f"""
╔{'═'*22}╗
║  💀 <b>HEIST FAILED!</b>
╠{'═'*22}╣
║  🎯 {target['name']}
║  💸 Lost: <code>${HEIST_COST * len(crew):,}</code>
║
║  <i>{random.choice(FAIL_MESSAGES)}</i>
╚{'═'*22}╝"""
    
    heists_collection.update_one({"_id": heist_id}, {"$set": {"status": "completed"}})
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 new heist", callback_data="heist_menu")],
        [Buttons.back("menu_games")]
    ])
    
    try:
        await query.edit_message_text(result_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        if "Message is not modified" in str(e): pass
        else:
            try: await query.edit_message_caption(caption=result_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except: pass

async def heist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await heist_menu(update, context)

