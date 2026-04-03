from src.database.database import cursor
from datetime import datetime

class TenantSeeder:
    
    def __init__(self):
        self.cursor = cursor

    def seed_tenants(self, tenants):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id INTEGER PRIMARY KEY,
                tenant_name TEXT NOT NULL
            )
        """)
        
        for tenant in tenants:
            self.cursor.execute(
                "INSERT OR IGNORE INTO tenants (tenant_id, tenant_name) VALUES (?, ?)",
                (tenant["tenant_id"], tenant["tenant_name"])
            )
            
        self.cursor.connection.commit()