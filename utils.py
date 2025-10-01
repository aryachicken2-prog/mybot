def get_admin_main_menu():
    return get_main_menu_buttons(is_admin=True)

from telethon import Button
import os
import time
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
import asyncio
import html
import threading
import base64
from typing import Optional
try:
    from cryptography.fernet import Fernet  # type: ignore[reportMissingImports]
except Exception:
    Fernet = None

CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@mnd_portal')
OWNER_ID = 7702648742

async def is_user_member(client, user_id):
    try:
        await client(GetParticipantRequest(channel=CHANNEL_USERNAME, participant=user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return True

def get_main_menu_buttons(is_admin=False):
    if is_admin:
        # show current console log language setting and provide a toggle button
        try:
            en_on = get_setting('console_logs_english', '1') == '1'
        except Exception:
            en_on = True
        en_label = "✅ EN" if en_on else "❌ EN"
        # Improved admin menu layout (cleaner labels, diagnostics button)
        # fetch counts for pending items so we can show badges like "تیکت‌ها (3)"
        try:
            import sqlite3
            from database import DB_NAME
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM registrations WHERE status = 'pending'")
            pending_regs = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM memberships WHERE LOWER(TRIM(status)) = 'pending'")
            membership_pending = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM ideas WHERE LOWER(TRIM(status)) = 'pending'")
            ideas_pending = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM collaborations WHERE LOWER(TRIM(status)) = 'pending'")
            collabs_pending = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM donations WHERE LOWER(TRIM(status)) = 'pending'")
            donations_pending = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
            tickets_open = c.fetchone()[0] or 0
            conn.close()
        except Exception:
            pending_regs = membership_pending = ideas_pending = collabs_pending = donations_pending = tickets_open = 0

        return [
            [Button.inline(f"📅 مدیریت رویدادها", b"admin_events"), Button.inline(f"⏳ ثبت‌نام‌های در انتظار ({pending_regs})", b"admin_pending_regs")],
            [Button.inline(f"👥 درخواست‌های عضویت ({membership_pending})", b"admin_membership_requests"), Button.inline("📤 ارسال همگانی", b"admin_broadcast")],
            [Button.inline(f"💡 ایده‌ها ({ideas_pending})", b"admin_ideas"), Button.inline(f"🤝 همکاری‌ها ({collabs_pending})", b"admin_collaborations")],
            [Button.inline(f"💰 حمایت‌ها ({donations_pending})", b"admin_donations"), Button.inline(f"🎟️ تیکت‌ها ({tickets_open})", b"admin_tickets")],
            [Button.inline("🧏‍♂️ مدیریت ادمین‌ها", b"admin_manage_admins"), Button.inline("❓ FAQ", b"admin_faq")],
            [Button.inline("🧹 نگهداری/پاکسازی", b"admin_maintenance"), Button.inline("📜 ارسال گواهی", b"admin_send_cert")],
            [Button.inline("📥 اکسل تاییدشدگان", b"admin_export_excel"), Button.inline("🎯 ظرفیت رویداد", b"admin_capacity")],
            [Button.inline("⚙️ تنظیمات", b"admin_settings")],
            [Button.inline("✏️ ویرایش", b"admin_edit_menu" )]
        ]
    else:
        import sqlite3
        from database import DB_NAME
        buttons = []
        try:
            main_ids_raw = get_setting('main_events', '')
            main_ids = [int(x) for x in main_ids_raw.split(',') if x.strip().isdigit()]
            if main_ids:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                q = f"SELECT id, title FROM events WHERE id IN ({','.join(['?']*len(main_ids))}) AND is_active = 1"
                c.execute(q, tuple(main_ids))
                mains = c.fetchall()
                conn.close()
                for mid, mtitle in mains:
                    buttons.append([Button.inline(f"⭐ {mtitle}", f"event_{mid}")])
        except Exception:
            pass
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT 1 FROM events WHERE is_active = 1 LIMIT 1")
            has_events = c.fetchone() is not None
            c.execute("SELECT 1 FROM faqs LIMIT 1")
            has_faq = c.fetchone() is not None
            c.execute("SELECT 1 FROM certificates LIMIT 1")
            has_any_cert = c.fetchone() is not None
            conn.close()
        except Exception:
            has_events = True
            has_faq = True
            has_any_cert = False
        flat = []
        # Primary actions
        flat.append(Button.inline("📅 رویدادها", b"user_events"))
        flat.append(Button.inline("👥 عضویت در انجمن", b"user_membership"))
        flat.append(Button.inline("🧑‍💼 پروفایل من", b"user_profile"))
        flat.append(Button.inline("📊 ثبت‌نام‌های من", b"user_my_regs"))
        if has_any_cert:
            flat.append(Button.inline("📜 گواهی‌های من", b"user_my_certs"))

        # Support & contact
        flat.append(Button.inline("📬 ارسال تیکت / تماس با ادمین", b"ask_ticket"))

        # Contributions and ideas
        flat.append(Button.inline("💡 ارسال ایده", b"user_send_idea"))
        flat.append(Button.inline("🤝 درخواست همکاری", b"user_request_collab"))
        flat.append(Button.inline("💳 حمایت مالی", b"user_donate"))

        # External channel link and FAQ
        flat.append(Button.url("📢 کانال انجمن", f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"))
        if has_faq:
            flat.append(Button.inline("❓ سوالات متداول", b"user_faq"))
    flat.append(Button.inline("📖 راهنمای جامع ربات", b"user_help"))
    flat.append(Button.inline("ℹ️ درباره ما", b"user_about"))
    row = []
    for btn in flat:
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

CANCEL_BUTTON = [Button.inline("❌ لغو و بازگشت به منو", b"cancel")]
BACK_BUTTON = [Button.inline("🔙 بازگشت", b"back")]

ABOUT_TEXT = f"""
🤖 *  ربات رسمی انجمن علمی دانشجویی X *  
  دانشگاه  Y 

📌 امکانات:
- ثبت‌نام در رویدادهای علمی و کارگاه‌ها
- دریافت گواهی شرکت
- پاسخ به سوالات متداول
- ارتباط مستقیم با ادمین‌ها از طریق تیکت

🌐 کانال رسمی: https://t.me/{CHANNEL_USERNAME.lstrip('@')}
"""

def paginate_buttons(data_list, data_type, page=0, per_page=5):
    if not data_list:
        return [[Button.inline("❌ موردی یافت نشد", b"dummy")], [Button.inline("🏠 منوی اصلی", b"main_menu")]]

    buttons = []
    start = page * per_page
    end = start + per_page
    slice_data = data_list[start:end]
    for item in slice_data:
        # item expected to be a sequence like (id, title, ...)
        try:
            label = item[1] if len(item) > 1 else str(item[0])
        except Exception:
            label = str(item)
        buttons.append([Button.inline(f"• {label}", f"{data_type}_{item[0]}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(Button.inline("⬅️ قبلی", f"{data_type}_page_{page-1}"))
    if end < len(data_list):
        nav_buttons.append(Button.inline("➡️ بعدی", f"{data_type}_page_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([Button.inline("🏠 بازگشت به منو", b"main_menu")])
    return buttons

def set_user_state(user_states, user_id, state, data=None):
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['state'] = state
    if data is not None:
        if 'data' not in user_states[user_id]:
            user_states[user_id]['data'] = {}
        user_states[user_id]['data'].update(data)

def get_user_state(user_states, user_id):
    return user_states.get(user_id, {}).get('state', None)

def get_user_data(user_states, user_id):
    return user_states.get(user_id, {}).get('data', {})

def clear_user_state(user_states, user_id):
    if user_id in user_states:
        del user_states[user_id]

async def get_message_text(event):
    if event.message.reply_to:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            return replied_msg.text
    return event.message.text.strip() if event.message.text else ""

def is_admin(db_path, user_id):
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_channel_join_buttons():
    return [
        [Button.url("عضویت در کانال انجمن", f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [Button.inline("✅ بررسی عضویت", b"check_membership")]
    ]

CHANNEL_JOIN_MESSAGE = "🔐 برای استفاده از ربات، باید عضو کانال «انجمن X دانشگاه Y» شوید."

def get_setting(key, default="0"):
    import sqlite3
    from database import DB_NAME
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] is not None else default
    except Exception:
        return default

def notify_admins_about(conn_client, db_path, text):
    """Notify all admins (non-blocking). conn_client may be None; caller provides Telegram client.
    This schedules send_message tasks for each admin ID.
    """
    try:
        admins = get_admin_ids()
        for aid in admins:
            try:
                if conn_client:
                    try:
                        import asyncio
                        asyncio.create_task(conn_client.send_message(aid, text))
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass


async def send_with_rate_limit(client, user_id, text=None, file=None, buttons=None, delay_between=0.18, max_retries=4):
    """Send a message/file to `user_id` with basic rate-limit/backoff handling.
    - `client` is a Telethon client instance.
    - `file` can be a path or Telethon message.file object (passed-through to send_file).
    - On FloodWaitError the helper will sleep for the required seconds and retry.
    - Returns the sent message object on success, or None on persistent failure.
    """
    try:
        import asyncio
        from telethon.errors import FloodWaitError
    except Exception:
        # If telethon not available in caller environment, attempt naive send
        try:
            if file:
                return await client.send_file(user_id, file, caption=text, buttons=buttons)
            else:
                return await client.send_message(user_id, text, buttons=buttons)
        except Exception:
            return None

    attempt = 0
    while attempt < max_retries:
        try:
            if file:
                sent = await client.send_file(user_id, file, caption=text, buttons=buttons)
            else:
                sent = await client.send_message(user_id, text, buttons=buttons)
            # small pause between sends to avoid hitting limits
            try:
                await asyncio.sleep(delay_between)
            except Exception:
                pass
            return sent
        except FloodWaitError as fw:
            wait_secs = getattr(fw, 'seconds', None) or 30
            try:
                await asyncio.sleep(wait_secs + 1)
            except Exception:
                pass
            attempt += 1
        except Exception:
            # exponential backoff for other errors
            try:
                await asyncio.sleep(1 + attempt * 2)
            except Exception:
                pass
            attempt += 1
    return None

def set_setting(key, value):
    import sqlite3
    from database import DB_NAME
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    conn.commit()
    conn.close()

def get_admin_ids():
    import sqlite3
    from database import DB_NAME
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids

def parse_jalali_to_epoch(jalali_datetime_str):
    """
    ورودی مثال: 1403/07/01 18:30
    خروجی: epoch seconds (int) در UTC تقریبی بر اساس تبدیل دستی (بدون کتابخانه)
    توجه: برای دقت بهتر می‌توان از jdatetime استفاده کرد؛ در اینجا الگوریتم متداول تبدیل جلالی به میلادی پیاده شده است.
    """
    try:
        s = str(jalali_datetime_str).strip()
        translation_table = str.maketrans(
            '٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹',
            '01234567890123456789'
        )
        s = s.translate(translation_table)
        parts = s.split()
        if len(parts) == 1:
            date_part = parts[0]
            time_part = '00:00'
        else:
            date_part, time_part = parts[0], parts[1]
        jy, jm, jd = [int(x) for x in date_part.replace('-', '/').split('/')]
        hh, mm = [int(x) for x in time_part.split(':')[:2]]
        g_y, g_m, g_d = _jalali_to_gregorian(jy, jm, jd)
        import datetime
        try:
            import pytz
            tz = pytz.timezone('Asia/Tehran')
            local_dt = datetime.datetime(g_y, g_m, g_d, hh, mm, 0)
            aware_local = tz.localize(local_dt)
            utc_dt = aware_local.astimezone(pytz.UTC)
            return int(utc_dt.timestamp())
        except Exception:
            offset = datetime.timedelta(hours=3, minutes=30)
            local_dt = datetime.datetime(g_y, g_m, g_d, hh, mm, 0)
            utc_dt = (local_dt - offset).replace(tzinfo=datetime.timezone.utc)
            return int(utc_dt.timestamp())
    except Exception:
        return None

def _jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        gy += 100 * ((days - 1) // 36524)
        days = (days - 1) % 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    sal_a = [0,31, (29 if ((gy%4==0 and gy%100!=0) or (gy%400==0)) else 28),31,30,31,30,31,31,30,31,30,31]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return gy, gm, gd

def _gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    jy = 0
    gy2 = gy - 1600
    days = (365 * gy2) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400)
    for i in range(1, gm):
        days += g_d_m[i]
    days += gd - 1
    j_days = days - 79
    j_np = j_days // 12053
    j_days = j_days % 12053
    jy = 979 + 33 * j_np + 4 * (j_days // 1461)
    j_days %= 1461
    if j_days >= 366:
        jy += (j_days - 1) // 365
        j_days = (j_days - 1) % 365
    jm = 0
    if j_days < 186:
        jm = 1 + j_days // 31
        jd = 1 + (j_days % 31)
    else:
        j_days -= 186
        jm = 7 + j_days // 30
        jd = 1 + (j_days % 30)
    return jy, jm, jd

def epoch_to_jalali_str(ts):
    """Return a formatted Jalali datetime string for an epoch (UTC) in Iran local time: '1403/07/01 18:30'"""
    try:
        import datetime
        try:
            import pytz
            tz = pytz.timezone('Asia/Tehran')
            dt = datetime.datetime.fromtimestamp(int(ts), tz=pytz.UTC)
            local = dt.astimezone(tz)
        except Exception:
            # fallback: apply fixed +3:30 offset
            offset = datetime.timedelta(hours=3, minutes=30)
            local = (datetime.datetime.fromtimestamp(int(ts)) + offset)
        gy, gm, gd = local.year, local.month, local.day
        hh, mm = local.hour, local.minute
        jy, jm, jd = _gregorian_to_jalali(gy, gm, gd)
        return f"{jy:04d}/{jm:02d}/{jd:02d} {hh:02d}:{mm:02d}"
    except Exception:
        return str(ts)

def is_safe_upload_path(path):
    try:
        base = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        target = os.path.abspath(path)
        return target.startswith(base + os.sep) and os.path.exists(target)
    except Exception:

        return False


# ---------------------- Security helpers ----------------------
# Simple in-memory rate limiter (per-user). Not persisted across restarts.
_rate_limit_cache = {}
_rate_limit_lock = threading.Lock()

def rate_limit_check(user_id: int, limit: int = 20, window: int = 60) -> bool:
    """Allow up to `limit` actions per `window` seconds for a given user_id.
    Returns True if allowed, False if rate-limited.
    """
    # Rate limiting disabled per user request — always allow actions.
    # If you later want to re-enable, restore the previous implementation.
    return True


def sanitize_text(text: Optional[str], max_len: int = 2000) -> str:
    """Lightweight input sanitizer for textual fields.
    - removes null bytes, collapses whitespace, HTML-escapes to reduce XSS risk
    - truncates to `max_len` characters
    Returns a safe string (never None).
    """
    if text is None:
        return ""
    try:
        s = str(text)
        s = s.replace('\x00', '')
        # collapse excessive whitespace
        s = ' '.join(s.split())
        # escape HTML special chars
        s = html.escape(s)
        if len(s) > max_len:
            s = s[:max_len]
        return s
    except Exception:
        return ""


# Optional encryption helpers (Fernet). Set environment variable ENCRYPTION_KEY
# to a valid Fernet key (44 url-safe base64-encoded bytes) to enable encryption.
_ENCRYPTOR = None

def init_encryption(key: Optional[str] = None):
    """Initialize Fernet encryptor from given key or `ENCRYPTION_KEY` env var.
    If cryptography is not installed or key is missing/invalid, encryption stays disabled.
    """
    global _ENCRYPTOR
    if Fernet is None:
        _ENCRYPTOR = None
        return None
    try:
        k = key or os.getenv('ENCRYPTION_KEY')
        if not k:
            _ENCRYPTOR = None
            return None
        if isinstance(k, str) and len(k) != 44:
            # user may provide plain passphrase; do not attempt derivation here to avoid complexity
            # require a proper Fernet key
            try:
                from log_helper import console_log
                console_log("[security] ENCRYPTION_KEY appears invalid length; encryption disabled.", "[security] طول ENCRYPTION_KEY نامعتبر است؛ رمزنگاری غیرفعال شد.")
            except Exception:
                print("[security] ENCRYPTION_KEY appears invalid length; encryption disabled.")
            _ENCRYPTOR = None
            return None
        _ENCRYPTOR = Fernet(k.encode() if isinstance(k, str) else k)
        return _ENCRYPTOR
    except Exception as e:
        try:
            from log_helper import console_log
            console_log("[security] init_encryption failed: %s" % str(e), "[security] init_encryption با خطا مواجه شد: %s" % str(e))
        except Exception:
            print("[security] init_encryption failed:", e)
    _ENCRYPTOR = None
    return None


def encrypt_string(plaintext: str) -> str:
    """Encrypt plaintext with Fernet if available. If not available, returns plaintext (no-op).
    NOTE: Callers should check whether encryption is actually enabled in their deployment.
    """
    if not plaintext:
        return plaintext
    if Fernet is None:
        return plaintext
    if _ENCRYPTOR is None:
        init_encryption()
    try:
        if _ENCRYPTOR:
            return _ENCRYPTOR.encrypt(plaintext.encode()).decode()
    except Exception:
        pass
    return plaintext


def decrypt_string(token: str) -> str:
    """Decrypt a Fernet token if possible; otherwise return the token unchanged."""
    if not token:
        return token
    if Fernet is None:
        return token
    if _ENCRYPTOR is None:
        init_encryption()
    try:
        if _ENCRYPTOR:
            return _ENCRYPTOR.decrypt(token.encode()).decode()
    except Exception:
        pass
    return token


def mask_secret(value: Optional[str], shown: int = 4) -> str:
    """Return masked version of a secret for safe logging: show last `shown` chars."""
    if not value:
        return ''
    s = str(value)
    if len(s) <= shown:
        return '*' * len(s)
    return '*' * (len(s) - shown) + s[-shown:]


def validate_secret_token(headers: dict, expected: str) -> bool:
    """Validate telegram webhook secret token header (if using webhooks).
    Expects header key 'X-Telegram-Bot-Api-Secret-Token'.
    """
    try:
        if not expected:
            return False
        token = headers.get('X-Telegram-Bot-Api-Secret-Token') or headers.get('x-telegram-bot-api-secret-token')
        return bool(token) and str(token) == expected
    except Exception:
        return False


# initialize encryption on import if key present
try:
    init_encryption()
except Exception:
    pass