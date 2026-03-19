from unittest import result

from src.app.utils.helpers.logging import logger
from telegram import Update
from telegram.ext import ContextTypes
from src.app.utils.database import get_paid, get_room_info, get_unpaid, reset_rooms
from src.app.utils.verify import is_admin

class AdminService:

    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        if not is_admin(user.id):
            await update.message.reply_text("❌ You do not have permission to access this command.")
            logger.warning(f"Unauthorized access attempt by user {user.id} ({user.username}) to /status command.")
            return
        
        unpaid = get_unpaid()
        if not unpaid:
            await update.message.reply_text("✅ All rooms are paid.")
            logger.info(f"Admin {user.id} checked status: all rooms are paid.")
            return
        
        msg = "❌ Unpaid Rooms:\n"
        for room in unpaid:
            info = get_room_info(room)
            tenant_name = info.get("tenant_name", "Unknown Tenant")
            msg += f"Room {room}: {tenant_name}\n"

        await update.message.reply_text(msg)
        logger.info(f"Admin {user.id} checked status: unpaid rooms - {unpaid}")
        
    @staticmethod
    async def paid_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        if not is_admin(user.id):
            await update.message.reply_text("❌ You do not have permission to access this command.")
            logger.warning(f"Unauthorized access attempt by user {user.id} ({user.username}) to /paid_done command.")
            return
        
        pay_done = get_paid()  
        
        if not pay_done:
            await update.message.reply_text("⚠️ No rooms are currently marked as paid.")
            logger.info(f"Admin {user.id} attempted to mark payment as done, but no rooms are currently marked as paid.")
            return
        
        if len(pay_done) == 1:
            msg = f"✅ Room {pay_done[0]} marked as paid for the month."
        else:
            msg = "✅ Rooms marked as paid for the month:\n"
            msg += "\n".join([f"Room {r}" for r in pay_done])
            
        # Get normalize result 
        
        result = {
            "paid_rooms": pay_done,
            "details": [get_room_info(r) for r in pay_done],
            "tenent_names": [get_room_info(r).get("tenant_name", "Unknown Tenant") for r in pay_done],
        }
        
        await update.message.reply_text(msg)
        logger.info(f"Admin {user.id} marked payment as done for the month.")
        
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
            logger.info(f"Admin {update.effective_user.id} attempted to send payment reminders, but all rooms are paid.")
            return

        msg = "⏰ Payment Reminder Sent for:\n"
        msg += "\n".join([f"Room {r}" for r in unpaid])

        await update.message.reply_text(msg)
        logger.info(f"Admin {update.effective_user.id} sent payment reminders for rooms: {unpaid}")
        
        