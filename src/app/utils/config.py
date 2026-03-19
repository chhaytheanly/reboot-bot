import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = []
    admin_ids = os.getenv('ADMIN_IDS')
    
    if admin_ids:
        try:
            ADMIN_IDS = [int(_id.strip()) for _id in admin_ids.split(',') if _id.strip()]
        except ValueError:
            pass  
    
config = Config()