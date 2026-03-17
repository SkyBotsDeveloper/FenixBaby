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


import html
import os
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from fenix_baby.config import OWNER_ID, UPSTREAM_REPO, GIT_TOKEN
from fenix_baby.utils import SUDO_USERS, get_mention, resolve_target, format_money, reload_sudoers
from fenix_baby.database import users_collection, sudoers_collection, groups_collection

async def sudo_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS: return
    msg = (
        "🔐 <b>Sudo Panel</b>\n\n"
        "<b>💰 Economy:</b>\n"
        "‣ /addcoins [amt] [user]\n"
        "‣ /rmcoins [amt] [user]\n"
        "‣ /freerevive [user]\n"
        "‣ /unprotect [user] (Remove Shield)\n\n" # <--- ADDED
        "<b>📢 Broadcast:</b>\n"
        "‣ /broadcast -user (Reply)\n"
        "‣ /broadcast -group (Reply)\n"
        "‣ <i>Flag:</i> -clean (No Tag)\n\n"
        "<b>👑 Owner Only:</b>\n"
        "‣ /update (Pull Changes)\n"
        "‣ /addsudo [user]\n"
        "‣ /rmsudo [user]\n"
        "‣ /cleandb\n"
        "‣ /sudolist\n"
        "‣ /stats"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS: return
    user_count = users_collection.count_documents({})
    group_count = groups_collection.count_documents({})
    
    msg = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 <b>Total Users:</b> <code>{user_count}</code>\n"
        f"🏘️ <b>Total Groups:</b> <code>{group_count}</code>\n"
        "✨ <i>Keep growing!</i>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- UPDATER LOGIC (Unchanged) ---
async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not UPSTREAM_REPO: return await update.message.reply_text("❌ <b>UPSTREAM_REPO</b> missing!", parse_mode=ParseMode.HTML)
    msg = await update.message.reply_text("🔄 <b>Checking for updates...</b>", parse_mode=ParseMode.HTML)
    try:
        import git
        try: repo = git.Repo()
        except: 
            repo = git.Repo.init()
            origin = repo.create_remote('origin', UPSTREAM_REPO)
            origin.fetch()
            repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    except ImportError: return await msg.edit_text("❌ <b>Git Error:</b> Library missing.", parse_mode=ParseMode.HTML)
    except Exception as e: return await msg.edit_text(f"❌ <b>Git Error:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
    repo_url = UPSTREAM_REPO
    if GIT_TOKEN and "https://github.com" in repo_url: repo_url = repo_url.replace("https://", f"https://{GIT_TOKEN}@")
    try:
        repo.remotes.origin.set_url(repo_url)
        repo.remotes.origin.pull()
        await msg.edit_text("✅ <b>Update Found!</b>\nRestarting bot now... 🚀", parse_mode=ParseMode.HTML)
        args = [sys.executable, "FenixBaby.py"]
        os.execl(sys.executable, *args)
    except Exception as e: await msg.edit_text(f"❌ <b>Update Failed!</b>\nError: <code>{e}</code>", parse_mode=ParseMode.HTML)

# --- ADMIN COMMANDS ---

async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "👑 <b>Owner & Sudoers:</b>\n\n"
    owner_doc = users_collection.find_one({"user_id": OWNER_ID})
    if not owner_doc:
        try: 
            u = await context.bot.get_chat(OWNER_ID)
            owner_name = u.first_name
        except: owner_name = "Owner"
        msg += f"👑 <a href='tg://user?id={OWNER_ID}'><b>{html.escape(owner_name)}</b></a> (Owner)\n"
    else: msg += f"👑 {get_mention(owner_doc)} (Owner)\n"
    for uid in SUDO_USERS:
        if uid == OWNER_ID: continue
        u_doc = users_collection.find_one({"user_id": uid})
        if u_doc: msg += f"👮 {get_mention(u_doc)}\n"
        else: msg += f"👮 <code>{uid}</code>\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- CONFIRMATION ---

def get_kb(act, arg):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Yes", callback_data=f"cnf|{act}|{arg}"), InlineKeyboardButton("❌ No", callback_data="cnf|cancel|0")]])

async def ask(update, text, act, arg):
    await update.message.reply_text(f"⚠️ <b>Wait!</b> {text}\nAre you sure?", parse_mode=ParseMode.HTML, reply_markup=get_kb(act, arg))

def parse_amount_and_target(args):
    amount = None
    target_str = None
    for arg in args:
        if arg.isdigit() and amount is None: amount = int(arg)
        else: target_str = arg
    return amount, target_str

# --- HANDLERS ---

async def addsudo(update, context):
    if update.effective_user.id != OWNER_ID: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.message.reply_text(err or "Usage: /addsudo <target>", parse_mode=ParseMode.HTML)
    if target['user_id'] in SUDO_USERS: return await update.message.reply_text("⚠️ Already Sudoer.", parse_mode=ParseMode.HTML)
    await ask(update, f"Promote {get_mention(target)}?", "addsudo", str(target['user_id']))

async def rmsudo(update, context):
    if update.effective_user.id != OWNER_ID: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.message.reply_text(err or "Usage: /rmsudo <target>", parse_mode=ParseMode.HTML)
    if target['user_id'] not in SUDO_USERS: return await update.message.reply_text("⚠️ Not a Sudoer.", parse_mode=ParseMode.HTML)
    await ask(update, f"Demote {get_mention(target)}?", "rmsudo", str(target['user_id']))

async def addcoins(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    if not context.args: return await update.message.reply_text("⚠️ Usage: <code>/addcoins 100 @user</code>", parse_mode=ParseMode.HTML)
    amount, target_str = parse_amount_and_target(context.args)
    if amount is None: return await update.message.reply_text("⚠️ Invalid Amount!", parse_mode=ParseMode.HTML)
    target, err = await resolve_target(update, context, specific_arg=target_str)
    if not target: return await update.message.reply_text(err or "⚠️ Reply or Tag user.", parse_mode=ParseMode.HTML)
    await ask(update, f"Give <b>{format_money(amount)}</b> to {get_mention(target)}?", "addcoins", f"{target['user_id']}|{amount}")

async def rmcoins(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    if not context.args: return await update.message.reply_text("⚠️ Usage: <code>/rmcoins 100 @user</code>", parse_mode=ParseMode.HTML)
    amount, target_str = parse_amount_and_target(context.args)
    if amount is None: return await update.message.reply_text("⚠️ Invalid Amount!", parse_mode=ParseMode.HTML)
    target, err = await resolve_target(update, context, specific_arg=target_str)
    if not target: return await update.message.reply_text(err or "⚠️ Reply or Tag user.", parse_mode=ParseMode.HTML)
    await ask(update, f"Remove <b>{format_money(amount)}</b> from {get_mention(target)}?", "rmcoins", f"{target['user_id']}|{amount}")

async def freerevive(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.message.reply_text(err or "Usage: /freerevive <target>", parse_mode=ParseMode.HTML)
    await ask(update, f"Free Revive {get_mention(target)}?", "freerevive", str(target['user_id']))

async def unprotect(update, context):
    """Remove protection from a user."""
    if update.effective_user.id not in SUDO_USERS: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await update.message.reply_text(err or "Usage: /unprotect <target>", parse_mode=ParseMode.HTML)
    await ask(update, f"Remove 🛡️ from {get_mention(target)}?", "unprotect", str(target['user_id']))

async def cleandb(update, context):
    if update.effective_user.id != OWNER_ID: return
    await ask(update, "<b>WIPE DATABASE?</b> 🗑️", "cleandb", "0")

async def confirm_handler(update, context):
    q = update.callback_query
    await q.answer()
    
    # Reload sudoers to ensure we have latest data
    reload_sudoers()
    
    if q.from_user.id not in SUDO_USERS: 
        return await q.message.edit_text("❌ <b>Fenix Baby!</b> You don't have rights to access this panel.", parse_mode=ParseMode.HTML)
    
    data = q.data.split("|")
    act = data[1]
    if act == "cancel": return await q.message.edit_text("❌ <b>Cancelled.</b>", parse_mode=ParseMode.HTML)

    if act == "addsudo":
        uid = int(data[2])
        sudoers_collection.insert_one({"user_id": uid})
        reload_sudoers()
        await q.message.edit_text(f"✅ User <code>{uid}</code> promoted.", parse_mode=ParseMode.HTML)
    elif act == "rmsudo":
        uid = int(data[2])
        sudoers_collection.delete_one({"user_id": uid})
        reload_sudoers()
        await q.message.edit_text(f"🗑️ User <code>{uid}</code> demoted.", parse_mode=ParseMode.HTML)
    elif act == "addcoins":
        uid, amt = int(data[2]), int(data[3])
        users_collection.update_one({"user_id": uid}, {"$inc": {"balance": amt}})
        await q.message.edit_text(f"✅ Added <b>{format_money(amt)}</b> to <code>{uid}</code>.", parse_mode=ParseMode.HTML)
    elif act == "rmcoins":
        uid, amt = int(data[2]), int(data[3])
        users_collection.update_one({"user_id": uid}, {"$inc": {"balance": -amt}})
        await q.message.edit_text(f"✅ Removed <b>{format_money(amt)}</b> from <code>{uid}</code>.", parse_mode=ParseMode.HTML)
    elif act == "freerevive":
        uid = int(data[2])
        users_collection.update_one({"user_id": uid}, {"$set": {"status": "alive", "death_time": None}})
        await q.message.edit_text(f"✅ User <code>{uid}</code> revived.", parse_mode=ParseMode.HTML)
    elif act == "unprotect":
        uid = int(data[2])
        # Set expiry to past
        users_collection.update_one({"user_id": uid}, {"$set": {"protection_expiry": datetime.utcnow()}}) 
        await q.message.edit_text(f"🛡️ Protection <b>REMOVED</b> from <code>{uid}</code>.", parse_mode=ParseMode.HTML)
    elif act == "cleandb":
        users_collection.delete_many({})
        groups_collection.delete_many({})
        await q.message.edit_text("🗑️ <b>DATABASE WIPED!</b>", parse_mode=ParseMode.HTML)

