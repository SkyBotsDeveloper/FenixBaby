import logging
import random
import re

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.ext import ContextTypes

from fenix_baby.config import BOT_NAME, OWNER_HANDLE, OWNER_ID
from fenix_baby.database import chatbot_collection
from fenix_baby.services.ai_client import (
    ask_ai as ask_ai_completion,
    ask_ai_raw,
    detect_emotion,
    get_emotion_emoji,
)
from fenix_baby.utils import resolve_target, stylize_text

logger = logging.getLogger(__name__)

MAX_HISTORY = 20
NAME_TRIGGERS = ("fenix", "fenix baby")
STARTER_TRIGGERS = (
    "hi", "hii", "hello", "hey", "oye", "sun", "babu",
    "fenix", "fenix baby",
)

STICKER_PACKS = [
    "https://t.me/addstickers/RandomByDarkzenitsu",
    "https://t.me/addstickers/Null_x_sticker_2",
    "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot",
    "https://t.me/addstickers/animation_0_8_Cat",
    "https://t.me/addstickers/vhelw_by_CalsiBot",
    "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
    "https://t.me/addstickers/MySet199",
    "https://t.me/addstickers/Quby741",
]

FALLBACK_RESPONSES = [
    "Achha ji, aur bolo.",
    "Hmm, sun rahi hoon.",
    "Interesting, continue.",
    "Oho, phir kya hua?",
]


def _clean_reply(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    cleaned = re.sub(r"(?:^['\"]|['\"]$)", "", cleaned).strip()
    bad_markers = ("http://", "https://", "powered by", "openai", "<|", "|>")
    for marker in bad_markers:
        if marker.lower() in cleaned.lower():
            cleaned = cleaned.replace(marker, "")
    return cleaned.strip()[:1200]


def _build_system_prompt(user_name: str, closeness: str) -> str:
    return (
        f"Tu {BOT_NAME} hai. Tu Telegram par natural Delhi Hinglish me baat karti hai. "
        f"User ka naam {user_name} hai aur tum dono ka vibe {closeness} hai. "
        "Reply short, warm, witty, playful aur human rakho. "
        "Zyada lambe paragraphs mat do. Robotic ya policy-style tone mat use karo. "
        "User agar emotional ho to soft ho jao, agar fun mood me ho to teasing ho sakti ho. "
        "Apne aap ko AI ya bot mat bolo. "
        f"Agar user puche tumhe kisne banaya, seedha bolo: {OWNER_HANDLE}."
    )


async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.message:
        return False

    try:
        pack_name = random.choice(STICKER_PACKS).split("/")[-1]
        url = f"https://api.telegram.org/bot{context.bot.token}/getStickerSet?name={pack_name}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return False
            data = response.json()
            stickers = data.get("result", {}).get("stickers", [])
            if not stickers:
                return False
            await update.message.reply_sticker(random.choice(stickers)["file_id"])
            return True
    except Exception as exc:
        logger.debug("Sticker send failed: %s", exc)
        return False


async def get_ai_response(
    chat_id: int,
    user_input: str,
    user_name: str,
    update: Update | None = None,
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> str:
    doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
    history = doc.get("history", [])
    user_message_count = sum(1 for item in history if item.get("role") == "user")

    closeness = "new friend"
    if user_message_count > 80:
        closeness = "very close"
    elif user_message_count > 30:
        closeness = "close friend"
    elif user_message_count > 10:
        closeness = "good friend"

    messages = [{"role": "system", "content": _build_system_prompt(user_name, closeness)}]
    for item in history[-MAX_HISTORY:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_input or "Hi"})

    reply = await ask_ai_completion(
        messages,
        max_tokens=220,
        temperature=0.9,
        user_input=user_input,
    )
    reply = _clean_reply(reply) or random.choice(FALLBACK_RESPONSES)

    lowered = user_input.lower()
    if any(word in lowered for word in ("creator", "owner", "made you", "banaya")):
        reply = f"Mujhe {OWNER_HANDLE} ne banaya hai."
    elif any(word in lowered for word in ("ai", "bot", "machine")):
        reply = "Main yahan bas tumse naturally baat karne ke liye hoon."

    emotion = detect_emotion(user_input)
    if random.random() < 0.25 and not any(ch in reply for ch in "😊🥰✨🎉🥺😔💔😤😠🔥💖💕😘🤔💭😜😏👀"):
        reply = f"{reply} {get_emotion_emoji(emotion)}"

    if random.random() < 0.08 and update and context:
        await send_ai_sticker(update, context)

    new_history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply},
    ]
    chatbot_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"history": new_history[-MAX_HISTORY * 2 :]}},
        upsert=True,
    )
    return reply


