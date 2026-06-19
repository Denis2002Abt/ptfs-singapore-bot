import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
# Вставь свой токен от BotFather
TOKEN = '8997502471:AAGZaie-f5mbT60Kf5rbg_RSofNO43hgNIk'
bot = telebot.TeleBot(TOKEN)

ADMIN_CODE = "codst"
TEMPLATE_FILENAME = "ticket_template.png"

# Временная база данных в памяти
AVAILABLE_FLIGHTS = {}
user_state = {}

# --- ШРИФТЫ ---
# Стараемся загрузить Arial. Если Thonny не видит, будет стандартный.
try:
    font_main = ImageFont.truetype("arial.ttf", 22) # Основной
    font_bold = ImageFont.truetype("arialbd.ttf", 24) # Жирный для рейса
except IOError:
    font_main = ImageFont.load_default()
    font_bold = ImageFont.load_default()

def draw_text(draw, x, y, text, font, color=(25, 25, 25)):
    draw.text((x, y), str(text), fill=color, font=font)

def get_moscow_time():
    return datetime.utcnow() + timedelta(hours=3)

# --- ГЕНЕРАЦИЯ БИЛЕТА С ПОЛНОЙ КОРРЕКЦИЕЙ КООРДИНАТ ---
def generate_ticket(ticket_data):
    with Image.open(TEMPLATE_FILENAME) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)

        nickname = ticket_data['nickname']
        flight_name = ticket_data['flight_name']
        gate = ticket_data['gate']
        from_loc = ticket_data['from']
        to_loc = ticket_data['to']
        
        now_msk = get_moscow_time()
        date_str = now_msk.strftime("%d.%m.%y")  
        time_str = now_msk.strftime("%H:%M")     
        board_time = (now_msk - timedelta(minutes=10)).strftime("%H:%M")

        # --- 1. ЛЕВАЯ ЧАСТЬ (ОСНОВНОЙ БИЛЕТ) ---
        # Поднимаем тексты и выравниваем по левому краю графы
        
        # Строка 1: NAME
        draw_text(draw, 140, 92, nickname, font_main)
        
        # Строка 2: FLIGHT и TO
        draw_text(draw, 140, 148, flight_name, font_bold) # Рейс жирным
        draw_text(draw, 410, 148, to_loc, font_main)      # Куда
        
        # Строка 3: DEP TIME
        draw_text(draw, 140, 204, time_str, font_main)
        
        # Овальные рамки внизу
        draw_text(draw, 140, 304, board_time, font_main)  # BOARDING
        draw_text(draw, 420, 304, gate, font_main)        # GATE

        # --- 2. КОРЕШОК (ПРАВАЯ ЧАСТЬ) ---
        # Полностью исправляем порядок данных на корешке
        
        # Строка 1: NAME (Ник теперь тут, а не в FROM)
        draw_text(draw, 740, 92, nickname, font_main)
        
        # Строка 2: FROM
        draw_text(draw, 740, 133, from_loc, font_main)    
        
        # Строка 3: TO
        draw_text(draw, 740, 172, to_loc, font_main)      
        
        # Строка 4: DATE
        draw_text(draw, 740, 218, date_str, font_main)
        
        # Нижние рамки корешка
        draw_text(draw, 755, 280, "8A", font_main)       # SEAT (Пример)
        draw_text(draw, 880, 280, flight_name, font_bold)# FLIGHT жирным

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer

# --- ОБРАБОТКА МЕНЮ (Без изменений) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Привет! Добро пожаловать в Singapore | PTFS RU.", reply_markup=get_main_keyboard())

# Функция для главной клавиатуры
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("✈️ Рейсы"),
        types.KeyboardButton("🛠️ Поддержка"),
        types.KeyboardButton("🎫 Проверка билетов (Админ)"),
        types.KeyboardButton("➕ Создание рейсов (Админ)")
    )
    return markup

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    chat_id = message.chat.id

    if message.text == "✈️ Рейсы":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        if not AVAILABLE_FLIGHTS:
            markup.add(types.KeyboardButton("✈️ Не существующий рейс"))
        else:
            for flight_name in AVAILABLE_FLIGHTS.keys():
                markup.add(types.KeyboardButton(flight_name))
        markup.add(types.KeyboardButton("⬅️ Назад в меню"))
        bot.send_message(chat_id, "Доступные рейсы:", reply_markup=markup)

    elif message.text == "✈️ Не существующий рейс":
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton("🎟️ Заполнить билет", callback_data="start_ticket_SQ-404"))
        bot.send_message(chat_id, "Рейс SQ-404: SIN / Singapore — HND / Tokyo.\nНажмите для оформления:", reply_markup=inline_markup)

    elif message.text in AVAILABLE_FLIGHTS:
        flight_info = AVAILABLE_FLIGHTS[message.text]
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton("🎟️ Заполнить билет", callback_data=f"start_ticket_{message.text}"))
        bot.send_message(chat_id, f"Рейс {message.text}.\nМаршрут: {flight_info['from']} ➡️ {flight_info['to']}\nНажмите для оформления:", reply_markup=inline_markup)

    elif message.text == "⬅️ Назад в меню":
        bot.send_message(chat_id, "Главное меню:", reply_markup=get_main_keyboard())

    elif message.text == "➕ Создание рейсов (Админ)":
        msg = bot.send_message(chat_id, "🔐 Введите секретный код доступа для администрации:")
        bot.register_next_step_handler(msg, check_admin_code)

