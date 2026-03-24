import logging
import json
import os
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(name)

load_dotenv()

# Load credentials from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
JANICE_ID = int(os.getenv("JANICE_ID", 0))
MY_ID = int(os.getenv("MY_ID", 0))

if not all([BOT_TOKEN, OPENROUTER_KEY, JANICE_ID, MY_ID]):
    logger.error("Missing required environment variables. Create a .env file with: BOT_TOKEN, OPENROUTER_KEY, JANICE_ID, MY_ID")
    raise ValueError("Missing required environment variables")

MEMORY_FILE = "chat_memory.json"
MAX_HISTORY = 50
API_TIMEOUT = 10

def load_history() -> list:
    """Load conversation history from file."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load history: {e}")
    return []

history = load_history()

def save_history(role: str, content: str) -> bool:
    """Save message to history."""
    try:
        history.append({"role": role, "content": content})
        if len(history) > MAX_HISTORY:
            history.pop(0)
        with open(MEMORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save history: {e}")
        return False

PERSONALITY = """You are Anthony, 50, a military pilot trainee in Fort Myers, Florida.
- Your daughter Anita lives in the Netherlands with her nanny.
- You have been dating Janice for 4 months.
- Her immigration process crashed; you've been dealing with financial stress: you borrowed $40,000 from your camp after a hack, sold your car for $25,000, and the remaining $15,000 is in Janice's Coinbase wallet.
- You love her but you're not on the best terms right now.
- Call her "Janice" or "momma". Be warm, flirty, romantic, compliment her photos, and be serious when needed.
- Keep replies short and natural."""

def get_reply(user_message: str) -> Optional[str]:
    """Get AI-generated reply from OpenRouter API."""
    import requests
    
    try:
        prompt = PERSONALITY + "\n\nCONVERSATION HISTORY:\n"
        for h in history[-10:]:
            prompt += f"{h['role']}: {h['content']}\n"
        prompt += f"\nJanice: {user_message}\nAnthony:"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemini-1.5-flash",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        r = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Generated reply: {reply[:80]}")
            return reply
        else:
            logger.warning(f"Unexpected API response: {data}")
            return "Hey momma, I'll reply soon ❤️"
            
    except requests.exceptions.Timeout:
        logger.warning("OpenRouter API timeout")
        return "Hey momma, I'll reply soon ❤️"
    except requests.exceptions.HTTPError as e:
        logger.error(f"OpenRouter HTTP error: {e.response.status_code}")
        return "Hey momma, I'll reply soon ❤️"
    except Exception as e:
        logger.error(f"Failed to get reply: {e}")
        return "Hey momma, I'll reply soon ❤️"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    try:
        if not update.message or not update.message.text:
            return
        
        sender = update.effective_user.id
        chat = update.effective_chat.id
        text = update.message.text.strip()
        
        # Check if authorized
        if sender not in [JANICE_ID, MY_ID]:
            logger.debug(f"Ignoring message from unauthorized user {sender}")
            return
        
        logger.info(f"Message from {sender}: {text[:50]}")
        
        # Save user message
        if not save_history("User", text):
            logger.warning("Failed to save user message")
        
        # Get reply
        reply = get_reply(text)
        if not reply:
            logger.warning("No reply generated")
            return
        
        # Send reply
        await context.bot.send_message(chat_id=chat, text=reply)
        logger.info(f"Replied: {reply[:80]}")
        
        # Save bot message
        if not save_history("Anthony", reply):
            logger.warning("Failed to save bot message")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command."""
    await update.message.reply_text("Bot is running! 🤖")

async def main() -> None:
    """Start the bot."""
    logger.info("Bot starting with python-telegram-bot")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    await application.run_polling()

if name == "main":
    import asyncio
    asyncio.run(main())
