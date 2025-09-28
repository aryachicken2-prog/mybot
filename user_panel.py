
from telethon import events, Button
from utils import (
    is_user_member, get_main_menu_buttons, CANCEL_BUTTON, BACK_BUTTON,
    paginate_buttons, ABOUT_TEXT, set_user_state, get_user_state, get_user_data, clear_user_state,
    CHANNEL_JOIN_MESSAGE, get_channel_join_buttons, get_setting, get_admin_ids, is_safe_upload_path
)
from utils import rate_limit_check, sanitize_text, notify_admins_about
from database import DB_NAME
import sqlite3
import os
import time
import random

# map user_id -> (chat_id, message_id) for last poster sent to that user
last_poster_msgs = {}

def setup_user_handlers(client, user_states):
    @client.on(events.NewMessage(pattern='/help'))
    async def help_command_handler(event):
        user_id = event.sender_id
        if not await is_user_member(client, user_id):
            return
        help_text = get_setting('user_help_text', 'راهنمای جامع ربات هنوز توسط ادمین تنظیم نشده است.')
        await event.reply(help_text, buttons=[[Button.inline("🏠 بازگشت به منو", b"main_menu")]])

    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        user_id = event.sender_id
        # rate limit welcome/start requests
        if not rate_limit_check(user_id, limit=3, window=60):
            # rate-limited: do not notify the user to avoid spam; just silently return
            return
        if not await is_user_member(client, user_id):
            await event.reply(CHANNEL_JOIN_MESSAGE, buttons=get_channel_join_buttons())
            return
        is_admin = False
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        if c.fetchone():
            is_admin = True
        conn.close()
        menu_text = "👑 به پنل ادمین خوش آمدید:" if is_admin else "👤 به پنل کاربر خوش آمدید:"
        await event.reply(menu_text, buttons=get_main_menu_buttons(is_admin))

    @client.on(events.NewMessage)
    async def fallback_message_handler(event):
        user_id = event.sender_id
        # sanitize free-text to avoid accidental HTML/XSS and collapse whitespace
        text = sanitize_text(event.message.text or "")
        state = get_user_state(user_states, user_id)
        if state:
            return
        if text.startswith('/'):
            return
        try:
            await event.reply("برای استفاده از ربات، دستور /start را ارسال کنید.")
        except:
            pass

    @client.on(events.CallbackQuery)
    async def callback_handler(event):
        data = event.data.decode('utf-8')
        user_id = event.sender_id

        async def edit_or_send(text, buttons=None, parse_mode=None):
            """Edit the callback message if it has no media, otherwise delete it and send a new message.

            This prevents a photo (poster) from remaining attached when menus are shown.
            """
            # if there is a stored poster message for this user, delete it first
            try:
                stored = last_poster_msgs.get(user_id)
                if stored:
                    try:
                        await client.delete_messages(stored[0], [stored[1]])
                    except Exception:
                        pass
                    try:
                        del last_poster_msgs[user_id]
                    except KeyError:
                        pass
            except Exception:
                pass
            try:
                msg = getattr(event, 'message', None)
                if msg and getattr(msg, 'media', None):
                    try:
                        await event.delete()
                    except Exception:
                        pass
                    await client.send_message(event.chat_id, text, buttons=buttons, parse_mode=parse_mode)
                else:
                    await event.edit(text, buttons=buttons, parse_mode=parse_mode)
            except Exception:
                # fallback to sending a new message
                try:
                    await client.send_message(event.chat_id, text, buttons=buttons, parse_mode=parse_mode)
                except Exception:
                    pass

        if data == "check_membership":
            if await is_user_member(client, user_id):
                is_admin = False
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
                if c.fetchone():
                    is_admin = True
                conn.close()
                menu_text = "👑 به پنل ادمین خوش آمدید:" if is_admin else "👤 به پنل کاربر خوش آمدید:"
                await edit_or_send(menu_text, buttons=get_main_menu_buttons(is_admin))
            else:
                await event.answer("❌ هنوز عضو کانال نشده‌اید!", alert=True)
                await event.edit(CHANNEL_JOIN_MESSAGE, buttons=get_channel_join_buttons())
            return

        if data == "cancel":
            clear_user_state(user_states, user_id)
            is_admin = False
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            if c.fetchone():
                is_admin = True
            conn.close()
            await edit_or_send("✅ عملیات لغو شد.", buttons=get_main_menu_buttons(is_admin))
            return

        if data == "main_menu":
            clear_user_state(user_states, user_id)
            is_admin = False
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            if c.fetchone():
                is_admin = True
            conn.close()
            await edit_or_send("منوی اصلی:", buttons=get_main_menu_buttons(is_admin))
            return

        if data == "user_events":
            buttons = [
                [Button.inline("📅 رویدادهای فعال", b"events_active_0")],
                [Button.inline("🗃 آرشیو رویدادها", b"events_archive_0")],
                [Button.inline("🏠 بازگشت به منو", b"main_menu")]
            ]
            await edit_or_send("لطفا دسته‌بندی مورد نظر را انتخاب کنید:", buttons=buttons)

        elif data.startswith("events_active_"):
            page = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, title FROM events WHERE is_active = 1")
            events_list = c.fetchall()
            conn.close()
            if not events_list:
                await event.edit("📭 هیچ رویداد فعالی وجود ندارد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                return
            buttons = paginate_buttons(events_list, "event", page, per_page=5)
            await edit_or_send("📅 رویدادهای فعال:", buttons=buttons)

        elif data.startswith("events_archive_"):
            page = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, title FROM events WHERE is_active = 0")
            events_list = c.fetchall()
            conn.close()
            if not events_list:
                await event.edit("📭 هیچ رویداد آرشیو شده‌ای وجود ندارد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                return
            buttons = paginate_buttons(events_list, "archive_event", page, per_page=5)
            await edit_or_send("🗃 آرشیو رویدادها:", buttons=buttons)

        elif data.startswith("event_"):
            parts = data.split("_")
            if len(parts) == 2 and parts[1].isdigit():
                event_id = int(parts[1])
                await show_event_details(client, event, event_id, is_archive=False)
                return
            else:
                try:
                    await event.answer("❌ درخواست نامعتبر!", alert=True)
                except:
                    pass

        elif data.startswith("archive_event_"):
            parts = data.split("_")
            if len(parts) >= 3 and parts[2].isdigit():
                event_id = int(parts[2])
                await show_event_details(client, event, event_id, is_archive=True)
                return
            else:
                try:
                    await event.answer("❌ درخواست نامعتبر!", alert=True)
                except:
                    pass



        elif data.startswith("start_register_"):
            event_id = int(data.split("_")[2])
            clear_user_state(user_states, user_id)
            buttons = [
                [Button.inline("✅ استفاده از اطلاعات پروفایل من", f"use_profile_{event_id}")],
                [Button.inline("✍️ وارد کردن دستی", f"start_register_manual_{event_id}")],
                [Button.inline("❌ لغو", b"cancel")]
            ]
            await event.edit("برای ثبت‌نام می‌خواهید از اطلاعات پروفایل خود استفاده کنید یا دستی وارد کنید؟", buttons=buttons)

        elif data == "user_my_regs":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""
                SELECT r.id, e.title, r.status 
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE r.user_id = ?
            """, (user_id,))
            regs = c.fetchall()
            conn.close()
            if not regs:
                await event.edit("📭 شما در هیچ رویدادی ثبت‌نام نکرده‌اید.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                return
            buttons = []
            for reg_id, title, status in regs:
                status_text = "⏳ در انتظار" if status == "pending" else "✅ تایید شده" if status == "approved" else "❌ رد شده"
                buttons.append([Button.inline(f"{title} — {status_text}", f"myreg_{reg_id}")])
            buttons.append([Button.inline("🏠 بازگشت به منو", b"main_menu")])
            await event.edit("📊 ثبت‌نام‌های من:", buttons=buttons)

        elif data.startswith("myreg_"):
            reg_id = int(data.split("_")[1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""
                SELECT e.title, r.status, r.register_date, u.reason_if_rejected
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                JOIN users u ON r.user_id = u.user_id
                WHERE r.id = ?
            """, (reg_id,))
            result = c.fetchone()
            conn.close()
            if not result:
                await event.answer("❌ ثبت‌نام یافت نشد!", alert=True)
                return
            title, status, reg_date, reason = result
            status_text = {
                "pending": "⏳ در حال بررسی",
                "approved": "✅ تایید شده",
                "rejected": f"❌ رد شده\nدلیل: {reason or '---'}"
            }.get(status, status)
            msg = f"📌 رویداد: {title}\n📆 تاریخ ثبت‌نام: {reg_date}\n📊 وضعیت: {status_text}"
            await event.edit(msg, buttons=[
                [Button.inline("🔙 بازگشت", b"user_my_regs")],
                [Button.inline("🏠 منوی اصلی", b"main_menu")]
            ])

        elif data == "user_faq":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, question FROM faqs")
            faqs = c.fetchall()
            conn.close()
            if not faqs:
                buttons = [
                    [Button.inline("📬 ارسال سوال جدید", b"ask_ticket")],
                    [Button.inline("🏠 منوی اصلی", b"main_menu")]
                ]
                await event.edit("📭 هیچ سوال متداولی وجود ندارد.", buttons=buttons)
                return
            buttons = paginate_buttons(faqs, "faq", 0, per_page=5)
            buttons.append([Button.inline("📬 ارسال سوال جدید", b"ask_ticket")])
            await event.edit("❓ سوالات متداول:", buttons=buttons)

        elif data == "user_profile":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT full_name, phone, national_id, is_student, student_id, language FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            conn.close()
            full_name = row[0] if row else "—"
            phone = row[1] if row else "—"
            national_id = row[2] if row and len(row) > 2 else "—"
            is_student = bool(row[3]) if row and len(row) > 3 else False
            student_id = row[4] if row and len(row) > 4 else "—"
            lang = row[5] if row and len(row) > 5 else "fa"
            student_txt = f"بله — شماره دانشجویی: {student_id}" if is_student else "خیر"
            msg = (
                f"👤 پروفایل شما\n\n"
                f"نام: {full_name}\n"
                f"تلفن: {phone}\n"
                f"کد ملی: {national_id}\n"
                f"دانشجو: {student_txt}\n"
                f"آیدی عددی: `{user_id}`"
            )
            buttons = [
                [Button.inline("✏️ ویرایش اطلاعات من", b"edit_profile_all")],
                [Button.inline("🏠 منوی اصلی", b"main_menu")]
            ]
            await event.edit(msg, buttons=buttons, parse_mode="markdown")

        elif data == "edit_profile_name":
            await event.edit("✏️ لطفاً نام کامل خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "waiting_edit_name")

        elif data == "edit_profile_phone":
            await event.edit("📞 لطفاً شماره تماس خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "waiting_edit_phone")

        elif data == "edit_profile_all":
            await event.edit("✏️ ویرایش پروفایل — لطفاً نام کامل خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "edit_profile_name")

        elif data in ("profile_student_yes", "profile_student_no"):
            state = get_user_state(user_states, user_id)
            if state != "edit_profile_student_choice":
                await event.answer("❌ عملیات نامعتبر", alert=True)
                return
            if data == "profile_student_yes":
                set_user_state(user_states, user_id, "edit_profile_student_id")
                await event.edit("🎓 لطفاً شماره دانشجویی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            else:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO users (user_id, is_student) VALUES (?, 0)", (user_id,))
                c.execute("UPDATE users SET is_student = ? WHERE user_id = ?", (0, user_id))
                conn.commit()
                conn.close()
                clear_user_state(user_states, user_id)
                await event.edit("✅ پروفایل شما با موفقیت به‌روزرسانی شد.", buttons=get_main_menu_buttons(False))


        elif data.startswith("faq_"):
            faq_id = int(data.split("_")[1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT question, answer FROM faqs WHERE id = ?", (faq_id,))
            faq = c.fetchone()
            conn.close()
            if not faq:
                await event.answer("❌ سوال یافت نشد!", alert=True)
                return
            question, answer = faq
            msg = f"❓ سوال:\n{question}\n\n📝 پاسخ:\n{answer}"
            await event.edit(msg, buttons=[
                [Button.inline("🔙 بازگشت به سوالات", b"user_faq")],
                [Button.inline("🏠 منوی اصلی", b"main_menu")]
            ])

        elif data == "ask_ticket":
            await event.edit("لطفا سوال یا پیام خود را ارسال کنید (می‌توانید عکس/فایل هم بفرستید):", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "waiting_for_ticket_message")

        elif data == "user_send_idea":
            await event.edit("📨 ارسال ایده — لطفا عنوان ایده را بنویسید:", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "idea_step_title")

        elif data == "user_request_collab":
            await event.edit("🤝 درخواست همکاری — لطفا نام و سازمانتان را وارد کنید (فرمت: نام | سازمان):", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "collab_step_org")

        elif data == "user_donate":
            # Show donation description from settings, ask to continue
            try:
                desc = get_setting('donation_description', '')
            except Exception:
                desc = ''
            text = "💳 حمایت مالی از انجمن\n\n" + (desc or 'متن توضیحات حمایتی هنوز توسط ادمین تنظیم نشده است.')
            buttons = [
                [Button.inline("✅ ادامه و حمایت", b"donate_confirm")],
                [Button.inline("❌ انصراف", b"main_menu")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "donate_confirm":
            # ask for amount
            await event.edit("💳 لطفا مبلغ حمایت را به تومان وارد کنید (مثلا: 50000). اگر می‌خواهید مقدار را اعلام نکنید، 0 وارد کنید.", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "donate_step_amount")
            return

        elif data == "donate_paid":
            # user clicked 'paid' button — prompt to upload receipt
            state_data = get_user_data(user_states, user_id) or {}
            # if amount not present (edge case), ask amount
            if not state_data.get('amount'):
                await event.edit("لطفا ابتدا مبلغ را وارد کنید:", buttons=CANCEL_BUTTON)
                set_user_state(user_states, user_id, "donate_step_amount")
                return
            set_user_state(user_states, user_id, "donate_waiting_receipt", state_data)
            await event.edit("📎 لطفا تصویر یا فایل رسید پرداخت را ارسال کنید:", buttons=CANCEL_BUTTON)
            return

        elif data == "user_tickets":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, message, status, created_at FROM tickets WHERE user_id = ? ORDER BY id DESC", (user_id,))
            rows = c.fetchall()
            conn.close()
            if not rows:
                await event.edit("📭 تیکتی برای پیگیری وجود ندارد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                return
            buttons = []
            for tid, msg, status, created in rows[:20]:
                status_txt = "✅ بسته" if status == "closed" else "⏳ باز"
                preview = msg[:28] + "..." if len(msg) > 28 else msg
                buttons.append([Button.inline(f"#{tid} — {status_txt} — {preview}", f"view_ticket_{tid}")])
            buttons.append([Button.inline("🏠 بازگشت", b"main_menu")])
            await event.edit("📨 پیگیری تیکت‌ها:", buttons=buttons)

        elif data.startswith("view_ticket_"):
            tid = int(data.split("_")[2])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT message, admin_reply, status, created_at, replied_at FROM tickets WHERE id = ? AND user_id = ?", (tid, user_id))
            row = c.fetchone()
            conn.close()
            if not row:
                await event.answer("❌ تیکت یافت نشد!", alert=True)
                return
            message, admin_reply, status, created_at, replied_at = row
            status_txt = "✅ بسته" if status == "closed" else "⏳ باز"
            details = f"📨 تیکت #{tid}\n📆 تاریخ: {created_at}\n📊 وضعیت: {status_txt}\n\nمتن شما:\n{message}"
            if admin_reply:
                details += f"\n\nپاسخ ادمین:\n{admin_reply}\n🕒 زمان پاسخ: {replied_at or '-'}"
            await event.edit(details, buttons=[[Button.inline("🔙 بازگشت", b"user_tickets")],[Button.inline("🏠 منوی اصلی", b"main_menu")]])

        

        elif data == "user_my_certs":
            buttons = [
                [Button.inline("📬 پیگیری گواهی", b"track_cert"), Button.inline("📥 دریافت گواهی‌های من", b"receive_certs")],
                [Button.inline("🧾 پیگیری تیکت‌ها", b"user_tickets"), Button.inline("🏠 بازگشت به منو", b"main_menu")]
            ]
            await event.edit("📜 بخش گواهی‌ها:", buttons=buttons)

        elif data == "track_cert":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO tickets (user_id, message, status) VALUES (?, ?, ?)",
                      (user_id, "درخواست پیگیری گواهی", "open"))
            conn.commit()
            conn.close()
            await event.edit("✅ درخواست پیگیری گواهی ثبت شد. ادمین‌ها به زودی پاسخ می‌دهند.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])

        elif data == "receive_certs":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""
                SELECT c.id, e.title 
                FROM certificates c
                JOIN events e ON c.event_id = e.id
                WHERE c.user_id = ?
            """, (user_id,))
            certs = c.fetchall()
            conn.close()
            if not certs:
                await event.edit("📭 شما هنوز هیچ گواهی‌ای دریافت نکرده‌اید.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                return
            buttons = []
            for cert_id, title in certs:
                buttons.append([Button.inline(f"📄 {title}", f"send_cert_{cert_id}")])
            buttons.append([Button.inline("🏠 بازگشت به منو", b"main_menu")])
            await event.edit("📥 گواهی‌های شما:", buttons=buttons)

        elif data.startswith("send_cert_"):
            cert_id = int(data.split("_")[2])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT file_id FROM certificates WHERE id = ? AND user_id = ?", (cert_id, user_id))
            result = c.fetchone()
            conn.close()
            if not result:
                await event.answer("❌ گواهی یافت نشد!", alert=True)
                return
            file_id = result[0]
            try:
                await client.send_file(event.chat_id, file_id, caption="📜 گواهی شما:")
                await event.answer("✅ گواهی ارسال شد.", alert=True)
            except Exception as e:
                await event.answer("❌ خطایی در ارسال گواهی رخ داد!", alert=True)
                try:
                    from log_helper import console_log
                    console_log(f"Error sending certificate: {e}", f"خطا در ارسال گواهی: {e}")
                except Exception:
                    print(f"Error sending certificate: {e}")

        elif data == "user_help":
            help_text = get_setting('user_help_text', 'راهنمای جامع ربات هنوز توسط ادمین تنظیم نشده است.')
            await event.edit(help_text, buttons=[[Button.inline("🏠 بازگشت به منو", b"main_menu")]])
            return
        elif data == "user_about":
            await event.edit(ABOUT_TEXT, buttons=[[Button.inline("🏠 بازگشت به منو", b"main_menu")]], parse_mode="markdown")

        elif data == "user_membership":
            text = (
                "👥 عضویت در انجمن\n\n"
                "با عضویت در انجمن، از مزایا و اطلاع‌رسانی‌های ویژه بهره‌مند می‌شوید.\n\n"
                "آیا مایل به شروع فرآیند ثبت‌نام عضویت هستید؟"
            )
            buttons = [
                [Button.inline("✅ تایید و ادامه", b"membership_confirm")],
                [Button.inline("❌ لغو و بازگشت", b"main_menu")]
            ]
            await event.edit(text, buttons=buttons)


    @client.on(events.NewMessage)
    async def message_handler(event):
        user_id = event.sender_id
        state = get_user_state(user_states, user_id)
        if not await is_user_member(client, user_id):
            return
        if state == "waiting_for_ticket_message":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            msg_text = event.message.text or "پیام رسانه‌ای (عکس/فایل)"
            c.execute("INSERT INTO tickets (user_id, message, status) VALUES (?, ?, ?)",
                      (user_id, msg_text, "open"))
            ticket_id = c.lastrowid
            conn.commit()
            conn.close()
            if event.message.file:
                file_id = event.message.file.id
            clear_user_state(user_states, user_id)
            await event.reply("✅ تیکت شما ثبت شد. ادمین‌ها به زودی پاسخ می‌دهند.", buttons=get_main_menu_buttons(False))
            try:
                if get_setting("notify_new_ticket","1") == "1":
                    admins = get_admin_ids()
                    note = f"🔔 تیکت جدید\nکاربر: {user_id}\nشناسه تیکت: #{ticket_id}"
                    for aid in admins:
                        try:
                            await client.send_message(aid, note)
                        except Exception:
                            pass
            except Exception:
                pass


        # --- idea submission flow ---
        if state == "idea_step_title":
            title = sanitize_text(event.message.text or "")
            if not title:
                await event.reply("❌ عنوان معتبر نیست. لطفا دوباره وارد کنید:", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "idea_step_description", {"title": title})
            await event.reply("📝 حالا توضیحات ایده را بنویسید (می‌توانید فایل یا عکس هم ارسال کنید):", buttons=CANCEL_BUTTON)
            return

        if state == "idea_step_description":
            desc = sanitize_text(event.message.text or "")
            data = get_user_data(user_states, user_id)
            data["description"] = desc
            file_path = None
            if event.message.file:
                ext = getattr(event.message.file, 'ext', '') or 'dat'
                unique_name = f"idea_{user_id}_{int(time.time())}.{ext}"
                save_path = os.path.join('uploads', unique_name)
                try:
                    await event.message.download_media(file=save_path)
                    file_path = save_path
                except Exception:
                    file_path = None
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO ideas (user_id, title, description, file_path) VALUES (?, ?, ?, ?)", (user_id, data.get('title'), data.get('description'), file_path))
                idea_id = c.lastrowid
                conn.commit()
                conn.close()
            except Exception:
                idea_id = None
            clear_user_state(user_states, user_id)
            await event.reply("✅ ایده شما ثبت شد. متشکریم!", buttons=get_main_menu_buttons(False))
            try:
                notify_admins_about(client, DB_NAME, f"📨 ایده جدید از {user_id} — #{idea_id} — {data.get('title')}")
            except Exception:
                pass
            return

        # --- collaboration request flow ---
        if state == "collab_step_org":
            raw = sanitize_text(event.message.text or "")
            parts = raw.split("|", 1)
            if len(parts) == 2:
                full_name = parts[0].strip()
                organization = parts[1].strip()
            else:
                full_name = raw
                organization = ''
            set_user_state(user_states, user_id, "collab_step_proposal", {"full_name": full_name, "organization": organization})
            await event.reply("📄 لطفا پیشنهاد همکاری یا شرح مختصر همکاری را ارسال کنید (می‌توانید فایل پیوست کنید):", buttons=CANCEL_BUTTON)
            return

        if state == "collab_step_proposal":
            proposal = sanitize_text(event.message.text or "")
            data = get_user_data(user_states, user_id)
            file_path = None
            if event.message.file:
                ext = getattr(event.message.file, 'ext', '') or 'dat'
                unique_name = f"collab_{user_id}_{int(time.time())}.{ext}"
                save_path = os.path.join('uploads', unique_name)
                try:
                    await event.message.download_media(file=save_path)
                    file_path = save_path
                except Exception:
                    file_path = None
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO collaborations (user_id, full_name, organization, proposal, file_path) VALUES (?, ?, ?, ?, ?)", (user_id, data.get('full_name'), data.get('organization'), proposal, file_path))
                collab_id = c.lastrowid
                conn.commit()
                conn.close()
            except Exception:
                collab_id = None
            clear_user_state(user_states, user_id)
            await event.reply("✅ درخواست همکاری ثبت شد. مدیران در اسرع وقت بررسی می‌کنند.", buttons=get_main_menu_buttons(False))
            try:
                notify_admins_about(client, DB_NAME, f"🤝 درخواست همکاری جدید از {user_id} — #{collab_id} — {data.get('full_name')} / {data.get('organization')}")
            except Exception:
                pass
            return

        # --- donation flow ---
        if state == "donate_step_amount":
            # user entered amount in toman
            raw = (event.message.text or '').replace(',', '').strip()
            try:
                amount = int(raw)
                if amount < 0:
                    raise ValueError()
            except Exception:
                await event.reply("❌ لطفا یک عدد مبلغ معتبر وارد کنید (مثلا: 50000):", buttons=CANCEL_BUTTON)
                return
            # show payment card info from settings
            try:
                card = get_setting('donation_card_number', '—')
            except Exception:
                card = '—'
            try:
                holder = get_setting('donation_card_holder', '')
            except Exception:
                holder = ''
            # include card holder name if available
            holder_line = f"\nبنام: {holder}\n" if holder else "\n"
            msg = (
                f"💳 لطفا کارت زیر را برای پرداخت استفاده کنید:\n\n"
                f"کارت: {card}{holder_line}\n"
                f"مبلغ اعلام‌شده: {amount:,} تومان\n\n"
                f"پس از پرداخت، روی '✅ پرداخت کردم' بزنید و سپس رسید پرداخت را ارسال کنید."
            )
            # ensure buttons is a list-of-rows; CANCEL_BUTTON is already a row (list), don't use CANCEL_BUTTON[0]
            buttons = [[Button.inline("✅ پرداخت کردم", b"donate_paid")], CANCEL_BUTTON]
            set_user_state(user_states, user_id, "donate_awaiting_paid", {"amount": amount})
            await event.reply(msg, buttons=buttons)
            return

        if state in ("donate_waiting_receipt", "donate_awaiting_paid"):
            # Expecting a file (photo/pdf) as receipt
            data = get_user_data(user_states, user_id) or {}
            amount = data.get('amount')
            if not event.message.file and not event.message.photo:
                await event.reply("❌ لطفا تصویر یا فایل رسید پرداخت را ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            # save file
            try:
                f = event.message.file or event.message.photo
                ext = getattr(f, 'ext', '') or 'jpg'
                unique_name = f"donation_{user_id}_{int(time.time())}_{random.randint(1000,9999)}.{ext}"
                save_path = os.path.join('uploads', unique_name)
                await event.message.download_media(file=save_path)
            except Exception:
                await event.reply("❌ خطا در ذخیره فایل رسید. مجددا تلاش کنید:", buttons=CANCEL_BUTTON)
                return
            # insert into donations table
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO donations (user_id, amount, currency, receipt_file, status) VALUES (?, ?, ?, ?, ?)",
                          (user_id, amount or None, 'IRR', save_path, 'pending'))
                did = c.lastrowid
                conn.commit()
                conn.close()
            except Exception:
                await event.reply("⚠️ خطا در ثبت اطلاعات پرداخت. لطفا با ادمین تماس بگیرید.", buttons=get_main_menu_buttons(False))
                clear_user_state(user_states, user_id)
                return
            # notify admins immediately (best-effort)
            try:
                note = f"🔔 حمایت مالی جدید — #{did} — کاربر: {user_id} — مبلغ: {amount}"
                # first try direct send (await) to all admins so owner/admin sees it instantly
                admins = get_admin_ids()
                for aid in admins:
                    try:
                        await client.send_message(aid, note)
                    except Exception:
                        pass
                # also call notify_admins_about to preserve existing async behaviour
                try:
                    notify_admins_about(client, DB_NAME, note)
                except Exception:
                    pass
            except Exception:
                pass
            clear_user_state(user_states, user_id)
            await event.reply("✅ رسید دریافت شد و برای بررسی به ادمین ارسال شد. متشکريم!", buttons=get_main_menu_buttons(False))
            return

        # duplicate/old donation flow removed — keep the primary donate_step_amount -> donate_awaiting_paid -> donate_waiting_receipt flow


        elif state == "waiting_edit_name":
            name = event.message.text.strip()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, name))
            c.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (name, user_id))
            conn.commit()
            conn.close()
            clear_user_state(user_states, user_id)
            await event.reply("✅ نام به‌روزرسانی شد.", buttons=get_main_menu_buttons(False))

        elif state == "edit_profile_name":
            name = event.message.text.strip()
            if len(name) < 3:
                await event.reply("❌ نام باید حداقل 3 کاراکتر باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, name))
            c.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (name, user_id))
            conn.commit()
            conn.close()
            set_user_state(user_states, user_id, "edit_profile_national")
            await event.reply("🆔 لطفا کد ملی خود را ارسال کنید (10 رقمی):", buttons=CANCEL_BUTTON)

        elif state == "edit_profile_national":
            national_id = event.message.text.strip()
            if not national_id.isdigit() or len(national_id) != 10:
                await event.reply("❌ کد ملی باید 10 رقمی و عددی باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, national_id) VALUES (?, ?)", (user_id, national_id))
            c.execute("UPDATE users SET national_id = ? WHERE user_id = ?", (national_id, user_id))
            conn.commit()
            conn.close()
            set_user_state(user_states, user_id, "edit_profile_phone")
            await event.reply("📞 لطفاً شماره تماس خود را ارسال کنید:", buttons=CANCEL_BUTTON)

        elif state == "edit_profile_phone":
            phone = event.message.text.strip()
            clean = phone.replace("+98", "").replace(" ", "").replace("-", "")
            if clean.startswith("0"):
                clean = clean[1:]
            if not clean.isdigit() or len(clean) != 10:
                await event.reply("❌ شماره معتبر نیست. مثال: 09123456789", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, phone) VALUES (?, ?)", (user_id, clean))
            c.execute("UPDATE users SET phone = ? WHERE user_id = ?", (clean, user_id))
            conn.commit()
            conn.close()
            set_user_state(user_states, user_id, "edit_profile_student_choice")
            buttons = [[Button.inline("🎓 من دانشجو هستم", b"profile_student_yes")], [Button.inline("🧑‍💼 دانشجو نیستم", b"profile_student_no")], [Button.inline("❌ لغو", b"cancel")]]
            await event.reply("❓ آیا شما دانشجو هستید؟", buttons=buttons)

        elif state == "edit_profile_student_id":
            student_id = event.message.text.strip()
            if not student_id.isdigit():
                await event.reply("❌ شماره دانشجویی باید عددی باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, student_id, is_student) VALUES (?, ?, ?)", (user_id, student_id, 1))
            c.execute("UPDATE users SET student_id = ?, is_student = ? WHERE user_id = ?", (student_id, 1, user_id))
            conn.commit()
            conn.close()
            clear_user_state(user_states, user_id)
            await event.reply("✅ پروفایل شما با موفقیت به‌روزرسانی شد.", buttons=get_main_menu_buttons(False))

        elif state == "waiting_edit_phone":
            phone = event.message.text.strip()
            clean = phone.replace("+98", "").replace(" ", "").replace("-", "")
            if clean.startswith("0"):
                clean = clean[1:]
            if not clean.isdigit() or len(clean) != 10:
                await event.reply("❌ شماره معتبر نیست. مثال: 09123456789", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, phone) VALUES (?, ?)", (user_id, clean))
            c.execute("UPDATE users SET phone = ? WHERE user_id = ?", (clean, user_id))
            conn.commit()
            conn.close()
            clear_user_state(user_states, user_id)
            await event.reply("✅ شماره تماس به‌روزرسانی شد.", buttons=get_main_menu_buttons(False))

        elif state == "waiting_edit_lang":
            lang = (event.message.text or "fa").strip().lower()
            if lang not in ("fa", "en"):
                await event.reply("❌ فقط fa یا en مجاز است.", buttons=CANCEL_BUTTON)
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)", (user_id, lang))
            c.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
            conn.commit()
            conn.close()
            clear_user_state(user_states, user_id)
            await event.reply("✅ زبان به‌روزرسانی شد.", buttons=get_main_menu_buttons(False))

    async def show_event_details(client, event, event_id, is_archive=False):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT title, description, cost_type, fixed_cost, student_cost, non_student_cost, card_number,
                   poster_file_id, is_active, cert_fee, cert_fee_student, cert_fee_non_student, cert_card_number, cert_card_holder
            FROM events WHERE id = ?
        """, (event_id,))
        result = c.fetchone()
        conn.close()
        if not result:
            await event.answer("❌ رویداد یافت نشد!", alert=True)
            return
        (title, desc, cost_type, fixed, student_cost, non_student_cost, card,
         poster_file_id, is_active, cert_fee, cert_fee_student, cert_fee_non_student, cert_card_number, cert_card_holder) = result
        # Only show title and description in the event preview for users.
        msg = f"� *{title}*\n{desc or '---'}"
        buttons = []
        if is_archive:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT report_message_ids, report_payloads FROM events WHERE id = ?", (event_id,))
            row = c.fetchone()
            conn.close()
            report_ids = row[0] if row else None
            report_payloads = row[1] if row else None
            if report_ids or report_payloads:
                buttons.append([Button.inline("📑 دریافت گزارش کار", f"forward_reports_{event_id}")])
            buttons.append([Button.inline("🔙 بازگشت به آرشیو", b"events_archive_0")])
        else:
            buttons.append([Button.inline("📝 شروع ثبت‌نام", f"start_register_{event_id}")])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ? AND status = 'approved'", (event.sender_id, event_id))
            is_approved = c.fetchone() is not None
            conn.close()
            if is_approved:
                buttons.append([Button.inline("📚 منابع رویداد", f"event_resources_{event_id}")])
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT reminders_enabled FROM events WHERE id = ?", (event_id,))
                rem = c.fetchone()
                reminders_enabled = bool(rem[0]) if rem and rem[0] else False
                c.execute("SELECT reminder_opt_in FROM registrations WHERE user_id = ? AND event_id = ?", (event.sender_id, event_id))
                rrow = c.fetchone()
                conn.close()
                if reminders_enabled and rrow is not None:
                    user_opt = 1 if (rrow[0] is None) else int(rrow[0])
                    label = "🔔 یادآوری: روشن" if user_opt == 1 else "🔕 یادآوری: خاموش"
                    buttons.insert(1, [Button.inline(label, f"toggle_reminder_{event_id}")])
                elif reminders_enabled and rrow is None:
                    buttons.insert(1, [Button.inline("🔔 یادآوری (برای ثبت‌نام‌کنندگان)", f"notify_after_register_{event_id}")])
            except Exception:
                pass
            buttons.append([Button.inline("🔙 بازگشت به رویدادها", b"events_active_0")])
        buttons.append([Button.inline("🏠 منوی اصلی", b"main_menu")])
        try:
            # همیشه پیام جدید ارسال شود و هیچ وقت پیام قبلی ویرایش یا حذف نشود
            back_buttons = {b[0].text for b in buttons if b and hasattr(b[0], 'text')}
            if poster_file_id and is_safe_upload_path(poster_file_id) and not (back_buttons == {"🔙 بازگشت به رویدادها"} or back_buttons == {"🏠 منوی اصلی"} or back_buttons == {"🔙 بازگشت به آرشیو"}):
                sent = await client.send_file(
                    event.chat_id,
                    file=poster_file_id,
                    caption=msg,
                    buttons=buttons,
                    parse_mode="markdown"
                )
                # remember this poster message so it can be deleted when user navigates away
                try:
                    last_poster_msgs[event.sender_id] = (sent.chat_id, sent.id)
                except Exception:
                    try:
                        # fallback: some client implementations return raw id
                        last_poster_msgs[event.sender_id] = (event.chat_id, sent)
                    except Exception:
                        pass
            else:
                await client.send_message(
                    event.chat_id,
                    msg,
                    buttons=buttons,
                    parse_mode="markdown"
                )
        except Exception as e:
            try:
                from log_helper import console_log
                console_log(f"Error showing event details: {e}", f"خطا در نمایش جزئیات رویداد: {e}")
            except Exception:
                print(f"Error showing event details: {e}")
            await client.send_message(
                event.chat_id,
                msg,
                buttons=buttons,
                parse_mode="markdown"

            )