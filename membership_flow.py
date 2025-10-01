from telethon import events, Button
from utils import (
    CANCEL_BUTTON,
    set_user_state, get_user_state, get_user_data, clear_user_state,
    is_user_member, get_setting, get_admin_ids,
    rate_limit_check, sanitize_text
)
from database import DB_NAME
import sqlite3
import os
import time
import random

def setup_membership_handlers(client, user_states):

    @client.on(events.CallbackQuery)
    async def membership_callback_handler(event):
        data = event.data.decode('utf-8')
        user_id = event.sender_id

        if data == "membership_confirm":
            # rate limit callback attempts
            if not rate_limit_check(user_id, limit=6, window=60):
                try:
                    await event.answer("❌ تلاش بیش از حد؛ لطفاً بعداً امتحان کنید.", alert=True)
                except:
                    pass
                return

            if not await is_user_member(client, user_id):
                try:
                    await event.answer("❌ ابتدا باید عضو کانال شوید!", alert=True)
                except:
                    pass
                return
            clear_user_state(user_states, user_id)
            # نمایش متن توضیحات عضویت قبل از شروع
            membership_desc = get_setting('membership_description', 'برای عضویت، لطفاً اطلاعات خود را کامل وارد کنید. پس از بررسی، نتیجه به شما اطلاع داده خواهد شد.')
            try:
                await event.edit(f"ℹ️ {membership_desc}\n\n👤 لطفاً نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            except:
                await event.reply(f"ℹ️ {membership_desc}\n\n👤 لطفاً نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            set_user_state(user_states, user_id, "membership_step_fullname", {})

    @client.on(events.NewMessage)
    async def membership_message_handler(event):
        user_id = event.sender_id
        # per-user rate limit for messages
        if not rate_limit_check(user_id, limit=8, window=60):
            try:
                await event.reply("❌ سرعت ارسال پیام‌ها زیاد است؛ لطفاً لحظاتی صبر کنید.")
            except:
                pass
            return

        state = get_user_state(user_states, user_id)
        if not state:
            return
        if not await is_user_member(client, user_id):
            return

        # step: full name
        if state == "membership_step_fullname":
            full_name = sanitize_text(event.message.text or "")
            if len(full_name) < 3:
                await event.reply("❌ نام باید حداقل 3 کاراکتر باشد. لطفاً دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_major", {"full_name": full_name})
            await event.reply("🎓 لطفاً رشته تحصیلی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            return

        # step: major
        if state == "membership_step_major":
            major = sanitize_text(event.message.text or "")
            if len(major) < 2:
                await event.reply("❌ رشته تحصیلی معتبر نیست. دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_entry_year", {"major": major})
            await event.reply("📆 لطفاً سال ورود خود را ارسال کنید (مثال: 1401):", buttons=CANCEL_BUTTON)
            return

        # step: entry year
        if state == "membership_step_entry_year":
            entry_year = sanitize_text(event.message.text or "")
            normalized = ''.join(ch for ch in entry_year if ch.isdigit())
            if len(normalized) != 4:
                await event.reply("❌ سال ورود باید 4 رقمی باشد. مثال: 1401", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_student_number", {"entry_year": normalized})
            await event.reply("🧾 لطفاً شماره دانشجویی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            return

        # step: student number
        if state == "membership_step_student_number":
            student_number = sanitize_text(event.message.text or "")
            digits = ''.join(ch for ch in student_number if ch.isdigit())
            if len(digits) < 5:
                await event.reply("❌ شماره دانشجویی معتبر نیست. دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_national_id", {"student_number": digits})
            await event.reply("🆔 لطفاً کد ملی خود را ارسال کنید (10 رقمی):", buttons=CANCEL_BUTTON)
            return

        # step: national id
        if state == "membership_step_national_id":
            national_id = sanitize_text(event.message.text or "")
            digits = ''.join(ch for ch in national_id if ch.isdigit())
            if len(digits) != 10:
                await event.reply("❌ کد ملی باید 10 رقمی باشد. دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_phone", {"national_id": digits})
            await event.reply("📞 لطفاً شماره تماس خود را ارسال کنید (مثال: 09123456789):", buttons=CANCEL_BUTTON)
            return

        # step: phone
        if state == "membership_step_phone":
            raw = sanitize_text(event.message.text or "")
            clean = raw.replace("+98", "").replace(" ", "").replace("-", "")
            if clean.startswith("0"):
                clean = clean[1:]
            if not clean.isdigit() or len(clean) != 10:
                await event.reply("❌ شماره معتبر نیست. مثال: 09123456789", buttons=CANCEL_BUTTON)
                return
            set_user_state(user_states, user_id, "membership_step_username", {"phone": clean})
            await event.reply("💬 لطفاً آیدی تلگرام خود را ارسال کنید (مثال: @username) — اگر ندارید، یک '-' بفرستید:", buttons=CANCEL_BUTTON)
            return

        # step: telegram username
        if state == "membership_step_username":
            username = (event.message.text or "").strip()
            if username == "-":
                username = None
            else:
                if username.startswith("@"):
                    username = username
                elif username:
                    username = "@" + username
            set_user_state(user_states, user_id, "membership_step_card_photo", {"telegram_username": username})
            await event.reply("🖼️ لطفاً عکس/فایل کارت دانشجویی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            return

        # step: student card photo
        if state == "membership_step_card_photo":
            if not event.message.photo and not event.message.document:
                await event.reply("❌ لطفاً یک عکس یا فایل کارت دانشجویی ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            if event.message.file:
                size = getattr(event.message.file, 'size', 0) or 0
                if size > 10 * 1024 * 1024:
                    await event.reply("❌ حجم فایل نباید بیش از 10MB باشد.", buttons=CANCEL_BUTTON)
                    return
            file_ext = "jpg" if event.message.photo else (event.message.file.ext or "dat").lower()
            if file_ext.startswith('.'):
                file_ext = file_ext[1:]
            allowed = {"jpg", "jpeg", "png", "pdf"}
            if file_ext not in allowed:
                await event.reply("❌ فقط فرمت‌های jpg, jpeg, png, pdf مجاز است.", buttons=CANCEL_BUTTON)
                return
            unique_name = f"studentcard_{user_id}_{int(time.time())}_{random.randint(1000,9999)}.{file_ext}"
            save_path = os.path.join("uploads", unique_name)
            await event.message.download_media(file=save_path)

            data = get_user_data(user_states, user_id)
            data["student_card_file"] = save_path

            # persist to DB
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO memberships (
                    user_id, full_name, major, entry_year, student_number,
                    national_id, phone, telegram_username, student_card_file, status
                ) VALUES (?,?,?,?,?,?,?,?,?, 'pending')
                """,
                (
                    user_id,
                    data.get("full_name"),
                    data.get("major"),
                    data.get("entry_year"),
                    data.get("student_number"),
                    data.get("national_id"),
                    data.get("phone"),
                    data.get("telegram_username"),
                    data.get("student_card_file"),
                )
            )
            req_id = c.lastrowid
            # reflect basic info in users table for consistency
            try:
                c.execute("""
                    INSERT OR IGNORE INTO users (user_id, full_name, national_id, student_id, phone, is_student, status)
                    VALUES (?,?,?,?,?,1,'pending')
                """, (user_id, data.get("full_name"), data.get("national_id"), data.get("student_number"), data.get("phone")))
                c.execute("""
                    UPDATE users SET full_name=?, national_id=?, student_id=?, phone=?, is_student=1 WHERE user_id=?
                """, (data.get("full_name"), data.get("national_id"), data.get("student_number"), data.get("phone"), user_id))
            except Exception:
                pass
            conn.commit()
            conn.close()

            clear_user_state(user_states, user_id)

            # notify admins
            try:
                if get_setting("notify_new_membership", "1") == "1":
                    admins = get_admin_ids()
                    note = (
                        f"🔔 درخواست عضویت جدید\n"
                        f"کاربر: {data.get('full_name','')} ({user_id})\n"
                        f"شناسه درخواست: #{req_id}"
                    )
                    for aid in admins:
                        try:
                            await client.send_message(aid, note)
                        except Exception:
                            pass
            except Exception:
                pass

            await event.reply(
                "✅ درخواست عضویت شما با موفقیت ثبت شد و در حال بررسی است.",
                buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]]
            )
