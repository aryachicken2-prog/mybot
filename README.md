# mybot

## 📝 معرفی (فارسی)


این ربات تلگرام برای مدیریت حرفه‌ای رویدادها و ثبت‌نام آنلاین طراحی شده است. هدف اصلی آن ساده‌سازی فرآیند ثبت‌نام، مدیریت اعضا و تسهیل ارتباط بین ادمین و کاربران است. ادمین می‌تواند رویدادهای مختلف تعریف کند، ظرفیت و هزینه هر رویداد را مشخص نماید و به راحتی وضعیت ثبت‌نام‌ها را مدیریت کند. کاربران نیز می‌توانند به سادگی در رویدادها ثبت‌نام کنند، مدارک لازم را ارسال نمایند و وضعیت خود را پیگیری کنند.

**کاربردهای اصلی ربات:**
- مناسب برای انجمن‌ها، موسسات آموزشی، همایش‌ها و هر مجموعه‌ای که نیاز به ثبت‌نام و مدیریت رویداد دارد.
- کاهش خطا و اتلاف وقت در مدیریت دستی ثبت‌نام‌ها و پرداخت‌ها.
- افزایش شفافیت و سرعت در اطلاع‌رسانی و تایید عضویت یا ثبت‌نام.

**چرخه کار ربات:**
1. ادمین رویداد جدید تعریف می‌کند و اطلاعات آن را وارد می‌نماید.
2. کاربران با عضویت در کانال و ورود به ربات، لیست رویدادها را مشاهده می‌کنند.
3. هر کاربر می‌تواند در رویداد مورد نظر ثبت‌نام کند و اطلاعات و مدارک لازم را ارسال نماید.
4. ادمین ثبت‌نام‌ها را بررسی و تایید یا رد می‌کند و پیام‌های لازم را ارسال می‌نماید.
5. آمار و گزارش‌های کامل برای هر رویداد و ثبت‌نام‌ها در دسترس ادمین است.

این ربات با ساختار ماژولار و قابلیت توسعه، می‌تواند متناسب با نیازهای هر مجموعه شخصی‌سازی شود.


### امکانات و ویژگی‌های ریز ربات
- ثبت‌نام مرحله‌ای کاربران در رویدادها (نام، کد ملی، شماره تماس، دانشجو/غیر دانشجو، شماره دانشجویی، آپلود فیش واریز)
	- کاربران برای هر رویداد باید اطلاعات خود را مرحله به مرحله وارد کنند تا ثبت‌نام کامل شود.
- امکان استفاده از اطلاعات پروفایل قبلی برای ثبت‌نام سریع‌تر
	- اگر قبلاً ثبت‌نام کرده باشند، می‌توانند اطلاعات قبلی را مجدداً استفاده کنند.
- بررسی ظرفیت رویداد و جلوگیری از ثبت‌نام بیش از ظرفیت
	- اگر ظرفیت رویداد تکمیل شود، ثبت‌نام جدید پذیرفته نمی‌شود.
- محدودیت ثبت‌نام تکراری (یک ثبت‌نام برای هر کاربر در هر رویداد)
	- هر کاربر فقط یک بار می‌تواند برای هر رویداد ثبت‌نام کند.
- مدیریت هزینه رویداد (رایگان، هزینه ثابت، هزینه متغیر برای دانشجو/غیردانشجو)
	- ادمین می‌تواند نوع هزینه را برای هر رویداد تعیین کند.
- مدیریت هزینه صدور گواهی (یکسان یا متفاوت برای دانشجو/غیردانشجو)
	- هزینه صدور گواهی حضور می‌تواند برای دانشجو و غیر دانشجو متفاوت باشد.
- ارسال و بررسی فیش واریز توسط ادمین
	- کاربران باید فیش واریز را ارسال کنند و ادمین آن را تایید یا رد می‌کند.
- تایید یا رد ثبت‌نام‌ها توسط ادمین
	- ادمین می‌تواند ثبت‌نام‌ها را تایید یا رد کند و وضعیت کاربر را تغییر دهد.
