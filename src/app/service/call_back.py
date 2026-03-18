from telegram import Update
from telegram.ext import ContextTypes
from src.app.utils.database import mark_paid
from src.app.utils.verify import is_admin
from src.app.service.tenant import TenantService
from src.app.utils.helpers import Logger

logger = Logger(__name__)


class CallbackService:

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data

        await query.answer()

        user_id = query.from_user.id

        if data.startswith("room_"):
            room = data.split("_")[1]
            return await TenantService.select_room(query, room, user_id)

        if data == "pay":
            return await TenantService.show_qr(update, context)

        if not is_admin(user_id):
            return

        if data.startswith("approve_"):
            _, tenant_id, room = data.split("_")

            mark_paid(room)

            await query.edit_message_caption(
                f"✅ Payment Approved\n🏠 Room {room}"
            )

            logger.info(f"Admin approved payment for Room {room}")

        elif data.startswith("reject_"):
            _, tenant_id, room = data.split("_")

            await query.edit_message_caption(
                f"❌ Payment Rejected\n🏠 Room {room}"
            )

            logger.info(f"Admin rejected payment for Room {room}")
            
        elif data.startswith("remind_"):
            _, tenant_id, room = data.split("_")

            await query.edit_message_caption(
                f"⏰ Payment Reminder Sent\n🏠 Room {room}"
            )

            logger.info(f"Admin sent payment reminder for Room {room}")
            
        elif data.startswith("history_"):
            _, tenant_id, room = data.split("_")

            await query.edit_message_caption(
                f"📜 Payment History\n🏠 Room {room}"
            )

            logger.info(f"Admin viewed payment history for Room {room}")