# --- АДМИНКА ---

def check_admin_code(message):
    chat_id = message.chat.id
    if message.text == ADMIN_CODE:
        msg = bot.send_message(chat_id, "🔓 Вход выполнен!\nШаг 1: Введите НАЗВАНИЕ рейса (например: Singapore-5):")
        bot.register_next_step_handler(msg, admin_get_name)
    else:
        bot.send_message(chat_id, "❌ Неверный код.", reply_markup=get_main_keyboard())

def admin_get_name(message):
    chat_id = message.chat.id
    user_state[chat_id] = {'new_flight_name': message.text}
    msg = bot.send_message(chat_id, "🌍 Шаг 2: Введите место ВЫЛЕТА (например: SIN / Singapore):")
    bot.register_next_step_handler(msg, admin_get_from)

def admin_get_from(message):
    chat_id = message.chat.id
    if chat_id not in user_state: return
    user_state[chat_id]['from'] = message.text
    msg = bot.send_message(chat_id, "🛬 Шаг 3: Введите место НАЗНАЧЕНИЯ (например: Rockford / PTFS):")
    bot.register_next_step_handler(msg, admin_get_to)

def admin_get_to(message):
    chat_id = message.chat.id
    if chat_id not in user_state: return
    user_state[chat_id]['to'] = message.text
    
    inline_gate = types.InlineKeyboardMarkup(row_width=3)
    inline_gate.add(
        types.InlineKeyboardButton("Gate 1", callback_data="set_gate_Gate 1"),
        types.InlineKeyboardButton("Gate 2", callback_data="set_gate_Gate 2"),
        types.InlineKeyboardButton("Gate 3", callback_data="set_gate_Gate 3"),
        types.InlineKeyboardButton("Gate 4", callback_data="set_gate_Gate 4"),
        types.InlineKeyboardButton("Gate 5", callback_data="set_gate_Gate 5"),
        types.InlineKeyboardButton("Gate 10", callback_data="set_gate_Gate 10")
    )
    bot.send_message(chat_id, f"🚪 Шаг 4: Выберите гейт для рейса {user_state[chat_id]['new_flight_name']}:", reply_markup=inline_gate)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_gate_'))
def admin_save_flight_callback(call):
    chat_id = call.message.chat.id
    if chat_id not in user_state: return
    
    gate_name = call.data.replace('set_gate_', '')
    f_name = user_state[chat_id]['new_flight_name']
    
    AVAILABLE_FLIGHTS[f_name] = {
        "from": user_state[chat_id]['from'],
        "to": user_state[chat_id]['to'],
        "gate": gate_name
    }
    del user_state[chat_id]
    
    bot.answer_callback_query(call.id, "Рейс создан!")
    bot.edit_message_text(f"✅ Рейс **{f_name}** создан!\nИгроки могут оформлять билеты.", chat_id, call.message.message_id, parse_mode="Markdown")

# --- СБОР ДАННЫХ ИГРОКА ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_ticket_'))
def start_ticket_wizard(call):
    chat_id = call.message.chat.id
    flight_name = call.data.replace('start_ticket_', '')
    bot.answer_callback_query(call.id)
    
    if flight_name == 'SQ-404':
        flight_info = {"from": "SIN / Singapore", "to": "HND / Tokyo", "gate": "Gate 10"}
    else:
        flight_info = AVAILABLE_FLIGHTS.get(flight_name, {"from": "---", "to": "---", "gate": "Gate 1"})
        
    user_state[chat_id] = {
        'flight_name': flight_name, 
        'gate': flight_info['gate'],
        'from': flight_info['from'],
        'to': flight_info['to']
    }
    
    msg = bot.send_message(chat_id, f"✍️ Оформление билета на {flight_name}.\nВведите ваш игровой Никнейм (NAME):")
    bot.register_next_step_handler(msg, process_ticket_final)

def process_ticket_final(message):
    chat_id = message.chat.id
    if chat_id not in user_state: return
    
    user_state[chat_id]['nickname'] = message.text
    bot.send_message(chat_id, "⏳ Секунду, печатаю ваш билет...")

    try:
        ticket_img = generate_ticket(user_state[chat_id])
        bot.send_photo(
            chat_id, 
            ticket_img, 
            caption=f"🎫 Ваш билет готов!\nНикнейм: {user_state[chat_id]['nickname']}\nРейс: {user_state[chat_id]['flight_name']}\nМаршрут: {user_state[chat_id]['from']} ➡️ {user_state[chat_id]['to']}"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка отрисовки билета: {e}")
        
    del user_state[chat_id]

if __name__ == '__main__':
    bot.infinity_polling()