- ارسال پیام گروهی به تاییدشدگان یا ردشدگان هر رویداد
	- ادمین می‌تواند به صورت گروهی به تاییدشدگان یا ردشدگان پیام ارسال کند.
- ارسال یادآوری به تاییدشدگان
	- امکان ارسال پیام یادآوری به تاییدشدگان هر رویداد وجود دارد.
- مشاهده و مدیریت گزارش‌های کار هر رویداد (متن، فایل، پیام فورواردی)
	- ادمین می‌تواند گزارش‌های متنی، فایل یا پیام‌های فورواردی را برای هر رویداد ثبت و مشاهده کند.
- مدیریت کامل رویدادها (افزودن، ویرایش، حذف، تعیین ظرفیت، تعیین مهلت، تغییر وضعیت فعال/غیرفعال)
	- رویدادها به طور کامل توسط ادمین قابل مدیریت هستند.
- مدیریت پوستر رویداد و فایل‌های مرتبط
	- امکان بارگذاری و تغییر پوستر و فایل‌های هر رویداد وجود دارد.
- مشاهده آمار دقیق ثبت‌نام‌ها (تاییدشده، ردشده، در انتظار) برای هر رویداد
	- ادمین می‌تواند آمار ثبت‌نام‌ها را به تفکیک وضعیت مشاهده کند.
- پنل ادمین با منوی گرافیکی و میانبرهای رویداد
	- پنل ادمین دارای منوی گرافیکی و قابلیت تعریف میانبر برای رویدادهای مهم است.
- مدیریت درخواست‌های عضویت و تایید/رد کاربران جدید
	- درخواست‌های عضویت جدید توسط ادمین بررسی و تایید یا رد می‌شوند.
- ارسال پیام همگانی به همه کاربران یا گروه خاص (تاییدشده/ردشده)
	- ادمین می‌تواند پیام همگانی به همه یا گروه خاصی از کاربران ارسال کند.
- تنظیمات پیشرفته (فعال/غیرفعال‌سازی اعلان‌ها، محدودیت ثبت‌نام، شماره کارت حمایت، توضیحات حمایت و ...)
	- تنظیمات مختلف مدیریتی برای شخصی‌سازی عملکرد ربات در دسترس است.
- پاکسازی داده‌ها و فایل‌های اضافی سرور و رویدادها
	- ابزارهایی برای حذف داده‌ها و فایل‌های اضافی و پاکسازی سرور وجود دارد.
- ثبت و نمایش تاریخچه اقدامات ادمین
	- تمامی اقدامات مهم ادمین ثبت و قابل مشاهده است.
- پشتیبانی از چند زبان برای پیام‌های سیستمی (فارسی/انگلیسی)
	- پیام‌های سیستمی ربات قابل نمایش به دو زبان هستند.
- ذخیره‌سازی امن داده‌ها در SQLite و مدیریت فایل‌ها در پوشه uploads
	- اطلاعات کاربران و رویدادها به صورت امن در پایگاه داده ذخیره می‌شود.
