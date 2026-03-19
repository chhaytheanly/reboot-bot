from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from src.database.database import get_room_by_user


class KeyboardFactory:

    @staticmethod
    def get_main_menu_keyboard(user_id: int = None, has_room: bool = None):
        if has_room is None and user_id:
            has_room = get_room_by_user(user_id) is not None

        buttons = [
            [KeyboardButton("🏠 My Room")],
            [KeyboardButton("💰 Pay Rent")],
            [KeyboardButton("📜 Payment History")],
            [KeyboardButton("❓ Help")]
        ]

        return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

    @staticmethod
    def get_admin_menu_keyboard():
        buttons = [
            [KeyboardButton("📊 Room Status")],
            [KeyboardButton("✅ Paid Rooms")],
            [KeyboardButton("🔄 Reset Month")],
            [KeyboardButton("⏰ Send Reminders")],
            [KeyboardButton("❓ Admin Help")]
        ]

        return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

    @staticmethod
    def get_room_selection_keyboard():
        """Get inline keyboard for room selection (5 per row)"""
        keyboard = []
        for i in range(1, 31, 5):
            row = []
            for j in range(i, min(i + 5, 31)):
                row.append(InlineKeyboardButton(f"🚪 {j}", callback_data=f"room_{j}"))
            keyboard.append(row)
        return keyboard

    @staticmethod
    def get_tenant_action_keyboard():
        """Get inline keyboard for tenant actions"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 My Room", callback_data="my_room")],
            [InlineKeyboardButton("💰 Pay Rent", callback_data="pay")],
            [InlineKeyboardButton("📜 Payment History", callback_data="history")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ])

    @staticmethod
    def get_payment_action_keyboard():
        """Get inline keyboard for payment actions"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Pay Now", callback_data="pay")],
            [InlineKeyboardButton("🏠 My Room", callback_data="my_room")]
        ])

    @staticmethod
    def get_receipt_approval_keyboard(user_id: str, room: str):
        """Get inline keyboard for admin receipt approval"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{room}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{room}")
            ],
            [
                InlineKeyboardButton("📜 View History", callback_data=f"history_{room}")
            ]
        ])

    @staticmethod
    def get_admin_room_action_keyboard(room: str):
        """Get inline keyboard for admin room actions"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Mark Paid", callback_data=f"admin_paid_{room}"),
                InlineKeyboardButton("❌ Mark Unpaid", callback_data=f"admin_unpaid_{room}")
            ],
            [
                InlineKeyboardButton("👤 Tenant Info", callback_data=f"tenant_info_{room}"),
                InlineKeyboardButton("📜 History", callback_data=f"history_{room}")
            ],
            [
                InlineKeyboardButton("⏰ Send Reminder", callback_data=f"remind_{room}")
            ]
        ])

    @staticmethod
    def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel"):
        """Get yes/no confirmation keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=confirm_data),
                InlineKeyboardButton("❌ No", callback_data=cancel_data)
            ]
        ])

    @staticmethod
    def get_back_keyboard(back_data: str = "back"):
        """Get simple back button keyboard"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data=back_data)]
        ])
