from telethon import events
from utils import paginate_buttons, CHANNEL_USERNAME
import json
from database import DB_NAME
import sqlite3


def setup_event_handlers(client, user_states):

    @client.on(events.CallbackQuery)
    async def event_manager_callback(event):
        data = event.data.decode('utf-8')

        # Pagination for active events (user side)
        if data.startswith("event_page_"):
            page = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, title FROM events WHERE is_active = 1 ORDER BY id DESC")
            events_list = c.fetchall()
            conn.close()
            buttons = paginate_buttons(events_list, "event", page, per_page=5)
            await event.edit("📅 رویدادهای فعال:", buttons=buttons)


        elif data.startswith("archive_event_page_"):
            page = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, title FROM events WHERE is_active = 0 ORDER BY id DESC")
            events_list = c.fetchall()
            conn.close()
            buttons = paginate_buttons(events_list, "archive_event", page, per_page=5)
            await event.edit("🗃 آرشیو رویدادها:", buttons=buttons)

        elif data.startswith("forward_reports_"):
            event_id = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT report_message_ids, report_payloads FROM events WHERE id = ?", (event_id,))
            row = c.fetchone()
            conn.close()
            msg_ids = row[0] if row else None
            payloads_json = row[1] if row else None
            sent_any = False
            if payloads_json:
                try:
                    payloads = json.loads(payloads_json)
                    forward_items = [p for p in payloads if p.get("type") == "forward" and p.get("channel_id") and p.get("message_id")]
                    other_items = [p for p in payloads if p.get("type") != "forward"]
                    if forward_items:
                        try:
                            from telethon.tl.types import PeerChannel
                            channel_cache = {}
                            for p in forward_items:
                                try:
                                    cid = int(p["channel_id"])
                                    mid = int(p["message_id"])
                                except Exception:
                                    continue
                                if cid not in channel_cache:
                                    try:
                                        channel_cache[cid] = await client.get_entity(PeerChannel(cid))
                                    except Exception:
                                        channel_cache[cid] = None
                                ch = channel_cache.get(cid)
                                if ch is not None:
                                    try:
                                        await client.forward_messages(entity=event.chat_id, messages=mid, from_peer=ch)
                                        sent_any = True
                                    except Exception as e:
                                        print(f"Error forwarding grouped report {mid} from {cid}: {e}")
                        except Exception as e:
                            print(f"Error resolving channels for forwarding: {e}")
                    for p in other_items:
                        if p.get("type") == "file" and p.get("path"):
                            try:
                                await client.send_message(event.chat_id, "⚠️ این گزارش شامل فایل(های) محلی است که به‌صورت مستقیم ارسال نمی‌شوند. برای دریافت فایل‌ها با ادمین تماس بگیرید.")
                            except Exception as e:
                                print(f"Error notifying about local report file: {e}")
                        elif p.get("type") == "text" and p.get("text"):
                            try:
                                await client.send_message(event.chat_id, p["text"])
                                sent_any = True
                            except Exception as e:
                                print(f"Error sending local report text: {e}")
                except Exception as e:
                    print(f"Error parsing report payloads: {e}")
            if not sent_any and msg_ids:
                try:
                    ids = [int(x) for x in msg_ids.split(',') if x.strip().isdigit()]
                except Exception:
                    ids = []
                try:
                    channel = await client.get_entity(CHANNEL_USERNAME)
                except Exception:
                    channel = None
                if channel:
                    for mid in ids:
                        try:
                            await client.forward_messages(entity=event.chat_id, messages=mid, from_peer=channel)
                            sent_any = True
                        except Exception as e:
                            print(f"Error forwarding report {mid}: {e}")
            if not sent_any:
                await client.send_message(event.chat_id, "📭 گزارشی برای این رویداد در دسترس نیست.")
