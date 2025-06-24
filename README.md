# 🤖 Telegram FAQ + Support Bot

This project is a **Telegram support bot** that answers frequently asked questions and auto-connects users to a human support agent when needed. Built with:

- `python-telegram-bot` (v20+ async)
- `FastAPI` (for webhook)
- Deployed on **Railway**
- Features automated session management, fuzzy matching for FAQs, and admin chat routing.

## 🚀 Features

- ✅ Welcomes users with a guided message
- 📋 Supports `/faq`, `/ping`, `/chat`, `/stopchat` commands
- 🤖 Auto-replies to common questions using fuzzy matching
- 🧠 Escalates to admin if no suitable answer is found
- 🔄 Allows direct admin-user communication
- 🕒 Auto-reminder if admin hasn't replied in 2 minutes
- ⏳ Auto-closes inactive chats after 10 minutes

## 🧾 Example Usage

**User**: `/start`  
**Bot**: Sends a welcome message with instructions.

**User**: _"How do I fund?"_  
**Bot**: Sends a predefined markdown guide.

**User**: _asks an unrecognized question_  
**Bot**: Escalates to admin + invites admin to reply directly.

## 📁 Project Structure

```
├── main.py              # Main bot + FastAPI logic
├── requirements.txt     # Python dependencies
├── Procfile             # For Railway deployment
├── .env                 # Environment config (not committed)
```

## ⚙️ Setup Instructions

### 1. Clone the project

```bash
git clone https://github.com/yourusername/telegram-faq-bot.git
cd telegram-faq-bot
```

### 2. Create `.env` file

```env
BOT_TOKEN=123456789:ABCdefGhIjkLmNoPQRstuVWXyz
ADMIN_CHAT_ID=123456789
WEBHOOK_DOMAIN=https://your-app-name.up.railway.app
```

> Use [@userinfobot](https://t.me/userinfobot) on Telegram to find your user ID.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Locally (optional, with ngrok)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Use a tool like [ngrok](https://ngrok.com/) to expose your local port:
```bash
ngrok http 8000
```

Set `WEBHOOK_DOMAIN=https://xxxx.ngrok.io` in your `.env`

### 5. Deploy on Railway

1. Push code to GitHub
2. Connect to Railway
3. Set the `.env` variables
4. Railway will detect the `Procfile` and run:
   ```bash
   web: uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 🔐 Telegram Bot Commands (Set via @BotFather)

```
start - 🚀 Start support session
faq - 📋 View frequently asked questions
chat - 👤 Connect to human support
stopchat - 🔕 Stop support chat
ping - 🧪 Test bot connection
```

## 🛠 Tech Stack

- `python-telegram-bot[fast]==20.6`
- `fastapi`
- `uvicorn`
- Deployed via Railway

## 🧠 To Do / Improvements

- [ ] Add database logging for chats
- [ ] Admin panel with chat history
- [ ] Rate limiting
- [ ] Satisfaction survey after chat

## 💬 Support

Having issues? Feel free to DM the admin in Telegram after typing `/chat` inside the bot.
