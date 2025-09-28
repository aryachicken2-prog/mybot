import sqlite3
import os

DB_PATH = os.getenv('JURISLAW_DB', 'jurislaw_bot.db')

def console_log(en_text: str, fa_text: str = None, setting_key: str = 'console_logs_english'):
    """Print either English or Farsi message depending on DB setting.
    If the setting is missing or DB not accessible, default to English.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (setting_key,))
        row = c.fetchone()
        conn.close()
        if row is None:
            enabled = True
        else:
            enabled = (str(row[0]) == '1')
    except Exception:
        # if anything fails, default to English to avoid silent logs
        enabled = True

    try:
        if enabled:
            print(en_text)
        else:
            print(fa_text if fa_text is not None else en_text)
    except Exception:
        # swallow printing errors
        pass
