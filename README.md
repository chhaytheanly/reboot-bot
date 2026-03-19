# Rental Telegram Bot

A Telegram bot for rental room management. Built for managing tenant assignments, rent payments, and payment approvals.

## Features

- **Tenant Self-Service**
  - Room selection (Rooms 1-30)
  - QR code payment display
  - Receipt upload via photo
  - Payment status tracking

- **Admin Management**
  - View paid/unpaid rooms
  - Approve/reject payment receipts
  - Monthly auto-reset of payment status
  - Daily payment reminders
  - Admin web panel integration

- **Automation**
  - Scheduled reminders at 8:00 PM daily
  - Auto-reset on the 1st of each month

## Project Structure

```
telegram-tool/
├── main.py                 # Entry point - starts FastAPI server
├── src/
│   ├── bot.py              # Telegram bot initialization & command handlers
│   ├── api/                # FastAPI REST API (not shown in current files)
│   ├── app/
│   │   ├── service/
│   │   │   ├── tenant.py   # Tenant commands: /start, /pay, receipt handling
│   │   │   ├── admin.py    # Admin commands: /status, /reset, /paid
│   │   │   └── call_back.py# Callback query handler for inline buttons
│   │   └── utils/
│   │       ├── config.py   # Environment configuration loader
│   │       ├── verify.py   # Admin permission checker
│   │       ├── scheduler.py# APScheduler for automated tasks
│   │       └── helpers/
│   │           └── logging.py  # Colored logging utility
│   └── database/
│       └── database.py     # SQLite database operations
├── receipts/               # Uploaded receipt images storage
├── public/images/          # QR code and static images
└── pyproject.toml          # Project dependencies
```

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Setup

1. **Clone and install dependencies:**

```bash
uv sync
```

