import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# إعداد السجلات لمتابعة الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق الويب البسيط لإرضاء متطلبات البورت في Railway
app = Flask(__name__)

@app.route('/')
def home():
    return "Sarah Bot is active and running successfully!"

# دالة الاستجابة لأمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في عالم الحلول الرقمية الذكية! 🚀\n\n"
        "أنا سارة، مساعدتك الذكية لإدارة المنتجات الرقمية والطلبات."
    )

def main():
    # قراءة التوكن من متغيرات البيئة بأمان تام
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found in environment variables!")
        return

    # بناء تطبيق التيليجرام
    application = ApplicationBuilder().token(token).build()

    # إضافة الأوامر (مثل /start)
    application.add_handler(CommandHandler("start", start))

    # الحصول على البورت المخصص من Railway (أو استخدام 5000 محلياً)
    port = int(os.environ.get("PORT", 5000))

    logger.info("Starting bot and web server...")

    # تشغيل البوت بطريقة متوافقة (أو يمكنك ضبط الـ Webhook حسب إعداداتك السابقة)
    # ملاحظة: إذا كنت تستخدم Webhook، يتم ربطه هنا. وإذا كنت تستخدم Polling:
    application.run_polling()

if __name__ == '__main__':
    # ملاحظة: لتشغيل خادم الويب بجانب البوت في نفس الملف على Railway،
    # يُفضل عادةً تشغيل الويب في خلفية المنفذ أو الاعتماد على إعدادات الـ Start Command الصحيحة.
    main()
