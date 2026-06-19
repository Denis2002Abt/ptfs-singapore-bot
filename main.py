import telebot
import os

# Вставь сюда токен своего нового или очищенного бота из @BotFather
TOKEN = os.environ.get'8997502471:AAGtvaXVifG4U9J2nz6HGfUD6Mv9eNBkTOE'
bot = telebot.TeleBot(TOKEN)

# Список Telegram ID тех, кто может менять расписание (ты и твой друг)
ADMIN_IDS = [5153757336]  # Поменяй на ваши реальные ID!

FILE_NAME = "flight_info.txt"

def get_flight():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return f.read()
    return "На данный момент активных рейсов нет. Ожидайте анонса!"

def save_flight(text):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write(text)

# Главное меню
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✈️ Расписание рейсов', '🎫 Купить билет')
    
    # Если пишет админ, добавляем ему кнопку управления
    if message.from_user.id in ADMIN_IDS:
        markup.add('🛠 Обновить рейс')
        
    bot.send_message(message.chat.id, "Добро пожаловать в авиакомпанию Singapore Airlines (PTFS)!", reply_markup=markup)

# Обработка кнопок
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == '✈️ Расписание рейсов':
        current_flight = get_flight()
        bot.send_message(message.chat.id, f"📋 *Текущее расписание рейсов:*\n\n{current_flight}", parse_mode="Markdown")
        
    elif message.text == '🎫 Купить билет':
        bot.send_message(message.chat.id, "Чтобы забронировать билет, свяжитесь с сотрудником в игре или заполните ник.")
        
    elif message.text == '🛠 Обновить рейс' and message.from_user.id in ADMIN_IDS:
        msg = bot.send_message(message.chat.id, "Введите новую информацию о рейсе (одним сообщением):")
        bot.register_next_step_handler(msg, update_flight_process)

def update_flight_process(message):
    if message.text:
        save_flight(message.text)
        bot.send_message(message.chat.id, "✅ Расписание успешно обновлено для всех игроков!")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка. Отправьте текст.")

# Запуск бота
bot.infinity_polling()
