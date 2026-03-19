from telegram import Bot
from src.app.utils.helpers.logging import Logger
from src.database.database import get_room_info, get_all_rooms
import asyncio

logger = Logger(__name__)


class NotificationService:
    """Service for sending notifications to tenants and admins"""

    @staticmethod
    async def notify_tenant(bot: Bot, tenant_id: int, message: str, parse_mode: str = "Markdown"):
        """Send notification to a tenant"""
        try:
            await bot.send_message(
                chat_id=tenant_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"Notification sent to tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to notify tenant {tenant_id}: {e}")
            return False

    @staticmethod
    async def notify_admins(bot: Bot, admin_ids: list, message: str, parse_mode: str = "Markdown"):
        """Send notification to all admins"""
        success_count = 0
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=parse_mode
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        logger.info(f"Admin notification: {success_count}/{len(admin_ids)} successful")
        return success_count

    @staticmethod
    async def notify_payment_approved(bot: Bot, tenant_id: int, room: str):
        """Notify tenant that payment was approved"""
        message = (
            f"✅ *Payment Approved!*\n\n"
            f"🏠 Room {room}\n"
            f"Your payment has been approved by the admin.\n\n"
            "Thank you for your timely payment!"
        )
        return await NotificationService.notify_tenant(bot, tenant_id, message)

    @staticmethod
    async def notify_payment_rejected(bot: Bot, tenant_id: int, room: str, reason: str = None):
        """Notify tenant that payment was rejected"""
        message = (
            f"❌ *Payment Issue*\n\n"
            f"🏠 Room {room}\n"
            f"Your payment receipt was rejected.\n\n"
        )
        if reason:
            message += f"*Reason:* {reason}\n\n"
        message += (
            "Please contact the admin for more information or re-upload a valid receipt."
        )
        return await NotificationService.notify_tenant(bot, tenant_id, message)

    @staticmethod
    async def notify_payment_due(bot: Bot, tenant_id: int, room: str, tenant_name: str = None):
        """Send payment due reminder to tenant"""
        name = tenant_name or "Tenant"
        message = (
            f"⏰ *Payment Reminder*\n\n"
            f"👋 Dear {name},\n\n"
            f"This is a friendly reminder that your rent payment for Room {room} is due.\n\n"
            "Please make your payment at your earliest convenience.\n\n"
            "Use /pay to view the payment QR code.\n\n"
            "_Thank you for your attention._"
        )
        return await NotificationService.notify_tenant(bot, tenant_id, message)

    @staticmethod
    async def notify_new_receipt(bot: Bot, admin_ids: list, room: str, tenant_name: str, tenant_id: int, photo_path: str):
        """Notify admins about a new receipt submission"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from src.app.service.keyboard import KeyboardFactory

        keyboard = KeyboardFactory.get_receipt_approval_keyboard(str(tenant_id), room)

        for admin_id in admin_ids:
            try:
                with open(photo_path, "rb") as photo_file:
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=photo_file,
                        caption=(
                            f"💰 *New Payment Request*\n\n"
                            f"🏠 *Room:* {room}\n"
                            f"👤 *Tenant:* {tenant_name}\n"
                            f"🆔 *User ID:* `{tenant_id}`"
                        ),
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about receipt: {e}")

    @staticmethod
    async def broadcast_to_all_tenants(bot: Bot, admin_ids: list, message: str):
        """Broadcast message to all tenants"""
        all_rooms = get_all_rooms()
        success_count = 0
        failed_count = 0

        for room in all_rooms:
            tenant_id = room.get("tenant_id")
            if not tenant_id:
                continue

            try:
                await bot.send_message(
                    chat_id=tenant_id,
                    text=message,
                    parse_mode="Markdown"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to tenant {tenant_id}: {e}")
                failed_count += 1

        # Notify admins about broadcast result
        summary_message = (
            f"📢 *Broadcast Complete*\n\n"
            f"✅ Successful: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Total: {success_count + failed_count}"
        )

        await NotificationService.notify_admins(bot, admin_ids, summary_message)

        logger.info(f"Broadcast complete: {success_count} successful, {failed_count} failed")
        return success_count, failed_count
