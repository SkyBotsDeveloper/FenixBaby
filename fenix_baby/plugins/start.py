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
    "Ready to dominate? ðŸ’ª",
    "The streets await you! ðŸŒƒ",
    "Time to make some money! ðŸ’°",
    "Your empire starts here! ðŸ‘‘",
]

def get_start_keyboard(bot_username):
    rows = [[
        InlineKeyboardButton("âž• á´€á´…á´… á´›á´ É¢Ê€á´á´œá´˜", url=f"https://t.me/{bot_username}?startgroup=true"),
    ]]

    link_row = []
    if SUPPORT_CHANNEL:
        link_row.append(InlineKeyboardButton("ðŸ“¢ á´œá´˜á´…á´€á´›á´‡s", url=SUPPORT_CHANNEL))
    if SUPPORT_GROUP:
        link_row.append(InlineKeyboardButton("ðŸ’¬ sá´œá´˜á´˜á´Ê€á´›", url=SUPPORT_GROUP))
    if link_row:
        rows.append(link_row)

    final_row = [InlineKeyboardButton("â“ Êœá´‡ÊŸá´˜", callback_data="help_main")]
    if OWNER_LINK:
        final_row.append(InlineKeyboardButton("ðŸ‘¨â€ðŸ’» á´…á´‡á´ ", url=OWNER_LINK))
    rows.append(final_row)

    return InlineKeyboardMarkup(rows)

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("âš”ï¸ É¢á´€á´á´‡s & Ê€á´˜É¢", callback_data="help_rpg"),
            InlineKeyboardButton("ðŸ’° á´‡á´„á´É´á´á´Ê", callback_data="help_economy"),
        ],
        [
            InlineKeyboardButton("ðŸ’ž sá´á´„Éªá´€ÊŸ", callback_data="help_social"),
            InlineKeyboardButton("ðŸ¤– á´€Éª & Ò“á´œÉ´", callback_data="help_fun"),
        ],
        [
            InlineKeyboardButton("âš™ï¸ É¢Ê€á´á´œá´˜", callback_data="help_group"),
            InlineKeyboardButton("ðŸ‘‘ sá´œá´…á´", callback_data="help_sudo"),
        ],
        [
            InlineKeyboardButton("ðŸ  Êœá´á´á´‡", callback_data="return_start"),
        ],
    ])

