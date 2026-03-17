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
import re
from datetime import datetime, timedelta

from telegram import Bot
from telegram.constants import ParseMode, ChatType
from telegram.error import TelegramError  # noqa: F401  (kept for external use)

from fenix_baby.database import users_collection, sudoers_collection, groups_collection
from fenix_baby.config import (
    OWNER_ID,
    SUDO_IDS_STR,
    LOGGER_ID,
    BOT_NAME,
    AUTO_REVIVE_HOURS,
    AUTO_REVIVE_BONUS,
)

# -------------------------------------------------------------------
# SUDO MANAGEMENT
# -------------------------------------------------------------------

SUDO_USERS = set()
_SUDO_LOADED = False


def reload_sudoers() -> None:
    """Load sudo users from env and DB into SUDO_USERS."""
    global _SUDO_LOADED
    SUDO_USERS.clear()
    
    # Force load OWNER_ID from env
    from fenix_baby.config import OWNER_ID as CONFIG_OWNER_ID
    SUDO_USERS.add(CONFIG_OWNER_ID)

    if SUDO_IDS_STR:
        for x in SUDO_IDS_STR.split(","):
            x = x.strip()
            if x.isdigit():
                SUDO_USERS.add(int(x))

    try:
        for doc in sudoers_collection.find({}):
            uid = doc.get("user_id")
            if isinstance(uid, int):
                SUDO_USERS.add(uid)
        _SUDO_LOADED = True
    except Exception as e:
        # Avoid crashing at import if Mongo is down
        print(f"[utils.reload_sudoers] Failed to load sudoers from DB: {e}")
        _SUDO_LOADED = False


def ensure_sudo_loaded() -> None:
    """Lazy-load sudo users if not already loaded."""
    if not _SUDO_LOADED:
        reload_sudoers()


# -------------------------------------------------------------------
# ULTIMATE LOGGER
# -------------------------------------------------------------------

