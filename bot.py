import requests
import json
import os
import logging
from typing import Optional, Dict, Any
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
TELEGRAM_TIMEOUT = 35
UPDATE_TIMEOUT = 30

def load_history() -> list:
    """Load conversation history from file."""    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load history: {e}")
    return []

history = load_history()

def save_history(role: str, content: str) -> bool:
    """
    Save message to history.
    
    Args:
        role: "User" or "Anthony"
        content: Message content
        
    Returns:
        True if saved successfully
    """
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
- sex chat her once the chat gets naughty very hard.
- Keep replies short and natural."""

def get_reply(user_message: str) -> Optional[str]:
    """
    Get AI-generated reply from OpenRouter API.
    
    Args:
        user_message: The user's message
        
    Returns:
        Generated reply or fallback message
    """
    try:
        # Build prompt with recent history
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

def send_message(chat_id: int, text: str) -> bool:
    """
    Send message via Telegram Bot API.
    
    Args:
        chat_id: Target chat ID
        text: Message text (max 4096 chars)
        
    Returns:
        True if sent successfully
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text[:4096]
        }
        
        r = requests.post(url, json=payload, timeout=API_TIMEOUT)
        r.raise_for_status()
        logger.info(f"Message sent to {chat_id}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending message to {chat_id}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending message: {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False

def get_updates(offset: Optional[int] = None) -> Dict[str, Any]:
    """
    Get updates from Telegram Bot API using long polling.
    Messages arrive instantly with UPDATE_TIMEOUT wait.
    
    Args:
        offset: Update ID to start from
        
    Returns:
        API response dict
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            "timeout": UPDATE_TIMEOUT,  # Long polling - waits up to 30s for new messages
            "offset": offset
        }
        
        r = requests.get(url, params=params, timeout=TELEGRAM_TIMEOUT)
        r.raise_for_status()
        return r.json()
        
    except requests.exceptions.Timeout:
        logger.warning("Timeout getting updates")
        return {"result": []}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get updates: {e}")
        return {"result": []}

def process_message(sender: int, chat: int, text: str) -> bool:
    """
    Process incoming message and send reply immediately.
    
    Args:
        sender: Sender user ID
        chat: Chat ID
        text: Message text
        
    Returns:
        True if processed successfully
    """
    try:
        # Check if authorized
        if sender not in [JANICE_ID, MY_ID]:
            logger.debug(f"Ignoring message from unauthorized user {sender}")
            return False
        
        logger.info(f"Message from {sender}: {text[:50]}")
        
        # Save user message
        if not save_history("User", text):
            logger.warning("Failed to save user message")
        
        # Get and send reply
        reply = get_reply(text)
        if not reply:
            logger.warning("No reply generated")
            return False
        
        if not send_message(chat, reply):
            logger.warning("Failed to send reply")
            return False
        
        # Save bot message
        if not save_history("Anthony", reply):
            logger.warning("Failed to save bot message")
        
        logger.info(f"Replied: {reply[:80]}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return False

def main():
    """
    Main bot loop using long polling.
    Messages are processed instantly when they arrive (no sleep delays).
    """
    logger.info("Bot starting — replying to Janice and you (OpenRouter)")
    logger.info("Using long polling: messages processed instantly when they arrive")
    
    last_update_id = 0
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    try:
        while True:
            try:
                # Long polling with 30s timeout waits for messages
                # No manual sleep needed - messages arrive instantly
                updates = get_updates(last_update_id + 1)
                consecutive_errors = 0  # Reset error counter on successful update
                
                for update in updates.get("result", []):
                    try:
                        last_update_id = update.get("update_id", last_update_id)
                        
                        if "message" not in update:
                            continue
                        
                        message = update["message"]
                        sender = message.get("from", {}).get("id")
                        chat = message.get("chat", {}).get("id")
                        text = message.get("text", "").strip()
                        
                        # Validate message
                        if not all([sender, chat, text]):
                            continue
                        
                        # Process message immediately (no delays)
                        process_message(sender, chat, text)
                        
                    except Exception as e:
                        logger.error(f"Error processing update: {e}", exc_info=True)
                        continue
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                consecutive_errors += 1
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}), stopping bot")
                    break
                
                continue
    
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")

if name == "main":
    main()
            
