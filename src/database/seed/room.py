from src.database.database import cursor

class RoomSeeder:
    
    def __init__(self):
        self.cursor = cursor

    def seed_rooms(self, rooms):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_number TEXT PRIMARY KEY,
                name TEXT,
                tenant_id INTEGER UNIQUE,
                tenant_name TEXT,
                paid INTEGER DEFAULT 0,
                last_paid TEXT
            )
        """)
        
        for room in rooms:
            # rooms are dicts from JSON with keys: room_number, name
            self.cursor.execute(
                "INSERT OR IGNORE INTO rooms (room_number, name) VALUES (?, ?)",
                (room.get("room_number"), room.get("name"))
            )
            
        self.cursor.connection.commit()