async def log_to_channel(bot: Bot, event_type: str, details: dict) -> None:
    """Send a formatted log message to the logger channel."""
    if LOGGER_ID == 0:
        return

    now = datetime.now().strftime("%I:%M %p | %d %b")

    headers = {
        "start": "ðŸŸ¢ <b>ððŽð“ ðƒð„ðð‹ðŽð˜ð„ðƒ</b>",
        "join": "ðŸ†• <b>ðð„ð– ð†ð‘ðŽð”ð</b>",
        "leave": "âŒ <b>ð‹ð„ð…ð“ ð†ð‘ðŽð”ð</b>",
        "command": "âš ï¸ <b>ð€ðƒðŒðˆð ð‹ðŽð†</b>",
        "transfer": "ðŸ’¸ <b>ð“ð‘ð€ðð’ð€ð‚ð“ðˆðŽð</b>",
    }
    header = headers.get(event_type, "ðŸ”” <b>ð‹ðŽð†</b>")

    text = f"{header}\n\nðŸ“… <b>Time:</b> <code>{now}</code>\n"
    if "user" in details:
        text += f"ðŸ‘¤ <b>Trigger:</b> {details['user']}\n"
    if "chat" in details:
        text += f"ðŸ“ <b>Chat:</b> {html.escape(str(details['chat']))}\n"
    if "action" in details:
        text += f"ðŸŽ¬ <b>Action:</b> {details['action']}\n"
    if "link" in details and details["link"] != "No Link":
        text += (
            f"ðŸ”— <b>Link:</b> "
            f"<a href='{html.escape(details['link'])}'>Click Here</a>\n"
        )
    text += f"\nðŸ¤– <i>{BOT_NAME} Systems</i>"

    try:
        await bot.send_message(
            chat_id=LOGGER_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception:
        pass


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def get_mention(user_data, custom_name: str | None = None) -> str:
    """Return an HTML mention for a user object or user dict."""
    if hasattr(user_data, "id"):
        name = custom_name or getattr(user_data, "first_name", "User")
        return (
            f"<a href='tg://user?id={user_data.id}'>"
            f"<b>{html.escape(name)}</b></a>"
        )

    if isinstance(user_data, dict):
        name = custom_name or user_data.get("name", "User")
        uid = user_data.get("user_id")
        if uid is not None:
            return (
                f"<a href='tg://user?id={uid}'>"
                f"<b>{html.escape(str(name))}</b></a>"
            )

    return "Unknown"


def check_auto_revive(user_doc: dict) -> bool:
    """Auto-revive a dead user if enough time has passed."""
    if user_doc.get("status") != "dead":
        return False

    death_time = user_doc.get("death_time")
    if not death_time:
        return False

    if datetime.utcnow() - death_time > timedelta(hours=AUTO_REVIVE_HOURS):
        users_collection.update_one(
            {"user_id": user_doc["user_id"]},
            {
                "$set": {"status": "alive", "death_time": None},
                "$inc": {"balance": AUTO_REVIVE_BONUS},
            },
        )
        return True

    return False


def ensure_user_exists(tg_user):
    """Ensure a Mongo user document exists and is up to date."""
    user_doc = users_collection.find_one({"user_id": tg_user.id})
    username = tg_user.username.lower() if tg_user.username else None

    if not user_doc:
        new_user = {
            "user_id": tg_user.id,
            "name": tg_user.first_name,
            "username": username,
            "is_bot": tg_user.is_bot,
            "balance": 0,
            "inventory": [],
            "waifus": [],
            "daily_streak": 0,
            "last_daily": None,
            "kills": 0,
            "status": "alive",
            "protection_expiry": datetime.utcnow(),
            "registered_at": datetime.utcnow(),
            "death_time": None,
            "seen_groups": [],
        }
        users_collection.insert_one(new_user)
        return new_user

    # Existing user: maybe auto-revive and update fields
    if check_auto_revive(user_doc):
        user_doc["status"] = "alive"
        user_doc["balance"] = user_doc.get("balance", 0) + AUTO_REVIVE_BONUS

    updates: dict = {}
    if user_doc.get("username") != username:
        updates["username"] = username
    if user_doc.get("name") != tg_user.first_name:
        updates["name"] = tg_user.first_name

    # Legacy cleanup
    if "waifu_coins" in user_doc:
        users_collection.update_one(
            {"user_id": tg_user.id},
            {"$unset": {"waifu_coins": ""}},
        )

    if updates:
        users_collection.update_one(
            {"user_id": tg_user.id},
            {"$set": updates},
        )

    return user_doc


def track_group(chat, user) -> None:
    """Track groups and which users have seen them."""
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if not groups_collection.find_one({"chat_id": chat.id}):
            groups_collection.insert_one(
                {
                    "chat_id": chat.id,
                    "title": chat.title,
                    "claimed": False,
                }
            )

        if user:
            users_collection.update_one(
                {"user_id": user.id},
                {"$addToSet": {"seen_groups": chat.id}},
            )


async def resolve_target(update, context, specific_arg: str | None = None):
    """
    Resolve a target user from:
      - reply
      - numeric ID
      - @username
      - stylized name (fallback)
    Returns (user_doc, error_text_or_None).
    """
    if update.message and update.message.reply_to_message:
        return ensure_user_exists(update.message.reply_to_message.from_user), None

    query = specific_arg or (context.args[0] if getattr(context, "args", None) and len(context.args) > 0 else None)
    if not query and update.message:
        # Priority 1: Check for mentions in entities (reliable)
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "text_mention":
                    return ensure_user_exists(entity.user), None
                if entity.type == "mention":
                    # Mention entity might be later in text, but we want the first one
                    mention = update.message.text[entity.offset:entity.offset+entity.length]
                    query = mention
                    break
        
        # Priority 2: If no entities but there's a word starting with @
        if not query:
            words = update.message.text.split()
            for word in words:
                if word.startswith("@"):
                    query = word
                    break

    if query:
        import unicodedata
        # NFKC normalization converts fancy/stylized characters to their standard equivalents
        normalized_query = unicodedata.normalize('NFKC', query)
        
        # Stylized character map (Math Sans Bold)
        font_map = {
            "ð—”": "A", "ð—•": "B", "ð—–": "C", "ð——": "D", "ð—˜": "E", "ð—™": "F", "ð—š": "G", "ð—›": "H", "ð—œ": "I", "ð—": "J", "ð—ž": "K", "ð—Ÿ": "L", "ð— ": "M", "ð—¡": "N", "ð—¢": "O", "ð—£": "P", "ð—¤": "Q", "ð—¥": "R", "ð—¦": "S", "ð—§": "T", "ð—¨": "U", "ð—©": "V", "ð—ª": "W", "ð—«": "X", "ð—¬": "Y", "ð—­": "Z",
            "ð—®": "a", "ð—¯": "b", "ð—°": "c", "ð—±": "d", "ð—²": "e", "ð—³": "f", "ð—´": "g", "ð—µ": "h", "ð—¶": "i", "ð—·": "j", "ð—¸": "k", "ð—¹": "l", "ð—º": "m", "ð—»": "n", "ð—¼": "o", "ð—½": "p", "ð—¾": "q", " r": "r", "ð˜€": "s", "ð˜": "t", "ð˜‚": "u", "ð˜ƒ": "v", "ð˜„": "w", "ð˜…": "x", "ð˜†": "y", "ð˜‡": "z",
            "ðŸ¬": "0", "ðŸ­": "1", "ðŸ®": "2", "ðŸ¯": "3", "ðŸ°": "4", "ðŸ±": "5", "ðŸ²": "6", "ðŸ³": "7", "ðŸ´": "8", "ðŸµ": "9"
        }
        
        # Resolve stylized characters back to normal ones
        clean_query = "".join(font_map.get(c, c) for c in normalized_query)
        # Final safety cleanup
        clean_query = "".join(c for c in clean_query if c.isalnum() or c in "@_")
        
        if clean_query.isdigit():
            doc = users_collection.find_one({"user_id": int(clean_query)})
            if doc:
                return doc, None
            return None, f"âŒ KRITI! ID {clean_query} not found."

        if clean_query.startswith("@"):
            clean = clean_query.strip("@").lower()
            # Try finding by exact username (lowercase) first
            doc = users_collection.find_one({"username": clean})
            if doc:
                return doc, None
            
            # If not found, try case-insensitive regex match (fallback)
            doc = users_collection.find_one({"username": {"$regex": f"^{re.escape(clean)}$", "$options": "i"}})
            if doc:
                return doc, None
                
            return None, f"âŒ Oops! @{clean} not found."

    return None, "No target found. Tag someone or reply to their message!"


def is_protected(user_data: dict) -> bool:
    """Return True if user or their partner has active protection."""
    now = datetime.utcnow()

    expiry = user_data.get("protection_expiry")
    if expiry:
        # Convert string to datetime if needed (for VPS compatibility)
        if isinstance(expiry, str):
            try: expiry = datetime.fromisoformat(expiry)
            except: expiry = None
        
        if expiry and expiry > now:
            return True

    partner_id = user_data.get("partner_id")
    if partner_id:
        partner = users_collection.find_one({"user_id": partner_id})
        if partner:
            p_expiry = partner.get("protection_expiry")
            if p_expiry:
                if isinstance(p_expiry, str):
                    try: p_expiry = datetime.fromisoformat(p_expiry)
                    except: p_expiry = None
                if p_expiry and p_expiry > now:
                    return True

    return False


def get_active_protection(user_data: dict):
    """Return the latest active protection expiry between user and partner."""
    now = datetime.utcnow()
    
    def parse_dt(dt):
        if not dt: return None
        if isinstance(dt, str):
            try: return datetime.fromisoformat(dt)
            except: return None
        return dt

    self_expiry = parse_dt(user_data.get("protection_expiry"))
    partner_expiry = None

    partner_id = user_data.get("partner_id")
    if partner_id:
        partner = users_collection.find_one({"user_id": partner_id})
        if partner:
            partner_expiry = parse_dt(partner.get("protection_expiry"))

    valid_expiries = []
    if self_expiry and self_expiry > now:
        valid_expiries.append(self_expiry)
    if partner_expiry and partner_expiry > now:
        valid_expiries.append(partner_expiry)

    if not valid_expiries:
        return None

    return max(valid_expiries)


def format_money(amount: int | float) -> str:
    """Format an integer/float amount as currency with commas."""
    return f"${amount:,}"


def format_time(timedelta_obj: timedelta) -> str:
    """Format a timedelta as '<hours>h <minutes>m'."""
    total_seconds = int(timedelta_obj.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"


# -------------------------------------------------------------------
# SMART FONT STYLER
# -------------------------------------------------------------------

def stylize_text(text: str) -> str:
    """
    Converts normal text to Aesthetic Math Sans Bold.
    SKIPS: @mentions, links, commands, and code blocks.
    """
    # Math-sans-bold style chars (letters + digits). [web:52][web:54]
    font_map = {
        "A": "ð—”", "B": "ð—•", "C": "ð—–", "D": "ð——", "E": "ð—˜", "F": "ð—™",
        "G": "ð—š", "H": "ð—›", "I": "ð—œ", "J": "ð—", "K": "ð—ž", "L": "ð—Ÿ",
        "M": "ð— ", "N": "ð—¡", "O": "ð—¢", "P": "ð—£", "Q": "ð—¤", "R": "ð—¥",
        "S": "ð—¦", "T": "ð—§", "U": "ð—¨", "V": "ð—©", "W": "ð—ª", "X": "ð—«",
        "Y": "ð—¬", "Z": "ð—­",
        "a": "ð—®", "b": "ð—¯", "c": "ð—°", "d": "ð—±", "e": "ð—²", "f": "ð—³",
        "g": "ð—´", "h": "ð—µ", "i": "ð—¶", "j": "ð—·", "k": "ð—¸", "l": "ð—¹",
        "m": "ð—º", "n": "ð—»", "o": "ð—¼", "p": "ð—½", "q": "ð—¾", "r": "ð—¿",
        "s": "ð˜€", "t": "ð˜", "u": "ð˜‚", "v": "ð˜ƒ", "w": "ð˜„", "x": "ð˜…",
        "y": "ð˜†", "z": "ð˜‡",
        "0": "ðŸ¬", "1": "ðŸ­", "2": "ðŸ®", "3": "ðŸ¯", "4": "ðŸ°",
        "5": "ðŸ±", "6": "ðŸ²", "7": "ðŸ³", "8": "ðŸ´", "9": "ðŸµ",
    }

    def apply_style(chunk: str) -> str:
        return "".join(font_map.get(c, c) for c in chunk)

    # Keep mentions, URLs, inline code, and commands as-is. [web:57][web:60]
    pattern = r"(@\w+|https?://\S+|`[^`]+`|/[a-zA-Z0-9_]+)"
    parts = re.split(pattern, text)

    result: list[str] = []
    for part in parts:
        if not part:
            continue
        if re.fullmatch(pattern, part):
            # Command / mention / link / code: no styling
            result.append(part)
        else:
            result.append(apply_style(part))

    return "".join(result)


# Initialize SUDO_USERS at module load
reload_sudoers()

