from flask import Flask
import os
import threading
import time

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Бот работает!"

@app.route('/ping')
def ping():
    return "Pong!", 200

def start_bot():
    time.sleep(3)
    try:
        import bot
        bot.run_bot()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("❌ Нет токена!")
    else:
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
