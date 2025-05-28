import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import json
import os
from datetime import datetime, timedelta
import random

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файлы для хранения данных
DATA_FILE = 'turtle_data.json'
LEADERBOARD_FILE = 'leaderboard.json'

# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    return []

user_data = load_data()
leaderboard = load_leaderboard()

# Магазин предметов
SHOP_ITEMS = {
    'salad': {'price': 10, 'hunger': 15, 'happiness': 5},
    'fish': {'price': 20, 'hunger': 30, 'happiness': 10},
    'shrimp': {'price': 35, 'hunger': 50, 'happiness': 15},
    'vitamins': {'price': 50, 'happiness': 30, 'health': 10},
    'toy': {'price': 40, 'happiness': 25},
    'medicine': {'price': 60, 'health': 30}
}

# Сохранение данных
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=4)
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=4)

# Инициализация черепашки
def init_turtle(user_id, username):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            'name': 'Черепашка',
            'username': username,
            'level': 1,
            'exp': 0,
            'hunger': 100,
            'happiness': 100,
            'health': 100,
            'coins': 50,
            'items': {},
            'last_played': None,
            'last_daily': None,
            'created_at': datetime.now().isoformat()
        }
        save_data()

# Обновление лидерборда
def update_leaderboard(user_id, username, level):
    for entry in leaderboard:
        if entry['user_id'] == user_id:
            if level > entry['level']:
                entry['level'] = level
                entry['username'] = username
            leaderboard.sort(key=lambda x: x['level'], reverse=True)
            save_data()
            return
    
    leaderboard.append({
        'user_id': user_id,
        'username': username,
        'level': level
    })
    leaderboard.sort(key=lambda x: x['level'], reverse=True)
    save_data()

# Проверка повышения уровня
def check_level_up(user_id):
    turtle = user_data[str(user_id)]
    exp_needed = turtle['level'] * 10
    
    if turtle['exp'] >= exp_needed:
        turtle['level'] += 1
        turtle['exp'] = 0
        turtle['coins'] += turtle['level'] * 5
        update_leaderboard(user_id, turtle['username'], turtle['level'])
        return True
    return False

# Клавиатуры
def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("🍽 Покормить", callback_data='feed'),
         InlineKeyboardButton("🎾 Поиграть", callback_data='play')],
        [InlineKeyboardButton("🛒 Магазин", callback_data='shop'),
         InlineKeyboardButton("💊 Лечить", callback_data='heal')],
        [InlineKeyboardButton("🏆 Лидеры", callback_data='leaderboard'),
         InlineKeyboardButton("✏️ Имя", callback_data='rename')],
        [InlineKeyboardButton("🎁 Ежедневная награда", callback_data='daily')]
    ]
    return InlineKeyboardMarkup(buttons)

def back_keyboard(target='back'):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=target)]])

# Команды бота
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    username = user.username or user.first_name
    init_turtle(user.id, username)
    
    update.message.reply_text(
        f"🐢 Привет, {user.first_name}! Добро пожаловать в TurtleBot!\n"
        "У тебя есть своя виртуальная черепашка, за которой нужно ухаживать.\n\n"
        "Используй кнопки ниже или команду /help для списка команд.",
        reply_markup=main_menu_keyboard()
    )
    show_status(update, context)

def show_status(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    turtle = user_data[str(user_id)]
    
    message = (
        f"🐢 Имя: {turtle['name']}\n"
        f"📊 Уровень: {turtle['level']}\n"
        f"⭐ Опыт: {turtle['exp']}/{turtle['level'] * 10}\n"
        f"🍽️ Сытость: {turtle['hunger']}/100\n"
        f"😊 Счастье: {turtle['happiness']}/100\n"
        f"❤️ Здоровье: {turtle['health']}/100\n"
        f"🪙 Монеты: {turtle['coins']}\n"
    )
    
    if update.callback_query:
        update.callback_query.edit_message_text(message, reply_markup=main_menu_keyboard())
    else:
        update.message.reply_text(message, reply_markup=main_menu_keyboard())

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "🐢 TurtleBot - команды:\n"
        "/start - начать игру\n"
        "/status - статус черепашки\n"
        "/feed - покормить\n"
        "/play - поиграть\n"
        "/shop - магазин\n"
        "/heal - лечить\n"
        "/rename - изменить имя\n"
        "/leaderboard - таблица лидеров\n"
        "/daily - ежедневная награда\n"
        "/help - список команд",
        reply_markup=main_menu_keyboard()
    )

