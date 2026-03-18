from src.app.utils.config import config

def is_admin(id: str) -> bool:
    return id in config.ADMIN_IDS
