import os
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8624856174:AAF8w8nF2GxHKTK5qiN8jUyDN1CPXkl2Q7Q"
bot = telebot.TeleBot(TOKEN)

# معرف المشرف الأساسي (Admin ID)
ADMIN_CHAT_ID = 6000524951

app = Flask(__name__)
DB_NAME = "store.db"

# تهيئة قاعدة البيانات والجداول الشاملة
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            referred_by INTEGER
        )
    ''')
    
    # جدول المنتجات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            description TEXT,
            file_url TEXT
        )
    ''')
    
    # جدول الطلبات المعلقة للتحقق
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # جدول الأكواد الترويجية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            discount_amount REAL
        )
    ''')
    
    # إعادة تعيين وتحديث المنتجات بمنتجات رقمية عالية الأهمية والطلب
    cursor.execute("DELETE FROM products")
    sample_products = [
        ("🚀 حزمة أتمتة الواتساب وخدمة العملاء بالذكاء الاصطناعي", 49.0, "دليل ونصوص برمجية جاهزة لربط بوت واتساب ذكي للرد على العملاء 24/7 وإتمام المبيعات تلقائياً.", "https://t.me/example_whatsapp_automation"),
        ("📚 المرجع الشامل لهندسة الأوامر المتقدمة (Prompt Engineering Masterclass)", 25.0, "أكثر من 500 أمر احترافي ومختبر لـ ChatGPT و Claude لتوليد المحتوى، البرمجة، وتحليل البيانات.", "https://t.me/example_prompt_masterclass"),
        ("💼 حزمة قوالب إدارة المشاريع ونظام العمل (Notion OS)", 19.0, "نظام متكامل لإدارة المهام، المبيعات، ومتابعة العملاء المحتملين عبر منصة Notion.", "https://t.me/example_notion_os"),
        ("📈 استراتيجية الإعلانات الممولة وحملات التحويل العالي", 35.0, "دليل خطوة بخطوة لإطلاق حملات إعلانية ناجحة بأقل تكلفة وأعلى عائد استثماري (ROI).", "https://t.me/example_ads_strategy"),
        ("🤖 دليل بناء وتطوير بوتات تيليجرام التجارية المتقدمة", 20.0, "كود وخطوات بناء بوت مبيعات متكامل مشابه لهذا البوت تماماً مع شرح طريقة ربطه بالسيرفر.", "https://t.me/example_telegram_bot_guide")
    ]
    cursor.executemany('INSERT INTO products (name, price, description, file_url) VALUES (?, ?, ?, ?)', sample_products)
    
    # إضافة كود خصم تجريبي
    cursor.execute("INSERT OR IGNORE INTO promo_codes (code, discount_amount) VALUES ('SARAH5OFF', 5.0)")

    conn.commit()
    conn.close()

init_db()

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📚 تصفح الكتالوج الرقمي الاحترافي", callback_data="catalog"))
    markup.row(InlineKeyboardButton("⭐ محفظة الولاء والإحالة", callback_data="loyalty"))
    markup.row(InlineKeyboardButton("💬 تواصل مع الدعم الفني", callback_data="support"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    args = message.text.split()
    referred_by = None
    if len(args) > 1:
        try:
            potential_referrer = int(args[1])
            if potential_referrer != user_id:
                referred_by = potential_referrer
        except ValueError:
            pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, points FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        initial_points = 10
        cursor.execute('INSERT INTO users (user_id, username, points, referred_by) VALUES (?, ?, ?, ?)',
                       (user_id, username, initial_points, referred_by))
        if referred_by:
            cursor.execute('UPDATE users SET points = points + 20 WHERE user_id = ?', (referred_by,))
            if ADMIN_CHAT_ID != 0:
                try:
                    bot.send_message(ADMIN_CHAT_ID, f"🔗 **إحالة جديدة ناجحة!**\nالمستخدم الجديد انضم عبر رابط المستخدم: `{referred_by}`", parse_mode="Markdown")
                except:
                    pass
        conn.commit()
    conn.close()

    welcome_text = (
        "أهلاً بك في منصة الحلول الرقمية المتقدمة! 🌟\n\n"
        "أنا **سارة**، وكيلتك الرقمية للمبيعات وتطوير الأعمال.\n"
        "حصلت على **10 نقاط هدية** عند انضمامك! تصفح أقوى الأدوات والحزم الرقمية لمضاعفة إنتاجيتك ومبيعاتك.\n\n"
        "**كيف يمكنني خدمتك اليوم؟**"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(commands=['myid'])
def show_my_id(message):
    bot.reply_to(message, f"معرفك الشخصي (Admin ID) هو:\n`{message.from_user.id}`", parse_mode="Markdown")

# لوحة تحكم المشرف الشاملة
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "عذراً، هذا الأمر مخصص للمدير فقط.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(points) FROM users')
    total_points = cursor.fetchone()[0] or 0
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]
    conn.close()

    admin_text = (
        "📊 **لوحة تحكم المشرف الاحترافية (Enterprise Panel)**\n\n"
        f"• إجمالي عدد المستخدمين: **{total_users}**\n"
        f"• إجمالي نقاط الولاء الموزعة: **{total_points}**\n"
        f"• عدد المنتجات الرقمية: **{total_products}**\n\n"
        "اختر العملية المطلوبة أدناه:"
    )
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 إرسال إعلان لجميع المستخدمين", callback_data="admin_broadcast"))
    markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
    
    bot.send_message(message.chat.id, admin_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if call.data == "catalog":
        cursor.execute('SELECT product_id, name, price, description FROM products')
        products = cursor.fetchall()
        markup = InlineKeyboardMarkup()
        for prod in products:
            p_id, name, price, desc = prod
            markup.row(InlineKeyboardButton(f"📦 {name} (${price})", callback_data=f"buy_{p_id}"))
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🛒 **الكتالوج الرقمي الاحترافي المتاح:**\nاختر الحزمة أو المنتج للاطلاع على التفاصيل والشراء:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif call.data == "loyalty":
        user_id = call.from_user.id
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        points = result[0] if result else 0
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
        referral_count = cursor.fetchone()[0]

        bot_username = bot.get_me().username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"

        loyalty_text = (
            f"⭐ **محفظة الولاء والإحالات الخاصة بك**\n\n"
            f"• رصيد النقاط الحالي: **{points} نقطة**\n"
            f"• عدد الأشخاص الذين دعيتهم: **{referral_count} شخص** (+20 نقطة لكل إحالة!)\n\n"
            f"🔗 **رابط الإحالة الخاص بك:**\n`{referral_link}`\n\n"
            "🎁 **نظام المكافآت:**\n"
            "عند وصول رصيدك إلى **50 نقطة**، يمكنك استبدالها بقسيمة خصم بقيمة 5$!"
        )
        markup = InlineKeyboardMarkup()
        if points >= 50:
            markup.row(InlineKeyboardButton("🎁 استبدال 50 نقطة بخصم 5$", callback_data="redeem_points"))
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=loyalty_text,
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif call.data == "redeem_points":
        user_id = call.from_user.id
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        points = cursor.fetchone()[0]
        
        if points >= 50:
            cursor.execute('UPDATE users SET points = points - 50 WHERE user_id = ?', (user_id,))
            conn.commit()
            bot.answer_callback_query(call.id, "🎉 تهانينا! تم خصم 50 نقطة وإصدار كود الخصم.", show_alert=True)
            
            redeem_success_text = (
                "🎉 **مبروك! تم استبدال النقاط بنجاح**\n\n"
                "تم خصم 50 نقطة من محفظتك.\n"
                "🎟️ **كود الخصم الخاص بك:** `SARAH5OFF` (يمنحك خصماً بقيمة 5$ عند الشراء).\n\n"
                "استخدم هذا الكود عند الدفع لتخفيض السعر!"
            )
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 العودة لمحفظة الولاء", callback_data="loyalty"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=redeem_success_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "عذراً، رصيدك أقل من 50 نقطة.", show_alert=True)

    elif call.data.startswith("buy_"):
        product_id = call.data.split("_")[1]
        cursor.execute('SELECT name, price, description FROM products WHERE product_id = ?', (product_id,))
        prod = cursor.fetchone()
        if prod:
            name, price, desc = prod
            purchase_text = (
                f"🛍️ **تأكيد الطلب**\n\n"
                f"• المنتج: **{name}**\n"
                f"• السعر: **${price}**\n"
                f"• الوصف: {desc}\n\n"
                "💳 **طريقة الدفع (عبر Orange Money):**\n"
                "يرجى تحويل المبلغ إلى رقم المحفظة المعتمد، ثم إرسال **صورة إيصال التحويل (Screenshot)** هنا في المحادثة."
            )
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 العودة للكتالوج", callback_data="catalog"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=purchase_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
            cursor.execute('INSERT INTO orders (user_id, product_id, status) VALUES (?, ?, ?)', (call.from_user.id, product_id, 'pending'))
            conn.commit()
            order_id = cursor.lastrowid

            if ADMIN_CHAT_ID != 0:
                customer_name = call.from_user.first_name
                customer_username = f"@{call.from_user.username}" if call.from_user.username else "بدون معرف"
                alert_msg = (
                    "🔔 **إشعار طلب جديد وإيصال مطلوب مراجعته!**\n\n"
                    f"• العميل: {customer_name} ({customer_username})\n"
                    f"• المعرف: `{call.from_user.id}`\n"
                    f"• المنتج: **{name}** (${price})"
                )
                admin_markup = InlineKeyboardMarkup()
                admin_markup.row(InlineKeyboardButton("✅ تأكيد الدفع وإرسال المنتج", callback_data=f"approve_{order_id}_{call.from_user.id}_{product_id}"))
                
                try:
                    bot.send_message(ADMIN_CHAT_ID, alert_msg, parse_mode="Markdown", reply_markup=admin_markup)
                except:
                    pass

    elif call.data.startswith("approve_"):
        parts = call.data.split("_")
        order_id = parts[1]
        target_user_id = int(parts[2])
        target_product_id = parts[3]

        cursor.execute('SELECT name, file_url FROM products WHERE product_id = ?', (target_product_id,))
        prod_data = cursor.fetchone()
        if prod_data:
            p_name, p_file = prod_data
            try:
                bot.send_message(target_user_id, f"🎉 **تم تأكيد الدفع بنجاح!**\nإليك رابط تحميل منتجك الرقمي: **{p_name}**\n\n🔗 رابط التحميل/الملف: {p_file}", parse_mode="Markdown")
                bot.answer_callback_query(call.id, "✅ تم تأكيد الطلب وإرسال المنتج للعميل بنجاح!", show_alert=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + "\n\n✅ **[تم تأكيد الطلب وإرسال المنتج للعميل]**", parse_mode="Markdown")
            except Exception as e:
                bot.answer_callback_query(call.id, f"حدث خطأ أثناء الإرسال للعميل: {e}", show_alert=True)

    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id, "خاصية البث المباشر مفعلة. أرسل الأمر /broadcast متبوعاً بالرسالة.")

    elif call.data == "support":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💬 للإستفسارات الفورية والدعم، اكتب رسالتك هنا وسيتم تحويلها للإدارة.",
            reply_markup=markup
        )

    elif call.data == "main_menu":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أهلاً بك مجدداً في القائمة الرئيسية:",
            reply_markup=get_main_menu()
        )
    conn.close()

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        bot.reply_to(message, "يرجى كتابة النص بعد الأمر، مثل: `/broadcast عروض جديدة بانتظاركم!`", parse_mode="Markdown")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    all_users = cursor.fetchall()
    conn.close()

    success_count = 0
    for u in all_users:
        uid = u[0]
        try:
            bot.send_message(uid, f"📢 **إعلان هام:**\n\n{text_to_send}", parse_mode="Markdown")
            success_count += 1
        except:
            pass

    bot.reply_to(message, f"✅ تم إرسال الإعلان بنجاح إلى **{success_count}** مستخدم.")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_user_messages(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_CHAT_ID:
        return

    if ADMIN_CHAT_ID != 0:
        forward_text = (
            "📩 **إيصال دفع أو رسالة جديدة من عميل:**\n\n"
            f"• الاسم: {message.from_user.first_name}\n"
            f"• المعرف: `{user_id}`\n"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, forward_text, parse_mode="Markdown")
            bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "✅ تم استلام إيصالك أو رسالتك وتحويلها للإدارة بنجاح. سيتم إرسال المنتج فور التحقق!")
        except Exception as e:
            bot.reply_to(message, "عذراً حدث خطأ في إرسال الرسالة.")
    else:
        bot.reply_to(message, "شكراً لتواصلك معنا، تم استلام رسالتك.")

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Internal Server Error", 403

@app.route("/")
def index():
    return "Sarah Enterprise Bot Webhook is running perfectly!", 200

if __name__ == "__main__":
    railway_domain = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        webhook_url = f"https://{railway_domain}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
