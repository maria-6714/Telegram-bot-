# Telegram Bot - Anthony

A Telegram bot that auto-replies to messages using OpenRouter AI (Google Gemini).

## Features

- ✅ Auto-replies to messages from authorized users only
- ✅ Uses Google Gemini AI for intelligent responses
- ✅ Maintains conversation history (last 50 messages)
- ✅ Runs 24/7 on Render
- ✅ Instant message processing (no delays)
- ✅ Error handling and logging

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- OpenRouter API Key
- Telegram User IDs (for authorized users)

### Local Installation

1. Clone the repository:
git clone https://github.com/maria-6714/Telegram-bot-.git
cd Telegram-bot-
2. Create a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Create .env file in the root directory:
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_KEY=your_openrouter_api_key
JANICE_ID=janice_telegram_user_id
MY_ID=your_telegram_user_id
4. Install dependencies:
pip install -r requirements.txt
5. Run the bot locally:
python bot.py
## Getting Your IDs

### BOT_TOKEN
1. Open Telegram
2. Search for @BotFather
3. Send /start
4. Follow instructions to create a new bot
5. Copy the token he provides

### OPENROUTER_KEY
1. Go to https://openrouter.ai
2. Sign up/Login
3. Go to Settings → API Keys
4. Create an API key
5. Copy it

### JANICE_ID & MY_ID (Telegram User IDs)
1. Start a conversation with your bot on Telegram
2. Send any message to the bot
3. Open this URL in your browser:
https://api.telegram.org/bot{BOT_TOKEN}/getUpdates
4. Replace {BOT_TOKEN} with your actual bot token
5. Look for "id": XXXXX in the response
6. That's the user ID

## Deployment on Render

### Step 1: Push to GitHub
git add .
git commit -m "Deploy to Render"
git push origin main
### Step 2: Create on Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Background Worker"
3. Connect your GitHub repository
4. Fill in:
   - Name: telegram-bot
   - Runtime: Python
   - Build Command: pip install -r requirements.txt
   - Start Command: python bot.py

### Step 3: Add Environment Variables
Click "Advanced" and add:
- BOT_TOKEN = your telegram bot token
- OPENROUTER_KEY = your openrouter api key
- JANICE_ID = janice's telegram user id
- MY_ID = your telegram user id

### Step 4: Deploy
Click "Create Web Service" and your bot will start running! 🚀

## How It Works

1. Bot connects to Telegram using long polling
2. Listens for messages from authorized users (JANICE_ID, MY_ID)
3. Sends message to OpenRouter AI API
4. Receives AI-generated reply
5. Sends reply back to Telegram
6. Saves conversation history locally

## Files Explained

| File | Purpose |
|------|---------|
| bot.py | Main bot code |
| requirements.txt | Python dependencies |
| render.yaml | Render deployment config |
| .env | Environment variables (not tracked by Git) |
| .gitignore | Files to hide from GitHub |
| chat_memory.json | Conversation history (auto-created) |

## Logs and Debugging

### On Render:
1. Go to your service dashboard
2. Scroll to "Logs" section
3. View real-time logs of your bot

### Locally:
tail -f bot.log
## Troubleshooting

### Bot not responding?
- Check BOT_TOKEN is correct
- Check user IDs (JANICE_ID, MY_ID) match
- Check Render logs for errors
- Verify OpenRouter API key is valid

### API errors?
- Check your OpenRouter account has credits
- Verify API key is correct
- Check internet connection

## License

Private Repository

## Support

For issues, check the logs on Render or run locally for debugging.
