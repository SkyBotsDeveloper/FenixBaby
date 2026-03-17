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
import httpx
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.database import groups_collection, users_collection
from fenix_baby.utils import ensure_user_exists, get_mention

logger = logging.getLogger(__name__)

# In-Memory Drop Storage
active_drops = {}
DROP_MESSAGE_COUNT = 100

WAIFU_NAMES = [
    ("Rem", "rem"), ("Ram", "ram"), ("Emilia", "emilia"), ("Asuna", "asuna"), 
    ("Zero Two", "zero two"), ("Makima", "makima"), ("Nezuko", "nezuko"),
    ("Hinata", "hinata"), ("Sakura", "sakura"), ("Mikasa", "mikasa"), 
    ("Yor", "yor"), ("Anya", "anya"), ("Power", "power"),
    ("Marin Kitagawa", "marin-kitagawa"), ("Hatsune Miku", "hatsune-miku"),
    ("Megumin", "megumin"), ("Aqua", "aqua"), ("Raphtalia", "raphtalia"),
    ("Kaguya Shinomiya", "kaguya-shinomiya"), ("Chika Fujiwara", "chika-fujiwara")
]

async def check_drops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat: return
    chat = update.effective_chat
    if chat.type == "private": return

    group = groups_collection.find_one_and_update(
        {"chat_id": chat.id}, {"$inc": {"msg_count": 1}}, upsert=True, return_document=True
    )
    
    # Spawn every 50-100 messages randomly
    spawn_threshold = group.get("spawn_threshold", random.randint(50, 100))
    
    if group.get("msg_count", 0) >= spawn_threshold:
        # Reset counter and set new threshold
        groups_collection.update_one(
            {"chat_id": chat.id}, 
            {"$set": {"msg_count": 0, "spawn_threshold": random.randint(50, 100)}}
        )
        
        char = random.choice(WAIFU_NAMES)
        name, slug = char
        
        async with httpx.AsyncClient() as client:
            # Priority 1: waifu.im
            try:
                r = await client.get("https://api.waifu.im/search?included_tags=waifu", timeout=5.0)
                if r.status_code == 200:
                    data = r.json()
                    if 'images' in data and data['images']:
                        url = data['images'][0]['url']
                        # Verify URL - if it's too long or has bad chars, skip to fallback
                        if len(url) > 200: raise Exception("URL too long")
                    else:
                        raise Exception("No images in waifu.im response")
                else:
                    raise Exception(f"waifu.im returned {r.status_code}")
            except Exception as e:
                logger.warning(f"waifu.im failed: {e}. Trying nekos.best...")
                try:
                    # Priority 2: nekos.best (reliable fallback)
                    r2 = await client.get("https://nekos.best/api/v2/waifu", timeout=5.0)
                    if r2.status_code == 200:
                        data2 = r2.json()
                        url = data2['results'][0]['url']
                    else:
                        raise Exception(f"nekos.best returned {r2.status_code}")
                except Exception as e2:
                    logger.error(f"nekos.best failed: {e2}. Using static fallback.")
                    # Final Fallback to a guaranteed working URL
                    url = "https://graph.org/file/5e5480760e412bd402e88.jpg"

        active_drops[chat.id] = name.lower()
        
        caption = f"👧 <b>A NEW WAIFU APPEARED!</b>\n\nGuess her name to catch her!\n<i>(Hint: {name[0]}...{name[-1]})</i>"
        
        try:
            # Atomic operation: Photo + Caption together
            await context.bot.send_photo(
                chat_id=chat.id,
                photo=url,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Waifu Photo Failed: {e}")
            # Fallback only if photo fails entirely
            await context.bot.send_message(
                chat_id=chat.id,
                text=caption,
                parse_mode=ParseMode.HTML
            )

async def collect_waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    
    if not msg or not msg.text:
        return
        
    if chat.id not in active_drops: return
    
    # Check if the message is actually a reply to the waifu spawn message
    # or if it starts with /catch
    is_reply = msg.reply_to_message and "A NEW WAIFU APPEARED" in (msg.reply_to_message.caption or msg.reply_to_message.text or "")
    is_command = msg.text.startswith("/")
    
    if not (is_reply or is_command):
        return

    guess = msg.text.lower().strip()
    if is_command:
        # Extract guess from command /catch name
        parts = guess.split(maxsplit=1)
        if len(parts) > 1:
            guess = parts[1]
        else:
            return # Ignore empty /catch
            
    correct = active_drops[chat.id]
    
    if chat and chat.id in active_drops and guess == correct:
        user = ensure_user_exists(msg.from_user) if msg.from_user else None
        if not user: return
        del active_drops[chat.id]
        
        rarity = random.choice(["Common", "Rare", "Epic", "Legendary"])
        waifu = {"name": correct.title(), "rarity": rarity, "date": datetime.utcnow()}
        users_collection.update_one({"user_id": user['user_id']}, {"$push": {"waifus": waifu}})
        
        await msg.reply_text(
            f"🎊 <b>Caught!</b> {get_mention(user)} got <b>{correct.title()}</b>!\n🌟 <b>Rarity:</b> {rarity}",
            parse_mode=ParseMode.HTML
        )
    else:
        # Only feedback if they were clearly trying to guess (reply or command)
        await msg.reply_text("❌ Wrong guess! Try again.")

async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guess waifu from /catch command."""
    if not update.effective_chat or not update.effective_message or not update.effective_user: return
    chat = update.effective_chat
    if chat and chat.id not in active_drops:
        return await update.effective_message.reply_text("❌ No active catch to guess!")
    
    if not context.args:
        return await update.effective_message.reply_text("📝 Usage: /catch [name]")
        
    guess = " ".join(context.args).lower().strip()
    correct = active_drops[chat.id]
    
    if guess == correct:
        user = ensure_user_exists(update.effective_user)
        del active_drops[chat.id]
        
        rarity = random.choice(["Common", "Rare", "Epic", "Legendary"])
        waifu = {"name": correct.title(), "rarity": rarity, "date": datetime.utcnow()}
        users_collection.update_one({"user_id": user['user_id']}, {"$push": {"waifus": waifu}})
        
        await update.effective_message.reply_text(
            f"🎯 <b>Perfect Guess!</b>\n\n👤 {get_mention(user)} caught <b>{correct.title()}</b>!\n🌟 <b>Rarity:</b> {rarity}",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.effective_message.reply_text("❌ Wrong name! Try again.")

