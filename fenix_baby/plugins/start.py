import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from fenix_baby.config import BOT_NAME, START_IMG_URL, HELP_IMG_URL, SUPPORT_GROUP, SUPPORT_CHANNEL, OWNER_LINK
from fenix_baby.utils import ensure_user_exists, get_mention, track_group, log_to_channel, SUDO_USERS, format_money
from fenix_baby.config import OWNER_ID
from fenix_baby.database import users_collection
from fenix_baby.ui.components import Templates, Buttons, quick_actions_keyboard, games_keyboard

SUDO_IMG = "https://files.catbox.moe/veuo1s.jpg"

WELCOME_QUOTES = [
    "Ready to dominate? 💪",
    "The streets await you! 🌃",
    "Time to make some money! 💰",
    "Your empire starts here! 👑",
]

def get_start_keyboard(bot_username):
    rows = [[
        InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true"),
    ]]

    link_row = []
    if SUPPORT_CHANNEL:
        link_row.append(InlineKeyboardButton("📢 Updates", url=SUPPORT_CHANNEL))
    if SUPPORT_GROUP:
        link_row.append(InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP))
    if link_row:
        rows.append(link_row)

    final_row = [InlineKeyboardButton("❓ Help", callback_data="help_main")]
    if OWNER_LINK:
        final_row.append(InlineKeyboardButton("👨‍💻 Owner", url=OWNER_LINK))
    rows.append(final_row)

    return InlineKeyboardMarkup(rows)

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ Games & RPG", callback_data="help_rpg"),
            InlineKeyboardButton("💰 Economy", callback_data="help_economy"),
        ],
        [
            InlineKeyboardButton("💞 Social", callback_data="help_social"),
            InlineKeyboardButton("🤖 AI & Fun", callback_data="help_fun"),
        ],
        [
            InlineKeyboardButton("⚙️ Group", callback_data="help_group"),
            InlineKeyboardButton("👑 Sudo", callback_data="help_sudo"),
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="return_start"),
        ],
    ])

