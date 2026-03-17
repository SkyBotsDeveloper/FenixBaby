from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from fenix_baby.config import SUPPORT_GROUP, SUPPORT_CHANNEL, OWNER_LINK

class Buttons:
    @staticmethod
    def primary(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"âœ¦ {text}", callback_data=callback)
    
    @staticmethod
    def secondary(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"â—‡ {text}", callback_data=callback)
    
    @staticmethod
    def danger(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"âš  {text}", callback_data=callback)
    
    @staticmethod
    def success(text: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"âœ“ {text}", callback_data=callback)
    
    @staticmethod
    def link(text: str, url: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(f"ðŸ”— {text}", url=url)
    
    @staticmethod
    def back(callback: str = "help_main") -> InlineKeyboardButton:
        return InlineKeyboardButton("â—„ Ê™á´€á´„á´‹", callback_data=callback)
    
    @staticmethod
    def home() -> InlineKeyboardButton:
        return InlineKeyboardButton("ðŸ  Êœá´á´á´‡", callback_data="return_start")

class Templates:
    DIVIDER = "â•" * 20
    DIVIDER_THIN = "â”€" * 18
    
    @staticmethod
    def header(title: str, emoji: str = "âœ¦") -> str:
        return f"{emoji} <b>{title}</b> {emoji}\n{'â”€' * 16}"
    
    @staticmethod
    def sub_header(title: str) -> str:
        return f"\nâŠš <b>{title}</b>\n"
    
    @staticmethod
    def stat_line(label: str, value: str, emoji: str = "â€¢") -> str:
        return f"{emoji} <b>{label}:</b> <code>{value}</code>"
    
    @staticmethod
    def success_box(message: str) -> str:
        return f"â”Œ{'â”€'*18}â”\nâ”‚ âœ… <b>{message}</b>\nâ””{'â”€'*18}â”˜"
    
    @staticmethod
    def error_box(message: str) -> str:
        return f"â”Œ{'â”€'*18}â”\nâ”‚ âŒ <b>{message}</b>\nâ””{'â”€'*18}â”˜"
    
    @staticmethod
    def warning_box(message: str) -> str:
        return f"â”Œ{'â”€'*18}â”\nâ”‚ âš ï¸ <b>{message}</b>\nâ””{'â”€'*18}â”˜"
    
    @staticmethod
    def info_card(title: str, content: str, footer: str = "") -> str:
        card = f"""
â•­â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â•®
â”ƒ <b>{title}</b>
â”ƒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
{content}
â•°â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â•¯"""
        if footer:
            card += f"\n<i>{footer}</i>"
        return card
    
    @staticmethod
    def game_result(title: str, emoji: str, lines: list) -> str:
        content = "\n".join([f"â”ƒ {line}" for line in lines])
        return f"""
â•”{'â•'*18}â•—
â•‘ {emoji} <b>{title}</b>
â• {'â•'*18}â•£
{content}
â•š{'â•'*18}â•"""

    @staticmethod
    def leaderboard_entry(rank: int, name: str, value: str) -> str:
        medals = {1: "ðŸ¥‡", 2: "ðŸ¥ˆ", 3: "ðŸ¥‰"}
        medal = medals.get(rank, f"#{rank}")
        return f"{medal} {name} âžœ <code>{value}</code>"

def quick_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ’° Ê™á´€ÊŸá´€É´á´„á´‡", callback_data="quick_bal"),
            InlineKeyboardButton("ðŸŽ á´…á´€ÉªÊŸÊ", callback_data="quick_daily"),
        ],
        [
            InlineKeyboardButton("ðŸŽ® É¢á´€á´á´‡s", callback_data="menu_games"),
            InlineKeyboardButton("ðŸ›’ sÊœá´á´˜", callback_data="shop_main"),
        ],
        [
            InlineKeyboardButton("ðŸ† Ê€á´€É´á´‹ÉªÉ´É¢", callback_data="quick_ranking"),
            InlineKeyboardButton("â“ Êœá´‡ÊŸá´˜", callback_data="help_main"),
        ],
    ])

def games_keyboard(back_callback: str = "return_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ”ª á´‹ÉªÊŸÊŸ", callback_data="game_kill_info"),
            InlineKeyboardButton("ðŸ’° Ê€á´Ê™", callback_data="game_rob_info"),
        ],
        [
            InlineKeyboardButton("ðŸŽ² á´…Éªá´„á´‡", callback_data="game_dice_info"),
            InlineKeyboardButton("ðŸŽ° sÊŸá´á´›s", callback_data="game_slots_info"),
        ],
        [
            InlineKeyboardButton("âš”ï¸ á´…á´œá´‡ÊŸ", callback_data="game_duel_info"),
            InlineKeyboardButton("ðŸŽ° ÊŸá´á´›á´›á´‡Ê€Ê", callback_data="game_lottery_info"),
        ],
        [
            InlineKeyboardButton("ðŸ¦ Êœá´‡Éªsá´›", callback_data="heist_menu"),
            InlineKeyboardButton("ðŸ›¡ï¸ á´˜Ê€á´á´›á´‡á´„á´›", callback_data="game_protect_info"),
        ],
        [Buttons.back(back_callback)],
    ])

def back_button(callback: str = "help_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[Buttons.back(callback)]])

def confirm_keyboard(action: str, cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("âœ… á´„á´É´Ò“ÉªÊ€á´", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("âŒ á´„á´€É´á´„á´‡ÊŸ", callback_data=cancel_callback),
        ]
    ])

