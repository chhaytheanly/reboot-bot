import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from src.app.utils.database import get_room_by_user, assign_tenant
from src.app.utils.helpers import Logger

logger = Logger(__name__)


class TenantService:

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton(f"Room {i}", callback_data=f"room_{i}")]
            for i in range(1, 31)
        ]

        await update.message.reply_text(
            "🏠 Select your room:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        logger.info(f"User {update.effective_user.id} started interaction.")

    @staticmethod
    async def select_room(query, room, user_id):
        success = assign_tenant(room, user_id)

        if not success:
            await query.message.reply_text("❌ Room already taken.")
            return

        keyboard = [[InlineKeyboardButton("💰 Pay Rent", callback_data="pay")]]

        await query.message.reply_text(
            f"✅ Room {room} assigned to you.\n\nClick below to pay:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        logger.info(f"User {user_id} assigned to Room {room}")

    @staticmethod
    async def show_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        room = get_room_by_user(user_id)

        if not room:
            await query.message.reply_text("❌ Please select your room first.")
            return

        qr_path = "public/images/kh-qr.jpg"

        if not os.path.exists(qr_path):
            await query.message.reply_text("⚠️ QR code not found.")
            return

        await query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=f"🏠 Room {room}\n\nScan QR → Pay → Upload receipt"
        )

        logger.info(f"User {user_id} requested QR")

    @staticmethod
    async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        user_id = user.id
        room = get_room_by_user(user_id)

        if not room:
            await update.message.reply_text("❌ Please select your room first.")
            return

        os.makedirs("receipts", exist_ok=True)

        photo = update.message.photo[-1]
        file = await photo.get_file()

        path = f"receipts/{user_id}_{room}.jpg"
        await file.download_to_drive(path)

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{room}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{room}")
            ]
        ]

        # Prefer validated admin list from bot_data when available.
        from src.app.utils.config import config

        admins = context.bot_data.get("admins") if hasattr(context, 'bot_data') else None
        if not admins:
            admins = config.ADMIN_IDS

        for admin in admins:
            try:
                with open(path, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=admin,
                        photo=photo_file,
                        caption=f"💰 Payment Request\n🏠 Room: {room}\n👤 User: {user_id}",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Failed to send receipt to admin {admin}: {e}")

        await update.message.reply_text("✅ Receipt sent for approval.")

        logger.info(f"Receipt submitted by user {user_id} for Room {room}")