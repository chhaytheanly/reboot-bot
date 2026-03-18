import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Extract admin IDs from environment variable one by one since we store them as arrays 
    
    ADMIN_IDS = []
    admin_ids = os.getenv('ADMIN_IDS')
    
    if admin_ids:
        try:
            ADMIN_IDS = [int(_id.strip()) for _id in admin_ids.split(',') if _id.strip()]
        except ValueError:
            pass  
    
    # _raw_admins = os.getenv('ADMIN_IDS', '')
    # ADMIN_IDS = []
    # if _raw_admins:
    #     for _part in _raw_admins.split(','):
    #         _part = _part.strip()
    #         if not _part:
    #             continue
    #         try:
    #             ADMIN_IDS.append(int(_part))
    #         except ValueError:
    #             continue
    
config = Config()