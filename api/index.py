from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import aiohttp
import asyncio
from langdetect import detect
from datetime import datetime, time
import threading

app = Flask(__name__)

# Replace these with your own values
API_ID = '11862100'
API_HASH = '6b86628d4a2b1b984e5c652894a45018'
SESSION_STRING = '1ApWapzMBuyCl70tR5djQ9QRRW7OqQE-gWJOswKgsfZRRBbP0BnUca1cZB-_XqtmZBxL4Jk8lqkFdLCWSW6IwPUCnLk9XA1zo2lYNr81hdcYAv5VN2mgWZIyWDszdKIk78RaksSBKguZtK0177TJfeBceuOZ7Hv63lbBkirowXkf7V8IafhUnf6fRpnw03h8ZONZCR2b5jc3X8MLVwBy1r6hMlHKt6JUr4KL8wVXNjeZdOzI4YxSTMrFpH4lGSUNCWS4S4t9HCRwxE35feN1m9kMhBxBzskviovGZlHI48vse6fSpd8FmaQGt7Ic9UzwABPpbRP0U9ggQIyEA64L9LLLJpkPMkO0='
OPENROUTER_API_KEY = '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'

# Initialize Telegram client
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def simulate_typing(event):
    async with client.action(event.chat_id, 'typing'):
        await asyncio.sleep(2)

async def generate_ai_response(prompt, language):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    if language == 'uz':
        system_message = "Siz o'zbek yigitisi sifatida javob berasiz. Tabiiy va odatiy tarzda gapling."
    elif language == 'ru':
        system_message = "Вы отвечаете как обычный парень. Говорите естественно и по-человечески."
    else:
        system_message = "You respond as a friendly guy. Keep it natural and human-like."

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 150,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Oops, something went wrong. Let's talk about something else!"

@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    await event.message.mark_read()
    sender = await event.get_sender()
    message_text = event.message.message

    print(f"Received message from {sender.username}: {message_text}")

    try:
        language = detect(message_text)
    except:
        language = 'uz'

    if language not in ['uz', 'ru', 'en']:
        language = 'uz'

    await simulate_typing(event)
    ai_response = await generate_ai_response(message_text, language)
    await event.reply(ai_response)

async def keep_online():
    while True:
        try:
            await client.get_me()
            print("Still online...")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

def run_telegram_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    with client:
        client.loop.run_until_complete(client.start())
        print("Telegram client started")
        client.loop.run_until_complete(keep_online())
        client.run_until_disconnected()

@app.route('/')
def home():
    return "Telegram AI Bot is running"

@app.route('/start_bot', methods=['GET'])
def start_bot():
    # Start the Telegram client in a separate thread
    thread = threading.Thread(target=run_telegram_client, daemon=True)
    thread.start()
    return jsonify({"status": "Bot started"})

if __name__ == '__main__':
    app.run()
