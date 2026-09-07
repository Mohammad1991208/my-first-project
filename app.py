import os
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# إعدادات البوت والاتصال بقاعدة البيانات
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

DB_NAME = "store.db"

# تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة
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
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("دليل أتمتة الأعمال الشامل", 15.0, "دليل عملي لاختصار الوقت وأتمتة المهام اليومية."),
            ("قوالب الأوامر المتقدمة (Prompt Pack)", 10.0, "أكثر من 100 أمر جاهز ومختبر للذكاء الاصطناعي."),
            ("استشارة رقمية خاصة", 25.0, "جلسة استشارية وتوجيهية لتطوير مشروعك الرقمي.")
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
        conn.commit()

    conn.close()

    welcome_text = (
        "أهلاً بك! 🌟\n\n"
        "أنا **سارة**، وكيلتك الرقمية للمبيعات وتطوير الأعمال.\n"
        "سعيد بوجودك هنا! أساعدك في الوصول إلى أقوى الأدلة الرقمية، وقوالب أوامر الذكاء الاصطناعي، وأدوات أتمتة الأعمال التي توفر عليك وقتاً وجهداً كبيراً.\n\n"
        "**كيف يمكنني خدمتك اليوم؟** يمكنك اختيار أحد الخيارات التالية من القائمة أدناه، أو مراسلتنا في أي وقت! 🚀"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

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
        
        bot_username = bot.get_me().username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"

        loyalty_text = (
            f"⭐ **محفظة الولاء الخاصة بك**\n\n"
            f"• رصيد النقاط الحالي: **{points} نقطة**\n\n"
            f"🔗 **رابط الإحالة الخاص بك:**\n`{referral_link}`\n\n"
            "قم بمشاركة هذا الرابط مع أصدقائك، واكسب نقاطاً وعروضاً حصرية عند انضمامهم للمتجر!"
        )
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=loyalty_text,
            parse_mode="Markdown",
            reply_markup=markup
        )

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

    elif call.data == "support":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💬 للإستفسارات الخاصة أو المساعدة الفورية، يمكنك كتابة رسالتك هنا وسنقوم بالرد عليك في أقرب وقت.",
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

if __name__ == "__main__":
    print("Sarah Sales Bot is running with polling...")
    bot.infinity_polling()