def get_back_keyboard(callback="help_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("â—„ Ê™á´€á´„á´‹", callback_data=callback)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    db_user = ensure_user_exists(user)
    track_group(chat, user)
    
    balance = db_user.get("balance", 0)
    status_emoji = "ðŸ’€" if db_user.get("status") == "dead" else "âœ¨"
    quote = random.choice(WELCOME_QUOTES)
    
    caption = f"""
â•”{'â•'*22}â•—
â•‘  {status_emoji} <b>Welcome, {get_mention(user)}!</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸŽ® <b>{BOT_NAME}</b>
â•‘  <i>The Ultimate RPG & Economy Bot</i>
â•‘  
â•‘  ðŸ’° Balance: <code>{format_money(balance)}</code>
â•‘  ðŸ“Š Status: <code>{db_user.get('status', 'alive').title()}</code>
â•‘  
â• {'â•'*22}â•£
â•‘  <i>{quote}</i>
â•š{'â•'*22}â•

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
â•”{'â•'*22}â•—
â•‘  ðŸ“– <b>{BOT_NAME} HELP</b>
â• {'â•'*22}â•£
â•‘  
â•‘  Select a category below to
â•‘  explore all available features!
â•‘  
â•‘  ðŸŽ® <b>Games</b> - RPG & Gambling
â•‘  ðŸ’° <b>Economy</b> - Money & Shop
â•‘  ðŸ’ž <b>Social</b> - Marriage & Love
â•‘  ðŸ¤– <b>AI</b> - Chat & Art
â•‘  
â•š{'â•'*22}â•"""
    
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
â•”{'â•'*22}â•—
â•‘  ðŸŽ® <b>GAMES MENU</b>
â• {'â•'*22}â•£
â•‘  
â•‘  âš”ï¸ <b>Combat Games</b>
â•‘  â€¢ Kill - Murder for loot
â•‘  â€¢ Rob - Steal coins
â•‘  â€¢ Duel - High stakes PvP!
â•‘  
â•‘  ðŸŽ² <b>Gambling</b>
â•‘  â€¢ Dice - Roll for money
â•‘  â€¢ Slots - Spin to win
â•‘  â€¢ Lottery - 10k Jackpot!
â•‘  
â•‘  ðŸ¦ <b>Cooperative</b>
â•‘  â€¢ Heist - Team robbery!
â•‘  
â•š{'â•'*22}â•

<i>Select a game to learn more!</i>"""
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        return
    
    if data == "menu_economy":
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ’° <b>ECONOMY MENU</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ’µ /bal - Check balance
â•‘  ðŸŽ /daily - Daily reward
â•‘  ðŸ† /ranking - Leaderboard
â•‘  ðŸ’¸ /give - Transfer coins
â•‘  ðŸ“¦ /claim - Group bonus
â•‘  ðŸ›’ /shop - Buy items
â•‘  
â•š{'â•'*22}â•"""
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ðŸ’µ Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
                InlineKeyboardButton("ðŸŽ á´…á´€ÉªÊŸÊ", callback_data="quick_daily"),
            ],
            [
                InlineKeyboardButton("ðŸ›’ sÊœá´á´˜", callback_data="shop_main"),
                InlineKeyboardButton("ðŸ† Ê€á´€É´á´‹ÉªÉ´É¢", callback_data="quick_ranking"),
            ],
            [Buttons.back("return_start")],
        ])
        
        try:
            if query.message.caption == text:
                return await query.answer("Already here! ðŸ˜Š")
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            try:
                if query.message.text == text:
                    return await query.answer("Already here! ðŸ˜Š")
                await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except Exception: pass
        return

    if data == "help_main":
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ“– <b>{BOT_NAME} HELP</b>
â• {'â•'*22}â•£
â•‘  
â•‘  Select a category below to
â•‘  explore all available features!
â•‘  
â•‘  ðŸŽ® <b>Games</b> - RPG & Gambling
â•‘  ðŸ’° <b>Economy</b> - Money & Shop
â•‘  ðŸ’ž <b>Social</b> - Marriage & Love
â•‘  ðŸ¤– <b>AI</b> - Chat & Art
â•‘  
â•š{'â•'*22}â•"""
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
â•”{'â•'*22}â•—
â•‘  ðŸ’ž <b>SOCIAL & LOVE</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ’ <b>/propose @user</b>
â•‘  â”” Propose marriage (5% tax perk)
â•‘  
â•‘  ðŸ’’ <b>/marry</b>
â•‘  â”” Check relationship status
â•‘  
â•‘  ðŸ’” <b>/divorce</b>
â•‘  â”” Break up (Cost: $2,000)
â•‘  
â•‘  ðŸ’˜ <b>/couple</b>
â•‘  â”” Fun matchmaking game!
â•‘  
â•‘  ðŸŒ¸ <b>/wpropose</b>
â•‘  â”” Propose to anime waifu
â•‘  
â•š{'â•'*22}â•"""

    elif data == "help_economy":
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ’° <b>ECONOMY & SHOP</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ’µ <b>/bal</b> - Wallet & Inventory
â•‘  ðŸŽ <b>/daily</b> - Streak Rewards
â•‘  ðŸ† <b>/ranking</b> - Leaderboards
â•‘  ðŸ’¸ <b>/give [amt] @user</b>
â•‘  â”” Transfer (10% tax)
â•‘  ðŸ“¦ <b>/claim</b> - Group Bonus
â•‘  ðŸ›’ <b>/shop</b> - Weapons & Armor
â•‘  ðŸ›ï¸ <b>/buy [item]</b>
â•‘  
â•š{'â•'*22}â•"""

    elif data == "help_rpg":
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸŽ® <b>GAMES MENU</b>
â• {'â•'*22}â•£
â•‘  
â•‘  âš”ï¸ <b>Combat Games</b>
â•‘  â€¢ Kill - Murder for loot
â•‘  â€¢ Rob - Steal coins
â•‘  â€¢ Duel - High stakes PvP!
â•‘  
â•‘  ðŸŽ² <b>Gambling</b>
â•‘  â€¢ Dice - Roll for money
â•‘  â€¢ Slots - Spin to win
â•‘  â€¢ Lottery - 10k Jackpot!
â•‘  
â•‘  ðŸ¦ <b>Cooperative</b>
â•‘  â€¢ Heist - Team robbery!
â•‘  
â•š{'â•'*22}â•

<i>Select a game to learn more!</i>"""
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard(back_callback="help_main"))
        return

    elif data == "help_fun":
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ¤– <b>AI & FUN</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸŽ¨ <b>/draw [prompt]</b>
â•‘  â”” AI generates anime art
â•‘  
â•‘  ðŸ—£ï¸ <b>/speak [text]</b>
â•‘  â”” Anime voice synthesis
â•‘  
â•‘  ðŸ§  <b>/chatbot</b>
â•‘  â”” AI chat settings
â•‘  
â•‘  â“ <b>/riddle</b>
â•‘  â”” Win coins with riddles!
â•‘  
â•‘  ðŸ’¬ <b>/ask [question]</b>
â•‘  â”” Ask AI anything
â•‘  
â•‘  ðŸŽ® <b>/catch [name]</b>
â•‘  â”” Catch appearing waifus!
â•‘  
â•š{'â•'*22}â•"""

    elif data == "help_group":
        text = f"""
