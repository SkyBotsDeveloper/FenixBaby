import functools
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}\n{traceback.format_exc()}")
            
            error_messages = {
                "Forbidden": "❌ I don't have permission to do that.",
                "Chat not found": "❌ Chat not found or I was removed.",
                "User not found": "❌ User not found.",
                "Message is not modified": None,
                "Query is too old": None,
                "Bad Request": "❌ Something went wrong. Try again.",
            }
            
            error_str = str(e)
            response = None
            for key, msg in error_messages.items():
                if key in error_str:
                    response = msg
                    break
            
            if response is None and "Query" not in error_str and "modified" not in error_str:
                response = "❌ <b>Oops!</b> Something went wrong.\n<i>Please try again later.</i>"
            
            if response:
                try:
                    if update.callback_query:
                        await update.callback_query.answer(response[:200], show_alert=True)
                    elif update.message:
                        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
                except:
                    pass
            
            return None
    return wrapper

def require_private(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type != "private":
            await update.message.reply_text(
                "📩 <b>DM Only!</b>\n<i>Use this command in private chat.</i>",
                parse_mode=ParseMode.HTML
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_group(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type == "private":
            await update.message.reply_text(
                "👥 <b>Groups Only!</b>\n<i>Use this command in a group.</i>",
                parse_mode=ParseMode.HTML
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper

def cooldown(seconds: int):
    cooldowns = {}
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            import time
            user_id = update.effective_user.id
            cmd = func.__name__
            key = f"{user_id}_{cmd}"
            
            now = time.time()
            if key in cooldowns:
                remaining = cooldowns[key] - now
                if remaining > 0:
                    await update.message.reply_text(
                        f"⏳ <b>Cooldown!</b> Wait <code>{int(remaining)}s</code>",
                        parse_mode=ParseMode.HTML
                    )
                    return None
            
            cooldowns[key] = now + seconds
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