# Обработчики действий
def feed_menu(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    turtle = user_data[str(user_id)]
    
    buttons = []
    for item in turtle['items']:
        if item in ['salad', 'fish', 'shrimp']:
            buttons.append([InlineKeyboardButton(
                f"{item.capitalize()} (x{turtle['items'][item]})", 
                callback_data=f'use_{item}'
            )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
    
    update.callback_query.edit_message_text(
        "Выберите еду для черепашки:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def use_item(update: Update, context: CallbackContext, item: str) -> None:
    user_id = update.callback_query.from_user.id
    turtle = user_data[str(user_id)]
    
    if turtle['items'].get(item, 0) > 0:
        turtle['items'][item] -= 1
        if turtle['items'][item] == 0:
            del turtle['items'][item]
        
        effects = SHOP_ITEMS[item]
        if 'hunger' in effects:
            turtle['hunger'] = min(100, turtle['hunger'] + effects['hunger'])
        if 'happiness' in effects:
            turtle['happiness'] = min(100, turtle['happiness'] + effects['happiness'])
        if 'health' in effects:
            turtle['health'] = min(100, turtle['health'] + effects['health'])
        
        turtle['exp'] += 2
        check_level_up(user_id)
        save_data()
        
        update.callback_query.edit_message_text(
            f"Вы использовали {item} для черепашки!",
            reply_markup=back_keyboard('feed')
        )
    else:
        update.callback_query.edit_message_text(
            "У вас нет этого предмета!",
            reply_markup=back_keyboard('feed')
        )

def play_with_turtle(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    turtle = user_data[str(user_id)]
    
    now = datetime.now()
    last_played = datetime.fromisoformat(turtle['last_played']) if turtle['last_played'] else None
    
    if last_played and (now - last_played) < timedelta(hours=1):
        next_play = last_played + timedelta(hours=1)
        wait_time = next_play - now
        hours = wait_time.seconds // 3600
        minutes = (wait_time.seconds % 3600) // 60
        
        update.callback_query.edit_message_text(
            f"Черепашка устала. Можно играть через {hours}ч {minutes}мин.",
            reply_markup=back_keyboard()
        )
        return
    
    happiness_gain = random.randint(5, 15)
    turtle['happiness'] = min(100, turtle['happiness'] + happiness_gain)
    turtle['exp'] += 5
    turtle['last_played'] = now.isoformat()
    
    check_level_up(user_id)
    save_data()
    
    update.callback_query.edit_message_text(
        f"Вы поиграли с черепашкой! 🎾\n"
        f"+{happiness_gain} к счастью\n"
        f"+5 опыта",
        reply_markup=back_keyboard()
    )

def show_shop(update: Update, context: CallbackContext) -> None:
    buttons = []
    for item, details in SHOP_ITEMS.items():
        buttons.append([InlineKeyboardButton(
            f"{item.capitalize()} - {details['price']}🪙", 
            callback_data=f'buy_{item}'
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
    
    update.callback_query.edit_message_text(
        "🛒 Магазин. Выберите предмет:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def buy_item(update: Update, context: CallbackContext, item: str) -> None:
    user_id = update.callback_query.from_user.id
    turtle = user_data[str(user_id)]
    item_data = SHOP_ITEMS[item]
    
    if turtle['coins'] >= item_data['price']:
        turtle['coins'] -= item_data['price']
        turtle['items'][item] = turtle['items'].get(item, 0) + 1
        save_data()
        
        update.callback_query.edit_message_text(
            f"Вы купили {item} за {item_data['price']} монет!",
            reply_markup=back_keyboard('shop')
        )
    else:
        update.callback_query.edit_message_text(
            "Недостаточно монет!",
            reply_markup=back_keyboard('shop')
        )

def heal_turtle(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    turtle = user_data[str(user_id)]
    
    if turtle['items'].get('medicine', 0) > 0:
        turtle['items']['medicine'] -= 1
        if turtle['items']['medicine'] == 0:
            del turtle['items']['medicine']
        
        health_gain = SHOP_ITEMS['medicine']['health']
        turtle['health'] = min(100, turtle['health'] + health_gain)
        save_data()
        
        update.callback_query.edit_message_text(
            f"Черепашка вылечена! +{health_gain} здоровья",
            reply_markup=back_keyboard()
        )
    else:
        update.callback_query.edit_message_text(
            "Нет лекарства! Купите в магазине.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Магазин", callback_data='shop')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back')]
            ])
        )

def show_leaderboard(update: Update, context: CallbackContext) -> None:
    text = "🏆 Топ 10 игроков:\n\n"
    for i, entry in enumerate(leaderboard[:10], 1):
        text += f"{i}. {entry['username']} - Уровень {entry['level']}\n"
    
    update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard()
    )

def rename_turtle(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        update.callback_query.edit_message_text(
            "Введите новое имя для черепашки:",
            reply_markup=back_keyboard()
        )
        context.user_data['awaiting_name'] = True
    else:
        update.message.reply_text("Используйте кнопку '✏️ Имя' в меню.")

def process_name(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    new_name = update.message.text.strip()[:20]
    
    if new_name:
        user_data[str(user_id)]['name'] = new_name
        save_data()
        update.message.reply_text(
            f"Теперь вашу черепашку зовут {new_name}!",
            reply_markup=main_menu_keyboard()
        )
        del context.user_data['awaiting_name']
    else:
        update.message.reply_text("Имя не может быть пустым!")

def daily_reward(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    turtle = user_data[str(user_id)]
    
    now = datetime.now()
    last_daily = datetime.fromisoformat(turtle['last_daily']) if turtle['last_daily'] else None
    
    if not last_daily or (now - last_daily) >= timedelta(days=1):
        reward = random.randint(10, 30)
        turtle['coins'] += reward
        turtle['last_daily'] = now.isoformat()
        save_data()
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                f"🎁 Вы получили {reward} монет!",
                reply_markup=back_keyboard()
            )
        else:
            update.message.reply_text(
                f"🎁 Вы получили {reward} монет!",
                reply_markup=main_menu_keyboard()
            )
    else:
        next_daily = last_daily + timedelta(days=1)
        wait_time = next_daily - now
        hours = wait_time.seconds // 3600
        minutes = (wait_time.seconds % 3600) // 60
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                f"Следующая награда через {hours}ч {minutes}мин.",
                reply_markup=back_keyboard()
            )
        else:
            update.message.reply_text(
                f"Следующая награда через {hours}ч {minutes}мин.",
                reply_markup=main_menu_keyboard()
            )

# Обработчик кнопок
def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    data = query.data
    if data == 'feed':
        feed_menu(update, context)
    elif data == 'play':
        play_with_turtle(update, context)
    elif data == 'shop':
        show_shop(update, context)
    elif data == 'heal':
        heal_turtle(update, context)
    elif data == 'leaderboard':
        show_leaderboard(update, context)
    elif data == 'rename':
        rename_turtle(update, context)
    elif data == 'daily':
        daily_reward(update, context)
    elif data.startswith('buy_'):
        buy_item(update, context, data[4:])
    elif data.startswith('use_'):
        use_item(update, context, data[4:])
    elif data == 'back':
        show_status(update, context)

# Обработчик сообщений
def message_handler(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_name', False):
        process_name(update, context)
    else:
        update.message.reply_text(
            "Используйте кнопки меню или команду /help",
            reply_markup=main_menu_keyboard()
        )

# Ошибки
def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Ошибка: {context.error}")
    if update.callback_query:
        update.callback_query.edit_message_text(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )
    else:
        update.message.reply_text(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )

# Запуск бота
def main():
    TOKEN = "your_token"  # Замените на ваш токен
    
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    # Команды
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("status", show_status))
    dp.add_handler(CommandHandler("daily", daily_reward))
    
    # Обработчики
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    
    # Ошибки
    dp.add_error_handler(error_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
