
import asyncio
import sys
import os
from telethon import TelegramClient
import sqlite3
import time
from database import DB_NAME
from utils import get_admin_ids
try:
    from dotenv import load_dotenv  # type: ignore[reportMissingImports]
except Exception:
    load_dotenv = None

if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if not os.path.exists("uploads"):
    os.makedirs("uploads")
    try:
        os.chmod("uploads", 0o700)
    except Exception:
        pass
    try:
        from log_helper import console_log
        console_log("uploads folder created.", "پوشه uploads ساخته شد.")
    except Exception:
        print("uploads folder created.")

if load_dotenv is not None:
    try:
        load_dotenv()
    except Exception:
        pass

# Prefer credentials from config.py (kept in-repo per user request). Fall back to env vars.
try:
    from config import API_ID as CFG_API_ID, API_HASH as CFG_API_HASH, BOT_TOKEN as CFG_BOT_TOKEN, OWNER_ID as CFG_OWNER_ID, CHANNEL_USERNAME as CFG_CHANNEL_USERNAME
except Exception:
    CFG_API_ID = CFG_API_HASH = CFG_BOT_TOKEN = CFG_OWNER_ID = CFG_CHANNEL_USERNAME = None

API_ID_raw = str(CFG_API_ID) if CFG_API_ID is not None else os.getenv('API_ID')
API_HASH = CFG_API_HASH if CFG_API_HASH is not None else os.getenv('API_HASH')
BOT_TOKEN = CFG_BOT_TOKEN if CFG_BOT_TOKEN is not None else os.getenv('BOT_TOKEN')
# Optional runtime settings
OWNER_ID = CFG_OWNER_ID if CFG_OWNER_ID is not None else os.getenv('OWNER_ID')
CHANNEL_USERNAME = CFG_CHANNEL_USERNAME if CFG_CHANNEL_USERNAME is not None else os.getenv('CHANNEL_USERNAME')

try:
    API_ID = int(API_ID_raw) if API_ID_raw is not None else None
except Exception:
    API_ID = None

# Normalize OWNER_ID to int when possible
try:
    OWNER_ID = int(OWNER_ID) if OWNER_ID is not None else None
except Exception:
    pass
missing_creds = any(x in ('', None) for x in [API_ID, API_HASH, BOT_TOKEN])
if missing_creds:
    try:
        from log_helper import console_log
        console_log("⚠️ API_ID / API_HASH / BOT_TOKEN are not set. Running in dry-run mode (no Telegram).",
                    "⚠️ API_ID / API_HASH / BOT_TOKEN تنظیم نشده‌اند. برنامه در حالت dry-run اجرا خواهد شد (بدون اتصال به تلگرام).")
    except Exception:
        print("⚠️ API_ID / API_HASH / BOT_TOKEN تنظیم نشده‌اند. برنامه در حالت dry-run اجرا خواهد شد (بدون اتصال به تلگرام).")
    DRY_RUN = True
else:
    DRY_RUN = False

async def main():
    # Create client after config is validated
    user_states = {}

    from database import init_db
    init_db()
    try:
        from log_helper import console_log
        console_log("database checked/initialized.", "دیتابیس بررسی/مقداردهی شد.")
    except Exception:
        print("database checked/initialized.")

    if not DRY_RUN:
        client = TelegramClient('bot_session', API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)

        from user_panel import setup_user_handlers
        from admin_panel import setup_admin_handlers
        from event_manager import setup_event_handlers
        from registration_flow import setup_registration_handlers
        from membership_flow import setup_membership_handlers

        setup_user_handlers(client, user_states)
        setup_admin_handlers(client, user_states)
        setup_event_handlers(client, user_states)
        setup_registration_handlers(client, user_states)
        setup_membership_handlers(client, user_states)

        try:
            from log_helper import console_log
            console_log("bot is up and running.", "بات روشن و در حال اجرا است.")
            console_log("for exiting, press Ctrl+C.", "برای خروج Ctrl+C را فشار دهید.")
        except Exception:
            print("bot is up and running.")
            print("for exiting, press Ctrl+C.")
    else:
        client = None
        try:
            from log_helper import console_log
            console_log("Running in dry-run mode: Telegram client not started. Handlers are not attached.",
                        "در حالت dry-run اجرا می‌شود: کلاینت تلگرام شروع نشد. هندلرها متصل نیستند.")
        except Exception:
            print("Running in dry-run mode: Telegram client not started. Handlers are not attached.")

    async def deadline_watcher():
        while True:
            try:
                now = int(time.time())
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT id, title FROM events WHERE is_active = 1 AND end_at_ts IS NOT NULL AND end_at_ts <= ?", (now,))
                rows = c.fetchall()
                for eid, title in rows:
                    c.execute("UPDATE events SET is_active = 0 WHERE id = ?", (eid,))
                conn.commit()
                conn.close()
                if rows:
                    if DRY_RUN:
                        try:
                            from log_helper import console_log
                            console_log(f"[dry-run] deadline_watcher: archived events: {[t for (_,t) in rows]}",
                                        f"[dry-run] deadline_watcher: رویدادهای بایگانی‌شده: {[t for (_,t) in rows]}")
                        except Exception:
                            print(f"[dry-run] deadline_watcher: archived events: {[t for (_,t) in rows]}")
                    else:
                        admins = get_admin_ids()
                        for eid, title in rows:
                            msg = f"⏱️ مهلت ثبت‌نام رویداد '{title}' تمام شد و به آرشیو منتقل شد."
                            for aid in admins:
                                try:
                                    await client.send_message(aid, msg)
                                except Exception:
                                    pass
            except Exception:
                pass
            await asyncio.sleep(60)

    asyncio.create_task(deadline_watcher())
    if not DRY_RUN:
        await client.run_until_disconnected()
    else:
        # In dry-run mode, keep the loop running until KeyboardInterrupt
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        try:
            from log_helper import console_log
            console_log("bot stopped by user request.", "بات به درخواست کاربر متوقف شد.")
        except Exception:
            print("bot stopped by user request.")