2. **Configure environment variables:**

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
WEBAPP_URL=https://your-webapp-domain.com
```

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |
| `ADMIN_IDS` | Comma-separated Telegram user IDs of admins |
| `WEBAPP_URL` | Base URL for the admin web panel (optional) |

3. **Add QR code:**

Place your payment QR code image at `public/images/kh-qr.jpg`

## Usage

### Running the Bot

```bash
# Run the bot (main.py starts FastAPI + Telegram polling)
uv run python main.py
```

**Note:** The current `main.py` starts a FastAPI server on port 8000. To run only the Telegram bot, use:

```bash
uv run python src/bot.py
```

### Commands

#### Tenant Commands

| Command | Description |
|---------|-------------|
| `/start` | Select your room number (1-30) |
| `/pay` | Display payment QR code (after room selection) |

**Tenant Flow:**
1. Send `/start` → Select room from inline keyboard
2. Room assigned to your Telegram account
3. Send `/pay` or click "💰 Pay Rent" → View QR code
4. Scan QR and pay → Take screenshot of receipt
5. Send receipt as photo to bot
6. Wait for admin approval

#### Admin Commands

| Command | Description |
|---------|-------------|
| `/status` | List all unpaid rooms with tenant names |
| `/paid` | List all paid rooms with tenant names |
| `/reset` | Reset all rooms to unpaid status (monthly) |

**Admin Actions:**
- Receive payment receipt notifications with approve/reject buttons
- Click "✅ Approve" → Marks room as paid, logs payment
- Click "❌ Reject" → Notifies tenant of rejection

## Code Explanation

### Core Components

#### `main.py`
Application entry point that starts the FastAPI server with hot reload enabled.

```python
uvicorn.run("src.api:api_app", host="0.0.0.0", port=8000, reload=True)
```

#### `src/bot.py`
Telegram bot initialization:
- Builds the bot application with token from config
- Validates admin IDs at startup (removes unreachable admins)
- Registers command and callback handlers
- Starts the scheduler for automated tasks
- Runs bot polling loop

**Handlers registered:**
- `CommandHandler("start", TenantService.start)` - Room selection
- `CommandHandler("status", AdminService.status)` - Unpaid rooms list
- `CommandHandler("reset", AdminService.reset)` - Monthly reset
- `CommandHandler("paid", AdminService.paid_done)` - Paid rooms list
- `CallbackQueryHandler(CallbackService.handle_callback)` - Button clicks
- `MessageHandler(filters.PHOTO, TenantService.handle_receipt)` - Receipt photos

#### `src/app/service/tenant.py`
Handles tenant interactions:

| Method | Purpose |
|--------|---------|
| `start()` | Shows room selection grid (3 buttons per row, 1-30) |
| `select_room()` | Assigns room to user, prevents reassignment |
| `show_qr()` | Displays payment QR code from `public/images/kh-qr.jpg` |
| `handle_receipt()` | Saves receipt, forwards to admins with approve/reject buttons |

#### `src/app/service/admin.py`
Admin management functions:

| Method | Purpose |
|--------|---------|
| `_check_admin()` | Permission decorator - rejects non-admins |
| `status()` | Lists unpaid rooms with tenant names and last payment date |
| `paid_done()` | Lists all paid rooms |
| `reset()` | Resets all rooms to unpaid status |
| `panel()` | Opens admin web panel (requires `WEBAPP_URL`) |
| `send_reminder()` | Sends payment reminders to tenants |

#### `src/app/service/call_back.py`
Handles all inline keyboard button clicks:

| Callback Pattern | Action |
|------------------|--------|
| `room_{number}` | Assign room to user |
| `pay` | Show QR code |
| `approve_{user}_{room}` | Mark room as paid, log payment |
| `reject_{user}_{room}` | Reject payment submission |
| `remind_{user}_{room}` | Send payment reminder |
| `history_{user}_{room}` | Show payment history |

#### `src/database/database.py`
SQLite database layer:

**Tables:**
- `rooms` - Room assignments and payment status
  - `room_number` (PK), `tenant_id`, `tenant_name`, `paid`, `last_paid`
- `payments` - Payment history log
  - `id`, `room_number`, `tenant_id`, `amount`, `date`, `status`

**Key Functions:**
- `init_db()` - Creates tables, initializes 30 rooms
- `assign_tenant()` - Links user to room (prevents duplicates)
- `mark_paid()` - Updates room status, inserts payment record
- `get_unpaid()` / `get_paid()` - Filter rooms by payment status
- `reset_rooms()` - Sets all rooms to unpaid
- `seed_data()` - Populates test data for development

#### `src/app/utils/scheduler.py`
Automated tasks using APScheduler:

| Job | Schedule | Action |
|-----|----------|--------|
| `reminder` | Daily at 20:00 | Notifies admins of unpaid room count |
| `monthly_reset` | 1st of month at 00:00 | Resets all rooms to unpaid |

#### `src/app/utils/config.py`
Environment configuration loader using `dotenv`:
- Loads `TELEGRAM_BOT_TOKEN` and `ADMIN_IDS` from `.env`
- Parses `ADMIN_IDS` as comma-separated integers

#### `src/app/utils/verify.py`
Simple admin permission checker:
```python
def is_admin(id: str) -> bool:
    return id in config.ADMIN_IDS
```

#### `src/app/utils/helpers/logging.py`
Colored console logging:
- **Green** - Info messages
- **Yellow** - Warnings
- **Red** - Errors
- **Cyan** - Debug messages

## Database Schema

```sql
-- Rooms table
CREATE TABLE rooms (
    room_number TEXT PRIMARY KEY,
    tenant_id INTEGER UNIQUE,
    tenant_name TEXT,
    paid INTEGER DEFAULT 0,
    last_paid TEXT
);

-- Payments history table
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT,
    tenant_id INTEGER,
    amount REAL,
    date TEXT,
    status TEXT,
    FOREIGN KEY (room_number) REFERENCES rooms(room_number) ON DELETE CASCADE
);
```

## Development

### Adding Test Data

Use the `seed_data()` function to populate test tenants:

```python
from src.database.database import seed_data
seed_data()
```

This creates 4 test tenants:
- Room 1 & 2: Paid
- Room 3 & 4: Unpaid

### Resetting Database

```python
from src.database.database import reset_db, init_db
reset_db()  # Drops all tables
init_db()   # Recreates tables
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-telegram-bot==20.0` | Telegram Bot API |
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `apscheduler` | Background task scheduling |
| `aiofiles` | Async file operations |
| `python-dotenv` | Environment variable management |
| `jinja2` | Template engine (for web panel) |
| `qrcode` | QR code generation |

## License

Private project - Rental room management tool
