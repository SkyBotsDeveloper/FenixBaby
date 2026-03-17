import logging
import random

from openai import AsyncOpenAI

from fenix_baby.config import (
    ELITE_LLM_API_KEY,
    ELITE_LLM_BASE_URL,
    ELITE_LLM_MODEL,
    ELITE_LLM_UTILITY_MODEL,
)

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

LOCAL_RESPONSES = {
    "greeting": [
        "Hii, kaise ho?",
        "Heyy, bolo na.",
        "Aaj kya scene hai?",
        "Hello ji, sun rahi hoon.",
    ],
    "emotion_happy": [
        "Aww, nicee.",
        "Yeh toh mast hai.",
        "Hehe, cute.",
        "Badiya laga sunke.",
    ],
    "emotion_sad": [
        "Aww, kya hua?",
        "Itna mat socho, theek ho jayega.",
        "Main hoon na, bolo.",
        "Dil chhota mat karo.",
    ],
    "emotion_angry": [
        "Oho, gussa kaafi high hai.",
        "Thoda chill karo.",
        "Theek hai, pehle shaant ho jao.",
        "Aise fire mode me mat raho.",
    ],
    "emotion_love": [
        "Aww, kitne sweet ho.",
        "Tum bhi na.",
        "Bohot pyaare ho.",
        "Dil jeet liya.",
    ],
    "confused": [
        "Hmm, thoda aur clear bolo.",
        "Samjha do properly.",
        "Context do zara.",
        "Phir se bolo, miss ho gaya.",
    ],
    "fallback": [
        "Achha ji.",
        "Hmm, aur batao.",
        "Interesting.",
        "Theek hai, sun rahi hoon.",
    ],
}

EMOTION_STICKERS = {
    "happy": ["😊", "🥰", "✨", "🎉"],
    "sad": ["🥺", "😔", "💔"],
    "angry": ["😤", "😠", "🔥"],
    "love": ["💖", "💕", "😘"],
    "thinking": ["🤔", "💭"],
    "excited": ["🎉", "✨", "🤩"],
    "shy": ["🙈", "☺️"],
    "playful": ["😜", "😏", "👀"],
}


def _get_client() -> AsyncOpenAI | None:
    global _client
    if not ELITE_LLM_API_KEY:
        return None
    if _client is None:
        _client = AsyncOpenAI(
            api_key=ELITE_LLM_API_KEY,
            base_url=ELITE_LLM_BASE_URL.rstrip("/"),
        )
    return _client


def _extract_text_content(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")).strip())
                continue

            item_type = getattr(item, "type", None)
            if item_type == "text":
                text_value = getattr(item, "text", "")
                if isinstance(text_value, str):
                    parts.append(text_value.strip())
                else:
                    nested_text = getattr(text_value, "value", "")
                    if nested_text:
                        parts.append(str(nested_text).strip())

        return " ".join(part for part in parts if part).strip()

    return ""


async def _chat_completion(
    messages: list,
    *,
    model: str,
    max_tokens: int = 150,
    temperature: float | None = 0.85,
) -> str | None:
    client = _get_client()
    if client is None:
        return None

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    try:
        response = await client.chat.completions.create(**payload)
        if not response or not response.choices:
            return None

        content = response.choices[0].message.content
        text = _extract_text_content(content)
        return text or None
    except Exception as exc:
        logger.warning("Elite LLM API request failed: %s", exc)
        return None


def detect_emotion(text: str) -> str:
    text_lower = text.lower()

    love_words = [
        "love", "pyaar", "pyar", "dil", "heart", "miss", "baby",
        "babu", "jaan", "darling", "sweetheart", "cute",
    ]
    sad_words = [
        "sad", "cry", "dukhi", "rona", "hurt", "pain",
        "alone", "akela", "depressed", "upset", "sorry",
    ]
    angry_words = [
        "angry", "gussa", "hate", "nafrat", "idiot", "stupid",
        "pagal", "shut up", "chup", "bewakoof",
    ]
    happy_words = [
        "happy", "khushi", "excited", "yay", "wow", "amazing",
        "awesome", "great", "good", "achha", "maza", "fun",
    ]
    greeting_words = [
        "hi", "hello", "hey", "hii", "hiii", "namaste",
        "kaise ho", "kya haal", "wassup", "sup",
    ]

    if any(word in text_lower for word in love_words):
        return "love"
    if any(word in text_lower for word in sad_words):
        return "sad"
    if any(word in text_lower for word in angry_words):
        return "angry"
    if any(word in text_lower for word in happy_words):
        return "happy"
    if any(word in text_lower for word in greeting_words):
        return "greeting"
    if "?" in text:
        return "thinking"

    return "neutral"


def get_emotion_emoji(emotion: str) -> str:
    if emotion in EMOTION_STICKERS:
        return random.choice(EMOTION_STICKERS[emotion])
    return random.choice(EMOTION_STICKERS["happy"])


def get_local_response(user_input: str) -> str:
    emotion = detect_emotion(user_input)

    if emotion == "greeting":
        return random.choice(LOCAL_RESPONSES["greeting"])
    if emotion == "love":
        return random.choice(LOCAL_RESPONSES["emotion_love"])
    if emotion == "sad":
        return random.choice(LOCAL_RESPONSES["emotion_sad"])
    if emotion == "angry":
        return random.choice(LOCAL_RESPONSES["emotion_angry"])
    if emotion == "happy":
        return random.choice(LOCAL_RESPONSES["emotion_happy"])
    if emotion == "thinking":
        return random.choice(LOCAL_RESPONSES["confused"])
    return random.choice(LOCAL_RESPONSES["fallback"])


async def ask_ai(
    messages: list,
    max_tokens: int = 180,
    temperature: float = 0.85,
    user_input: str = "",
    model: str | None = None,
) -> str:
    response = await _chat_completion(
        messages,
        model=model or ELITE_LLM_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if response:
        return response
    return get_local_response(user_input or messages[-1].get("content", ""))


async def ask_ai_raw(
    system_prompt: str,
    user_input: str,
    max_tokens: int = 150,
    temperature: float = 0.8,
    model: str | None = None,
) -> str | None:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    return await _chat_completion(
        messages,
        model=model or ELITE_LLM_UTILITY_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
    )
