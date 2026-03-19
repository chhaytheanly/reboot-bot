from src.database.database import init_db, reset_db, seed_data
from src.app.utils.helpers.logging import logger    

class SeedDatabase:
    @staticmethod
    def run():
        reset_db()
        logger.info("Database reset successfully.")
        init_db()
        logger.info("Database initialized successfully.")
        seed_data()
        logger.info("Database seeded with initial data.")
        
if __name__ == "__main__":
    SeedDatabase.run()
    
# How to run this script via CLI:

# python -m src.database.seed