import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from agent_core.engine.runner import run_task

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = (
        f"Hello! I am your IT Support Agent.\n"
        # We show the ID so the user knows what ID to whitelist later
        f"Your Telegram ID is: `{user_id}`\n\n"
        f"Send me any task and I will perform it on the Admin Panel."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ── Security Implication Placeholder ──
    # To implement allowed users later, you would do something like this:
    # allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
    # allowed_users = [int(u.strip()) for u in allowed_users_str.split(",") if u.strip()]
    # if allowed_users and user_id not in allowed_users:
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text="Unauthorized access.")
    #     return

    task_text = update.message.text
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"⚙️ Processing task: '{task_text}'..."
    )
    
    try:
        # We explicitly set headed=False because this runs completely in the background via Telegram
        result = await run_task(task_text, url="http://localhost:8000/", headed=False, max_steps=40)
        
        if not result:
            result = "Task finished but returned no specific summary."
            
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"✅ Task Completed!\n\n**Result:**\n{result}"
        )
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"❌ An error occurred while processing the task:\n\n{str(e)}"
        )

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is missing from .env")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Telegram IT Support Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
