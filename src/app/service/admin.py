from src.app.utils.helpers.logging import logger
from telegram import Update
from telegram.ext import ContextTypes
from src.app.utils.database import get_unpaid, reset_rooms
from src.app.utils.verify import is_admin

class AdminService:

    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return

        unpaid = get_unpaid()

        if not unpaid:
            await update.message.reply_text("✅ All rooms are paid.")
            return

        msg = "❌ Unpaid Rooms:\n"
        msg += "\n".join([f"Room {r}" for r in unpaid])

        await update.message.reply_text(msg)

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return

        reset_rooms()
        await update.message.reply_text("🔄 Monthly reset complete")

    @staticmethod
    async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return

        import os
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        webapp_url = os.getenv("WEBAPP_URL")

        if not webapp_url:
            await update.message.reply_text("⚠️ WEBAPP_URL not set.")
            return

        keyboard = [
            [InlineKeyboardButton("🏢 Open Admin Panel", web_app=WebAppInfo(url=f"{webapp_url}/admin"))]
        ]

        await update.message.reply_text(
            "📊 Admin Dashboard",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @staticmethod
    async def send_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return

        unpaid = get_unpaid()

        if not unpaid:
            await update.message.reply_text("✅ All rooms are paid.")
            return

        msg = "⏰ Payment Reminder Sent for:\n"
        msg += "\n".join([f"Room {r}" for r in unpaid])

        await update.message.reply_text(msg)
        logger.info(f"Admin {update.effective_user.id} sent payment reminders for rooms: {unpaid}")
        
        