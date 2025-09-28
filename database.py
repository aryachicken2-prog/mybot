
import sqlite3
import os
DB_NAME = os.getenv('JURISLAW_DB', "jurislaw_bot.db")
try:
    OWNER_ID = int(os.getenv('OWNER_ID', '7702648742'))
except Exception:
    OWNER_ID = 7702648742

def init_db(db_path=None):
    """Initialize the database. Use db_path to override default DB file.
    This sets safer pragmas and creates audit tables for admin actions and send errors.
    """
    if db_path:
        path = db_path
    else:
        path = DB_NAME
    d = os.path.dirname(path) or '.'
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(path, isolation_level=None)
    c = conn.cursor()
    try:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        national_id TEXT,
        student_id TEXT,
        phone TEXT,
        is_student INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        join_date TEXT DEFAULT (datetime('now', 'localtime')),
        reason_if_rejected TEXT,
        language TEXT DEFAULT 'fa'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        role TEXT DEFAULT 'admin',
        added_date TEXT DEFAULT (datetime('now', 'localtime'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        cost_type TEXT NOT NULL DEFAULT 'free',
        fixed_cost INTEGER DEFAULT 0,
        student_cost INTEGER DEFAULT 0,
        non_student_cost INTEGER DEFAULT 0,
        card_number TEXT,
        poster_file_id TEXT,
        is_active INTEGER DEFAULT 1,
        report_message_ids TEXT,
        report_payloads TEXT,
        tags TEXT,
        attendance_code TEXT,
        end_at_ts INTEGER,
        end_set_by INTEGER,
        created_by INTEGER,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        register_date TEXT DEFAULT (datetime('now', 'localtime')),
        payment_receipt_file_id TEXT,
        status TEXT DEFAULT 'pending'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        admin_reply TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        replied_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        file_id TEXT NOT NULL,
        sent_by_admin INTEGER NOT NULL,
        sent_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        file_path TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        checked_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')

    try:
        c.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'admin'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN capacity INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN reminders_enabled INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN end_at_ts INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN end_set_by INTEGER")
    except Exception:
        pass
    # certificate issuance fields for free events
    try:
        c.execute("ALTER TABLE events ADD COLUMN cert_fee INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN cert_card_number TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN cert_card_holder TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN cert_fee_student INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN cert_fee_non_student INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN single_registration INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_reg_unique ON registrations(user_id, event_id)")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE registrations ADD COLUMN reminder_opt_in INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE registrations ADD COLUMN reminder_intervals TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN reminder_recipients TEXT DEFAULT 'pending,approved'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN reminder_intervals TEXT DEFAULT '24h,2h'")
    except Exception:
        pass
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_att_unique ON attendance(user_id, event_id)")
    except Exception:
        pass

    try:
        c.execute('''CREATE TABLE IF NOT EXISTS reminders_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            sent_at INTEGER NOT NULL
        )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(admins)")
        cols = [r[1] for r in c.fetchall()]
        if 'role' not in cols:
            try:
                c.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'admin'")
            except Exception:
                pass
        c.execute("INSERT OR IGNORE INTO admins (user_id, added_by, role) VALUES (?, ?, 'owner')", (OWNER_ID, OWNER_ID))
    except Exception:
        try:
            c.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (OWNER_ID, OWNER_ID))
        except Exception:
            pass

    # Membership requests table
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            major TEXT,
            entry_year TEXT,
            student_number TEXT,
            national_id TEXT,
            phone TEXT,
            telegram_username TEXT,
            student_card_file TEXT,
            status TEXT DEFAULT 'pending',
            reason_if_rejected TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
    except Exception:
        pass
    # Ideas, collaboration requests and donations tables
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
    except Exception:
        pass

    try:
        c.execute('''CREATE TABLE IF NOT EXISTS collaborations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            organization TEXT,
            proposal TEXT,
            file_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
    except Exception:
        pass

    try:
        c.execute('''CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT DEFAULT 'IRR',
            receipt_file TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
    except Exception:
        pass
    # Ensure admin metadata columns exist on submission tables
    try:
        c.execute("ALTER TABLE ideas ADD COLUMN admin_note TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE ideas ADD COLUMN processed_by INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE ideas ADD COLUMN processed_at TEXT")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE collaborations ADD COLUMN admin_note TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE collaborations ADD COLUMN processed_by INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE collaborations ADD COLUMN processed_at TEXT")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE donations ADD COLUMN admin_note TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE donations ADD COLUMN processed_by INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE donations ADD COLUMN processed_at TEXT")
    except Exception:
        pass

    # central admin actions audit table
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_table TEXT,
            target_id INTEGER,
            note TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
    except Exception:
        pass
    conn.commit()
    try:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('notify_new_registration','1')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('notify_new_ticket','1')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('notify_new_membership','1')")
    except Exception:
        pass
    conn.close()
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

    try:
        from log_helper import console_log
        console_log(f"✅ database '{path}' successfully created.", f"✅ دیتابیس '{path}' با موفقیت ساخته شد.")
    except Exception:
        print(f"✅ database '{path}' successfully created.")