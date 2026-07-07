import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== ТОКЕН БЕРЁМ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (БЕЗОПАСНО!) ==========
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ Токен не найден! Установите TELEGRAM_BOT_TOKEN в переменных окружения.")

# ========== ДАННЫЕ ==========
DATA_FILE = "taxi_data.json"
PARTS_FILE = "parts_config.json"

DEFAULT_PARTS = {
    "масло": {"km": 10000, "days": 180},
    "масляный фильтр": {"km": 10000, "days": 180},
    "воздушный фильтр": {"km": 15000, "days": 365},
    "топливный фильтр": {"km": 30000, "days": 365},
    "ремень ГРМ": {"km": 60000, "days": 1095},
    "тормозные колодки": {"km": 25000, "days": 365},
    "тормозные диски": {"km": 50000, "days": 730},
    "свечи зажигания": {"km": 30000, "days": 365},
    "охлаждающая жидкость": {"km": 60000, "days": 730},
    "трансмиссионное масло": {"km": 60000, "days": 1095},
}

def load_json(file, default):
    return json.load(open(file, "r", encoding="utf-8")) if os.path.exists(file) else default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_data():
    return load_json(DATA_FILE, {})

def get_parts():
    return load_json(PARTS_FILE, DEFAULT_PARTS.copy())

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🚗 Добавить машину", callback_data="add_car")],
        [InlineKeyboardButton("🔧 Добавить запчасть", callback_data="add_part")],
        [InlineKeyboardButton("📋 Список запчастей", callback_data="list_parts")],
        [InlineKeyboardButton("🛞 Добавить замену", callback_data="add_event")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("🚕 Мои машины", callback_data="my_cars")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚕 **Такси-Трекер**\n\n"
        "Я помогаю отслеживать замены запчастей.\n"
        "Выбирай действие по кнопкам:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = get_data()
    parts = get_parts()

    if query.data == "back":
        await query.edit_message_text("🚕 Главное меню", reply_markup=main_menu())
        return

    # Добавить машину
    if query.data == "add_car":
        context.user_data['action'] = 'add_car'
        await query.edit_message_text("🚗 Введите госномер машины:", reply_markup=back_button())
        return

    # Добавить запчасть
    if query.data == "add_part":
        context.user_data['action'] = 'add_part_name'
        await query.edit_message_text("🔧 Введите название запчасти:", reply_markup=back_button())
        return

    # Список запчастей
    if query.data == "list_parts":
        text = "📋 **Запчасти:**\n\n"
        for part, vals in parts.items():
            km = f"{vals['km']} км" if vals['km'] > 0 else "—"
            days = f"{vals['days']} дн" if vals['days'] > 0 else "—"
            text += f"• **{part}** — пробег: {km}, время: {days}\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button())
        return

    # Добавить замену
    if query.data == "add_event":
        if not data:
            await query.edit_message_text("❌ Сначала добавьте машину!", reply_markup=main_menu())
            return
        context.user_data['action'] = 'select_car'
        keyboard = [[InlineKeyboardButton(plate, callback_data=f"car_{plate}")] for plate in data.keys()]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        await query.edit_message_text("🚗 Выберите машину:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Статистика
    if query.data == "stats":
        if not data:
            await query.edit_message_text("❌ Нет машин!", reply_markup=main_menu())
            return
        context.user_data['action'] = 'view_stats'
        keyboard = [[InlineKeyboardButton(plate, callback_data=f"car_{plate}")] for plate in data.keys()]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        await query.edit_message_text("🚗 Выберите машину:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Поиск
    if query.data == "search":
        if not data:
            await query.edit_message_text("❌ Нет машин!", reply_markup=main_menu())
            return
        context.user_data['action'] = 'search'
        keyboard = [[InlineKeyboardButton(part, callback_data=f"part_{part}")] for part in list(parts.keys())[:10]]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
        await query.edit_message_text("🔍 Выберите запчасть:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Мои машины
    if query.data == "my_cars":
        if not data:
            await query.edit_message_text("📭 Нет машин.", reply_markup=main_menu())
            return
        text = "🚕 **Ваши машины:**\n\n"
        for plate, car in data.items():
            text += f"• {plate} — {len(car['events'])} записей, пробег: {car.get('current_mileage', 0)} км\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button())
        return

    # Выбор машины
    if query.data.startswith("car_"):
        plate = query.data[4:]
        action = context.user_data.get('action')
        
        if action == 'select_car':
            context.user_data['car'] = plate
            context.user_data['action'] = 'select_part'
            keyboard = [[InlineKeyboardButton(part, callback_data=f"part_{part}")] for part in list(parts.keys())[:10]]
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
            await query.edit_message_text(f"🚗 {plate}\n\nВыберите запчасть:", reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif action == 'view_stats':
            car = data[plate]
            text = f"🚗 **{plate}**\n📊 Пробег: {car['current_mileage']} км\n📝 Записей: {len(car['events'])}\n\n"
            if car['events']:
                last_events = {}
                for e in car['events']:
                    if e['part'] not in last_events or e['mileage'] > last_events[e['part']]['mileage']:
                        last_events[e['part']] = e
                for part, e in last_events.items():
                    text += f"**{part}**\n  {e['date']} ({e['mileage']} км)\n"
                    if e.get('comment'):
                        text += f"  💬 {e['comment']}\n"
                    text += "\n"
            else:
                text += "Нет записей."
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button())

    # Выбор запчасти
    if query.data.startswith("part_"):
        part = query.data[5:]
        action = context.user_data.get('action')
        
        if action == 'select_part':
            context.user_data['part'] = part
            context.user_data['action'] = 'enter_mileage'
            await query.edit_message_text(
                f"🛞 {part}\n🚗 {context.user_data['car']}\n\nВведите пробег (км):",
                reply_markup=back_button()
            )
        
        elif action == 'search':
            text = f"🔍 **{part}**\n\n"
            found = False
            for plate, car in data.items():
                last = None
                for e in reversed(car['events']):
                    if e['part'] == part:
                        last = e
                        break
                if last:
                    km_int = last.get('km_interval', parts.get(part, {}).get('km', 0))
                    if km_int > 0:
                        next_km = last['mileage'] + km_int
                        remain = next_km - car['current_mileage']
                        if remain <= 1000:
                            found = True
                            text += f"**{plate}** — осталось {remain} км\n"
            if not found:
                text += "✅ Все в норме!"
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    action = context.user_data.get('action')
    
    if action == 'add_car':
        data = get_data()
        plate = text.upper()
        if plate in data:
            await update.message.reply_text("⚠️ Уже есть!")
            return
        data[plate] = {"events": [], "current_mileage": 0, "added_date": datetime.now().strftime("%d.%m.%Y")}
        save_json(DATA_FILE, data)
        del context.user_data['action']
        await update.message.reply_text(f"✅ {plate} добавлена!", reply_markup=main_menu())
    
    elif action == 'add_part_name':
        context.user_data['part_name'] = text.lower()
        context.user_data['action'] = 'add_part_km'
        await update.message.reply_text("Введите интервал по пробегу (км, 0 если нет):", reply_markup=back_button())
    
    elif action == 'add_part_km':
        try:
            km = int(text)
            context.user_data['km'] = km
            context.user_data['action'] = 'add_part_days'
            await update.message.reply_text("Введите интервал по времени (дней, 0 если нет):", reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Введите число!")
    
    elif action == 'add_part_days':
        try:
            days = int(text)
            parts = get_parts()
            parts[context.user_data['part_name']] = {"km": context.user_data['km'], "days": days}
            save_json(PARTS_FILE, parts)
            del context.user_data['action']
            await update.message.reply_text(
                f"✅ '{context.user_data['part_name']}' добавлена!",
                reply_markup=main_menu()
            )
        except:
            await update.message.reply_text("❌ Введите число!")
    
    elif action == 'enter_mileage':
        try:
            mileage = int(text)
            context.user_data['mileage'] = mileage
            context.user_data['action'] = 'enter_date'
            await update.message.reply_text("Введите дату (ДД.ММ.ГГГГ) или Enter для сегодня:", reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Введите число!")
    
    elif action == 'enter_date':
        date_str = text if text else datetime.now().strftime("%d.%m.%Y")
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            context.user_data['date'] = date_str
            context.user_data['action'] = 'enter_comment'
            await update.message.reply_text("Введите комментарий (или Enter):", reply_markup=back_button())
        except:
            await update.message.reply_text("❌ Неверный формат! Используйте ДД.ММ.ГГГГ")
    
    elif action == 'enter_comment':
        data = get_data()
        parts = get_parts()
        plate = context.user_data['car']
        part = context.user_data['part']
        event = {
            "date": context.user_data['date'],
            "part": part,
            "mileage": context.user_data['mileage'],
            "km_interval": parts.get(part, {}).get("km", 0),
            "days_interval": parts.get(part, {}).get("days", 0),
            "comment": text if text else ""
        }
        data[plate]['events'].append(event)
        if context.user_data['mileage'] > data[plate]['current_mileage']:
            data[plate]['current_mileage'] = context.user_data['mileage']
        save_json(DATA_FILE, data)
        del context.user_data['action']
        await update.message.reply_text(
            f"✅ Записано!\n🚗 {plate}\n🛞 {part}\n📅 {context.user_data['date']}\n📊 {context.user_data['mileage']} км",
            reply_markup=main_menu()
        )

# ========== ФУНКЦИЯ ЗАПУСКА (ДЛЯ FLASK) ==========
def run_bot():
    """Запускает бота (вызывается из app.py)"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Бот Такси-Трекер успешно запущен!")
    app.run_polling()

# ========== ЗАПУСК (ДЛЯ ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ) ==========
if __name__ == "__main__":
    # Для локального теста - просто запускаем бота
    # Но сначала проверяем, есть ли токен
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN")
    else:
        print("🚕 Запуск Такси-Трекера...")
        run_bot()
