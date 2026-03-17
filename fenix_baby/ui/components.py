from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from fenix_baby.config import SUPPORT_GROUP, SUPPORT_CHANNEL, OWNER_LINK

class Buttons:
    @staticmethod
    def primary(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"✦ {text}", callback_data=callback)
    
    @staticmethod
    def secondary(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"◇ {text}", callback_data=callback)
    
    @staticmethod
    def danger(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"⚠ {text}", callback_data=callback)
    
    @staticmethod
    def success(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"✓ {text}", callback_data=callback)
    
    @staticmethod
    def link(text: str, url: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"🔗 {text}", url=url)
    
    @staticmethod
    def back(callback: str = "help_main") -> InlineKeyboardButton:
        return InlineKeyboardButton("◄ Back", callback_data=callback)
    
    @staticmethod
    def home() -> InlineKeyboardButton:
        return InlineKeyboardButton("🏠 Home", callback_data="return_start")

class Templates:
    DIVIDER = "═" * 20
    DIVIDER_THIN = "─" * 18
    
    @staticmethod
    def header(title: str, emoji: str = "✦") -> str:
        return f"{emoji} <b>{title}</b> {emoji}\n{'─' * 16}"
    
    @staticmethod
    def sub_header(title: str) -> str:
        return f"\n⊚ <b>{title}</b>\n"
    
    @staticmethod
    def stat_line(label: str, value: str, emoji: str = "•") -> str:
        return f"{emoji} <b>{label}:</b> <code>{value}</code>"
    
    @staticmethod
    def success_box(message: str) -> str:
        return f"┌{'─'*18}┐\n│ ✅ <b>{message}</b>\n└{'─'*18}┘"
    
    @staticmethod
    def error_box(message: str) -> str:
        return f"┌{'─'*18}┐\n│ ❌ <b>{message}</b>\n└{'─'*18}┘"
    
    @staticmethod
    def warning_box(message: str) -> str:
        return f"┌{'─'*18}┐\n│ ⚠️ <b>{message}</b>\n└{'─'*18}┘"
    
    @staticmethod
    def info_card(title: str, content: str, footer: str = "") -> str:
        card = f"""
╭━━━━━━━━━━━━━━━━╮
┃ <b>{title}</b>
┃ ─────────────
{content}
╰━━━━━━━━━━━━━━━━╯"""
        if footer:
            card += f"\n<i>{footer}</i>"
        return card
    
    @staticmethod
    def game_result(title: str, emoji: str, lines: list) -> str:
        content = "\n".join([f"┃ {line}" for line in lines])
        return f"""
╔{'═'*18}╗
║ {emoji} <b>{title}</b>
╠{'═'*18}╣
{content}
╚{'═'*18}╝"""

    @staticmethod
    def leaderboard_entry(rank: int, name: str, value: str) -> str:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, f"#{rank}")
        return f"{medal} {name} ➜ <code>{value}</code>"

def quick_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Balance", callback_data="quick_bal"),
            InlineKeyboardButton("🎁 Daily", callback_data="quick_daily"),
        ],
        [
            InlineKeyboardButton("🎮 Games", callback_data="menu_games"),
            InlineKeyboardButton("🛒 Shop", callback_data="shop_main"),
        ],
        [
            InlineKeyboardButton("🏆 Ranking", callback_data="quick_ranking"),
            InlineKeyboardButton("❓ Help", callback_data="help_main"),
        ],
    ])

def games_keyboard(back_callback: str = "return_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔪 Kill", callback_data="game_kill_info"),
            InlineKeyboardButton("💰 Rob", callback_data="game_rob_info"),
        ],
        [
            InlineKeyboardButton("🎲 Dice", callback_data="game_dice_info"),
            InlineKeyboardButton("🎰 Slots", callback_data="game_slots_info"),
        ],
        [
            InlineKeyboardButton("⚔️ Duel", callback_data="game_duel_info"),
            InlineKeyboardButton("🎰 Lottery", callback_data="game_lottery_info"),
        ],
        [
            InlineKeyboardButton("🏦 Heist", callback_data="heist_menu"),
            InlineKeyboardButton("🛡️ Protect", callback_data="game_protect_info"),
        ],
        [Buttons.back(back_callback)],
    ])

def back_button(callback: str = "help_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[Buttons.back(callback)]])

def confirm_keyboard(action: str, cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback),
        ]
    ])
