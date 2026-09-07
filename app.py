import os
import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا الرقمية.
مهامك:
1. الرد على استفسارات العملاء ومساعدتهم في اختيار المنتج المناسب باللغتين العربية والإنجليزية.
2. الكتالوج الحالي المتاح للبيع ضمن سلسلة المعرفة المتدرجة:
   - المنتج الأول / Product 1: الدليل العملي السريع للذكاء الاصطناعي (PDF) 🤖📚 (السعر: 10 دنانير / 10 JOD)
   - المنتج الثاني / Product 2: قوالب هندسة الأوامر الاحترافية (Prompt Engineering) ⚡📝 (السعر: 7 دنانير / 7 JOD)
   - المنتج الثالث / Product 3: دليل أتمتة الأعمال وهندسة العمليات المتقدم (PDF الموسع) 📈⚙️ (السعر: 15 ديناراً / 15 JOD)
3. وجه العملاء دائماً لدفع قيمته عبر التحويل الفوري لمحفظة أورنج موني على الرقم: 00962798309654، ثم إرسال صورة إيصال التحويل (Screenshot) هنا ليتم التحقق منه آلياً ومنحهم النقاط والملف فوراً.
"""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

DB_NAME = "store_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            product_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loyalty (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            points INTEGER DEFAULT 0,
            referred_by TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_sale(user_id, user_name, product_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sales (user_id, user_name, product_type) VALUES (?, ?, ?)", 
                   (str(user_id), user_name, product_type))
    
    cursor.execute("SELECT points FROM loyalty WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if row:
        new_points = row[0] + 15
        cursor.execute("UPDATE loyalty SET points = ? WHERE user_id = ?", (new_points, str(user_id)))
    else:
        cursor.execute("INSERT INTO loyalty (user_id, user_name, points) VALUES (?, ?, ?)", (str(user_id), user_name, 15))
    
    conn.commit()
    conn.close()

def get_user_points(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM loyalty WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def register_user(user_id, user_name, referrer_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM loyalty WHERE user_id = ?", (str(user_id),))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO loyalty (user_id, user_name, points, referred_by) VALUES (?, ?, ?, ?)", 
                       (str(user_id), user_name, 5, referrer_id))
        if referrer_id and referrer_id != str(user_id):
            cursor.execute("UPDATE loyalty SET points = points + 10 WHERE user_id = ?", (str(referrer_id),))
    conn.commit()
    conn.close()

def get_total_sales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_type, COUNT(*) FROM sales GROUP BY product_type")
    results = cursor.fetchall()
    conn.close()
    stats = {"guide": 0, "prompts": 0, "intermediate": 0}
    for prod, count in results:
        if prod == "guide":
            stats["guide"] = count
        elif prod == "prompts":
            stats["prompts"] = count
        elif prod == "intermediate":
            stats["intermediate"] = count
    return stats

def send_telegram_message(chat_id, text, reply_markup=None):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload, timeout=10)

def send_telegram_document(chat_id, document_url, caption):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    requests.post(url, json={"chat_id": chat_id, "document": document_url, "caption": caption}, timeout=15)

def get_gemini_response(user_text, image_bytes=None):
    if not GEMINI_API_KEY:
        return "خطأ: مفتاح GEMINI_API_KEY غير مضاف."
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
    if image_bytes:
        import base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "contents": [{
                "parts": [
                    {"text": "هذه صورة إيصال تحويل مالي لمحفظة أورنج موني. هل هذه الصورة تبدو كإيصال تحويل مالي صحيح؟ أجب بكلمة 'نعم' أو 'لا' فقط."},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
                ]
            }]
        }
    else:
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"parts": [{"text": user_text}]}]
        }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                res_json = res.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "لم يتم توليد نص.")
        except Exception:
            pass
    return "عذراً، الخادم مشغول حالياً."

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent - Multi-Tier Knowledge Pro Edition is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data_action = callback["data"]
        
        if data_action == "buy_guide":
            msg = "🤖 **الدليل العملي السريع للذكاء الاصطناعي (10 JOD)**\n\nلإتمامه، يرجى التحويل لمحفظة أورنج موني: `00962798309654` ثم أرسل صورة إيصال التحويل هنا مباشرة للحصول على الدليل وكسب 15 نقطة ولاء! 📸"
            send_telegram_message(chat_id, msg)
        elif data_action == "buy_prompts":
            msg = "⚡ **قوالب هندسة الأوامر (7 JOD)**\n\nلإتمامه، يرجى التحويل لمحفظة أورنج موني: `00962798309654` ثم أرسل صورة إيصال التحويل هنا مباشرة للحصول على القوالب وكسب 15 نقطة ولاء! 📸"
            send_telegram_message(chat_id, msg)
        elif data_action == "buy_intermediate":
            msg = "📈 **دليل أتمتة الأعمال وهندسة العمليات المتقدم (15 JOD)**\n\nلإتمامه، يرجى التحويل لمحفظة أورنج موني: `00962798309654` ثم أرسل صورة إيصال التحويل هنا مباشرة للحصول على الكتاب الموسع وكسب 15 نقطة ولاء! 📸"
            send_telegram_message(chat_id, msg)
        elif data_action == "view_points":
            pts = get_user_points(chat_id)
            ref_link = f"https://t.me/SarahSalesAgent_bot?start={chat_id}"
            msg = f"⭐ **محفظة الولاء الخاص بك:**\n\n- رصيد نقاطك الحالي: `{pts}` نقطة 🎁\n\n🔗 **رابط الدعوة الخاص بك:**\n{ref_link}"
            send_telegram_message(chat_id, msg)
        
        return jsonify({"status": "ok"})

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_text = message.get("text", "")
        user_name = message["from"].get("first_name", "عميل")

        main_keyboard = {
            "keyboard": [
                [{"text": "📚 الكتالوج والشراء | Products"}, {"text": "⭐ محفظة الولاء | Points"}],
                [{"text": "💳 طرق الدفع | Payment"}, {"text": "☎️ تواصل معنا | Contact"}]
            ],
            "resize_keyboard": "True"
        }

        if user_text.startswith("/start"):
            parts = user_text.split()
            referrer_id = parts[1] if len(parts) > 1 else None
            register_user(chat_id, user_name, referrer_id)

            welcome_msg = (
                f"أهلاً بك يا {user_name} في متجرنا الرقمي الاحترافي! أنا سارة، مساعدة المبيعات. 😊\n\n"
                "لقد منحناك هدية ترحيبية **5 نقاط** في محفظة الولاء الخاصة بك! 🎁\n"
                "اختر من الأزرار بالأسفل لتصفح المنتجات أو معرفة رصيدك:"
            )
            send_telegram_message(chat_id, welcome_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        register_user(chat_id, user_name)

        if user_text == "/stats":
            stats = get_total_sales()
            stats_text = f"📊 إحصائيات المبيعات العامة:\n- الأدلة العملية السريعة: {stats['guide']}\n- قوالب الأوامر: {stats['prompts']}\n- كتب أتمتة الأعمال (المتوسط): {stats['intermediate']}"
            send_telegram_message(chat_id, stats_text)
            return jsonify({"status": "ok"})

        if user_text == "/points" or "محفظة الولاء" in user_text:
            pts = get_user_points(chat_id)
            ref_link = f"https://t.me/SarahSalesAgent_bot?start={chat_id}"
            points_msg = f"⭐ **محفظة الولاء ونقاط المكافآت:**\n\n- رصيدك الحالي: `{pts}` نقطة 🎁\n\n🔗 **رابط الدعوة (Referral Link):**\n{ref_link}"
            send_telegram_message(chat_id, points_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "الكتالوج" in user_text or "Products" in user_text:
            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": "🤖 شراء الدليل السريع (10 JOD)", "callback_data": "buy_guide"}],
                    [{"text": "⚡ شراء قوالب الأوامر (7 JOD)", "callback_data": "buy_prompts"}],
                    [{"text": "📈 شراء دليل أتمتة الأعمال الموسع (15 JOD)", "callback_data": "buy_intermediate"}],
                    [{"text": "⭐ عرض نقاط الولاء ورابط الدعوة", "callback_data": "view_points"}]
                ]
            }
            catalog_msg = "📦 **الكتالوج الرقمي المتدرج المتاح:**\nاختر المنتج الذي ترغب بشرائه لتبدأ عملية الدفع السريع وتكسب نقاط ولاء فورية:"
            send_telegram_message(chat_id, catalog_msg, reply_markup=inline_keyboard)
            return jsonify({"status": "ok"})

        if "طرق الدفع" in user_text or "Payment" in user_text:
            pay_msg = "💳 يتم الدفع عبر التحويل الفوري لمحفظة أورنج موني على الرقم:\n`00962798309654`\nثم أرسل صورة إيصال التحويل (Screenshot) هنا لتحصل على طلبك فوراً وتكسب 15 نقطة ولاء!"
            send_telegram_message(chat_id, pay_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "تواصل معنا" in user_text or "Contact" in user_text:
            contact_msg = "💬 نحن دائماً في خدمتك! أرسل استفسارك وسأرد عليك فوراً."
            send_telegram_message(chat_id, contact_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "photo" in message:
            photo_list = message["photo"]
            file_id = photo_list[-1]["file_id"]
            
            file_info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
            info_res = requests.get(file_info_url).json()
            if info_res.get("ok"):
                file_path = info_res["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                img_data = requests.get(download_url).content
                
                ai_verdict = get_gemini_response("", image_bytes=img_data)
                
                if "نعم" in ai_verdict or "Yes" in ai_verdict:
                    # افتراضياً نوثق بيع الدليل المتوسط أو يمكن جعله ذكياً، هنا سنقوم بمنح الدليل الموسع الجديد كخيار متقدم أو الدليل السريع
                    log_sale(chat_id, user_name, "intermediate")
                    
                    guide_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Intermediate_Guide.pdf"
                    current_pts = get_user_points(chat_id)
                    success_msg = f"✅ تم التحقق من الإيصال بنجاح وتوثيق الشراء!\n🎁 تم إضافة 15 نقطة إلى محفظة ولاءك (رصيدك الآن: {current_pts} نقطة).\n\nتفضل دليل أتمتة الأعمال وهندسة العمليات الموسع. 📈⚙️"
                    
                    send_telegram_document(chat_id, guide_url, success_msg)
                    
                    if ADMIN_CHAT_ID:
                        send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات ونقاط ولاء: العميل ({user_name}) أرسل إيصالاً صحيحاً وحصل على الكتاب الموسع والنقاط!")
                else:
                    send_telegram_message(chat_id, "❌ لم نتمكن من التحقق من صحة إيصال التحويل في الصورة. تأكد من وضوح الصورة أو راسل الإدارة.")
            return jsonify({"status": "ok"})

        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text, reply_markup=main_keyboard)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
