from telegram import Update
from telegram.ext import ContextTypes
from src.database.database import mark_paid, get_room_info, get_payment_history
from src.app.utils.verify import is_admin
from src.app.service.tenant import TenantService
from src.app.service.keyboard import KeyboardFactory
from src.app.utils.helpers.logging import Logger
from src.app.service.admin import AdminService
import datetime

logger = Logger(__name__)


class CallbackService:
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback to appropriate handler"""
        query = update.callback_query
        data = query.data
        user = query.from_user

        await query.answer()

        # Tenant room selection
        if data.startswith("room_"):
            room = data.split("_")[1]
            return await TenantService.select_room(query, room, user)

        # Tenant actions
        if data == "pay":
            return await TenantService.show_qr(update, context)

        if data == "my_room":
            return await TenantService.show_my_room(update, context)

        if data == "history":
            return await TenantService.show_payment_history(update, context)

        if data == "help":
            return await TenantService.show_help(update, context)

        if data == "upload_receipt":
            await query.message.reply_text(
                "📸 *Upload Receipt*\n\n"
                "Please send your receipt image now.\n\n"
                "_Tips:_\n"
                "• Ensure the image is clear and readable\n"
                "• Include transaction details and date\n"
                "• Crop out unnecessary background",
                parse_mode="Markdown"
            )
            return

        # Admin-only actions
        if not is_admin(user.id):
            await query.answer("⚠️ Admin access required", show_alert=True)
            return

        if data.startswith("approve_"):
            return await CallbackService._approve_payment(query, data, context)

        if data.startswith("reject_"):
            return await CallbackService._reject_payment(query, data, context)

        if data.startswith("admin_paid_"):
            return await CallbackService._admin_mark_paid(query, data, context)

        if data.startswith("admin_unpaid_"):
            return await CallbackService._admin_mark_unpaid(query, data, context)

        if data.startswith("tenant_info_"):
            return await CallbackService._show_tenant_info(query, data, context)

        if data.startswith("history_"):
            return await CallbackService._show_history(query, data, context)

        if data.startswith("remind_"):
            return await CallbackService._send_reminder(query, data, context)

        # Admin panel quick actions
        if data == "admin_status":
            return await AdminService.status(update, context)

        if data == "admin_paid_list":
            return await AdminService.paid_done(update, context)

        if data == "admin_unpaid_list":
            # Currently show full status which includes unpaid rooms
            return await AdminService.status(update, context)

        if data == "admin_reset_confirm":
            return await AdminService.confirm_reset(update, context)

        if data == "admin_remind_all":
            return await AdminService.send_reminder(update, context)

        if data == "cancel":
            await query.message.reply_text("❌ Operation cancelled.")
            return

        logger.debug(f"Unhandled callback: {data}")

    @staticmethod
    async def _approve_payment(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Admin approves payment"""
        _, tenant_id, room = data.split("_", 2)

        mark_paid(room)

        await query.edit_message_caption(
            f"✅ *Payment Approved*\n\n"
            f"🏠 Room {room}\n"
            f"🕒 Approved: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "_Tenant has been notified._",
            parse_mode="Markdown"
        )

        try:
            await context.bot.send_message(
                chat_id=int(tenant_id),
                text=(
                    f" ✅ *Payment Approved*\n By Admin\n\n"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify tenant {tenant_id}: {e}")

        logger.info(f"Admin {query.from_user.id} approved payment for Room {room}")

    @staticmethod
    async def _reject_payment(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Admin rejects payment"""
        _, tenant_id, room = data.split("_", 2)

        keyboard = KeyboardFactory.get_back_keyboard("back")

        await query.edit_message_caption(
            f"❌ *Payment Rejected*\n\n"
            f"🏠 Room {room}\n\n"
            "_Reason (optional):_\n"
            "Please contact admin for details.\n\n"
            "_You can re-upload a valid receipt._",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        try:
            await context.bot.send_message(
                chat_id=int(tenant_id),
                text=(
                    f"❌ *Payment Issue*\n\n"
                    f"🏠 Room {room}\n"
                    "Your payment receipt was rejected.\n\n"
                    "Please contact the admin for more information or re-upload a valid receipt.",
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify tenant {tenant_id}: {e}")

        logger.info(f"Admin {query.from_user.id} rejected payment for Room {room}")

    @staticmethod
    async def _admin_mark_paid(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Admin manually marks room as paid"""
        room = data.replace("admin_paid_", "")

        mark_paid(room)

        await query.message.reply_text(
            f"✅ *Room Marked as Paid*\n\n"
            f"🏠 Room {room}\n"
            f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode="Markdown"
        )

        logger.info(f"Admin manually marked Room {room} as paid")

    @staticmethod
    async def _admin_mark_unpaid(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Admin manually marks room as unpaid"""
        from src.database.database import cursor, conn

        room = data.replace("admin_unpaid_", "")

        cursor.execute(
            "UPDATE rooms SET paid=0, last_paid=NULL WHERE room_number=?",
            (room,)
        )
        conn.commit()

        await query.message.reply_text(
            f"⏳ *Room Marked as Unpaid*\n\n"
            f"🏠 Room {room}\n\n"
            "_Tenant will be notified to make payment._",
            parse_mode="Markdown"
        )

        logger.info(f"Admin marked Room {room} as unpaid")

    @staticmethod
    async def _show_tenant_info(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Show tenant information for a room"""
        room = data.replace("tenant_info_", "")
        room_info = get_room_info(room)

        if not room_info:
            await query.message.reply_text("❌ Room not found.")
            return

        tenant_id = room_info.get("tenant_id")
        tenant_name = room_info.get("tenant_name", "Unknown")
        is_paid = room_info.get("paid", False)
        last_paid = room_info.get("last_paid", "Never")

        status_emoji = "✅" if is_paid else "⏳"
        status_text = "Paid" if is_paid else "Unpaid"

        info_text = (
            f"🏠 *Room {room} Information*\n\n"
            f"👤 *Tenant:* {tenant_name if tenant_name else 'Vacant'}\n"
            f"🆔 *User ID:* `{tenant_id if tenant_id else 'N/A'}`\n"
            f"{status_emoji} *Status:* {status_text}\n"
            f"📅 *Last Payment:* {last_paid if last_paid else 'Never'}"
        )

        keyboard = KeyboardFactory.get_back_keyboard("back")

        await query.message.reply_text(
            info_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        logger.info(f"Admin viewed tenant info for Room {room}")

    @staticmethod
    async def _show_history(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Show payment history for a room"""
        room = data.replace("history_", "")
        history = get_payment_history(room)

        if not history:
            await query.message.reply_text(
                f"📜 *Payment History - Room {room}*\n\n"
                "No payment records found.",
                parse_mode="Markdown"
            )
            return

        lines = [f"📜 *Payment History - Room {room}*\n\n"]

        for amount, date, status in history:
            status_emoji = "✅" if status == "approved" else "❌"
            lines.append(f"{status_emoji} {date} - ${amount:.2f} ({status.title()})")

        keyboard = KeyboardFactory.get_back_keyboard("back")

        await query.message.reply_text(
            "\n".join(lines),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        logger.info(f"Admin viewed payment history for Room {room}")

    @staticmethod
    async def _send_reminder(query, data: str, context: ContextTypes.DEFAULT_TYPE):
        """Send payment reminder to tenant"""
        room = data.replace("remind_", "")
        room_info = get_room_info(room)

        if not room_info or not room_info.get("tenant_id"):
            await query.message.reply_text("❌ Room is vacant. No reminder needed.")
            return

        tenant_id = room_info.get("tenant_id")
        tenant_name = room_info.get("tenant_name", "Tenant")

        try:
            await context.bot.send_message(
                chat_id=int(tenant_id),
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

            await query.message.reply_text(
                f"✅ *Reminder Sent*\n\n"
                f"🏠 Room {room}\n"
                f"👤 Tenant: {tenant_name}",
                parse_mode="Markdown"
            )

            logger.info(f"Admin sent reminder to Room {room}")

        except Exception as e:
            await query.message.reply_text(f"❌ Failed to send reminder: {e}")
            logger.error(f"Failed to send reminder to Room {room}: {e}")