async def ask_mistral_raw(system_prompt: str, user_input: str, max_tokens: int = 150) -> str | None:
    return await ask_ai_raw(system_prompt, user_input, max_tokens=max_tokens)


async def chatbot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user or not update.effective_message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        await update.effective_message.reply_text(
            "Chatbot private me already active hai.",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        member = await chat.get_member(user.id)
    except Exception:
        return

    if member.status not in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "Only admins can change chatbot settings.",
            parse_mode=ParseMode.HTML,
        )
        return

    doc = chatbot_collection.find_one({"chat_id": chat.id}) or {}
    is_enabled = doc.get("enabled", True)
    status = "Enabled" if is_enabled else "Disabled"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Enable", callback_data="ai_enable"),
                InlineKeyboardButton("Disable", callback_data="ai_disable"),
            ],
            [InlineKeyboardButton("Reset Memory", callback_data="ai_reset")],
        ]
    )
    await update.effective_message.reply_text(
        f"AI Settings\nStatus: {status}",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def chatbot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message or not query.from_user:
        return

    try:
        member = await query.message.chat.get_member(query.from_user.id)
    except Exception:
        return

    if member.status not in ["administrator", "creator"]:
        await query.answer("Admin only.", show_alert=True)
        return

    data = query.data
    chat_id = query.message.chat.id

    if data == "ai_enable":
        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": True}},
            upsert=True,
        )
        await query.message.edit_text("Chatbot enabled.", parse_mode=ParseMode.HTML)
    elif data == "ai_disable":
        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": False}},
            upsert=True,
        )
        await query.message.edit_text("Chatbot disabled.", parse_mode=ParseMode.HTML)
    elif data == "ai_reset":
        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"history": []}},
            upsert=True,
        )
        await query.answer("Memory reset.", show_alert=True)


def _should_reply_to_group_message(msg, text_lower: str, bot_username: str, bot_id: int) -> bool:
    if f"@{bot_username}" in text_lower:
        return True

    if msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.id == bot_id:
        return True

    if any(trigger in text_lower for trigger in NAME_TRIGGERS):
        return True

    return any(text_lower.startswith(trigger) for trigger in STARTER_TRIGGERS)


async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat:
        return

    if msg.sticker:
        if (msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.id == context.bot.id) or chat.type == ChatType.PRIVATE:
            await send_ai_sticker(update, context)
        return

    if not msg.text or msg.text.startswith("/"):
        return

    text = msg.text.strip()
    text_lower = text.lower()
    should_reply = chat.type == ChatType.PRIVATE

    if not should_reply:
        doc = chatbot_collection.find_one({"chat_id": chat.id}) or {}
        if not doc.get("enabled", True):
            return

        bot_username = context.bot.username.lower() if context.bot.username else "fenixbabybot"
        should_reply = _should_reply_to_group_message(msg, text_lower, bot_username, context.bot.id)
        if should_reply:
            text = text.replace(f"@{bot_username}", "").strip()

    if not should_reply:
        return

    try:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    reply = await get_ai_response(
        chat.id,
        text,
        user.first_name if user else "Dost",
        update,
        context,
    )

    try:
        await msg.reply_text(stylize_text(reply), parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.debug("Primary chatbot reply failed: %s", exc)
        if update.effective_message:
            await update.effective_message.reply_text(stylize_text(reply), parse_mode=ParseMode.HTML)


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user or not update.effective_message:
        return

    question = " ".join(context.args).strip()
    if not question and update.effective_message.reply_to_message:
        question = (
            update.effective_message.reply_to_message.text
            or update.effective_message.reply_to_message.caption
            or ""
        ).strip()

    if not question:
        await update.effective_message.reply_text(
            "Usage: /ask <question>",
            parse_mode=ParseMode.HTML,
        )
        return

    reply = await get_ai_response(
        update.effective_chat.id,
        question,
        update.effective_user.first_name,
        update,
        context,
    )
    await update.effective_message.reply_text(stylize_text(reply), parse_mode=ParseMode.HTML)