â•”{'â•'*22}â•—
â•‘  âš™ï¸ <b>GROUP SETTINGS</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ‘‹ <b>/welcome on/off</b>
â•‘  â”” Toggle welcome messages
â•‘  
â•‘  ðŸ“Š <b>/ping</b>
â•‘  â”” Bot status & latency
â•‘  
â•‘  ðŸ“¦ <b>/claim</b>
â•‘  â”” Claim group bonus ($2k)
â•‘  â”” Requires 100+ members
â•‘  
â•š{'â•'*22}â•"""

    elif data == "help_sudo":
        if query.from_user.id != OWNER_ID:
            return await query.answer("âŒ Owner Only!", show_alert=True)
        target_photo = SUDO_IMG
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ‘‘ <b>SUDO PANEL</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ’° <b>/addcoins [amt] @user</b>
â•‘  ðŸ’¸ <b>/rmcoins [amt] @user</b>
â•‘  âœ¨ <b>/freerevive @user</b>
â•‘  ðŸ›¡ï¸ <b>/unprotect @user</b>
â•‘  
â•‘  ðŸ“¢ <b>/broadcast</b>
â•‘  â”” -user / -group / -clean
â•‘  
â•‘  <b>Owner Only:</b>
â•‘  ðŸ”„ <b>/update</b>
â•‘  âž• <b>/addsudo @user</b>
â•‘  âž– <b>/rmsudo @user</b>
â•‘  ðŸ—‘ï¸ <b>/cleandb</b>
â•‘  
â•š{'â•'*22}â•"""

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
            "title": "ðŸ”ª KILL",
            "desc": """Murder another player for coins!

<b>How it works:</b>
â€¢ Reply to a user or use /kill @user
â€¢ You earn 100-200 coins per kill
â€¢ Weapons boost your earnings
â€¢ Victim's flex items are burned!

<b>Tips:</b>
â€¢ Buy weapons from /shop
â€¢ Can't kill protected users
â€¢ Dead users can't kill""",
        },
        "game_rob_info": {
            "title": "ðŸ’° ROB",
            "desc": """Steal coins from other players!

<b>Usage:</b> /rob [amount] @user

<b>How it works:</b>
â€¢ Specify amount to steal
â€¢ Armor can block robbery
â€¢ No protection cooldown

<b>Tips:</b>
â€¢ Check target's balance first
â€¢ Armor reduces success rate""",
        },
        "game_dice_info": {
            "title": "ðŸŽ² DICE",
            "desc": """Roll the dice to win coins!

<b>Usage:</b> /dice [amount]

<b>Rules:</b>
â€¢ Roll 4, 5, 6 = WIN (2x)
â€¢ Roll 1, 2, 3 = LOSE
â€¢ Min bet: $50

<b>Tips:</b>
â€¢ 50% win chance
â€¢ Double your money!""",
        },
        "game_slots_info": {
            "title": "ðŸŽ° SLOTS",
            "desc": """Spin the slot machine!

<b>Usage:</b> /slots

<b>Payouts:</b>
â€¢ 777 = JACKPOT (10x)
â€¢ 3 matching = WIN (3x)
â€¢ Others = LOSE

<b>Cost:</b> $100 per spin""",
        },
        "game_protect_info": {
            "title": "ðŸ›¡ï¸ PROTECT",
            "desc": """Buy protection from attacks!

<b>Usage:</b> /protect 1d or /protect 2d

<b>Prices:</b>
â€¢ 1 Day: $1,000
â€¢ 2 Days: $1,800

<b>Perks:</b>
â€¢ Blocks kill & rob
â€¢ Protects your partner too!""",
        },
        "game_duel_info": {
            "title": "âš”ï¸ DUEL",
            "desc": """Challenge a user to PvP!

<b>Usage:</b> /duel [bet] @user

<b>How it works:</b>
â€¢ Winner takes the pot!
â€¢ Opponent must accept.
â€¢ Min bet: 100 coins.""",
        },
        "game_lottery_info": {
            "title": "ðŸŽ° LOTTERY",
            "desc": """Try your luck in the lottery!

<b>Usage:</b> /lottery

<b>How it works:</b>
â€¢ Ticket cost: 500 coins.
â€¢ 10% chance to win.
â€¢ Jackpot: Up to 10k!""",
        },
    }
    
    game = info.get(data, {"title": "Unknown", "desc": "Game not found"})
    
    text = f"""
â•”{'â•'*22}â•—
â•‘  {game['title']}
â• {'â•'*22}â•£
{game['desc']}
â•š{'â•'*22}â•"""
    
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
â•”{'â•'*22}â•—
â•‘  ðŸ’° <b>YOUR WALLET</b>
â• {'â•'*22}â•£
â•‘  
â•‘  ðŸ’µ Balance: <code>{format_money(balance)}</code>
â•‘  âš”ï¸ Kills: <code>{kills}</code>
â•‘  ðŸ“Š Status: <code>{status.title()}</code>
â•‘  
â•š{'â•'*22}â•

