from apscheduler.schedulers.background import BackgroundScheduler
from src.database.database import get_unpaid, get_all_rooms, reset_rooms
from src.app.utils.helpers.logging import Logger
import asyncio

logger = Logger(__name__)


def start_scheduler(bot):
    """Start background scheduler for automated tasks"""
    
    scheduler = BackgroundScheduler()

    async def _send_reminder(tenant_id, room, tenant_name):
        """Async helper to send reminder"""
        message = (
            f"⏰ *Payment Reminder*\n\n"
            f"👋 Dear {tenant_name or 'Tenant'},\n\n"
            f"This is a friendly reminder that your rent payment for Room {room} is due.\n\n"
            "Please make your payment at your earliest convenience.\n\n"
            "Use /pay to view the payment QR code.\n\n"
            "_Thank you for your attention._"
        )
        
        try:
            await bot.bot.send_message(
                chat_id=tenant_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"Reminder sent to Room {room}")
        except Exception as e:
            logger.error(f"Failed to send reminder to Room {room}: {e}")

    def daily_reminder():
        """Send daily reminders to unpaid tenants (8 PM)"""
        all_rooms = get_all_rooms()
        unpaid_count = 0

        for room in all_rooms:
            if not room.get("paid", False):
                tenant_id = room.get("tenant_id")
                tenant_name = room.get("tenant_name")
                
                if tenant_id:
                    unpaid_count += 1
                    # Run async function in event loop
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(
                            _send_reminder(tenant_id, room["room_number"], tenant_name)
                        )
                    except RuntimeError:
                        # No event loop running, create new one
                        asyncio.run(_send_reminder(tenant_id, room["room_number"], tenant_name))
                    except Exception as e:
                        logger.error(f"Failed to send reminder to Room {room['room_number']}: {e}")

        if unpaid_count > 0:
            # Notify admins about reminder summary
            admin_msg = f"✅ Sent {unpaid_count} payment reminders today."
            
            async def _notify_admins():
                for admin in bot.bot_data.get("admins", []):
                    try:
                        await bot.bot.send_message(chat_id=admin, text=admin_msg)
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin}: {e}")
            
            try:
                asyncio.run(_notify_admins())
            except Exception as e:
                logger.error(f"Failed to notify admins about reminders: {e}")

        logger.info(f"Daily reminder job completed: {unpaid_count} reminders sent")

    def monthly_reset():
        """Reset all rooms at the start of each month"""
        reset_rooms()
        
        admin_msg = (
            "🔄 *Monthly Reset Complete*\n\n"
            "All rooms have been marked as unpaid.\n"
            "Tenants can now make payments for the new month."
        )
        
        async def _notify_admins():
            for admin in bot.bot_data.get("admins", []):
                try:
                    await bot.bot.send_message(
                        chat_id=admin,
                        text=admin_msg,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin} about reset: {e}")
        
        try:
            asyncio.run(_notify_admins())
        except Exception as e:
            logger.error(f"Failed to notify admins about reset: {e}")

        logger.info("Monthly reset job completed")

    # Schedule jobs
    # Daily reminder at 8:00 PM
    scheduler.add_job(daily_reminder, 'cron', hour=20, minute=0)
    
    # Monthly reset on the 1st day of each month at midnight
    scheduler.add_job(monthly_reset, 'cron', day=1, hour=0, minute=0)

    scheduler.start()
    
    logger.info("Scheduler started: daily reminders at 20:00, monthly reset on 1st day")
