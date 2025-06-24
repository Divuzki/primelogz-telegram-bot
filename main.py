import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from difflib import get_close_matches
from datetime import datetime, timedelta
import asyncio
import os

# === Logging Setup ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Configuration ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# === Welcome Message ===
WELCOME_MSG = """GOOD DAY ❤️\n\nWelcome to Primelogz support, how may we be of service to you..?\n\nFor any complaints or issues please send the following:\n\n1. Account/Logs details  \n2. Category of account on site  \n3. Screenrecord/Screenshot of the problem  \n\nWith these we will be able to respond to you accordingly. Thank you ✅"""

# === FAQ Responses ===
faq_data = {
    "how to reset password": "You can reset your password here: https://example.com/reset",
    "where is my order": "Track your order here: https://example.com/orders",
    "how to fund": """**To fund your accounts simply go through the following procedures;**\n\n1. Login into your account if you don’t have one create before proceeding unto the next step.\n\n2. After logging click the icon with three dashes by your left and tap on add funds 👍\n\n3. You’ll be redirected to another page where you’d put in the amount you’d like to fund ✅\n\n4. Afterwards you’ll be taken to a different page where you can either select manual payment or online payment method\n\n6. Pick whichever you’d prefer and pay the exact amount shown on screen (For manual payment make sure to add the reference given to you)\n\n7. Now once all that is done your payment will be automatically added in a matter of seconds 💯\n\nIncase you still need some help or more assistance you can watch our tutorial on how to fund your acct below ⬇️\n\nhttps://t.me/Bigtunez1/39"""
}

# === Memory Store for Seen Users and Active Chats ===
seen_users = set()
active_chats = {}  # user_id: True if in human chat mode
pending_replies = {}  # user_id: timestamp of last unanswered message

# === /start Command Handler ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start used by {update.message.from_user.id}")
    await update.message.reply_text(WELCOME_MSG)

# === /faq Command Handler ===
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_list = "\n\n".join([f"• {q}" for q in faq_data.keys()])
    await update.message.reply_text(f"Here are the common FAQs you can ask about:\n\n{faq_list}")
    logger.info(f"Sent FAQ list to {update.message.from_user.id}")

# === /chat Command ===
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        active_chats[user_id] = True
        await update.message.reply_text(f"Chat started with user {user_id}. Use /stopchat {user_id} to end it.")
        logger.info(f"Admin started chat with user {user_id}")
    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        await update.message.reply_text("Usage: /chat <user_id>")

# === /stopchat Command ===
async def stopchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        active_chats.pop(user_id, None)
        pending_replies.pop(user_id, None)
        await update.message.reply_text(f"Chat ended with user {user_id}.")
        logger.info(f"Admin stopped chat with user {user_id}")
    except Exception as e:
        logger.error(f"Error in /stopchat: {e}")
        await update.message.reply_text("Usage: /stopchat <user_id>")

# === Main User Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_msg = update.message.text
    logger.info(f"Message from {user_id}: {user_msg}")

    if user_id not in seen_users:
        seen_users.add(user_id)
        await update.message.reply_text(WELCOME_MSG)
        logger.info(f"Sent welcome message to {user_id}")

    if active_chats.get(user_id):
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"📨 Message from @{update.message.from_user.username or user_id}:\n{user_msg}"
        )
        pending_replies[user_id] = datetime.utcnow()
        logger.info(f"Forwarded message to admin from {user_id}")
        return

    # Try to answer with FAQ
    questions = list(faq_data.keys())
    match = get_close_matches(user_msg.lower(), questions, n=1, cutoff=0.5)

    if match:
        await update.message.reply_text(faq_data[match[0]], parse_mode="Markdown")
        logger.info(f"Answered FAQ for {user_id}: {match[0]}")
    else:
        await update.message.reply_text("I'm not sure how to answer that. Let me connect you with a support agent.")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🚨 User @{update.message.from_user.username or user_id} needs help:\n{user_msg}\n\nUse /chat {user_id} to begin chatting."
        )
        active_chats[user_id] = True
        pending_replies[user_id] = datetime.utcnow()
        logger.warning(f"Escalated user {user_id} to human support")

# === Admin Message Forwarder ===
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    for user_id in active_chats:
        await context.bot.send_message(chat_id=user_id, text=f"Support: {update.message.text}")
        pending_replies.pop(user_id, None)
        logger.info(f"Admin message sent to user {user_id}")

# === Background Task for Unread Message Reminders ===
async def notify_unread_messages(app):
    while True:
        now = datetime.utcnow()
        for user_id, timestamp in list(pending_replies.items()):
            if (now - timestamp) > timedelta(minutes=2):
                await app.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"⏰ Reminder: You have an unread message from user {user_id} pending response."
                )
                pending_replies.pop(user_id)
                logger.warning(f"Sent unread reminder for user {user_id}")
        await asyncio.sleep(60)

# === Run Bot with Async Main ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("faq", faq))
app.add_handler(CommandHandler("chat", chat))
app.add_handler(CommandHandler("stopchat", stopchat))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(MessageHandler(filters.TEXT & filters.Chat(chat_id=ADMIN_CHAT_ID), admin_message_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and responding.")
    logger.info(f"Ping received from {update.message.from_user.id}")

async def main():
    await app.initialize()
    await app.bot.set_my_commands([
        BotCommand("start", "🚀 Start support session"),
        BotCommand("faq", "📋 View frequently asked questions"),
        BotCommand("chat", "👤 Start human support (admin only)"),
        BotCommand("stopchat", "🔕 Stop human support (admin only)")
    ])
    asyncio.create_task(notify_unread_messages(app))
    logger.info("Bot started and polling")
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