def get_back_keyboard(callback="help_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("◄ Back", callback_data=callback)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    db_user = ensure_user_exists(user)
    track_group(chat, user)
    
    balance = db_user.get("balance", 0)
    status_emoji = "💀" if db_user.get("status") == "dead" else "✨"
    quote = random.choice(WELCOME_QUOTES)
    
    caption = f"""
╔{'═'*22}╗
║  {status_emoji} <b>Welcome, {get_mention(user)}!</b>
╠{'═'*22}╣
║  
║  🎮 <b>{BOT_NAME}</b>
║  <i>The Ultimate RPG & Economy Bot</i>
║  
║  💰 Balance: <code>{format_money(balance)}</code>
║  📊 Status: <code>{db_user.get('status', 'alive').title()}</code>
║  
╠{'═'*22}╣
║  <i>{quote}</i>
╚{'═'*22}╝

<b>Quick Actions:</b> Use buttons below!"""

    kb = get_start_keyboard(context.bot.username)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_media(
                InputMediaPhoto(media=START_IMG_URL, caption=caption, parse_mode=ParseMode.HTML),
                reply_markup=kb
            )
        except:
            await update.callback_query.message.edit_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        if START_IMG_URL and START_IMG_URL.startswith("http"):
            try:
                await update.message.reply_photo(photo=START_IMG_URL, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
            except:
                await update.effective_message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.effective_message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)

    if chat.type == ChatType.PRIVATE and not update.callback_query:
        await log_to_channel(context.bot, "command", {"user": f"{get_mention(user)} (`{user.id}`)", "action": "Started Bot", "chat": "Private"})

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
╔{'═'*22}╗
║  📖 <b>{BOT_NAME} HELP</b>
╠{'═'*22}╣
║  
║  Select a category below to
║  explore all available features!
║  
║  🎮 <b>Games</b> - RPG & Gambling
║  💰 <b>Economy</b> - Money & Shop
║  💞 <b>Social</b> - Marriage & Love
║  🤖 <b>AI</b> - Chat & Art
║  
╚{'═'*22}╝"""
    
    await update.message.reply_photo(
        photo=HELP_IMG_URL,
        caption=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_help_keyboard()
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data
    if not data:
        return
    
    await query.answer()
    
    if data == "return_start":
        await start(update, context)
        return
    
    if data == "menu_games":
        text = f"""
╔{'═'*22}╗
║  🎮 <b>GAMES MENU</b>
╠{'═'*22}╣
║  
║  ⚔️ <b>Combat Games</b>
║  • Kill - Murder for loot
║  • Rob - Steal coins
║  • Duel - High stakes PvP!
║  
║  🎲 <b>Gambling</b>
║  • Dice - Roll for money
║  • Slots - Spin to win
║  • Lottery - 10k Jackpot!
║  
║  🏦 <b>Cooperative</b>
║  • Heist - Team robbery!
║  
╚{'═'*22}╝

<i>Select a game to learn more!</i>"""
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        return
    
    if data == "menu_economy":
        text = f"""
╔{'═'*22}╗
║  💰 <b>ECONOMY MENU</b>
╠{'═'*22}╣
║  
║  💵 /bal - Check balance
║  🎁 /daily - Daily reward
║  🏆 /ranking - Leaderboard
║  💸 /give - Transfer coins
║  📦 /claim - Group bonus
║  🛒 /shop - Buy items
║  
╚{'═'*22}╝"""
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💵 Balance", callback_data="quick_bal"),
                InlineKeyboardButton("🎁 Daily", callback_data="quick_daily"),
            ],
            [
                InlineKeyboardButton("🛒 Shop", callback_data="shop_main"),
                InlineKeyboardButton("🏆 Ranking", callback_data="quick_ranking"),
            ],
            [Buttons.back("return_start")],
        ])
        
        try:
            if query.message.caption == text:
                return await query.answer("Already here! 😊")
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            try:
                if query.message.text == text:
                    return await query.answer("Already here! 😊")
                await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except Exception: pass
        return

    if data == "help_main":
        text = f"""
╔{'═'*22}╗
║  📖 <b>{BOT_NAME} HELP</b>
╠{'═'*22}╣
║  
║  Select a category below to
║  explore all available features!
║  
║  🎮 <b>Games</b> - RPG & Gambling
║  💰 <b>Economy</b> - Money & Shop
║  💞 <b>Social</b> - Marriage & Love
║  🤖 <b>AI</b> - Chat & Art
║  
╚{'═'*22}╝"""
        try:
            await query.message.edit_media(
                InputMediaPhoto(media=HELP_IMG_URL, caption=text, parse_mode=ParseMode.HTML),
                reply_markup=get_help_keyboard()
            )
        except Exception:
            try:
                await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=get_help_keyboard())
            except Exception: pass
        return

    target_photo = HELP_IMG_URL
    kb = get_back_keyboard()
    text = ""
    
    if data == "help_social":
        text = f"""
╔{'═'*22}╗
║  💞 <b>SOCIAL & LOVE</b>
╠{'═'*22}╣
║  
║  💍 <b>/propose @user</b>
║  └ Propose marriage (5% tax perk)
║  
║  💒 <b>/marry</b>
║  └ Check relationship status
║  
║  💔 <b>/divorce</b>
║  └ Break up (Cost: $2,000)
║  
║  💘 <b>/couple</b>
║  └ Fun matchmaking game!
║  
║  🌸 <b>/wpropose</b>
║  └ Propose to anime waifu
║  
╚{'═'*22}╝"""

    elif data == "help_economy":
        text = f"""
╔{'═'*22}╗
║  💰 <b>ECONOMY & SHOP</b>
╠{'═'*22}╣
║  
║  💵 <b>/bal</b> - Wallet & Inventory
║  🎁 <b>/daily</b> - Streak Rewards
║  🏆 <b>/ranking</b> - Leaderboards
║  💸 <b>/give [amt] @user</b>
║  └ Transfer (10% tax)
║  📦 <b>/claim</b> - Group Bonus
║  🛒 <b>/shop</b> - Weapons & Armor
║  🛍️ <b>/buy [item]</b>
║  
╚{'═'*22}╝"""

    elif data == "help_rpg":
        text = f"""
╔{'═'*22}╗
║  🎮 <b>GAMES MENU</b>
╠{'═'*22}╣
║  
║  ⚔️ <b>Combat Games</b>
║  • Kill - Murder for loot
║  • Rob - Steal coins
║  • Duel - High stakes PvP!
║  
║  🎲 <b>Gambling</b>
║  • Dice - Roll for money
║  • Slots - Spin to win
║  • Lottery - 10k Jackpot!
║  
║  🏦 <b>Cooperative</b>
║  • Heist - Team robbery!
║  
╚{'═'*22}╝

<i>Select a game to learn more!</i>"""
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        return

    elif data == "help_fun":
        text = f"""
╔{'═'*22}╗
║  🤖 <b>AI & FUN</b>
╠{'═'*22}╣
║  
║  🎨 <b>/draw [prompt]</b>
║  └ AI generates anime art
║  
║  🗣️ <b>/speak [text]</b>
║  └ Anime voice synthesis
║  
║  🧠 <b>/chatbot</b>
║  └ AI chat settings
║  
║  ❓ <b>/riddle</b>
║  └ Win coins with riddles!
║  
║  💬 <b>/ask [question]</b>
║  └ Ask AI anything
║  
║  🎮 <b>/catch [name]</b>
║  └ Catch appearing waifus!
║  
╚{'═'*22}╝"""

    elif data == "help_group":
        text = f"""
╔{'═'*22}╗
║  ⚙️ <b>GROUP SETTINGS</b>
╠{'═'*22}╣
║  
║  👋 <b>/welcome on/off</b>
║  └ Toggle welcome messages
║  
║  📊 <b>/ping</b>
║  └ Bot status & latency
║  
║  📦 <b>/claim</b>
║  └ Claim group bonus ($2k)
║  └ Requires 100+ members
║  
╚{'═'*22}╝"""

    elif data == "help_sudo":
        if query.from_user.id != OWNER_ID:
            return await query.answer("❌ Owner Only!", show_alert=True)
        target_photo = SUDO_IMG
        text = f"""
╔{'═'*22}╗
║  👑 <b>SUDO PANEL</b>
╠{'═'*22}╣
║  
║  💰 <b>/addcoins [amt] @user</b>
║  💸 <b>/rmcoins [amt] @user</b>
║  ✨ <b>/freerevive @user</b>
║  🛡️ <b>/unprotect @user</b>
║  
║  📢 <b>/broadcast</b>
║  └ -user / -group / -clean
║  
║  <b>Owner Only:</b>
║  🔄 <b>/update</b>
║  ➕ <b>/addsudo @user</b>
║  ➖ <b>/rmsudo @user</b>
║  🗑️ <b>/cleandb</b>
║  
╚{'═'*22}╝"""

    try:
        await query.message.edit_media(
            InputMediaPhoto(media=target_photo, caption=text, parse_mode=ParseMode.HTML),
            reply_markup=kb
        )
    except:
        await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def game_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data
    if not data:
        return
    await query.answer()
    
    info = {
        "game_kill_info": {
            "title": "🔪 KILL",
            "desc": """Murder another player for coins!

<b>How it works:</b>
• Reply to a user or use /kill @user
• You earn 100-200 coins per kill
• Weapons boost your earnings
• Victim's flex items are burned!

<b>Tips:</b>
• Buy weapons from /shop
• Can't kill protected users
• Dead users can't kill""",
        },
        "game_rob_info": {
            "title": "💰 ROB",
            "desc": """Steal coins from other players!

<b>Usage:</b> /rob [amount] @user

<b>How it works:</b>
• Specify amount to steal
• Armor can block robbery
• No protection cooldown

<b>Tips:</b>
• Check target's balance first
• Armor reduces success rate""",
        },
        "game_dice_info": {
            "title": "🎲 DICE",
            "desc": """Roll the dice to win coins!

<b>Usage:</b> /dice [amount]

<b>Rules:</b>
• Roll 4, 5, 6 = WIN (2x)
• Roll 1, 2, 3 = LOSE
• Min bet: $50

<b>Tips:</b>
• 50% win chance
• Double your money!""",
        },
        "game_slots_info": {
            "title": "🎰 SLOTS",
            "desc": """Spin the slot machine!

<b>Usage:</b> /slots

<b>Payouts:</b>
• 777 = JACKPOT (10x)
• 3 matching = WIN (3x)
• Others = LOSE

<b>Cost:</b> $100 per spin""",
        },
        "game_protect_info": {
            "title": "🛡️ PROTECT",
            "desc": """Buy protection from attacks!

<b>Usage:</b> /protect 1d or /protect 2d

<b>Prices:</b>
• 1 Day: $1,000
• 2 Days: $1,800

<b>Perks:</b>
• Blocks kill & rob
• Protects your partner too!""",
        },
        "game_duel_info": {
            "title": "⚔️ DUEL",
            "desc": """Challenge a user to PvP!

<b>Usage:</b> /duel [bet] @user

<b>How it works:</b>
• Winner takes the pot!
• Opponent must accept.
• Min bet: 100 coins.""",
        },
        "game_lottery_info": {
            "title": "🎰 LOTTERY",
            "desc": """Try your luck in the lottery!

<b>Usage:</b> /lottery

<b>How it works:</b>
• Ticket cost: 500 coins.
• 10% chance to win.
• Jackpot: Up to 10k!""",
        },
    }
    
    game = info.get(data, {"title": "Unknown", "desc": "Game not found"})
    
    text = f"""
╔{'═'*22}╗
║  {game['title']}
╠{'═'*22}╣
{game['desc']}
╚{'═'*22}╝"""
    
    kb = InlineKeyboardMarkup([
        [Buttons.back("menu_games")],
    ])
    
    try:
        await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except:
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def quick_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    data = query.data
    if not data:
        return
    user = ensure_user_exists(query.from_user)
    
    await query.answer()
    
    if data == "quick_bal":
        balance = user.get("balance", 0)
        kills = user.get("kills", 0)
        status = user.get("status", "alive")
        
        text = f"""
╔{'═'*22}╗
║  💰 <b>YOUR WALLET</b>
╠{'═'*22}╣
║  
║  💵 Balance: <code>{format_money(balance)}</code>
║  ⚔️ Kills: <code>{kills}</code>
║  📊 Status: <code>{status.title()}</code>
║  
╚{'═'*22}╝

<i>Use /bal for full details!</i>"""
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Inventory", callback_data="inv_view")],
            [Buttons.back("return_start")],
        ])
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    
    elif data == "quick_daily":
        await query.message.reply_text(
            "🎁 <b>Daily Reward</b>\n\n<i>Use /daily command to claim!</i>",
            parse_mode=ParseMode.HTML
        )
    
    elif data == "quick_ranking":
        top_users = list(users_collection.find().sort("balance", -1).limit(10))
        
        ranking_text = ""
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        
        for i, u in enumerate(top_users):
            medal = medals.get(i, f"#{i+1}")
            name = u.get("first_name", "Unknown")[:15]
            bal = format_money(u.get("balance", 0))
            ranking_text += f"║  {medal} {name}: {bal}\n"
        
        text = f"""
╔{'═'*22}╗
║  🏆 <b>TOP 10 RICHEST</b>
╠{'═'*22}╣
{ranking_text}╚{'═'*22}╝"""
        
        kb = InlineKeyboardMarkup([[Buttons.back("return_start")]])
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
