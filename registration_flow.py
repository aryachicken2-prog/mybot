
from telethon import events, Button
from utils import (
    CANCEL_BUTTON, BACK_BUTTON,
    set_user_state, get_user_state, get_user_data, clear_user_state,
    is_user_member, get_setting, get_admin_ids,
    rate_limit_check, sanitize_text
)
from database import DB_NAME
import sqlite3
import os
import time
import random

def setup_registration_handlers(client, user_states):

    @client.on(events.NewMessage)
    async def registration_message_handler(event):
        user_id = event.sender_id
        # basic per-user rate limiting (limit requests to reasonable amount)
        if not rate_limit_check(user_id, limit=10, window=60):
            try:
                await event.reply("❌ سرعت درخواست‌ها زیاد است؛ لطفاً چند لحظه صبر کرده و دوباره تلاش کنید.")
            except:
                pass
            return

        state = get_user_state(user_states, user_id)

        if not await is_user_member(client, user_id):
            return  

        if state == "register_step_1":
            full_name = sanitize_text(event.message.text or "")
            if len(full_name) < 3:
                await event.reply("❌ نام باید حداقل 3 کاراکتر باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            data = get_user_data(user_states, user_id)
            if not data:
                data = {}
            data["full_name"] = full_name
            set_user_state(user_states, user_id, "register_step_2", data)
            await event.reply("🆔 لطفا کد ملی خود را ارسال کنید (10 رقمی):", buttons=CANCEL_BUTTON)

        elif state == "register_step_2":
            national_id = sanitize_text(event.message.text or "")
            if not national_id.isdigit() or len(national_id) != 10:
                await event.reply("❌ کد ملی باید 10 رقمی و عددی باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            if not validate_national_id(national_id):
                await event.reply("❌ کد ملی وارد شده معتبر نیست. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            data = get_user_data(user_states, user_id)
            data["national_id"] = national_id
            set_user_state(user_states, user_id, "register_step_3", data)
            await event.reply("📞 لطفا شماره تماس خود را ارسال کنید:", buttons=CANCEL_BUTTON)

        elif state == "register_step_3":
            phone = sanitize_text(event.message.text or "")
            clean_phone = phone.replace("+98", "").replace("0", "", 1).replace(" ", "").replace("-", "")
            if not clean_phone.isdigit() or len(clean_phone) != 10:
                await event.reply("❌ شماره تماس باید 10 رقمی باشد (مثال: 09123456789). لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            data = get_user_data(user_states, user_id)
            data["phone"] = clean_phone
            event_id = data.get("event_id")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT cost_type, fixed_cost, student_cost, non_student_cost, card_number FROM events WHERE id = ?", (event_id,))
            event_info = c.fetchone()
            conn.close()
            if not event_info:
                await event.reply("❌ خطایی در دریافت اطلاعات رویداد رخ داد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                clear_user_state(user_states, user_id)
                return
            cost_type, fixed_cost, student_cost, non_student_cost, card_number = event_info
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # respect global setting: single registration per user (default on)
            # check per-event single_registration flag (default True)
            try:
                c.execute("SELECT single_registration FROM events WHERE id = ?", (event_id,))
                sr_row = c.fetchone()
                single_reg = True if sr_row is None or sr_row[0] is None else bool(sr_row[0])
            except Exception:
                single_reg = True
            if single_reg:
                # block only if user already has an approved or pending registration
                c.execute("SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ? AND status IN ('approved','pending')", (user_id, event_id))
                if c.fetchone():
                    conn.close()
                    await event.reply("ℹ️ شما قبلاً برای این رویداد ثبت‌نام کرده‌اید.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                    clear_user_state(user_states, user_id)
                    return
            c.execute("SELECT capacity FROM events WHERE id = ?", (event_id,))
            cap_row = c.fetchone()
            capacity = cap_row[0] if cap_row else None
            if capacity is not None:
                c.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status IN ('approved','pending')", (event_id,))
                current_cnt = c.fetchone()[0]
                if current_cnt >= capacity:
                    conn.close()
                    await event.reply("❌ ظرفیت این رویداد تکمیل شده است.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
                    clear_user_state(user_states, user_id)
                    return
            conn.close()
            data["cost_type"] = cost_type
            set_user_state(user_states, user_id, "register_step_4", data)

            msg = "❓ آیا شما دانشجو هستید؟"
            buttons = [
                [Button.inline("🎓 دانشجو", b"student_yes")],
                [Button.inline("🧑‍💼 غیر دانشجو", b"student_no")],
                [Button.inline("❌ لغو", b"cancel")]
            ]
            await event.reply(msg, buttons=buttons)

        elif state == "register_step_5":
            student_id = sanitize_text(event.message.text or "")
            if not student_id.isdigit():
                await event.reply("❌ شماره دانشجویی باید عددی باشد. لطفا دوباره ارسال کنید:", buttons=CANCEL_BUTTON)
                return
            data = get_user_data(user_states, user_id)
            data["student_id"] = student_id
            data["is_student"] = 1
            # If event is free, check certificate fees (single or student-specific)
            if data.get("cost_type") == "free":
                event_id = data.get("event_id")
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT cert_fee, cert_fee_student, cert_fee_non_student, cert_card_number, cert_card_holder FROM events WHERE id = ?", (event_id,))
                row = c.fetchone()
                conn.close()
                cert_fee = cert_fee_student = cert_fee_non_student = cert_card = cert_holder = None
                if row:
                    cert_fee, cert_fee_student, cert_fee_non_student, cert_card, cert_holder = row
                cert_fee = cert_fee or 0
                cert_fee_student = cert_fee_student or 0
                cert_fee_non_student = cert_fee_non_student or 0
                # student: prefer single cert_fee if set, otherwise student-specific fee
                amount = 0
                if cert_fee > 0:
                    amount = cert_fee
                elif cert_fee_student > 0:
                    amount = cert_fee_student

                if amount > 0:
                    data["amount"] = amount
                    data["card_number"] = cert_card or ''
                    data["card_holder"] = cert_holder or ''
                    set_user_state(user_states, user_id, "register_step_6", data)
                    msg = f"💳 شماره کارت: `{data['card_number']}`\n💰 مبلغ قابل پرداخت: {amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
                    buttons = [
                        [Button.inline("✅ واریز کردم", b"payment_done")],
                        [Button.inline("❌ لغو فرایند", b"cancel")]
                    ]
                    await event.reply(msg, buttons=buttons, parse_mode="markdown")
                    return
                else:
                    await finalize_registration(client, event, user_id, data, used_profile=False)
                    return

            # non-free events: follow existing amount logic
            event_id = data["event_id"]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT cost_type, fixed_cost, student_cost, non_student_cost, card_number FROM events WHERE id = ?", (event_id,))
            event_info = c.fetchone()
            conn.close()
            cost_type, fixed_cost, student_cost, non_student_cost, card_number = event_info
            amount = 0
            if cost_type == "fixed":
                amount = fixed_cost
            elif cost_type == "variable":
                amount = student_cost 
            data["amount"] = amount
            data["card_number"] = card_number
            msg = f"💳 شماره کارت: `{card_number}`\n💰 مبلغ قابل پرداخت: {amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
            buttons = [
                [Button.inline("✅ واریز کردم", b"payment_done")],
                [Button.inline("❌ لغو فرایند", b"cancel")]
            ]
            set_user_state(user_states, user_id, "register_step_6", data)
            await event.reply(msg, buttons=buttons, parse_mode="markdown")

        elif state == "register_step_6":
            pass

        elif state == "register_step_7":
            if not event.message.photo and not event.message.document:
                await event.reply("❌ لطفا یک عکس یا فایل فیش واریز ارسال کنید:", buttons=CANCEL_BUTTON)
                return

            if event.message.file:
                size = getattr(event.message.file, 'size', 0) or 0
                if size > 10 * 1024 * 1024:
                    await event.reply("❌ حجم فایل نباید بیش از 10MB باشد.", buttons=CANCEL_BUTTON)
                    return
            file_ext = "jpg" if event.message.photo else (event.message.file.ext or "dat").lower()
            allowed = {"jpg", "jpeg", "png", "pdf"}
            if file_ext.startswith('.'):
                file_ext = file_ext[1:]
            if file_ext not in allowed:
                await event.reply("❌ فقط فرمت‌های jpg, jpeg, png, pdf مجاز است.", buttons=CANCEL_BUTTON)
                return
            unique_name = f"receipt_{user_id}_{int(time.time())}_{random.randint(1000,9999)}.{file_ext}"
            temp_path = os.path.join("uploads", unique_name)
            await event.message.download_media(file=temp_path)

            data = get_user_data(user_states, user_id)
            data["payment_receipt_path"] = temp_path

            await finalize_registration(client, event, user_id, data, used_profile=False)

    @client.on(events.CallbackQuery)
    async def registration_callback_handler(event):
        data = event.data.decode('utf-8')
        user_id = event.sender_id

        if not await is_user_member(client, user_id):
            try:
                await event.answer("❌ ابتدا باید عضو کانال شوید!", alert=True)
            except:
                pass
            return

        if data.startswith("start_register_manual_"):
            event_id = int(data.split("_")[-1])
            clear_user_state(user_states, user_id)
            set_user_state(user_states, user_id, "register_step_1", {"event_id": event_id})
            try:
                await event.edit("👤 لطفا نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
            except:
                try:
                    await event.reply("👤 لطفا نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
                except:
                    pass
            return

        if data.startswith("use_profile_"):
            event_id = int(data.split("_")[-1])
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT full_name, national_id, phone, is_student, student_id FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            conn.close()
            if not row:
                await event.answer("📌 پروفایلی پیدا نشد. لطفا اطلاعات را به صورت دستی وارد کنید.", alert=True)
                clear_user_state(user_states, user_id)
                set_user_state(user_states, user_id, "register_step_1", {"event_id": event_id})
                try:
                    await event.edit("👤 لطفا نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
                except:
                    pass
                return
            full_name, national_id, phone, is_student, student_id = row
            missing = []
            if not full_name:
                missing.append('نام')
            if not national_id:
                missing.append('کد ملی')
            if not phone:
                missing.append('تلفن')
            if is_student and not student_id:
                missing.append('شماره دانشجویی')
            if missing:
                await event.answer("📌 پروفایل شما تکمیل نیست: " + ", ".join(missing) + " — لطفا به صورت دستی وارد کنید.", alert=True)
                clear_user_state(user_states, user_id)
                set_user_state(user_states, user_id, "register_step_1", {"event_id": event_id})
                try:
                    await event.edit("👤 لطفا نام و نام خانوادگی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
                except:
                    pass
                return
            data = {
                "event_id": event_id,
                "full_name": full_name,
                "national_id": national_id,
                "phone": phone,
                "is_student": 1 if is_student else 0,
                "student_id": student_id
            }
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT cost_type, fixed_cost, student_cost, non_student_cost, card_number, capacity FROM events WHERE id = ?", (event_id,))
            event_info = c.fetchone()
            if not event_info:
                conn.close()
                await event.answer("❌ خطا در دریافت اطلاعات رویداد. لطفا دوباره تلاش کنید.", alert=True)
                return
            cost_type, fixed_cost, student_cost, non_student_cost, card_number, capacity = event_info
            # check per-event single_registration flag (default True)
            try:
                c.execute("SELECT single_registration FROM events WHERE id = ?", (event_id,))
                sr_row = c.fetchone()
                single_reg = True if sr_row is None or sr_row[0] is None else bool(sr_row[0])
            except Exception:
                single_reg = True
            if single_reg:
                # block only if user already has an approved or pending registration
                c.execute("SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ? AND status IN ('approved','pending')", (user_id, event_id))
                if c.fetchone():
                    conn.close()
                    await event.answer("ℹ️ شما قبلاً برای این رویداد ثبت‌نام کرده‌اید.", alert=True)
                    return
            if capacity is not None:
                c.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status IN ('approved','pending')", (event_id,))
                current_cnt = c.fetchone()[0]
                if current_cnt >= capacity:
                    conn.close()
                    await event.answer("❌ ظرفیت این رویداد تکمیل شده است.", alert=True)
                    return
            conn.close()
            amount = 0
            if cost_type == 'fixed':
                amount = fixed_cost
            elif cost_type == 'variable':
                amount = student_cost if data['is_student'] == 1 else non_student_cost
            data['cost_type'] = cost_type
            # if event is free or amount == 0 then check certificate fees
            if cost_type == 'free' or amount == 0:
                # check cert fees
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT cert_fee, cert_fee_student, cert_fee_non_student, cert_card_number, cert_card_holder FROM events WHERE id = ?", (event_id,))
                row = c.fetchone()
                conn.close()
                cert_fee = cert_fee_student = cert_fee_non_student = cert_card = cert_holder = None
                if row:
                    cert_fee, cert_fee_student, cert_fee_non_student, cert_card, cert_holder = row
                cert_fee = cert_fee or 0
                cert_fee_student = cert_fee_student or 0
                cert_fee_non_student = cert_fee_non_student or 0
                chosen_amount = 0
                # choose proper cert fee based on user's student status
                if cert_fee > 0:
                    chosen_amount = cert_fee
                else:
                    chosen_amount = cert_fee_student if data['is_student'] == 1 else cert_fee_non_student
                if chosen_amount and chosen_amount > 0:
                    data['amount'] = chosen_amount
                    data['card_number'] = cert_card or ''
                    data['card_holder'] = cert_holder or ''
                    set_user_state(user_states, user_id, 'register_step_6', data)
                    msg = f"💳 شماره کارت: `{data['card_number']}`\n💰 مبلغ قابل پرداخت: {chosen_amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
                    buttons = [[Button.inline("✅ واریز کردم", b"payment_done")], [Button.inline("❌ لغو فرایند", b"cancel")]]
                    try:
                        await event.edit(msg, buttons=buttons, parse_mode='markdown')
                    except:
                        try:
                            await event.reply(msg, buttons=buttons)
                        except:
                            pass
                    return
                else:
                    await finalize_registration(client, event, user_id, data, used_profile=True)
                    return
            data['amount'] = amount
            data['card_number'] = card_number
            set_user_state(user_states, user_id, 'register_step_6', data)
            msg = f"💳 شماره کارت: `{card_number}`\n💰 مبلغ قابل پرداخت: {amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
            buttons = [[Button.inline("✅ واریز کردم", b"payment_done")], [Button.inline("❌ لغو فرایند", b"cancel")]]
            try:
                await event.edit(msg, buttons=buttons, parse_mode='markdown')
            except:
                try:
                    await event.reply(msg, buttons=buttons)
                except:
                    pass
            return

        if data == "payment_done":
            state = get_user_state(user_states, user_id)
            if state != "register_step_6":
                try:
                    await event.answer("❌ عملیات نامعتبر!", alert=True)
                except:
                    pass
                return
            set_user_state(user_states, user_id, "register_step_7", get_user_data(user_states, user_id))
            try:
                await event.edit("🖼️ لطفا فیش واریز را به صورت عکس یا فایل ارسال کنید:", buttons=CANCEL_BUTTON)
            except:
                pass

        elif data == "cancel":
            clear_user_state(user_states, user_id)
            try:
                await event.edit("✅ عملیات لغو شد.", buttons=[[Button.inline("🏠 منوی اصلی", b"main_menu")]])
            except:
                pass

    @client.on(events.CallbackQuery(pattern=b"student_(yes|no)"))
    async def student_status_handler(event):
        user_id = event.sender_id
        state = get_user_state(user_states, user_id)
        if state != "register_step_4":
            return
        choice = event.data.decode('utf-8').split("_")[1]
        is_student = 1 if choice == "yes" else 0
        data = get_user_data(user_states, user_id)
        data["is_student"] = is_student
        if is_student == 1:
            set_user_state(user_states, user_id, "register_step_5", data)
            await event.edit("🎓 لطفا شماره دانشجویی خود را ارسال کنید:", buttons=CANCEL_BUTTON)
        else:
            data["student_id"] = None
            cost_type = data.get("cost_type")
            event_id = data.get("event_id")
            if cost_type == "free":
                # check certificate fees for non-students
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT cert_fee, cert_fee_student, cert_fee_non_student, cert_card_number, cert_card_holder FROM events WHERE id = ?", (event_id,))
                row = c.fetchone()
                conn.close()
                cert_fee = cert_fee_student = cert_fee_non_student = cert_card = cert_holder = None
                if row:
                    cert_fee, cert_fee_student, cert_fee_non_student, cert_card, cert_holder = row
                cert_fee = cert_fee or 0
                cert_fee_student = cert_fee_student or 0
                cert_fee_non_student = cert_fee_non_student or 0
                amount = 0
                # non-student: prefer single cert_fee if set, otherwise non-student specific
                if cert_fee > 0:
                    amount = cert_fee
                elif cert_fee_non_student > 0:
                    amount = cert_fee_non_student

                if amount > 0:
                    data["amount"] = amount
                    data["card_number"] = cert_card or ''
                    data["card_holder"] = cert_holder or ''
                    set_user_state(user_states, user_id, "register_step_6", data)
                    msg = f"💳 شماره کارت: `{data['card_number']}`\n💰 مبلغ قابل پرداخت: {amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
                    buttons = [
                        [Button.inline("✅ واریز کردم", b"payment_done")],
                        [Button.inline("❌ لغو فرایند", b"cancel")]
                    ]
                    await event.edit(msg, buttons=buttons, parse_mode="markdown")
                    return
                else:
                    await finalize_registration(client, event, user_id, data, used_profile=False)
                    return
            else:
                event_id = data["event_id"]
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT cost_type, fixed_cost, student_cost, non_student_cost, card_number FROM events WHERE id = ?", (event_id,))
                event_info = c.fetchone()
                conn.close()
                cost_type, fixed_cost, student_cost, non_student_cost, card_number = event_info
                amount = 0
                if cost_type == "fixed":
                    amount = fixed_cost
                elif cost_type == "variable":
                    amount = non_student_cost
                data["amount"] = amount
                data["card_number"] = card_number
                msg = f"💳 شماره کارت: `{card_number}`\n💰 مبلغ قابل پرداخت: {amount:,} تومان\n\nپس از واریز، دکمه «واریز کردم» را بزنید."
                buttons = [
                    [Button.inline("✅ واریز کردم", b"payment_done")],
                    [Button.inline("❌ لغو فرایند", b"cancel")]
                ]
                set_user_state(user_states, user_id, "register_step_6", data)
                await event.edit(msg, buttons=buttons, parse_mode="markdown")

    async def finalize_registration(client, event_or_callback, user_id, data, used_profile=False):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, full_name, national_id, student_id, phone, is_student, status) VALUES (?, ?, ?, ?, ?, ?, 'pending')",
                  (user_id, data["full_name"], data["national_id"], data.get("student_id"), data["phone"], data["is_student"]))
        c.execute("UPDATE users SET full_name = ?, national_id = ?, student_id = ?, phone = ?, is_student = ? WHERE user_id = ?",
                  (data["full_name"], data["national_id"], data.get("student_id"), data["phone"], data["is_student"], user_id))
        try:
            c.execute("""
                INSERT INTO registrations (user_id, event_id, payment_receipt_file_id, status)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                data["event_id"],
                data.get("payment_receipt_path"),
                "pending"
            ))
        except Exception:
            pass
        conn.commit()
        conn.close()
        clear_user_state(user_states, user_id)
        try:
            if get_setting("notify_new_registration","1") == "1":
                admins = get_admin_ids()
                msg = f"🔔 ثبت‌نام جدید\nکاربر: {data.get('full_name','')} ({user_id})\nرویداد: {data.get('event_id')}"
                for aid in admins:
                    try:
                        await client.send_message(aid, msg)
                    except Exception:
                        pass
        except Exception:
            pass
        # Try to edit the triggering message (if supported), otherwise reply/send a new message.
        sent = False
        success_text = (
            "✅ ثبت‌نام شما با موفقیت انجام شد و در حال بررسی است.\n"
            "پس از تایید ادمین، از طریق ربات به شما اطلاع داده می‌شود."
        )
        buttons = [[Button.inline("🏠 منوی اصلی", b"main_menu")]]
        if hasattr(event_or_callback, "edit"):
            try:
                await event_or_callback.edit(success_text, buttons=buttons)
                sent = True
                if used_profile:
                    try:
                        # CallbackQuery has answer; NewMessage may not. Best-effort.
                        await event_or_callback.answer("✅ ثبت‌نام با اطلاعات پروفایل انجام شد.", alert=True)
                    except Exception:
                        pass
            except Exception:
                sent = False

        if not sent:
            try:
                # fallback to a normal reply/send
                try:
                    await event_or_callback.reply(success_text, buttons=buttons)
                except Exception:
                    # If the event object doesn't support reply, try sending directly
                    await client.send_message(user_id, success_text, buttons=buttons)
                if used_profile:
                    try:
                        await client.send_message(user_id, "✅ ثبت‌نام با اطلاعات پروفایل انجام شد.")
                    except Exception:
                        pass
            except Exception:
                # nothing else we can do; swallow to avoid crashing the bot
                pass


def validate_national_id(national_id):
    """اعتبارسنجی کد ملی با چک‌سام"""
    if len(national_id) != 10 or not national_id.isdigit():
        return False
    
    check_digit = int(national_id[9])
    sum_digits = 0
    
    for i in range(9):
        sum_digits += int(national_id[i]) * (10 - i)
    
    remainder = sum_digits % 11
    calculated_check = 11 - remainder if remainder >= 2 else remainder
    

    return calculated_check == check_digit