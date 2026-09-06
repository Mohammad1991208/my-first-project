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
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
            color: #f8fafc; 
            margin: 0; 
            padding: 12px; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
        }
        .chat-container { 
            width: 100%; 
            max-width: 480px; 
            height: 90vh; 
            max-height: 680px; 
            background: #1e293b; 
            border-radius: 16px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); 
            display: flex; 
            flex-direction: column; 
            overflow: hidden; 
            border: 1px solid #334155; 
        }
        .chat-header { 
            padding: 16px; 
            background: #0f172a; 
            border-bottom: 1px solid #334155; 
            display: flex; 
            align-items: center; 
            justify-content: space-between;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .avatar { 
            width: 42px; 
            height: 42px; 
            background: linear-gradient(135deg, #38bdf8, #0284c7); 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 20px; 
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.3); 
        }
        .header-info h2 { margin: 0; font-size: 1.1rem; color: #38bdf8; }
        .header-info p { margin: 2px 0 0 0; font-size: 0.8rem; color: #94a3b8; }
        .clear-btn {
            background: transparent;
            border: 1px solid #475569;
            color: #94a3b8;
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        .clear-btn:hover { background: #334155; color: #f8fafc; }
        .chat-box { 
            flex: 1; 
            overflow-y: auto; 
            padding: 16px; 
            display: flex; 
            flex-direction: column; 
            gap: 12px; 
            background: #0f172a; 
            scroll-behavior: smooth; 
        }
        .msg { 
            padding: 12px 16px; 
            border-radius: 14px; 
            max-width: 85%; 
            line-height: 1.5; 
            font-size: 0.95rem; 
            word-break: break-word; 
            animation: fadeIn 0.3s ease-in-out; 
        }
        .msg p { margin: 0 0 8px 0; }
        .msg p:last-child { margin-bottom: 0; }
        .msg ul, .msg ol { margin: 4px 0; padding-right: 20px; }
        .user { 
            background: linear-gradient(135deg, #0284c7, #2563eb); 
            color: #ffffff; 
            align-self: flex-start; 
            border-bottom-right-radius: 4px; 
            box-shadow: 0 2px 5px rgba(2, 132, 199, 0.2); 
        }
        .bot { 
            background: #334155; 
            color: #f8fafc; 
            align-self: flex-end; 
            border-bottom-left-radius: 4px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
        }
        .typing-indicator { 
            display: none; 
            align-self: flex-end; 
            background: #334155; 
            padding: 10px 16px; 
            border-radius: 14px; 
            border-bottom-left-radius: 4px; 
        }
        .dots { display: flex; gap: 4px; align-items: center; }
        .dot { 
            width: 8px; 
            height: 8px; 
            background: #94a3b8; 
            border-radius: 50%; 
            animation: pulse 1.4s infinite ease-in-out; 
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        .input-container { 
            padding: 12px; 
            background: #1e293b; 
            border-top: 1px solid #334155; 
            display: flex; 
            gap: 8px; 
        }
        input { 
            flex: 1; 
            padding: 12px 14px; 
            border-radius: 10px; 
            border: 1px solid #475569; 
            background: #0f172a; 
            color: #fff; 
            font-size: 0.95rem; 
            outline: none; 
            transition: border-color 0.2s; 
        }
        input:focus { border-color: #38bdf8; }
        button.send-btn { 
            padding: 12px 20px; 
            background: linear-gradient(135deg, #10b981, #059669); 
            color: white; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 0.95rem; 
            transition: transform 0.1s; 
        }
        button.send-btn:active { transform: scale(0.96); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="header-left">
                <div class="avatar">👩💼</div>
                <div class="header-info">
                    <h2>سارة - مساعد المبيعات</h2>
                    <p>متصلة الآن لمساعدتك</p>
                </div>
            </div>
            <button class="clear-btn" onclick="clearHistory()">محادثة جديدة</button>
        </div>
        <div class="chat-box" id="chatBox">
            <div class="msg bot">أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟ 😊</div>
            <div class="typing-indicator" id="typingIndicator">
                <div class="dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>
        <div class="input-container">
            <input type="text" id="userInput" placeholder="اكتب سؤالك هنا..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button class="send-btn" onclick="sendMsg()">إرسال</button>
        </div>
    </div>
    <script>
        // حفظ سجل المحادثة في مصفوفة
        let chatHistory = [];

        async function sendMsg() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const typingIndicator = document.getElementById('typingIndicator');
            const text = input.value.trim();
            if(!text) return;

            // إدراج رسالة العميل
            const userDiv = document.createElement('div');
            userDiv.className = 'msg user';
            userDiv.innerText = text;
            chatBox.insertBefore(userDiv, typingIndicator);

            input.value = '';
            typingIndicator.style.display = 'block';
            chatBox.scrollTop = chatBox.scrollHeight;

            // إضافة رسالة المستخدم للسجل
            chatHistory.push({ role: "user", parts: [{ text: text }] });

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ history: chatHistory })
                });
                const data = await res.json();
                
                // إدراج رد سارة مع تنسيق Markdown
                const replyText = data.reply || data.error;
                const botDiv = document.createElement('div');
                botDiv.className = 'msg bot';
                botDiv.innerHTML = marked.parse(replyText);
                chatBox.insertBefore(botDiv, typingIndicator);

                // إضافة رد البوت للسجل
                if (data.reply) {
                    chatHistory.push({ role: "model", parts: [{ text: data.reply }] });
                }
            } catch(e) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'msg bot';
                errorDiv.style.color = '#ef4444';
                errorDiv.innerText = 'حدث خطأ في الاتصال، يرجى المحاولة مرة أخرى.';
                chatBox.insertBefore(errorDiv, typingIndicator);
            }

            typingIndicator.style.display = 'none';
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function clearHistory() {
            chatHistory = [];
            const chatBox = document.getElementById('chatBox');
            const typingIndicator = document.getElementById('typingIndicator');
            chatBox.innerHTML = '<div class="msg bot">أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟ 😊</div>';
            chatBox.appendChild(typingIndicator);
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
    history = request.json.get('history', [])
    if not history:
        return jsonify({'error': 'الرسالة فارغة'}), 400
    try:
        # إرسال السجل الكامل مع تعليمات النظام
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=history,
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'error': f"خطأ: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
