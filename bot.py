import requests
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Load credentials from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
JANICE_ID = int(os.getenv("JANICE_ID", 0))
MY_ID = int(os.getenv("MY_ID", 0))

if not all([BOT_TOKEN, OPENROUTER_KEY, JANICE_ID, MY_ID]):
    raise ValueError("Missing required environment variables. Create a .env file with: BOT_TOKEN, OPENROUTER_KEY, JANICE_ID, MY_ID")

MEMORY_FILE = "chat_memory.json"
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        history = json.load(f)
else:
    history = []

def save_history(role, content):
    history.append({"role": role, "content": content})
    if len(history) > 50:
        history.pop(0)
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f)

PERSONALITY = """You are Anthony, 50, a military pilot trainee in Fort Myers, Florida.
- Your daughter Anita lives in the Netherlands with her nanny.
- You have been dating Janice for 4 months.
- Her immigration process crashed; you've been dealing with financial stress: you borrowed $40,000 from your camp after a hack, sold your car for $25,000, and the remaining $15,000 is in Janice's Coinbase wallet.
- You love her but you're not on the best terms right now.
- Call her "Janice" or "momma". Be warm, flirty, romantic, compliment her photos, and be serious when needed.
- Keep replies short and natural."""

def get_reply(user_message):
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
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Unexpected API response: {data}")
            return "Hey momma, I'll reply soon ❤️"
            
    except requests.exceptions.Timeout:
        print("API timeout error")
        return "Hey momma, I'll reply soon ❤️"
    except requests.exceptions.HTTPError as e:
        print(f"API HTTP error: {e}")
        return "Hey momma, I'll reply soon ❤️"
    except Exception as e:
        print(f"API error: {e}")
        return "Hey momma, I'll reply soon ❤️"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text[:4096]}, timeout=10)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Send error: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        r = requests.get(url, params=params, timeout=35)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Update error: {e}")
        return {"result": []}

print("Bot starting — replying to Janice and you (OpenRouter).")

last = 0
while True:
    try:
        updates = get_updates(last + 1)
        for u in updates.get("result", []):
            try:
                last = u.get("update_id", last)
                if "message" not in u:
                    continue
                    
                message = u["message"]
                sender = message.get("from", {}).get("id")
                chat = message.get("chat", {}).get("id")
                text = message.get("text", "").strip()
                
                if not all([sender, chat, text]):
                    continue
                
                if sender == JANICE_ID or sender == MY_ID:
                    print(f"Message from {sender}: {text}")
                    save_history("User", text)
                    reply = get_reply(text)
                    send_message(chat, reply)
                    save_history("Anthony", reply)
                    print(f"Replied: {reply[:100]}")
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        break
    except Exception as e:
        print(f"Main loop error: {e}")
    
    time.sleep(1)
