import sqlite3
from datetime import datetime

conn = sqlite3.connect("rent.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_number TEXT PRIMARY KEY,
        tenant_id INTEGER UNIQUE,
        paid INTEGER DEFAULT 0,
        last_paid TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT,
        tenant_id INTEGER,
        amount REAL,
        date TEXT,
        status TEXT
    )
    """)

    # Initialize 30 rooms
    for i in range(1, 31):
        cursor.execute(
            "INSERT OR IGNORE INTO rooms (room_number) VALUES (?)",
            (str(i),)
        )

    conn.commit()


def assign_tenant(room_number, tenant_id):
    """
    Assign a tenant to a room.
    - Prevents duplicate room assignment
    - Ensures one tenant = one room
    """

    # Check if room already taken
    existing = cursor.execute(
        "SELECT tenant_id FROM rooms WHERE room_number=?",
        (room_number,)
    ).fetchone()

    if existing and existing[0] is not None:
        return False  # Room already assigned

    # Remove tenant from previous room (if any)
    cursor.execute(
        "UPDATE rooms SET tenant_id=NULL WHERE tenant_id=?",
        (tenant_id,)
    )

    # Assign tenant to new room
    cursor.execute(
        "UPDATE rooms SET tenant_id=? WHERE room_number=?",
        (tenant_id, room_number)
    )

    conn.commit()
    return True


def get_room_by_user(tenant_id):
    result = cursor.execute(
        "SELECT room_number FROM rooms WHERE tenant_id=?",
        (tenant_id,)
    ).fetchone()

    return result[0] if result else None


def get_room_info(room_number):
    result = cursor.execute(
        "SELECT room_number, tenant_id, paid, last_paid FROM rooms WHERE room_number=?",
        (room_number,)
    ).fetchone()

    if result:
        return {
            "room_number": result[0],
            "tenant_id": result[1],
            "paid": result[2],
            "last_paid": result[3]
        }

    return None


def get_all_rooms():
    rows = cursor.execute(
        "SELECT room_number, tenant_id, paid, last_paid FROM rooms"
    ).fetchall()

    return [
        {
            "room_number": r[0],
            "tenant_id": r[1],
            "paid": r[2],
            "last_paid": r[3]
        }
        for r in rows
    ]

def mark_paid(room_number, amount=0):
    """
    Mark a room as paid and log payment history
    """

    # Get tenant
    result = cursor.execute(
        "SELECT tenant_id FROM rooms WHERE room_number=?",
        (room_number,)
    ).fetchone()

    tenant_id = result[0] if result else None

    now = datetime.now().strftime("%Y-%m-%d")

    # Update room status
    cursor.execute(
        "UPDATE rooms SET paid=1, last_paid=? WHERE room_number=?",
        (now, room_number)
    )

    # Insert payment history
    cursor.execute(
        """
        INSERT INTO payments (room_number, tenant_id, amount, date, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (room_number, tenant_id, amount, now, "approved")
    )

    conn.commit()


def get_payment_history(room_number):
    rows = cursor.execute(
        """
        SELECT amount, date, status
        FROM payments
        WHERE room_number=?
        ORDER BY date DESC
        """,
        (room_number,)
    ).fetchall()

    return rows


def get_unpaid():
    rows = cursor.execute(
        "SELECT room_number FROM rooms WHERE paid=0"
    ).fetchall()

    return [r[0] for r in rows]


def get_paid():
    rows = cursor.execute(
        "SELECT room_number FROM rooms WHERE paid=1"
    ).fetchall()

    return [r[0] for r in rows]


def reset_rooms():
    cursor.execute("UPDATE rooms SET paid=0")
    conn.commit()


def remove_tenant(tenant_id):
    """
    Remove tenant from their room
    """
    cursor.execute(
        "UPDATE rooms SET tenant_id=NULL WHERE tenant_id=?",
        (tenant_id,)
    )
    conn.commit()
    
def seed_data():
    tenants = [
        {"id": 1001, "room": "1", "paid": True},
        {"id": 1002, "room": "2", "paid": True},
        {"id": 1003, "room": "3", "paid": False},
        {"id": 1004, "room": "4", "paid": False},
    ]

    now = datetime.now().strftime("%Y-%m-%d")

    for t in tenants:
        cursor.execute(
            "UPDATE rooms SET tenant_id=?, paid=?, last_paid=? WHERE room_number=?",
            (
                t["id"],
                1 if t["paid"] else 0,
                now if t["paid"] else None,
                t["room"]
            )
        )

        if t["paid"]:
            cursor.execute(
                """
                INSERT INTO payments (room_number, tenant_id, amount, date, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (t["room"], t["id"], 120, now, "approved")
            )

    conn.commit()