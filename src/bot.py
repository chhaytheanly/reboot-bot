from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    TypeHandler
)
from src.app.service.tenant import TenantService
from src.app.service.admin import AdminService
from src.app.service.call_back import CallbackService
from src.app.utils.scheduler import start_scheduler
from src.app.utils.config import config
from src.app.utils.helpers.logging import Logger
import asyncio

logger = Logger(__name__)


def main():
    
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
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
    
    async def setup_menu(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("myroom", "My Room"),
            BotCommand("pay", "Pay Rent"),
            BotCommand("history", "Payment History"),
        ])
        await app.bot.set_chat_menu_button(menu_button={"type": "commands"})
        
    app.add_handler(CommandHandler("start", TenantService.start))
    app.add_handler(CommandHandler("myroom", TenantService.show_my_room))
    app.add_handler(CommandHandler("pay", TenantService.show_qr))
    app.add_handler(CommandHandler("history", TenantService.show_payment_history))
    app.add_handler(CommandHandler("help", TenantService.show_help))

    app.add_handler(CommandHandler("status", AdminService.status))
    app.add_handler(CommandHandler("paid", AdminService.paid_done))
    app.add_handler(CommandHandler("reset", AdminService.reset))
    app.add_handler(CommandHandler("panel", AdminService.panel))
    app.add_handler(CommandHandler("remind", AdminService.send_reminder))
    app.add_handler(CommandHandler("adminhelp", AdminService.admin_help))
    app.add_handler(CallbackQueryHandler(CallbackService.handle_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🏠 My Room$"),
        TenantService.show_my_room
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^💰 Pay Rent$"),
        TenantService.show_qr
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📜 Payment History$"),
        TenantService.show_payment_history
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^❓ Help$"),
        TenantService.show_help
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📊 Room Status$"),
        AdminService.status
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^✅ Paid Rooms$"),
        AdminService.paid_done
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔄 Reset Month$"),
        AdminService.reset
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^⏰ Send Reminders$"),
        AdminService.send_reminder
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^❓ Admin Help$"),
        AdminService.admin_help
    ))

    app.add_handler(MessageHandler(filters.PHOTO, TenantService.handle_receipt))

    start_scheduler(app)
    
    app.post_init = setup_menu
    app.run_polling()


if __name__ == "__main__":
    main()
