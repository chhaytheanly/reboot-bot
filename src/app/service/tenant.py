import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from src.database.database import get_room_by_user, assign_tenant
from src.app.utils.helpers import Logger

logger = Logger(__name__)


class TenantService:

    # ------------------- START -------------------
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        # Prevent re-selection
        existing_room = get_room_by_user(user.id)
        if existing_room:
            await update.message.reply_text(
                f"🏠 You are already assigned to Room {existing_room}.\nUse /pay to continue."
            )
            return

        # Create grid (3 per row)
        keyboard = []
        row = []
        for i in range(1, 31):
            row.append(InlineKeyboardButton(f"{i}", callback_data=f"room_{i}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        await update.message.reply_text(
            "🏠 Select your room:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        logger.info(f"User {user.id} started interaction")

    # ------------------- SELECT ROOM -------------------
    @staticmethod
    async def select_room(query, room, user):
        user_id = user.id
        tenant_name = user.full_name

        # Prevent reassignment
        existing_room = get_room_by_user(user_id)
        if existing_room:
            await query.message.reply_text(f"⚠️ You already have Room {existing_room}")
            return

        success = assign_tenant(room, user_id, tenant_name)

        if not success:
            await query.message.reply_text("❌ Room already taken.")
            return

        keyboard = [[InlineKeyboardButton("💰 Pay Rent", callback_data="pay")]]

        await query.message.reply_text(
            f"✅ Room {room} assigned to *{tenant_name}*\n\nClick below to pay:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        logger.info(f"User {user_id} ({tenant_name}) assigned to Room {room}")

    # ------------------- SHOW QR -------------------
    @staticmethod
    async def show_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user = query.from_user
        room = get_room_by_user(user.id)

        if not room:
            await query.message.reply_text("❌ Please select your room first.")
            return

        qr_path = "public/images/kh-qr.jpg"

        if not os.path.exists(qr_path):
            await query.message.reply_text("⚠️ QR code not found.")
            logger.error("QR file missing")
            return

        # Use context manager
        with open(qr_path, "rb") as qr_file:
            await query.message.reply_photo(
                photo=qr_file,
                caption=f"🏠 Room {room}\n\nScan QR → Pay → Upload receipt"
            )

        logger.info(f"User {user.id} requested QR")

    # ------------------- HANDLE RECEIPT -------------------
    @staticmethod
    async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        tenant_name = user.full_name

        room = get_room_by_user(user_id)

        if not room:
            await update.message.reply_text("❌ Please select your room first.")
            return

        if not update.message.photo:
            await update.message.reply_text("⚠️ Please send a valid image receipt.")
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

        # Load admins safely
        from src.app.utils.config import config

        admins = context.bot_data.get("admins") if hasattr(context, "bot_data") else None
        if not admins:
            admins = config.ADMIN_IDS

        caption = (
            f"💰 *Payment Request*\n"
            f"🏠 Room: {room}\n"
            f"👤 Name: {tenant_name}\n"
            f"🆔 ID: `{user_id}`"
        )

        for admin in admins:
            try:
                with open(path, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=admin,
                        photo=photo_file,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Failed to send receipt to admin {admin}: {e}")

        await update.message.reply_text("✅ Receipt sent for approval.")

        logger.info(f"Receipt submitted by {tenant_name} ({user_id}) for Room {room}")