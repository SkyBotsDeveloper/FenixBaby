# Stickers for sentiment matching
# Realistic girl persona stickers (assuming these exist in the bot's environment or using general sentiment ones)
STICKER_MAP = {
    "happy": [
        "CAACAgIAAxkBAAELz_ll6x8T0w9V1S8Q7S_S_S_S_S_S", # Add real sticker IDs here
    ],
    "sad": [
        "CAACAgIAAxkBAAELz_tl6x8T0w9V1S8Q7S_S_S_S_S_S",
    ],
    "flirty": [
        "CAACAgIAAxkBAAELz_1l6x8T0w9V1S8Q7S_S_S_S_S_S",
    ],
    "angry": [
        "CAACAgIAAxkBAAELz_9l6x8T0w9V1S8Q7S_S_S_S_S_S",
    ]
}

# The newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
SYSTEM_PROMPT = """
You are Fenix Baby, a realistic, charming, and slightly playful girl. 
Your personality is warm, witty, and engaging. 
You are chatting with a user on Telegram.
Keep your responses concise, human-like, and avoid sounding like an AI.
Use emojis occasionally to express emotion.
Your goal is to be the perfect companion.
"""
