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

import os
import sys
import logging
from threading import Thread

# --- CRITICAL FIX: MUST BE AT THE VERY TOP ---
# Prevents Heroku/Cloud crashes due to Git/Path issues
os.environ["GIT_PYTHON_REFRESH"] = "quiet"
# -----------------------------------------------

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

# --- INTERNAL IMPORTS ---
from fenix_baby.config import TOKEN, PORT
from fenix_baby.utils import track_group, log_to_channel, BOT_NAME

# --- IMPORT ALL PLUGINS ---
from fenix_baby.plugins import (
    start,
    economy,
    game,
    admin,
    broadcast,
    fun,
    events,
    welcome,
    ping,
    chatbot,
    riddle,
    social,
    ai_media,
    waifu,
    collection,
    shop,
    daily,
    heist,
    games_extra,
)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- FLASK SERVER (Health Check) ---
app = Flask(__name__)


@app.route("/")
def health():
    """Health check endpoint for Heroku/Cloud platforms."""
    return "Alive"


@app.route("/health")
def health_detailed():
    """Detailed health check."""
    return {
        "status": "ok",
        "bot": BOT_NAME,
        "service": "FenixBabyBot",
    }


def run_flask():
    """Run Flask on 0.0.0.0 to bind to Heroku's external port."""
    try:
        app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except Exception as e:
        logger.error(f"Flask error: {e}")


# --- STARTUP LOGIC ---
async def post_init(application):
    """Runs immediately after bot connects to Telegram."""
    logger.info("ðŸš€ Bot initialization starting...")

    try:
        # Set the blue "Menu" button in Telegram
        await application.bot.set_my_commands(
            [
                ("start", "ðŸŒ¸ Main Menu"),
                ("help", "ðŸ“– Command Diary"),
                ("bal", "ðŸ‘› Check Wallet & Rank"),
                ("kill", "ðŸ”ª Murder for Loot"),
                ("rob", "ðŸ’° Steal Coins"),
                ("give", "ðŸ’¸ Transfer Coins"),
                ("daily", "ðŸ“… Daily Reward"),
                ("shop", "ðŸ›’ Item Shop"),
                ("ranking", "ðŸ† Global Leaderboard"),
                ("wpropose", "ðŸ’ Waifu Propose"),
                ("wmarry", "ðŸ’’ Waifu Random"),
                ("propose", "ðŸ’ Marry User"),
                ("couple", "ðŸ’˜ Match Maker"),
                ("marry", "ðŸ’ž Check Status"),
                ("divorce", "ðŸ’” Break Up"),
                ("claim", "ðŸ’Ž Claim Group Bonus"),
                ("draw", "ðŸŽ¨ AI Art"),
                ("speak", "ðŸ—£ï¸ AI Voice"),
                ("dice", "ðŸŽ² Gamble"),
                ("protect", "ðŸ›¡ï¸ Buy Immunity"),
                ("revive", "âœ¨ Revive"),
                ("chatbot", "ðŸ§  AI Settings"),
                ("heist", "ðŸ¦ Team Heist"),
                ("duel", "âš”ï¸ PvP Duel"),
                ("lottery", "ðŸŽ° Try Your Luck"),
                ("ping", "ðŸ“¶ Status"),
                ("update", "ðŸ”„ Update Bot"),
            ]
        )
        logger.info("âœ… Menu commands set successfully")

        # Get bot info
        bot_info = await application.bot.get_me()
        logger.info(f"âœ… Logged in as @{bot_info.username} (ID: {bot_info.id})")

        # Send "Online" Log to Channel
        try:
            await log_to_channel(
                application.bot,
                "start",
                {
                    "user": "System",
                    "chat": "Cloud Server",
                    "action": f"{BOT_NAME} (@{bot_info.username}) is now Online! ðŸš€",
                },
            )
            logger.info("âœ… Startup log sent to logger channel")
        except Exception as log_err:
            logger.warning(f"âš ï¸ Could not send startup log: {log_err}")

    except Exception as e:
        logger.error(f"âŒ Post-init error: {e}", exc_info=True)
        raise


