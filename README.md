# Fenix Baby

Fenix Baby is a Telegram bot with economy, RPG, waifu, media, and AI chat features. It is ready for Heroku worker deployment and uses a single OpenAI-compatible backend powered by Elite LLMs.

## Required env

```env
BOT_TOKEN=your_bot_token
MONGO_URI=your_mongodb_uri
OWNER_ID=your_telegram_id
ELITE_LLM_API_KEY=your_elite_llm_api_key
```

## Optional env

```env
MONGO_DB_NAME=fenix_baby_db
ELITE_LLM_BASE_URL=https://elite-llms-pro-042f44b0a301.herokuapp.com/v1
ELITE_LLM_MODEL=gpt-5-mini
ELITE_LLM_UTILITY_MODEL=gpt-4o-mini
LOGGER_ID=-100xxxxxxxxxx
SUPPORT_GROUP=https://t.me/FenixMusicSupport
SUPPORT_CHANNEL=https://t.me/FenixMusicSupport
OWNER_LINK=https://t.me/llFenixxll
OWNER_HANDLE=@llFenixxll
START_IMG_URL=https://files.catbox.moe/veuo1s.jpg
HELP_IMG_URL=https://files.catbox.moe/zpj2tc.jpg
WELCOME_IMG_URL=https://files.catbox.moe/7lkkx0.jpg
PORT=5000
```

## Heroku

1. Create a Heroku app.
2. Set the env vars above.
3. Deploy this repo.
4. Start the `worker` dyno from the included `Procfile`.

The app entrypoint is:

```bash
python FenixBaby.py
```

## Elite LLMs API

Default base URL:

```text
https://elite-llms-pro-042f44b0a301.herokuapp.com/v1
```

Used routes:

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

Default models:

- `gpt-5-mini` for main chat
- `gpt-4o-mini` for utility prompts like riddles, roasts, and narration

## Support

- Owner: [@llFenixxll](https://t.me/llFenixxll)
- Support: [FenixMusicSupport](https://t.me/FenixMusicSupport)
