from src.app.utils.helpers.logging import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from src.database.database import get_paid, get_room_info, get_unpaid, reset_rooms
from src.app.utils.verify import is_admin
import os

class AdminService:

    @staticmethod
    async def _check_admin(update: Update) -> bool:
        user = update.effective_user
        if not is_admin(user.id):
            await update.message.reply_text("❌ You do not have permission to access this command.")
            logger.warning(f"Unauthorized access attempt by {user.id} ({user.username})")
            return False
        return True

    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await AdminService._check_admin(update):
            return

        user = update.effective_user
        unpaid_rooms = get_unpaid()

        if not unpaid_rooms:
            await update.message.reply_text("✅ All rooms are paid.")
            logger.info(f"Admin {user.id} checked status: all paid")
            return

        lines = ["❌ *Unpaid Rooms:*"]

        for room in unpaid_rooms:
            info = get_room_info(room)

            if not info:
                continue

            tenant_name = info.get("tenant_name") or "Unknown"
            last_paid = info.get("last_paid") or "Never"

            lines.append(f"• Room {room} → {tenant_name} (Last: {last_paid})")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        logger.info(f"Admin {user.id} checked unpaid rooms: {unpaid_rooms}")

    @staticmethod
    async def paid_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await AdminService._check_admin(update):
            return

        user = update.effective_user
        paid_rooms = get_paid()

        if not paid_rooms:
            await update.message.reply_text("⚠️ No rooms are currently marked as paid.")
            return

        room_details = [get_room_info(r) for r in paid_rooms]

        lines = ["✅ *Paid Rooms:*"]

        for r, info in zip(paid_rooms, room_details):
            tenant_name = (info or {}).get("tenant_name", "Unknown")
            lines.append(f"• Room {r} → {tenant_name}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

        result = {
            "paid_rooms": paid_rooms,
            "details": room_details,
            "tenant_names": [
                (info or {}).get("tenant_name", "Unknown")
                for info in room_details
            ],
        }

        logger.info(f"Admin {user.id} viewed paid rooms: {result}")

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await AdminService._check_admin(update):
            return

        reset_rooms()
        await update.message.reply_text("🔄 Monthly reset complete")
        logger.info(f"Admin {update.effective_user.id} performed monthly reset")

    @staticmethod
    async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await AdminService._check_admin(update):
            return

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
        if not await AdminService._check_admin(update):
            return

        user = update.effective_user
        unpaid_rooms = get_unpaid()

        if not unpaid_rooms:
            await update.message.reply_text("✅ All rooms are paid.")
            return

        lines = ["⏰ *Payment Reminder Sent:*"]

        for r in unpaid_rooms:
            info = get_room_info(r)
            tenant_name = (info or {}).get("tenant_name", "Unknown")
            lines.append(f"• Room {r} → {tenant_name}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

        logger.info(f"Admin {user.id} sent reminders for: {unpaid_rooms}")