import os
import sqlite3
from flask import Flask, render_template_string, request, jsonify
from google import genai

# قراءة مفتاح الـ API من متغيرات البيئة
API_KEY = os.environ.get("GEMINI_API_KEY")
DB_FILE = "digital_store_chat.db"

# --- 1. كتالوج المنتجات الرقمية ---
PRODUCTS_CATALOG = [
    {
        "id": "PROD-01",
        "title": "كتاب احتراف التسويق الرقمي (PDF)",
        "category": "كتّب إلكترونية",
        "price": "$19",
        "description": "دليل شامل يتضمن أسرار الحملات الإعلانية واستراتيجيات النمو وتنمية الأرباح.",
        "link": "https://your-store.com/checkout/marketing-ebook"
    },
    {
        "id": "PROD-02",
        "title": "دورة أساسيات الذكاء الاصطناعي (فيديو)",
        "category": "دورات تدريبية",
        "price": "$49",
        "description": "دورة عمليّة تشرح كيفية بناء أدوات وتطبيقات بالذكاء الاصطناعي من الصفر.",
        "link": "https://your-store.com/checkout/ai-course"
    }
]

# --- 2. إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO history (role, content) VALUES (?, ?)', (role, content))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT role, content FROM history ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def clear_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM history')
    conn.commit()
    conn.close()

app = Flask(__name__)

# --- 3. بناء تعليمات المساعد ---
def build_sales_agent_prompt(user_query, history):
    catalog_text = ""
    for p in PRODUCTS_CATALOG:
        catalog_text += f"- **{p['title']}** | الفئة: {p['category']} | السعر: {p['price']}\n  الوصف: {p['description']}\n  رابط الشراء: {p['link']}\n\n"

    system_instruction = f"""أنت "سارة"، وكيلة المبيعات الرقمية الذكية للمتجر.
مهمتك الترحيب بالعملاء وترشيح المنتجات الرقمية المتاحة ومساعدتهم في الوصول لرابط الشراء.

قائمة المنتجات:
{catalog_text}

قواعد الإجابة:
1. الإجابة بأسلوب محترف ومشجع.
2. توفير روابط الشراء المباشرة عند ترشيح أي منتج.
3. استخدام تنسيق Markdown للترتيب.
"""
    
    messages_payload = [system_instruction]
    for h in history[-6:]:
        role_label = "العميل" if h["role"] == "user" else "سارة"
        messages_payload.append(f"{role_label}: {h['content']}")
        
    messages_payload.append(f"العميل: {user_query}")
    messages_payload.append("سارة:")
    return "\n".join(messages_payload)

# --- 4. الواجهة البرمجية (API Routes) ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_history', methods=['GET'])
def get_chat_history():
    return jsonify(get_history())

@app.route('/clear_history', methods=['POST'])
def clear_chat_history():
    clear_db()
    return jsonify({'status': 'cleared'})

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.json.get('query', '')
    save_message('user', user_query)
    
    history = get_history()
    prompt = build_sales_agent_prompt(user_query, history)

    try:
        client = genai.Client(api_key=API_KEY.strip() if API_KEY else "")
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        reply_text = response.text
        save_message('bot', reply_text)
        return jsonify({'reply': reply_text})
    except Exception as e:
        error_msg = f"خطأ في الاتصال: {e}"
        save_message('bot', error_msg)
        return jsonify({'reply': error_msg})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>المتجر الرقمي</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 15px; }
        .container { max-width: 650px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 12px; }
        .header h2 { margin: 0; font-size: 18px; color: #38bdf8; }
        .clear-btn { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
        .chat-box { background: #1e293b; height: 380px; overflow-y: auto; padding: 15px; border-radius: 10px; margin-bottom: 12px; }
        .msg { margin-bottom: 12px; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.6; }
        .user { background: #0284c7; text-align: right; }
        .bot { background: #334155; text-align: right; }
        .bot a { color: #38bdf8; font-weight: bold; }
        .input-area { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; }
        button.send-btn { padding: 12px 20px; border: none; background: #10b981; color: white; border-radius: 8px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🛍️ مساعد المبيعات الرقمي</h2>
            <button class="clear-btn" onclick="clearHistory()">مسح السجل</button>
        </div>
        <div class="chat-box" id="chatBox"></div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="اسأل عن المنتجات..." onkeypress="if(event.key==='Enter') sendMsg()">
            <button class="send-btn" id="sendBtn" onclick="sendMsg()">إرسال</button>
        </div>
    </div>
    <script>
        window.onload = async function() {
            let res = await fetch('/get_history');
            let history = await res.json();
            let box = document.getElementById('chatBox');
            box.innerHTML = '';
            if(history.length === 0) {
                box.innerHTML = `<div class="msg bot"><b>سارة:</b> أهلاً بك! كيف يمكنني مساعدتك اليوم؟</div>`;
            } else {
                history.forEach(item => {
                    let parsed = typeof marked !== 'undefined' ? marked.parse(item.content) : item.content;
                    box.innerHTML += `<div class="msg ${item.role === 'user' ? 'user' : 'bot'}"><b>${item.role === 'user' ? 'أنت' : 'سارة'}:</b><br>${parsed}</div>`;
                });
            }
            box.scrollTop = box.scrollHeight;
        };

        async function sendMsg() {
            let input = document.getElementById('userInput');
            let box = document.getElementById('chatBox');
            let text = input.value.trim();
            if(!text) return;

            box.innerHTML += `<div class="msg user"><b>أنت:</b> ${text}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;

            try {
                let res = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: text})
                });
                let data = await res.json();
                let parsedReply = typeof marked !== 'undefined' ? marked.parse(data.reply) : data.reply;
                box.innerHTML += `<div class="msg bot"><b>سارة:</b><br>${parsedReply}</div>`;
            } catch (e) {
                box.innerHTML += `<div class="msg bot" style="color: #ef4444;"><b>خطأ:</b> تعذر الاتصال</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        async function clearHistory() {
            if(confirm("مسح السجل؟")) {
                await fetch('/clear_history', { method: 'POST' });
                location.reload();
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