- ثبت‌نام مرحله‌ای کاربران در رویدادها (نام، کد ملی، شماره تماس، دانشجو/غیر دانشجو، شماره دانشجویی، آپلود فیش واریز)
- امکان استفاده از اطلاعات پروفایل قبلی برای ثبت‌نام سریع‌تر
- بررسی ظرفیت رویداد و جلوگیری از ثبت‌نام بیش از ظرفیت
- محدودیت ثبت‌نام تکراری (یک ثبت‌نام برای هر کاربر در هر رویداد)
- مدیریت هزینه رویداد (رایگان، هزینه ثابت، هزینه متغیر برای دانشجو/غیردانشجو)
- مدیریت هزینه صدور گواهی (یکسان یا متفاوت برای دانشجو/غیردانشجو)
- ارسال و بررسی فیش واریز توسط ادمین
- تایید یا رد ثبت‌نام‌ها توسط ادمین
- ارسال پیام گروهی به تاییدشدگان یا ردشدگان هر رویداد
- ارسال یادآوری به تاییدشدگان
- مشاهده و مدیریت گزارش‌های کار هر رویداد (متن، فایل، پیام فورواردی)
- مدیریت کامل رویدادها (افزودن، ویرایش، حذف، تعیین ظرفیت، تعیین مهلت، تغییر وضعیت فعال/غیرفعال)
- مدیریت پوستر رویداد و فایل‌های مرتبط
- مشاهده آمار دقیق ثبت‌نام‌ها (تاییدشده، ردشده، در انتظار) برای هر رویداد
- پنل ادمین با منوی گرافیکی و میانبرهای رویداد
- مدیریت درخواست‌های عضویت و تایید/رد کاربران جدید
- ارسال پیام همگانی به همه کاربران یا گروه خاص (تاییدشده/ردشده)
- تنظیمات پیشرفته (فعال/غیرفعال‌سازی اعلان‌ها، محدودیت ثبت‌نام، شماره کارت حمایت، توضیحات حمایت و ...)
- پاکسازی داده‌ها و فایل‌های اضافی سرور و رویدادها
- ثبت و نمایش تاریخچه اقدامات ادمین
- پشتیبانی از چند زبان برای پیام‌های سیستمی (فارسی/انگلیسی)
- ذخیره‌سازی امن داده‌ها در SQLite و مدیریت فایل‌ها در پوشه uploads

### نصب و راه‌اندازی
1. پایتون ۳.۸ یا بالاتر را نصب کنید.
2. کتابخانه‌های مورد نیاز را نصب کنید:
	```bash
	pip install -r requirements.txt
	```
3. مقادیر `API_ID`، `API_HASH` و `BOT_TOKEN` را در فایل `.env` یا `config.py` قرار دهید.
4. اجرای ربات:
	```bash
	python main.py
	```

### ساختار ماژول‌ها
- `main.py`: نقطه شروع و مدیریت کلی ربات
- `admin_panel.py`: پنل مدیریت ادمین‌ها و رویدادها
- `user_panel.py`: پنل کاربری و تعامل با کاربران
- `registration_flow.py`: فرآیند ثبت‌نام در رویدادها
- `membership_flow.py`: مدیریت عضویت و درخواست‌ها
- `event_manager.py`: مدیریت و نمایش رویدادها
- `broadcast_manager.py`: ارسال پیام همگانی
- `database.py`: مدیریت پایگاه داده و جداول
- `utils.py`: توابع کمکی و تنظیمات
- `log_helper.py`: مدیریت لاگ و پیام‌های سیستمی

---

## 📝 English Description

This Telegram bot is designed for professional event management and online registration. Its main goal is to simplify the registration process, manage members, and facilitate communication between admins and users. Admins can define various events, set capacity and costs, and easily manage registration statuses. Users can register for events, upload required documents, and track their status with ease.

**Main Use Cases:**
- Suitable for associations, educational institutions, conferences, and any organization needing event registration and management.
- Reduces errors and time wasted in manual registration and payment management.
- Increases transparency and speed in notifications and membership/registration approvals.

**Bot Workflow:**
1. Admin defines a new event and enters its details.
2. Users join the channel and interact with the bot to see the list of events.
3. Each user can register for their desired event and upload required information and documents.
4. Admin reviews, approves, or rejects registrations and sends necessary messages.
5. Complete statistics and reports for each event and registration are available to the admin.

The bot is modular and extensible, making it customizable for any organization’s needs.

This project is an advanced Telegram bot for event management, user registration, membership handling, admin panel, and mass messaging. It is built using the Telethon library and SQLite database, and is highly customizable.


### Detailed Features
- Step-by-step user registration for events (name, national ID, phone, student/non-student, student ID, payment receipt upload)
	- Users must enter their information step by step for each event to complete registration.
- Use previous profile info for faster registration
	- If registered before, users can reuse their previous info for new registrations.
