import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_LINK = os.getenv("WHATSAPP_LINK")

# Инициализация OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 Задать вопрос боту", callback_data="bot_chat")],
        [InlineKeyboardButton("👩‍⚕️ Хочу консультацию с врачом", callback_data="whatsapp")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "Привет! Я skin-бот 💆‍♀️\n"
        "Помогаю с уходом за кожей и подсказываю, как улучшить её состояние.\n\n"
        "📌 Консультация ознакомительная и не является лечением."
    )
    # Если update.message отсутствует (например, при вызове webhook),
    # можно проверить update.effective_message
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer(text=welcome_text)

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "bot_chat":
        await query.edit_message_text("Напишите ваш вопрос по уходу за кожей. Я постараюсь помочь 🧴")
        context.user_data["chat_mode"] = True
    elif query.data == "whatsapp":
        keyboard = [[InlineKeyboardButton("Перейти в WhatsApp", url=WHATSAPP_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "👩‍⚕️ Наш врач готов проконсультировать вас лично!\n"
            "Нажмите кнопку ниже и напишите в WhatsApp:",
            reply_markup=reply_markup
        )
        context.user_data["chat_mode"] = False

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("chat_mode"):
        return

    user_msg = update.message.text
    prompt = (
        "Ты — профессиональный косметолог. Отвечай только на вопросы по уходу за кожей. "
        "Если вопрос не по теме — скажи, что ты можешь говорить только о косметологии.\n"
        f"Вопрос: {user_msg}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка GPT: {e}")
        reply = "Упс, что-то пошло не так. Попробуйте позже."

    await update.message.reply_text(reply)

# Команда /done
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо, что обратились! Будьте красивы и здоровы 💖")

# Запуск с вебхуком
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url="https://bbac51afk9redqr4egbf.containers.yandexcloud.net/"
    )

if __name__ == "__main__":
    main()

