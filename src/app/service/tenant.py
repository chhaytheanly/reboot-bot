import os
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    WebAppInfo
)
from telegram.ext import ContextTypes
from src.database.database import (
    get_room_by_user, 
    assign_tenant, 
    get_room_info,
    get_payment_history
)
from src.app.utils.helpers.logging import Logger
import datetime

logger = Logger(__name__)


class TenantService:

    @staticmethod
    def _get_main_keyboard(user_id: int):
        room = get_room_by_user(user_id)
        
        buttons = [
            [KeyboardButton("🏠 My Room", callback_data="my_room")],
            [KeyboardButton("💰 Pay Rent", callback_data="pay")],
            [KeyboardButton("📜 Payment History", callback_data="history")],
            [KeyboardButton("❓ Help", callback_data="help")]
        ]
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with welcome message and room selection"""
        user = update.effective_user
        existing_room = get_room_by_user(user.id)
        
        welcome_text = (
            f"👋 *Welcome to Room Rental Bot*, {user.first_name}!\n\n"
            "This bot helps you manage your room rental payments easily.\n\n"
            "_What can you do?_\n"
            "• Select your room number\n"
            "• Pay rent via QR code\n"
            "• Upload payment receipts\n"
            "• Track your payment history\n\n"
        )
        
        if existing_room:
            welcome_text += (
                f"✅ *You are already assigned to Room {existing_room}*\n\n"
                "Use the menu below to manage your room:"
            )
            
            keyboard = [
                [InlineKeyboardButton("🏠 My Room", callback_data="my_room")],
                [InlineKeyboardButton("💰 Pay Rent", callback_data="pay")],
                [InlineKeyboardButton("📜 Payment History", callback_data="history")],
                [InlineKeyboardButton("❓ Help", callback_data="help")]
            ]
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            welcome_text += "👇 *Select your room number to get started:*\n\n"
            
            # Create grid (5 per row for better mobile UX)
            room_keyboard = []
            for i in range(1, 31, 5):
                row = []
                for j in range(i, min(i + 5, 31)):
                    row.append(InlineKeyboardButton(f"🚪 {j}", callback_data=f"room_{j}"))
                room_keyboard.append(row)
            
            room_keyboard.append([InlineKeyboardButton("❓ Need Help?", callback_data="help")])
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=InlineKeyboardMarkup(room_keyboard),
                parse_mode="Markdown"
            )

        logger.info(f"User {user.id} started interaction")

    @staticmethod
    async def select_room(query, room, user):
        """Handle room selection with confirmation"""
        user_id = user.id
        tenant_name = user.full_name
        existing_room = get_room_by_user(user_id)
        
        if existing_room:
            await query.message.reply_text(
                f"⚠️ *You already have Room {existing_room}*\n\n"
                "You cannot select another room. Contact admin if you need to change.",
                parse_mode="Markdown"
            )
            return

        # Check if room is available
        room_info = get_room_info(room)
        if room_info and room_info.get("tenant_id"):
            await query.message.reply_text(
                f"❌ *Room {room} is already occupied*\n\n"
                "Please select another room.",
                parse_mode="Markdown"
            )
            return

        success = assign_tenant(room, user_id, tenant_name)

        if not success:
            await query.message.reply_text(
                "❌ *Room already taken*\n\n"
                "Please select another room.",
                parse_mode="Markdown"
            )
            return

        keyboard = [
            [InlineKeyboardButton("💰 Pay Now", callback_data="pay")],
            [InlineKeyboardButton("🏠 My Room", callback_data="my_room")]
        ]

        await query.message.reply_text(
            f"✅ *Room {room} Assigned Successfully!*\n\n"
            f"👤 *Name:* {tenant_name}\n"
            f"🏠 *Room:* {room}\n\n"
            "_You can now proceed to make your payment._\n\n"
            "_Note: Please complete payment within 24 hours to confirm your booking._",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        logger.info(f"User {user_id} ({tenant_name}) assigned to Room {room}")

    @staticmethod
    async def show_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show QR code for payment"""
        query = update.callback_query if update.callback_query else None
        user = update.effective_user
        room = get_room_by_user(user.id)

        if not room:
            await (query.message.reply_text if query else update.message.reply_text)(
                "❌ *No Room Assigned*\n\n"
                "Please select your room first using /start",
                parse_mode="Markdown"
            )
            return

        room_info = get_room_info(room)
        is_paid = room_info.get("paid", False) if room_info else False
        
        if is_paid:
            await (query.message.reply_text if query else update.message.reply_text)(
                f"✅ *Payment Status: Paid*\n\n"
                f"🏠 Room {room}\n"
                f"📅 Last Payment: {room_info.get('last_paid', 'N/A')}\n\n"
                "Thank you for your timely payment!",
                parse_mode="Markdown"
            )
            return

        qr_path = "public/images/kh-qr.jpg"

        if not os.path.exists(qr_path):
            await (query.message.reply_text if query else update.message.reply_text)(
                "⚠️ *QR Code Not Found*\n\n"
                "Please contact the administrator.",
                parse_mode="Markdown"
            )
            logger.error("QR file missing")
            return

        keyboard = [
            [InlineKeyboardButton("📸 Upload Receipt", callback_data="upload_receipt")]
        ]

        # Use context manager
        with open(qr_path, "rb") as qr_file:
            caption = (
                f"💰 *Payment Instructions*\n\n"
                f"🏠 *Room:* {room}\n\n"
                "1️⃣ Scan the QR code above\n"
                "2️⃣ Complete the payment\n"
                "3️⃣ Upload your receipt\n\n"
                "_Please ensure the receipt is clear and readable._"
            )
            
            if query:
                await query.message.reply_photo(
                    photo=qr_file,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_photo(
                    photo=qr_file,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

        logger.info(f"User {user.id} requested QR")

    @staticmethod
    async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle receipt upload with improved feedback"""
        user = update.effective_user
        user_id = user.id
        tenant_name = user.full_name

        room = get_room_by_user(user_id)

        if not room:
            await update.message.reply_text(
                "❌ *No Room Assigned*\n\n"
                "Please select your room first using /start",
                parse_mode="Markdown"
            )
            return

        if not update.message.photo:
            await update.message.reply_text(
                "⚠️ *Invalid Receipt*\n\n"
                "Please send a valid image receipt.\n\n"
                "_Tips:_\n"
                "• Ensure the image is clear\n"
                "• Include transaction details\n"
                "• Show payment date and amount",
                parse_mode="Markdown"
            )
            return

        os.makedirs("receipts", exist_ok=True)

        photo = update.message.photo[-1]
        file = await photo.get_file()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"receipts/receipt_{user_id}_{room}_{timestamp}.jpg"
        await file.download_to_drive(path)

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{room}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{room}")
            ],
            [
                InlineKeyboardButton("📜 View History", callback_data=f"history_{room}")
            ]
        ]

        # Load admins safely
        from src.app.utils.config import config

        admins = context.bot_data.get("admins") if hasattr(context, "bot_data") else None
        if not admins:
            admins = config.ADMIN_IDS

        caption = (
            f"💰 *New Payment Request*\n\n"
            f"🏠 *Room:* {room}\n"
            f"👤 *Tenant:* {tenant_name}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"🕒 *Submitted:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        sent_count = 0
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
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send receipt to admin {admin}: {e}")

        await update.message.reply_text(
            "✅ *Receipt Submitted Successfully!*\n\n"
            f"📸 Your receipt has been sent to {sent_count} admin(s) for approval.\n\n"
            "_You will be notified once your payment is approved._\n\n"
            "_Typical approval time: Within 24 hours_",
            parse_mode="Markdown"
        )

        logger.info(f"Receipt submitted by {tenant_name} ({user_id}) for Room {room}")

    @staticmethod
    async def show_my_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's room information"""
        user = update.effective_user
        
        # Handle both callback query and text message
        if update.callback_query:
            reply_func = update.callback_query.message.reply_text
        elif update.message:
            reply_func = update.message.reply_text
        else:
            return
        
        room = get_room_by_user(user.id)

        if not room:
            await reply_func(
                "❌ *No Room Assigned*\n\n"
                "Please select your room first using /start",
                parse_mode="Markdown"
            )
            return

        room_info = get_room_info(room)
        is_paid = room_info.get("paid", False) if room_info else False
        last_paid = room_info.get("last_paid", "Never") if room_info else None

        status_emoji = "✅" if is_paid else "⏳"
        status_text = "Paid" if is_paid else "Pending"

        keyboard = [
            [InlineKeyboardButton("💰 Pay Rent", callback_data="pay")],
            [InlineKeyboardButton("📜 Payment History", callback_data="history")]
        ]

        await reply_func(
            f"🏠 *Your Room Information*\n\n"
            f"🚪 *Room Number:* {room}\n"
            f"👤 *Tenant:* {user.full_name}\n"
            f"{status_emoji} *Payment Status:* {status_text}\n"
            f"📅 *Last Payment:* {last_paid if last_paid else 'N/A'}\n\n"
            "_Use the buttons below to manage your room._",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        logger.info(f"User {user.id} viewed room info")

    @staticmethod
    async def show_payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's payment history"""
        user = update.effective_user

        # Prefer the effective message (works for callbacks and messages)
        target_message = update.effective_message

        room = get_room_by_user(user.id)

        if not room:
            text = (
                "❌ *No Room Assigned*\n\n"
                "Please select your room first using /start"
            )
            if target_message:
                await target_message.reply_text(text, parse_mode="Markdown")
            else:
                chat_id = update.effective_chat.id if update.effective_chat else (user.id if user else None)
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                else:
                    logger.error("No target to send 'no room' message to")
            return

        history = get_payment_history(room)

        if not history:
            text = (
                "📜 *Payment History*\n\n"
                "No payment records found.\n\n"
                "_Make your first payment to see history here._"
            )
            if target_message:
                await target_message.reply_text(text, parse_mode="Markdown")
            else:
                chat_id = update.effective_chat.id if update.effective_chat else (user.id if user else None)
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                else:
                    logger.error("No target to send 'no history' message to")
            return

        lines = ["📜 *Payment History*\n\n"]
        for amount, date, status in history:
            status_emoji = "✅" if status == "approved" else "❌"
            lines.append(f"{status_emoji} {date} - ${amount:.2f} ({status.title()})")

        if target_message:
            await target_message.reply_text("\n".join(lines), parse_mode="Markdown")
        else:
            chat_id = update.effective_chat.id if update.effective_chat else (user.id if user else None)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown")
            else:
                logger.error("No target to send payment history to")

        logger.info(f"User {user.id} viewed payment history")

    @staticmethod
    async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = (
            "❓ *Help & FAQ*\n\n"
            "*Getting Started:*\n"
            "1. Click /start to begin\n"
            "2. Select your room number\n"
            "3. Pay rent via QR code\n"
            "4. Upload your receipt\n\n"
            "*Commands:*\n"
            "• /start - Start the bot and select room\n"
            "• /myroom - View your room info\n"
            "• /pay - View payment QR code\n"
            "• /history - View payment history\n"
            "• /help - Show this help message\n\n"
            "*Need Assistance?*\n"
            "Contact the administrator for support.\n\n"
            "_Bot Version: 2.0_"
        )

        keyboard = [
            [InlineKeyboardButton("🏠 My Room", callback_data="my_room")],
            [InlineKeyboardButton("💰 Pay Rent", callback_data="pay")]
        ]

        # Prefer the effective message which works for both messages and callback queries
        target_message = update.effective_message

        if target_message:
            await target_message.reply_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Fallback: send directly to chat id when no message object is available
            chat_id = None
            if update.effective_chat:
                chat_id = update.effective_chat.id
            elif update.effective_user:
                chat_id = update.effective_user.id

            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                logger.error("No target to send help to (no message, chat, or user available)")

        logger.info(f"User {update.effective_user.id} viewed help")