- Event capacity check and prevention of over-registration
	- If the event is full, new registrations are not accepted.
- Duplicate registration prevention (one registration per user per event)
	- Each user can only register once per event.
- Event cost management (free, fixed, variable for student/non-student)
	- Admin can set the cost type for each event.
- Certificate fee management (same or different for student/non-student)
	- Certificate fees can be set differently for students and non-students.
- Payment receipt upload and admin review
	- Users must upload payment receipts, which are reviewed and approved/rejected by admin.
- Admin approval or rejection of registrations
	- Admin can approve or reject registrations and change user status.
- Group messaging to approved or rejected users of each event
	- Admin can send group messages to approved or rejected users of each event.
- Reminders to approved users
	- Admin can send reminder messages to approved users of each event.
- View and manage event reports (text, file, forwarded message)
	- Admin can register and view text, file, or forwarded message reports for each event.
- Full event management (add, edit, delete, set capacity, set deadline, activate/deactivate)
	- Events are fully manageable by admin.
- Manage event posters and related files
	- Posters and files for each event can be uploaded and changed.
- View detailed registration stats (approved, rejected, pending) for each event
	- Admin can view registration stats by status for each event.
- Admin panel with graphical menu and event shortcuts
	- Admin panel has a graphical menu and allows defining shortcuts for important events.
- Membership request management and approval/rejection of new users
	- New membership requests are reviewed and approved/rejected by admin.
- Broadcast messaging to all users or specific groups (approved/rejected)
	- Admin can broadcast messages to all or specific groups of users.
- Advanced settings (enable/disable notifications, registration limits, donation card, donation description, etc.)
	- Various management settings are available for customizing bot behavior.
- Data and file cleanup for server and events
	- Tools are available for deleting extra data and files and cleaning up the server.
- Admin action history logging and display
	- All important admin actions are logged and viewable.
- Multi-language support for system messages (Farsi/English)
	- System messages can be displayed in both languages.
- Secure data storage in SQLite and file management in uploads folder
	- User and event data are securely stored in the database.
- Step-by-step user registration for events (name, national ID, phone, student/non-student, student ID, payment receipt upload)
- Use previous profile info for faster registration
- Event capacity check and prevention of over-registration
- Duplicate registration prevention (one registration per user per event)
- Event cost management (free, fixed, variable for student/non-student)
- Certificate fee management (same or different for student/non-student)
- Payment receipt upload and admin review
- Admin approval or rejection of registrations
- Group messaging to approved or rejected users of each event
- Reminders to approved users
- View and manage event reports (text, file, forwarded message)
- Full event management (add, edit, delete, set capacity, set deadline, activate/deactivate)
- Manage event posters and related files
- View detailed registration stats (approved, rejected, pending) for each event
- Admin panel with graphical menu and event shortcuts
- Membership request management and approval/rejection of new users
- Broadcast messaging to all users or specific groups (approved/rejected)
- Advanced settings (enable/disable notifications, registration limits, donation card, donation description, etc.)
- Data and file cleanup for server and events
- Admin action history logging and display
- Multi-language support for system messages (Farsi/English)
- Secure data storage in SQLite and file management in uploads folder

### Installation & Setup
1. Install Python 3.8 or higher.
2. Install required packages:
	```bash
	pip install -r requirements.txt
	```
3. Set your `API_ID`, `API_HASH`, and `BOT_TOKEN` in a `.env` file or `config.py`.
4. Run the bot:
	```bash
	python main.py
	```

### Module Structure
- `main.py`: Entry point and main bot logic
- `admin_panel.py`: Admin panel and event management
- `user_panel.py`: User panel and interactions
- `registration_flow.py`: Event registration flow
- `membership_flow.py`: Membership management
- `event_manager.py`: Event display and management
- `broadcast_manager.py`: Mass messaging
- `database.py`: Database and table management
- `utils.py`: Utility functions and settings
- `log_helper.py`: Logging and system messages

---
> توسعه‌دهنده: telegram:@iq_arya