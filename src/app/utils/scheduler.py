from apscheduler.schedulers.background import BackgroundScheduler
from src.database.database import get_unpaid, reset_rooms

def start_scheduler(bot):
    scheduler = BackgroundScheduler()

    def reminder():
        unpaid = get_unpaid()
        if unpaid:
            msg = f"⚠️ {len(unpaid)} rooms unpaid"
            for admin in bot.bot_data.get("admins", []):
                bot.bot.send_message(admin, msg)

    def monthly_reset():
        reset_rooms()

    scheduler.add_job(reminder, 'cron', hour=20)
    scheduler.add_job(monthly_reset, 'cron', day=1, hour=0)

    scheduler.start()