from flask import Flask
import os
import threading
import time
import sys

app = Flask(__name__)

@app.route('/')
def health_check():
    return "🚕 Такси-Трекер бот работает!"

@app.route('/ping')
def ping():
    return "Pong!", 200

def start_bot():
    """Запускает бота в отдельном потоке"""
    time.sleep(2)
    try:
        # Импортируем и запускаем бота
        from bot import main
        main()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Проверяем токен
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")
        print("Добавьте её в настройках Render!")
        sys.exit(1)
    
    print("🚀 Запуск веб-сервера и бота...")
    
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
