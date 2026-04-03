from src.database.database import cursor
from datetime import datetime

class PaymentSeeder:
    
    def __init__(self):
        self.cursor = cursor
        
    def seed_payments(self, tenants):
        now = datetime.now().strftime("%Y-%m-%d")

        for t in tenants:
            if t.get("paid"):
                self.cursor.execute(
                    """
                    INSERT INTO payments (room_number, tenant_id, amount, date, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        t["room"],
                        t["tenant_id"],
                        t.get("amount", 0),
                        now,
                        "approved"
                    )
                )
        self.cursor.connection.commit()