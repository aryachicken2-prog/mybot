
from telethon import events, Button
from utils import set_user_state, get_user_state, get_user_data, clear_user_state, rate_limit_check, sanitize_text
from database import DB_NAME
import sqlite3

def setup_broadcast_handlers(client, user_states):

    @client.on(events.NewMessage)
    async def broadcast_message_handler(event):
        user_id = event.sender_id
        state = get_user_state(user_states, user_id)

        if state == "admin_waiting_broadcast_content":
            # basic admin rate limit for starting broadcast
            if not rate_limit_check(user_id, limit=2, window=300):
                try:
                    await event.reply("❌ امکان ارسال پیام همگانی در این لحظه وجود ندارد. لطفاً بعداً تلاش کنید.")
                except:
                    pass
                return
            data = get_user_data(user_states, user_id)
            target = data["target"]

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            if target == "all":
                c.execute("SELECT user_id FROM users")
            elif target == "approved":
                c.execute("SELECT user_id FROM users WHERE status = 'approved'")
            elif target == "rejected":
                c.execute("SELECT user_id FROM users WHERE status = 'rejected'")
            recipients = [row[0] for row in c.fetchall()]
            conn.close()

            if not recipients:
                await event.reply("📭 هیچ کاربری در این گروه وجود ندارد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                clear_user_state(user_states, user_id)
                return

            should_pin = False
            text = sanitize_text(event.message.text or "")
            if text.endswith("#پین"):
                should_pin = True
                text = text[:-4].strip()

            total = len(recipients)
            sent_count = 0
            failed_count = 0

            status_msg = await event.reply(f"📤 در حال ارسال به {total} کاربر...")

            for i, uid in enumerate(recipients, 1):
                try:
                    if event.message.file:
                        sent_msg = await client.send_file(uid, event.message.file, caption=text or None)
                    else:
                        sent_msg = await client.send_message(uid, text)

                    if should_pin:
                        await client.pin_message(uid, sent_msg, notify=False)

                    sent_count += 1

                    if i % 10 == 0 or i == total:
                        await status_msg.edit(f"📤 ارسال به {total} کاربر...\n✅ ارسال شده: {sent_count}\n❌ خطا: {failed_count}")

                except Exception as e:
                    failed_count += 1
                    print(f"Failed to send to {uid}: {str(e)}")
                    continue

            clear_user_state(user_states, user_id)
            summary = f"✅ ارسال همگانی به پایان رسید.\n\n" \
                      f"📬 کل کاربران: {total}\n" \
                      f"✅ دریافت کردند: {sent_count}\n" \
                      f"❌ ارسال نشد: {failed_count}"

            await status_msg.edit(summary, buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])