async def error_handler(update: object, context):
    """Handle errors gracefully without crashing."""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    
    # Optionally send error notification
    if isinstance(update, Update) and update.effective_chat:
        try:
            await update.effective_chat.send_message(
                f"âŒ An error occurred. Admin notified.\nError: {str(context.error)[:100]}"
            )
        except Exception:
            pass


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Start Web Server (Background Thread)
    logger.info("ðŸŒ Starting Flask health check server...")
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"âœ… Flask server running on 0.0.0.0:{PORT}")

    # 2. Check Token
    if not TOKEN:
        logger.critical("BOT_TOKEN is missing. Check fenix_baby/config.py or environment variables.")
        sys.exit(1)

    # Optimization: Pre-warm the database
    from fenix_baby.database import users_collection
    try:
        users_collection.find_one()
        logger.info("âœ… Database pre-warmed")
    except Exception as e:
        logger.error(f"âš ï¸ Database pre-warm failed: {e}")

    try:
        # 3. Configure Network (High Timeouts for Stability)
        logger.info("ðŸ”§ Configuring network settings...")
        t_request = HTTPXRequest(
            connection_pool_size=100,
            connect_timeout=60.0,
            read_timeout=60.0,
            write_timeout=60.0,
            pool_timeout=60.0,
        )

        # 4. Build Application
        logger.info("ðŸ—ï¸ Building bot application...")
        app_bot = (
            ApplicationBuilder()
            .token(TOKEN)
            .request(t_request)
            .post_init(post_init)
            .concurrent_updates(True)
            .build()
        )

        # Add error handler
        app_bot.add_error_handler(error_handler)

        # ================= REGISTER HANDLERS =================

        logger.info("ðŸ“ Registering command handlers...")

        # --- Basics ---
        app_bot.add_handler(CommandHandler("start", start.start))
        app_bot.add_handler(CommandHandler("help", start.help_command))
        app_bot.add_handler(CommandHandler("ping", ping.ping))
        app_bot.add_handler(CallbackQueryHandler(ping.ping_callback, pattern="^sys_stats$"))
        app_bot.add_handler(CallbackQueryHandler(start.help_callback, pattern="^help_"))
        app_bot.add_handler(
            CallbackQueryHandler(start.help_callback, pattern="^return_start$")
        )

        # --- Economy ---
        app_bot.add_handler(CommandHandler("register", economy.register))
        app_bot.add_handler(CommandHandler("bal", economy.balance))
        app_bot.add_handler(
            CallbackQueryHandler(economy.inventory_callback, pattern="^inv_")
        )
        app_bot.add_handler(CommandHandler("ranking", economy.ranking))
        app_bot.add_handler(CommandHandler("give", economy.give))
        app_bot.add_handler(CommandHandler("claim", economy.claim))
        app_bot.add_handler(CommandHandler("daily", daily.daily))

        # --- Shop ---
        app_bot.add_handler(CommandHandler("shop", shop.shop_menu))
        app_bot.add_handler(CommandHandler("buy", shop.buy))
        app_bot.add_handler(CallbackQueryHandler(shop.shop_callback, pattern="^shop_"))

        # --- RPG / Game ---
        app_bot.add_handler(CommandHandler("kill", game.kill))
        app_bot.add_handler(CommandHandler("rob", game.rob))
        app_bot.add_handler(CommandHandler("protect", game.protect))
        app_bot.add_handler(CommandHandler("revive", game.revive))

        # --- Heist Game ---
        app_bot.add_handler(CommandHandler("heist", heist.heist_command))
        app_bot.add_handler(CommandHandler("duel", games_extra.duel))
        app_bot.add_handler(CommandHandler("lottery", games_extra.lottery))
        app_bot.add_handler(CommandHandler("catch", collection.catch_command))
        app_bot.add_handler(CallbackQueryHandler(games_extra.duel_callback, pattern="^duel_"))
        app_bot.add_handler(CallbackQueryHandler(heist.heist_menu, pattern="^heist_menu$"))
        app_bot.add_handler(CallbackQueryHandler(heist.heist_start_callback, pattern="^heist_start_"))
        app_bot.add_handler(CallbackQueryHandler(heist.heist_join_callback, pattern="^heist_join_"))
        app_bot.add_handler(CallbackQueryHandler(heist.heist_execute_callback, pattern="^heist_execute_"))

        # --- Enhanced Menu Callbacks ---
        app_bot.add_handler(CallbackQueryHandler(start.game_info_callback, pattern="^game_"))
        app_bot.add_handler(CallbackQueryHandler(start.quick_action_callback, pattern="^quick_"))
        app_bot.add_handler(CallbackQueryHandler(start.help_callback, pattern="^menu_"))

        # --- Social ---
        app_bot.add_handler(CommandHandler("propose", social.propose))
        app_bot.add_handler(CommandHandler("marry", social.marry_status))
        app_bot.add_handler(CommandHandler("divorce", social.divorce))
        app_bot.add_handler(CommandHandler("couple", social.couple_game))
        app_bot.add_handler(
            CallbackQueryHandler(social.proposal_callback, pattern="^marry_")
        )

        # --- Waifu System ---
        app_bot.add_handler(CommandHandler("wpropose", waifu.wpropose))
        app_bot.add_handler(CommandHandler("wmarry", waifu.wmarry))
        for a in waifu.SFW_ACTIONS:
            app_bot.add_handler(CommandHandler(a, waifu.waifu_action))

        # --- Fun / AI / Media ---
        app_bot.add_handler(CommandHandler("dice", fun.dice))
        app_bot.add_handler(CommandHandler("slots", fun.slots))
        app_bot.add_handler(CommandHandler("riddle", riddle.riddle_command))
        app_bot.add_handler(CommandHandler("draw", ai_media.draw_command))
        app_bot.add_handler(CommandHandler("speak", ai_media.speak_command))
        app_bot.add_handler(CommandHandler("chatbot", chatbot.chatbot_menu))
        app_bot.add_handler(CommandHandler("ask", chatbot.ask_ai))
        app_bot.add_handler(
            CallbackQueryHandler(chatbot.chatbot_callback, pattern="^ai_")
        )

        # --- Admin & System ---
        app_bot.add_handler(CommandHandler("welcome", welcome.welcome_command))
        app_bot.add_handler(CommandHandler("broadcast", broadcast.broadcast))
        app_bot.add_handler(CommandHandler("sudo", admin.sudo_help))
        app_bot.add_handler(CommandHandler("sudolist", admin.sudolist))
        app_bot.add_handler(CommandHandler("addsudo", admin.addsudo))
        app_bot.add_handler(CommandHandler("rmsudo", admin.rmsudo))
        app_bot.add_handler(CommandHandler("addcoins", admin.addcoins))
        app_bot.add_handler(CommandHandler("rmcoins", admin.rmcoins))
        app_bot.add_handler(CommandHandler("freerevive", admin.freerevive))
        app_bot.add_handler(CommandHandler("unprotect", admin.unprotect))
        app_bot.add_handler(CommandHandler("cleandb", admin.cleandb))
        app_bot.add_handler(CommandHandler("stats", admin.stats))
        app_bot.add_handler(CommandHandler("update", admin.update_bot))
        app_bot.add_handler(
            CallbackQueryHandler(admin.confirm_handler, pattern="^cnf\\|")
        )

        logger.info("ðŸ“ Registering message handlers (groups)...")

        # --- EVENTS & MESSAGE LISTENERS (ORDER IS CRITICAL) ---

        # 1. Chat Member Updates (Join/Left Logs)
        app_bot.add_handler(
            ChatMemberHandler(events.chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER)
        )

        # 2. Welcome New Users
        app_bot.add_handler(
            MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome.new_member)
        )

        # 3. Collection (Waifu Guessing) - Group 1
        # Catches correct answers before AI sees them
        app_bot.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
                collection.collect_waifu,
            ),
            group=1,
        )

        # 4. Drop Check (Message Counting) - Group 2
        # Runs on every message to count for drops
        app_bot.add_handler(
            MessageHandler(filters.ChatType.GROUPS, collection.check_drops),
            group=2,
        )

        # 5. Riddle Answer - Group 3
        app_bot.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
                riddle.check_riddle_answer,
            ),
            group=3,
        )

        # 6. AI Chat (General Talk & Stickers) - Group 4
        # Must be later so it doesn't reply to game inputs
        app_bot.add_handler(
            MessageHandler(
                (filters.TEXT | filters.Sticker.ALL) & filters.ChatType.GROUPS & ~filters.COMMAND,
                chatbot.ai_message_handler,
            ),
            group=4,
        )

        # 7. Track Group (Silent db update) - Group 5
        app_bot.add_handler(
            MessageHandler(filters.ChatType.GROUPS, events.group_tracker),
            group=5,
        )

        logger.info("All handlers registered successfully.")
        logger.info(f"{BOT_NAME} starting polling...")

        # 8. Start Polling
        app_bot.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )

    except KeyboardInterrupt:
        logger.info("âš ï¸ Bot interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"âŒ Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)

