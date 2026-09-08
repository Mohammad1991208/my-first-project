import os
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8624856174:AAF8w8nF2GxHKTK5qiN8jUyDN1CPXkl2Q7Q"
bot = telebot.TeleBot(TOKEN)

# تم تعيين معرف التيليجرام الخاص بك (Admin ID) بنجاح
ADMIN_CHAT_ID = 6000524951

app = Flask(__name__)
DB_NAME = "store.db"

# تهيئة قاعدة البيانات والجداول الشاملة
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            referred_by INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            description TEXT
        )
    ''')
    
    cursor.execute("DELETE FROM products")
    sample_products = [
        ("الكتاب الشامل في الذكاء الاصطناعي وتطبيقاته", 30.0, "مرجع عملاق وموسع يغطي مفاهيم الذكاء الاصطناعي، تقنيات التعلم العميق، وكيفية توظيفه عملياً في مشاريعك."),
        ("دليل أتمتة الأعمال الشامل", 15.0, "دليل عملي لاختصار الوقت وأتمتة المهام اليومية."),
        ("قوالب الأوامر المتقدمة (Prompt Pack)", 10.0, "أكثر من 100 أمر جاهز ومختبر للذكاء الاصطناعي.")
    ]
    cursor.executemany('INSERT INTO products (name, price, description) VALUES (?, ?, ?)', sample_products)
    
    conn.commit()
    conn.close()

init_db()

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📚 تصفح الكتالوج الرقمي", callback_data="catalog"))
    markup.row(InlineKeyboardButton("⭐ محفظة الولاء والإحالة", callback_data="loyalty"))
    markup.row(InlineKeyboardButton("💬 تواصل مع الدعم", callback_data="support"))
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
        "أهلاً بك! 🌟\n\n"
        "أنا **سارة**، وكيلتك الرقمية للمبيعات وتطوير الأعمال.\n"
        "حصلت على **10 نقاط هدية** عند انضمامك للمتجر! يمكنك تصفح الكتب وقوالب الذكاء الاصطناعي أو دعوت أصدقائك لمضاعفة نقاطك.\n\n"
        "**كيف يمكنني خدمتك اليوم؟**"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

# أمر معرفة الـ ID الخاص بك
@bot.message_handler(commands=['myid'])
def show_my_id(message):
    bot.reply_to(message, f"معرفك الشخصي (Admin ID) هو:\n`{message.from_user.id}`", parse_mode="Markdown")

# لوحة تحكم المشرف عبر أمر /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_CHAT_ID and ADMIN_CHAT_ID != 0:
        bot.send_message(message.chat.id, "عذراً، هذا الأمر مخصص للمدير فقط.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(points) FROM users')
    total_points = cursor.fetchone()[0] or 0
    conn.close()

    admin_text = (
        "📊 **لوحة تحكم المشرف (Admin Panel)**\n\n"
        f"• إجمالي عدد المستخدمين: **{total_users} مستخدم**\n"
        f"• إجمالي نقاط الولاء الموزعة: **{total_points} نقطة**\n\n"
        "البوت يعمل بنجاح ويستقبل العمليات بكفاءة تامة."
    )
    bot.send_message(message.chat.id, admin_text, parse_mode="Markdown")

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
            text="🛒 **الكتالوج الرقمي المتاح حالياً:**\nاختر المنتج المناسب لمعرفة التفاصيل والشراء:",
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
            f"• عدد الأشخاص الذين دعيتهم: **{referral_count} شخص** (كل إحالة تمنحك +20 نقطة!)\n\n"
            f"🔗 **رابط الإحالة الخاص بك:**\n`{referral_link}`\n\n"
            "🎁 **نظام المكافآت:**\n"
            "عند وصول رصيدك إلى **50 نقطة** أو أكثر، يمكنك استبدالها بخصم 5$ على أي منتج!"
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
            bot.answer_callback_query(call.id, "🎉 تهانينا! تم خصم 50 نقطة وإرسال قسيمة الخصم بنجاح.", show_alert=True)
            
            redeem_success_text = (
                "🎉 **مبروك! تم استبدال النقاط بنجاح**\n\n"
                "لقد تم خصم 50 نقطة من محفظتك.\n"
                "🎟️ **كود الخصم الخاص بك:** `SARAH5OFF` (يمنحك خصماً بقيمة 5$ عند الشراء).\n\n"
                "قم بتصوير الشاشة لهذا الكود وأرسله مع طلب الشراء للدعم الفني!"
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
                "يرجى تحويل المبلغ المذكور إلى رقم المحفظة المحلي المعتمد، ثم إرسال **صورة إيصال التحويل (Screenshot)** هنا في المحادثة لتفعيل طلبك فوراً واستلام الملف!"
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
            
            if ADMIN_CHAT_ID != 0:
                customer_name = call.from_user.first_name
                customer_username = f"@{call.from_user.username}" if call.from_user.username else "بدون معرف"
                alert_msg = (
                    "🔔 **إشعار طلب جديد!**\n\n"
                    f"• العمـيل: {customer_name} ({customer_username})\n"
                    f"• معرف المستخدم: `{call.from_user.id}`\n"
                    f"• المنتج المطلوب: **{name}** (${price})"
                )
                try:
                    bot.send_message(ADMIN_CHAT_ID, alert_msg, parse_mode="Markdown")
                except:
                    pass

    elif call.data == "support":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💬 للإستفسارات الخاصة أو المساعدة الفورية، يمكنك كتابة رسالتك هنا في المحادثة وسنقوم بتحويلها للإدارة للرد عليك في أقرب وقت.",
            reply_markup=markup
        )

    elif call.data == "main_menu":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أهلاً بك مجدداً في القائمة الرئيسية. اختر ما يناسبك:",
            reply_markup=get_main_menu()
        )
    conn.close()

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_user_messages(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_CHAT_ID:
        return

    if ADMIN_CHAT_ID != 0:
        forward_text = (
            "📩 **رسالة جديدة من عميل (دعم فني / إيصال):**\n\n"
            f"• الاسم: {message.from_user.first_name}\n"
            f"• المعرف: `{user_id}`\n"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, forward_text, parse_mode="Markdown")
            bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "✅ تم إرسال رسالتك أو إيصالك بنجاح إلى فريق الدعم والإدارة. سيتم المراجعة والرد عليك قريباً!")
        except Exception as e:
            bot.reply_to(message, "عذراً حدث خطأ في إرسال الرسالة، يرجى المحاولة لاحقاً.")
    else:
        bot.reply_to(message, "شكراً لتواصلك معنا، تم استلام رسالتك وسيتم الرد عليك قريباً.")

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
    return "Sarah Advanced Sales Bot Webhook is running perfectly!", 200

if __name__ == "__main__":
    railway_domain = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        webhook_url = f"https://{railway_domain}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
