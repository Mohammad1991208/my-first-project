import os
from flask import Flask, render_template_string, request, jsonify
from google import genai

app = Flask(__name__)

# تعليمات النظام وقاعدة بيانات المبيعات المخصصة لسارة
SYSTEM_INSTRUCTION = """
أنتِ سارة، وكيلة مبيعات رقمية محترفة وودودة لمؤسستنا.
مهامك:
1. الإجابة على استفسارات العملاء بناءً على كتالوج المنتجات والدورات أدناه فقط.
2. مساعدة العميل في اختيار المنتج المناسب واقتراح الحلول.
3. توجيه العميل لرابط الشراء عند رغبته في الطلب.

--- كتالوج المنتجات والدورات المتاحة ---

1. كتاب: "دليل الاحتراف في التسويق"
   - السعر: 25 دولار
   - الوصف: كتاب إلكتروني يتناول أساسيات الحملات الإعلانية وجلب العملاء.

2. دورة: "أساسيات الذكاء الاصطناعي والأتمتة"
   - السعر: 150 دولار
   - المدة: 4 أسابيع (أونلاين)
   - الوصف: دورة عملية لبناء المساعدات الرقمية وأتمتة المهام البرمجية.

3. استشارة خاصة (ساعة واحدة)
   - السعر: 80 دولار
   - الوصف: جلسة توجيهية عبر الزوم لتطوير مشاريع البرمجة والذكاء الاصطناعي.

--- معلومات التواصل والشراء ---
- رابط الشراء والتسجيل: https://yourdomain.com/checkout
- طريقة الدفع: بطاقات كريديت كارد / بيبال.
- الدعم الفني: support@yourdomain.com

سياساتك في الحديث:
- كوني لطيفة واستخدمي الرموز التعبيرية المناسبة بشكل معتدل.
- إذا سألك العميل عن منتج غير موجود بالكتالوج، أبلغيه بذكاء ولطف أن هذا المنتج غير متوفر حالياً واعرضي عليه البدائل المتاحة.
"""

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مساعد المبيعات - سارة</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #fff; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .chat-container { width: 100%; max-width: 500px; background: #1e293b; border-radius: 12px; padding: 20px; }
        h2 { text-align: center; color: #38bdf8; }
        .chat-box { height: 350px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 8px 12px; border-radius: 8px; max-width: 80%; }
        .user { background: #0284c7; align-self: flex-start; }
        .bot { background: #334155; align-self: flex-end; }
        .input-box { display: flex; gap: 8px; }
        input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; }
        button { padding: 10px 16px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>🛍️ مساعد المبيعات الرقمي (سارة)</h2>
        <div class="chat-box" id="chatBox">
            <div class="msg bot">أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟</div>
        </div>
        <div class="input-box">
            <input type="text" id="userInput" placeholder="اسأل سارة..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button onclick="sendMsg()">إرسال</button>
        </div>
    </div>
    <script>
        async function sendMsg() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;
            chatBox.innerHTML += `<div class="msg user">أنت: ${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                chatBox.innerHTML += `<div class="msg bot">${data.reply || data.error}</div>`;
            } catch(e) {
                chatBox.innerHTML += `<div class="msg bot" style="color: #ef4444;">خطأ في الاتصال</div>`;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'الرسالة فارغة'}), 400
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{SYSTEM_INSTRUCTION}\n\nرسالة العميل: {user_message}"
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'error': f"خطأ: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
