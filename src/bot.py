from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from src.app.service.tenant import TenantService
from src.app.service.admin import AdminService
from src.app.service.call_back import CallbackService
from src.app.utils.scheduler import start_scheduler
from src.app.utils.config import config
from src.app.utils.database import init_db, reset_db, seed_data
from src.app.utils.helpers import Logger
import asyncio

logger = Logger(__name__)

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    reset_db()
    logger.info("Database reset successfully.")
    init_db()
    logger.info("Database initialized successfully.")
    seed_data()
    logger.info("Database seeded with initial data.")

    # Validate admin IDs at startup and keep only reachable ones.
    async def _validate_admins(bot, admin_ids):
        valid = []
        for a in admin_ids:
            try:
                await bot.get_chat(a)
                valid.append(a)
            except Exception as e:
                logger.error(f"Admin {a} unreachable at startup: {e}")
        return valid

    try:
        validated = asyncio.get_event_loop().run_until_complete(
            _validate_admins(app.bot, config.ADMIN_IDS)
        )
    except RuntimeError:
        validated = config.ADMIN_IDS

    app.bot_data["admins"] = validated
    logger.info(f"Admin IDs loaded: {validated}")

    app.add_handler(CommandHandler("start", TenantService.start))
    app.add_handler(CommandHandler("status", AdminService.status))
    app.add_handler(CommandHandler("reset", AdminService.reset))
    app.add_handler(CallbackQueryHandler(CallbackService.handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, TenantService.handle_receipt))

    start_scheduler(app)

    app.run_polling()

if __name__ == "__main__":
    main()