<i>Use /bal for full details!</i>"""
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ“¦ ÉªÉ´á´ á´‡É´á´›á´Ê€Ê", callback_data="inv_view")],
            [Buttons.back("return_start")],
        ])
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    
    elif data == "quick_daily":
        await query.message.reply_text(
            "ðŸŽ <b>Daily Reward</b>\n\n<i>Use /daily command to claim!</i>",
            parse_mode=ParseMode.HTML
        )
    
    elif data == "quick_ranking":
        top_users = list(users_collection.find().sort("balance", -1).limit(10))
        
        ranking_text = ""
        medals = {0: "ðŸ¥‡", 1: "ðŸ¥ˆ", 2: "ðŸ¥‰"}
        
        for i, u in enumerate(top_users):
            medal = medals.get(i, f"#{i+1}")
            name = u.get("first_name", "Unknown")[:15]
            bal = format_money(u.get("balance", 0))
            ranking_text += f"â•‘  {medal} {name}: {bal}\n"
        
        text = f"""
â•”{'â•'*22}â•—
â•‘  ðŸ† <b>TOP 10 RICHEST</b>
â• {'â•'*22}â•£
{ranking_text}â•š{'â•'*22}â•"""
        
        kb = InlineKeyboardMarkup([[Buttons.back("return_start")]])
        
        try:
            await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except:
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

