import logging
import os
import asyncio
from datetime import datetime, timedelta
from difflib import get_close_matches
from fastapi import FastAPI, Request
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# === Configuration ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
DOMAIN = os.getenv("WEBHOOK_DOMAIN")  # e.g. https://yourapp.up.railway.app
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{DOMAIN}{WEBHOOK_PATH}"

# === Logging Setup ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === Telegram Bot App ===
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Welcome Message ===
WELCOME_MSG = """GOOD DAY ❤️\n\nWelcome to Primelogz support, how may we be of service to you..?\n\nFor any complaints or issues please send the following:\n\n1. Account/Logs details  \n2. Category of account on site  \n3. Screenrecord/Screenshot of the problem  \n\nWith these we will be able to respond to you accordingly. Thank you ✅"""

# === FAQ Responses ===
faq_data = {
    "how to reset password": "You can reset your password here: https://www.primelogz.com/auth/forget-password",
    "where is my order": "Track your order here: https://www.primelogz.com/orders",
    "how to fund": """**To fund your accounts simply go through the following procedures;**\n\n1. Login into your account if you don’t have one create before proceeding unto the next step.\n\n2. After logging click the icon with three dashes by your left and tap on add funds 👍\n\n3. You’ll be redirected to another page where you’d put in the amount you’d like to fund ✅\n\n4. Afterwards you’ll be taken to a different page where you can either select manual payment or online payment method\n\n6. Pick whichever you’d prefer and pay the exact amount shown on screen (For manual payment make sure to add the reference given to you)\n\n7. Now once all that is done your payment will be automatically added in a matter of seconds 💯\n\nIncase you still need some help or more assistance you can watch our tutorial on how to fund your acct below ⬇️\n\nhttps://t.me/Bigtunez1/39"""
}

# === Memory Store ===
seen_users = set()
active_chats = {}
pending_replies = {}

# === Handlers ===
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and responding.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    logger.info(f"/start used by {update.message.from_user.id}")
    await update.message.reply_text(WELCOME_MSG)

def make_faq():
    return "".join([f"• {q} — type '{q}' or use /chat" for q in faq_data.keys()])

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.message.reply_text(f"Here are the common FAQs you can ask about:\n\n{make_faq()}")
    logger.info(f"Sent FAQ list to {update.message.from_user.id}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    active_chats[user_id] = datetime.utcnow()
    await update.message.reply_text("✅ You are now connected to an admin. Please type your message.")
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"""👤 User @{update.message.from_user.username or user_id} has initiated a support chat.
Intent: manual_chat_request"""
    )
    await update.message.reply_text("✅ You are now connected to an admin. Please type your message.")
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"👤 User @{update.message.from_user.username or user_id} has initiated a support chat."
    )

async def stopchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    active_chats.pop(user_id, None)
    pending_replies.pop(user_id, None)
    await update.message.reply_text("👋 You have been disconnected from admin support. If you need further help later, feel free to use /chat to reconnect or check /faq for common solutions.")
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🔕 User @{update.message.from_user.username or user_id} has ended the support chat."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    user_id = update.message.from_user.id
    user_msg = update.message.text.lower()

    if active_chats.get(user_id):
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"""📨 Message from @{update.message.from_user.username or user_id}:
{update.message.text}""")
        pending_replies[user_id] = datetime.utcnow()
        return

    if user_id not in seen_users:
        seen_users.add(user_id)
        await update.message.reply_text(WELCOME_MSG)

    if all(keyword in user_msg for keyword in ["account", "category", "screen"]):
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"""🚨 Auto-escalated: @{update.message.from_user.username or user_id} provided details.
Intent: user_issue_details
Message: {update.message.text}"""
        )
        active_chats[user_id] = datetime.utcnow()
        pending_replies[user_id] = datetime.utcnow()
        await update.message.reply_text("✅ You have been connected to an admin. Please wait while they respond.")
        return

    match = get_close_matches(user_msg, faq_data.keys(), n=1, cutoff=0.5)
    if match:
        await update.message.reply_text(faq_data[match[0]], parse_mode="Markdown")
    else:
        await update.message.reply_text("I'm not sure how to answer that. Let me connect you with a support agent.")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"""🚨 User @{update.message.from_user.username or user_id} needs help:
{update.message.text}

Use /chat to begin chatting."""
        )
        active_chats[user_id] = datetime.utcnow()
        pending_replies[user_id] = datetime.utcnow()

    

async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    for user_id in active_chats:
        await context.bot.send_message(chat_id=user_id, text=f"💬 *Admin*: {update.message.text}", parse_mode="Markdown")
        pending_replies.pop(user_id, None)

# === Register Handlers ===
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("faq", faq))
telegram_app.add_handler(CommandHandler("chat", chat))
telegram_app.add_handler(CommandHandler("stopchat", stopchat))
telegram_app.add_handler(CommandHandler("ping", ping))
telegram_app.add_handler(MessageHandler(filters.TEXT & filters.Chat(chat_id=ADMIN_CHAT_ID), admin_message_handler))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Background Task for Unread Reminders and Auto-Close ===
async def notify_unread_messages():
    while True:
        now = datetime.utcnow()
        for user_id, timestamp in list(pending_replies.items()):
            if (now - timestamp) > timedelta(minutes=2):
                await telegram_app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⏰ Reminder: You have an unread message from user {user_id}.")
                pending_replies.pop(user_id)

        # Auto-close chats after 10 minutes of inactivity
        for user_id, timestamp in list(active_chats.items()):
            if isinstance(timestamp, datetime) and (now - timestamp) > timedelta(minutes=10):
                active_chats.pop(user_id)
                await telegram_app.bot.send_message(chat_id=user_id, text="⌛ Your support session has been automatically closed due to inactivity. Use /chat to reconnect anytime.")
                await telegram_app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🔒 Auto-closed chat with user {user_id} due to inactivity.")

        await asyncio.sleep(60)

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_my_commands([
        BotCommand("start", "🚀 Start support session"),
        BotCommand("faq", "📋 View frequently asked questions"),
        BotCommand("chat", "👤 Start human support (admin only)"),
        BotCommand("stopchat", "🔕 Stop human support (admin only)"),
        BotCommand("ping", "🧪 Test bot connection")
    ])
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(notify_unread_messages())
    logging.info("Bot webhook registered and ready.")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
