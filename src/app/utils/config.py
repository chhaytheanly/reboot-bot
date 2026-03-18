import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    _raw_admins = os.getenv('ADMIN_IDS', '')
    ADMIN_IDS = []
    if _raw_admins:
        for _part in _raw_admins.split(','):
            _part = _part.strip()
            if not _part:
                continue
            try:
                ADMIN_IDS.append(int(_part))
            except ValueError:
                continue
    DATABASE_URL = os.getenv('DATABASE_URL')
    
config = Config()