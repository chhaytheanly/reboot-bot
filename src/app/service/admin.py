from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from src.database.database import get_paid, get_room_info, get_unpaid, reset_rooms, get_all_rooms
from src.app.utils.verify import is_admin
from src.app.service.keyboard import KeyboardFactory
from src.app.utils.helpers.logging import Logger
import os
import datetime

logger = Logger(__name__)


class AdminService:
    """Admin service with improved UX for better management"""

    @staticmethod
    async def _reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
        """Safe reply that works for messages and callback queries; falls back to send_message."""
        target = update.effective_message
        if target:
            return await target.reply_text(text, **kwargs)

        chat_id = None
        if update.effective_chat:
            chat_id = update.effective_chat.id
        elif update.effective_user:
            chat_id = update.effective_user.id

        if chat_id:
            return await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)

        logger.error("No target to send message to (no effective_message, chat, or user)")
        return None

    @staticmethod
    async def _check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verify admin permissions"""
        user = update.effective_user
        if not is_admin(user.id):
            await AdminService._reply(
                update,
                context,
                "❌ *Access Denied*\n\n"
                "You do not have permission to access this command.\n\n"
                "_Only administrators can use this feature._",
                parse_mode="Markdown"
            )
            logger.warning(f"Unauthorized access attempt by {user.id} ({user.username})")
            return False
        return True

    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all rooms status with improved formatting"""
        if not await AdminService._check_admin(update, context):
            return

        user = update.effective_user
        all_rooms = get_all_rooms()

        if not all_rooms:
            await AdminService._reply(update, context, "⚠️ No room data available.")
            return

        # Separate paid and unpaid
        paid_rooms = [r for r in all_rooms if r.get("paid", False)]
        unpaid_rooms = [r for r in all_rooms if not r.get("paid", False)]

        # Build status message
        lines = [
            f"📊 *Room Status Report*\n",
            f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            f"✅ Paid: {len(paid_rooms)}/30",
            f"⏳ Unpaid: {len(unpaid_rooms)}/30\n",
        ]

        if unpaid_rooms:
            lines.append("❌ *Unpaid Rooms:*")
            for room in unpaid_rooms[:10]:  # Limit to first 10
                info = get_room_info(room["room_number"])
                if info:
                    tenant_name = info.get("tenant_name") or "Unknown"
                    lines.append(f"  • Room {room['room_number']} → {tenant_name}")

            if len(unpaid_rooms) > 10:
                lines.append(f"  _... and {len(unpaid_rooms) - 10} more_")

        # Create inline keyboard for quick actions
        keyboard = [
            [
                InlineKeyboardButton("✅ Paid List", callback_data="admin_paid_list"),
                InlineKeyboardButton("❌ Unpaid List", callback_data="admin_unpaid_list")
            ],
            [
                InlineKeyboardButton("🔄 Reset Month", callback_data="admin_reset_confirm"),
                InlineKeyboardButton("⏰ Remind All", callback_data="admin_remind_all")
            ]
        ]

        await AdminService._reply(
            update,
            context,
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        logger.info(f"Admin {user.id} checked room status")

    @staticmethod
    async def paid_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all paid rooms with details"""
        if not await AdminService._check_admin(update, context):
            return

        user = update.effective_user
        paid_rooms = get_paid()

        if not paid_rooms:
            await AdminService._reply(
                update,
                context,
                "⚠️ *No Paid Rooms*\n\n"
                "No rooms are currently marked as paid.",
                parse_mode="Markdown"
            )
            return

        room_details = [get_room_info(r) for r in paid_rooms]

        lines = ["✅ *Paid Rooms*\n"]

        for r, info in zip(paid_rooms, room_details):
            tenant_name = (info or {}).get("tenant_name", "Unknown")
            last_paid = (info or {}).get("last_paid", "N/A")
            lines.append(f"• Room {r} → {tenant_name} (Paid: {last_paid})")

        await AdminService._reply(update, context, "\n".join(lines), parse_mode="Markdown")

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
        """Reset all rooms for new month with confirmation"""
        if not await AdminService._check_admin(update, context):
            return

        # Show confirmation
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm Reset", callback_data="admin_reset_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ])

        await AdminService._reply(
            update,
            context,
            "⚠️ *Monthly Reset Confirmation*\n\n"
            "This will:\n"
            "• Mark all rooms as unpaid\n"
            "• Clear payment status\n"
            "• Keep tenant assignments\n\n"
            "_Are you sure you want to proceed?_",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        logger.info(f"Admin {update.effective_user.id} initiated reset")

    @staticmethod
    async def confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the monthly reset"""
        if not await AdminService._check_admin(update, context):
            return

        reset_rooms()

        await AdminService._reply(
            update,
            context,
            "✅ *Monthly Reset Complete*\n\n"
            f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "All rooms have been marked as unpaid.\n"
            "Tenants can now make payments for the new month.",
            parse_mode="Markdown"
        )

        logger.info(f"Admin {update.effective_user.id} completed monthly reset")

    @staticmethod
    async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel with web app button"""
        if not await AdminService._check_admin(update, context):
            return

        webapp_url = os.getenv("WEBAPP_URL")

        if not webapp_url:
            await AdminService._reply(
                update,
                context,
                "⚠️ *Web App Not Configured*\n\n"
                "The WEBAPP_URL environment variable is not set.\n"
                "Please contact the system administrator.",
                parse_mode="Markdown"
            )
            return

        keyboard = [
            [InlineKeyboardButton("🏢 Open Admin Panel", web_app=WebAppInfo(url=f"{webapp_url}/admin"))],
            [InlineKeyboardButton("📊 View Status", callback_data="admin_status")]
        ]

        await AdminService._reply(
            update,
            context,
            "📊 *Admin Dashboard*\n\n"
            "Access the full admin panel to manage rooms, tenants, and payments.\n\n"
            "Or use the quick actions below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    @staticmethod
    async def send_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send reminders to all unpaid tenants"""
        if not await AdminService._check_admin(update, context):
            return

        user = update.effective_user
        unpaid_rooms = get_unpaid()

        if not unpaid_rooms:
            await AdminService._reply(
                update,
                context,
                "✅ *All Rooms Paid*\n\n"
                "No reminders needed - all rooms are paid!",
                parse_mode="Markdown"
            )
            return

        sent_count = 0
        failed_count = 0

        for room in unpaid_rooms:
            info = get_room_info(room)
            tenant_id = info.get("tenant_id") if info else None
            tenant_name = info.get("tenant_name", "Tenant") if info else "Tenant"

            if not tenant_id:
                continue

            try:
                await context.bot.send_message(
                    chat_id=tenant_id,
                    text=(
                        f"⏰ *Payment Reminder*\n\n"
                        f"👋 Dear {tenant_name},\n\n"
                        f"This is a friendly reminder that your rent payment for Room {room} is due.\n\n"
                        "Please make your payment at your earliest convenience.\n\n"
                        "Use /pay to view the payment QR code.\n\n"
                        "_Thank you for your attention._",
                    ),
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send reminder to Room {room}: {e}")
                failed_count += 1

        await AdminService._reply(
            update,
            context,
            f"✅ *Reminders Sent*\n\n"
            f"📤 Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"🏠 Total Unpaid: {len(unpaid_rooms)}",
            parse_mode="Markdown"
        )

        logger.info(f"Admin {user.id} sent reminders: {sent_count} sent, {failed_count} failed")

    @staticmethod
    async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin help information"""
        if not await AdminService._check_admin(update, context):
            return

        help_text = (
            "📖 *Admin Command Reference*\n\n"
            "*Commands:*\n"
            "• /status - View all rooms status\n"
            "• /paid - View paid rooms list\n"
            "• /reset - Reset for new month\n"
            "• /remind - Send payment reminders\n"
            "• /panel - Open admin web panel\n"
            "• /adminhelp - Show this help\n\n"
            "*Quick Actions:*\n"
            "Use the inline buttons in messages for quick access to common actions.\n\n"
            "*Approval Workflow:*\n"
            "1. Tenants upload receipts\n"
            "2. You receive notification\n"
            "3. Click ✅ Approve or ❌ Reject\n\n"
            "_Admin Panel Version: 2.0_"
        )

        keyboard = [
            [InlineKeyboardButton("📊 View Status", callback_data="admin_status")],
            [InlineKeyboardButton("✅ Paid Rooms", callback_data="admin_paid_list")]
        ]

        await AdminService._reply(update, context, help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        logger.info(f"Admin {update.effective_user.id} viewed admin help")
