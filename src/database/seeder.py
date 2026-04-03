import json
from .seed.payment import PaymentSeeder
from .seed.room import RoomSeeder
from .seed.tenant import TenantSeeder
from src.database.database import cursor
from src.database.database import init_db, conn


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def seed_all(rooms_data, tenants_data):
    cursor.execute("PRAGMA foreign_keys = OFF")

    try:
        data = {
            "rooms": rooms_data.get("rooms", []),
            "tenants": tenants_data.get("tenants", [])
        }

        # Reset database
        cursor.execute("DELETE FROM payments")
        cursor.execute("""
            UPDATE rooms
            SET tenant_id=NULL,
                tenant_name=NULL,
                paid=0,
                last_paid=NULL
        """)

        # Seed order matters
        room_seeder = RoomSeeder()
        tenant_seeder = TenantSeeder()
        payment_seeder = PaymentSeeder()

        room_seeder.seed_rooms(data["rooms"])
        tenant_seeder.seed_tenants(data["tenants"])
        payment_seeder.seed_payments(data["tenants"])

        conn.commit()
        print("✅ Seeding successful")

    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)

    finally:
        cursor.execute("PRAGMA foreign_keys = ON")


def seed_from_files(rooms_file, tenants_file):
    rooms_data = load_json(rooms_file)
    tenants_data = load_json(tenants_file)

    seed_all(rooms_data, tenants_data)


if __name__ == "__main__":
    init_db()

    seed_from_files(
        "src/database/data/room.json",
        "src/database/data/tenant.json"
    )