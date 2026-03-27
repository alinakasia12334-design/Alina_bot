import telebot
import json
import os
from datetime import datetime
import pytz
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ========== НАСТРОЙКИ ==========
TOKEN = "8721756439:AAFjZgd7EFllbqJorgGZCqM5mFPcYSfey_Y"
ADMIN_ID = 463620997  # твой Telegram ID

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "finance.json"
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# ========== ФУНКЦИИ РАБОТЫ С ДАННЫМИ ==========
def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "allowed_users" not in data:
                data["allowed_users"] = []
            return data
    return {
        "usd": 20.0,
        "rub": 27700,
        "transactions": [],
        "allowed_users": []
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_allowed(user_id):
    data = load_data()
    return user_id == ADMIN_ID or user_id in data.get("allowed_users", [])

# ========== КЛАВИАТУРЫ ==========
def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💰 Остаток"),
        KeyboardButton("📊 Отчёты"),
        KeyboardButton("➕ Приход"),
        KeyboardButton("➖ Расход"),
        KeyboardButton("↩️ Отменить последнее"),
        KeyboardButton("⚙️ Установить остаток"),
        KeyboardButton("👥 Управление пользователями")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💰 Остаток"),
        KeyboardButton("📊 Отчёты")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_reports_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За конкретный день", callback_data="report_single_day"),
        InlineKeyboardButton("🗓️ За период (с ___ по ___)", callback_data="report_period")
    )
    return keyboard

def get_currency_keyboard(action_type):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("💵 Доллар ($)", callback_data=f"{action_type}_$"),
        InlineKeyboardButton("₽ Рубль (₽)", callback_data=f"{action_type}_₽")
    )
    keyboard.row(
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return keyboard

def get_instructions():
    return (
        "📚 *ИНСТРУКЦИЯ ПО КНОПКАМ*\n\n"
        "👇 *Что делает каждая кнопка:*\n\n"
        "💰 *Остаток* — показывает текущий баланс\n\n"
        "📊 *Отчёты* — открывает меню выбора:\n"
        "   • 📅 Отчёт за сегодня\n"
        "   • 📆 Отчёт за конкретный день\n"
        "   • 🗓️ Отчёт за период (с ___ по ___)\n\n"
        "❌ *Изменять данные могут только администраторы*\n"
        "Вы можете только просматривать информацию."
    )

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if not is_allowed(user_id):
        bot.reply_to(message, 
            "🔒 *Доступ запрещён*\n\n"
            "Этот бот работает только по приглашению.\n\n"
            "Чтобы получить доступ — напишите @privetetoalina и отправьте свой ID командой /getid",
            parse_mode='Markdown')
        return
    
    if is_admin(user_id):
        welcome = (
            "💰 *Привет, создательница!* 🤍\n\n"
            "Этот бота собрала *Алина* — и да, она *сама ахуеть* это сделала 🔥\n\n"
            "👇 Используй кнопки внизу, чтобы вести учёт.\n\n"
            "📚 Если нужно добавить пользователя — нажми *«Управление пользователями»*"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        welcome = (
            "💰 *Привет!* 🤍\n\n"
            "Этот бота собрала *Алина* — и да, она *сама ахуеть* это сделала 🔥\n\n"
            "Теперь ты можешь смотреть, куда уходят деньги 💸\n\n"
            "👇 *Вот что тут можно делать:*"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_user_keyboard())
        bot.send_message(message.chat.id, get_instructions(), parse_mode='Markdown')

@bot.message_handler(commands=['getid'])
def get_id(message):
    user_id = message.from_user.id
    bot.reply_to(message, 
        f"🆔 *Твой Telegram ID:* `{user_id}`\n\n"
        f"Перешли этот ID @privetetoalina, чтобы получить доступ к боту.",
        parse_mode='Markdown')

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только администратор может добавлять пользователей.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /adduser 123456789")
            return
        
        new_user_id = int(parts[1])
        data = load_data()
        
        if "allowed_users" not in data:
            data["allowed_users"] = []
        
        if new_user_id not in data["allowed_users"] and new_user_id != ADMIN_ID:
            data["allowed_users"].append(new_user_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен!", parse_mode='Markdown')
            
            try:
                bot.send_message(new_user_id, 
                    "🎉 *Вам открыли доступ!*\n\n"
                    "Напишите /start, чтобы начать пользоваться ботом.\n\n"
                    f"{get_instructions()}",
                    parse_mode='Markdown')
            except:
                pass
        else:
            bot.reply_to(message, f"ℹ️ Пользователь `{new_user_id}` уже в списке.", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Формат: /adduser 123456789")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только администратор может удалять пользователей.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /removeuser 123456789")
            return
        
        user_id = int(parts[1])
        data = load_data()
        
        if "allowed_users" in data and user_id in data["allowed_users"]:
            data["allowed_users"].remove(user_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь `{user_id}` удалён.", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"ℹ️ Пользователь `{user_id}` не найден.", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Формат: /removeuser 123456789")

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    
    data = load_data()
    allowed = data.get("allowed_users", [])
    
    if not allowed:
        bot.reply_to(message, "📋 *СПИСОК ПОЛЬЗОВАТЕЛЕЙ*\n━━━━━━━━━━━━━━━━━━\n\nПока нет добавленных пользователей.", parse_mode='Markdown')
        return
    
    text = "👥 *СПИСОК ПОЛЬЗОВАТЕЛЕЙ*\n━━━━━━━━━━━━━━━━━━\n\n"
    for uid in allowed:
        text += f"🆔 `{uid}`\n"
    
    text += f"\n👤 *Админ:* `{ADMIN_ID}`"
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== ОБРАБОТКА КНОПОК ==========
@bot.message_handler(func=lambda m: m.text == "💰 Остаток")
def button_cash(message):
    if not is_allowed(message.from_user.id):
        return
    data = load_data()
    now = get_moscow_time()
    keyboard = get_admin_keyboard() if is_admin(message.from_user.id) else get_user_keyboard()
    bot.reply_to(message, 
        f"💰 *ОСТАТОК*\n━━━━━━━━━━━━━━━━━━\n$ {data['usd']:.2f}\n₽ {int(data['rub'])}\n\n🕐 {now.strftime('%d.%m.%Y %H:%M')} МСК", 
        parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def button_reports(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📊 *Выбери отчёт:*", parse_mode='Markdown', reply_markup=get_reports_keyboard())

@bot.message_handler(func=lambda m: m.text == "➕ Приход")
def button_add_income(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💰 *Введите сумму и комментарий:*\n\nПример: `1000 Илья`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_income_amount)

@bot.message_handler(func=lambda m: m.text == "➖ Расход")
def button_add_expense(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💸 *Введите сумму и комментарий:*\n\nПример: `700 Макс реклама`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_expense_amount)

@bot.message_handler(func=lambda m: m.text == "↩️ Отменить последнее")
def button_undo(message):
    if not is_admin(message.from_user.id):
        return
    undo_last(message)

@bot.message_handler(func=lambda m: m.text == "⚙️ Установить остаток")
def button_set_balance(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "📝 *Введите валюту и сумму:*\n\nПримеры:\n`$ 1000`\n`₽ 50000`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_set_balance)

@bot.message_handler(func=lambda m: m.text == "👥 Управление пользователями")
def button_user_management(message):
    if not is_admin(message.from_user.id):
        return
    bot.reply_to(message, 
        "👥 *УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ*\n━━━━━━━━━━━━━━━━━━\n\n"
        "📌 *Команды:*\n"
        "`/adduser 123456789` — добавить пользователя\n"
        "`/removeuser 123456789` — удалить пользователя\n"
        "`/users` — список разрешённых\n"
        "`/getid` — узнать свой ID\n\n"
        "📎 *Новый пользователь:*\n"
        "1. Просишь написать `/getid`\n"
        "2. Получаешь его ID\n"
        "3. Вводишь `/adduser ID`\n"
        "4. Готово!",
        parse_mode='Markdown')

# ========== ОБРАБОТКА ВВОДА ==========
def process_income_amount(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "Выбери валюту:", reply_markup=get_currency_keyboard("income"))
    except:
        bot.reply_to(message, "❌ Неправильный формат. Пример: `1000 Илья`", parse_mode='Markdown')

def process_expense_amount(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "Выбери валюту:", reply_markup=get_currency_keyboard("expense"))
    except:
        bot.reply_to(message, "❌ Неправильный формат. Пример: `700 Макс`", parse_mode='Markdown')

def process_set_balance(message):
    try:
        parts = message.text.split()
        currency = parts[0]
        amount = float(parts[1])
        data = load_data()
        
        if currency == "$":
            data["usd"] = amount
            bot.reply_to(message, f"✅ Остаток в долларах установлен: {amount:.2f}$")
        elif currency == "₽":
            data["rub"] = amount
            bot.reply_to(message, f"✅ Остаток в рублях установлен: {int(amount)}₽")
        else:
            bot.reply_to(message, "❌ Укажи валюту: $ или ₽\nПример: `$ 1000`", parse_mode='Markdown')
            return
        save_data(data)
    except:
        bot.reply_to(message, "❌ Формат: `$ 1000` или `₽ 50000`", parse_mode='Markdown')

# ========== ОБРАБОТКА КНОПОК ВАЛЮТ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("income") or call.data.startswith("expense") or call.data == "cancel")
def handle_operation_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        return
    
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор может добавлять операции")
        return
    
    data = load_data()
    user_data = getattr(bot, "temp_data", {}).get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка, попробуйте ещё раз")
        return
    
    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] += amount
        else:
            data["rub"] += amount
        action = "ПРИХОД"
    else:
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] -= amount
        else:
            data["rub"] -= amount
        action = "РАСХОД"
    
    now = get_moscow_time()
    transaction = {
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": action.lower(),
        "amount": amount,
        "currency": currency,
        "comment": comment,
        "sign": '+' if action == "ПРИХОД" else '-'
    }
    data["transactions"].append(transaction)
    save_data(data)
    
    bot.edit_message_text(f"✅ {action} {amount:.2f}{currency} {comment}\n🕐 {now.strftime('%H:%M')} МСК", 
                          call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f"💰 Остаток: $ {data['usd']:.2f} | ₽ {int(data['rub'])}")
    
    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
        del bot.temp_data[call.message.chat.id]
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ ==========
def send_today_report(chat_id):
    data = load_data()
    now = get_moscow_time()
    today = now.strftime("%Y-%m-%d")
    today_name = now.strftime("%d.%m.%y")
    
    income_usd = 0.0
    income_rub = 0
    expense_usd = 0.0
    expense_rub = 0
    today_tx = []
    
    for tx in data["transactions"]:
        if tx["date"].startswith(today):
            today_tx.append(tx)
            if tx["sign"] == '+':
                if tx["currency"] == "$":
                    income_usd += tx["amount"]
                else:
                    income_rub += tx["amount"]
            else:
                if tx["currency"] == "$":
                    expense_usd += tx["amount"]
                else:
                    expense_rub += tx["amount"]
    
    if not today_tx:
        bot.send_message(chat_id, f"📅 *ОТЧЕТ ЗА {today_name}*\n━━━━━━━━━━━━━━━━━━\n\nЗа сегодня операций нет", parse_mode='Markdown')
        return
    
    report = f"📅 *ОТЧЕТ ЗА {today_name}*\n━━━━━━━━━━━━━━━━━━\n\n"
    report += "📋 *ОПЕРАЦИИ:*\n"
    for tx in today_tx:
        time = tx["date"].split()[1][:5]
        sign = "➕" if tx["sign"] == '+' else "➖"
        if tx["currency"] == "$":
            report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time} МСК)\n"
        else:
            report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time} МСК)\n"
    
    report += f"\n📈 *ПРИХОД:*"
    if income_usd > 0:
        report += f"\n  {income_usd:.2f}$"
    if income_rub > 0:
        report += f"\n  {int(income_rub)}₽"
    if income_usd == 0 and income_rub == 0:
        report += " —"
    
    report += f"\n\n📉 *РАСХОД:*"
    if expense_usd > 0:
        report += f"\n  {expense_usd:.2f}$"
    if expense_rub > 0:
        report += f"\n  {int(expense_rub)}₽"
    if expense_usd == 0 and expense_rub == 0:
        report += " —"
    
    report += "\n\n━━━━━━━━━━━━━━━━━━\n"
    data_now = load_data()
    report += f"💰 *ОСТАТОК НА СЕГОДНЯ:*\n  $ {data_now['usd']:.2f}\n  ₽ {int(data_now['rub'])}"
    
    bot.send_message(chat_id, report, parse_mode='Markdown')

def send_single_day_report(chat_id, date_input):
    try:
        day, month = date_input.split('.')
        year = datetime.now().year
        date_str = f"{year}-{month}-{day}"
        display_date = f"{day}.{month}.{year}"
        
        data = load_data()
        income_usd = 0.0
        income_rub = 0
        expense_usd = 0.0
        expense_rub = 0
        day_tx = []
        
        for tx in data["transactions"]:
            if tx["date"].startswith(date_str):
                day_tx.append(tx)
                if tx["sign"] == '+':
                    if tx["currency"] == "$":
                        income_usd += tx["amount"]
                    else:
                        income_rub += tx["amount"]
                else:
                    if tx["currency"] == "$":
                        expense_usd += tx["amount"]
                    else:
                        expense_rub += tx["amount"]
        
        if not day_tx:
            bot.send_message(chat_id, f"📆 *ОТЧЕТ ЗА {display_date}*\n━━━━━━━━━━━━━━━━━━\n\nЗа этот день операций нет", parse_mode='Markdown')
            return
        
        report = f"📆 *ОТЧЕТ ЗА {display_date}*\n━━━━━━━━━━━━━━━━━━\n\n"
        report += "📋 *ОПЕРАЦИИ:*\n"
        for tx in day_tx:
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time} МСК)\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time} МСК)\n"
        
        report += f"\n📈 *ПРИХОД:*"
        if income_usd > 0:
            report += f"\n  {income_usd:.2f}$"
        if income_rub > 0:
            report += f"\n  {int(income_rub)}₽"
        if income_usd == 0 and income_rub == 0:
            report += " —"
        
        report += f"\n\n📉 *РАСХОД:*"
        if expense_usd > 0:
            report += f"\n  {expense_usd:.2f}$"
        if expense_rub > 0:
            report += f"\n  {int(expense_rub)}₽"
        if expense_usd == 0 and expense_rub == 0:
            report += " —"
        
        bot.send_message(chat_id, report, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ Неправильный формат даты. Используй: `27.03`", parse_mode='Markdown')

def send_period_report(chat_id, start_date_str, end_date_str):
    try:
        start_day, start_month = start_date_str.split('.')
        end_day, end_month = end_date_str.split('.')
        year = datetime.now().year
        
        start_date = datetime(year, int(start_month), int(start_day))
        end_date = datetime(year, int(end_month), int(end_day))
        
        data = load_data()
        income_usd = 0.0
        income_rub = 0
        expense_usd = 0.0
        expense_rub = 0
        period_tx = []
        
        for tx in data["transactions"]:
            tx_date_str = tx["date"].split()[0]
            tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d")
            
            if start_date <= tx_date <= end_date:
                period_tx.append(tx)
                if tx["sign"] == '+':
                    if tx["currency"] == "$":
                        income_usd += tx["amount"]
                    else:
                        income_rub += tx["amount"]
                else:
                    if tx["currency"] == "$":
                        expense_usd += tx["amount"]
                    else:
                        expense_rub += tx["amount"]
        
        if not period_tx:
            bot.send_message(chat_id, f"📅 *ОТЧЕТ ЗА ПЕРИОД*\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━━━━\n\nЗа этот период операций нет", parse_mode='Markdown')
            return
        
        report = f"📅 *ОТЧЕТ ЗА ПЕРИОД*\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━━━━\n\n"
        report += "📋 *ОПЕРАЦИИ:*\n"
        for tx in period_tx:
            tx_date = tx["date"].split()[0][5:]
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time} МСК\n\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time} МСК\n\n"
        
        report += "━━━━━━━━━━━━━━━━━━\n"
        report += f"📈 *ИТОГО ПРИХОД:*\n"
        if income_usd > 0:
            report += f"  $ {income_usd:.2f}\n"
        if income_rub > 0:
            report += f"  ₽ {int(income_rub)}\n"
        if income_usd == 0 and income_rub == 0:
            report += "  —\n"
        
        report += f"\n📉 *ИТОГО РАСХОД:*\n"
        if expense_usd > 0:
            report += f"  $ {expense_usd:.2f}\n"
        if expense_rub > 0:
            report += f"  ₽ {int(expense_rub)}\n"
        if expense_usd == 0 and expense_rub == 0:
            report += "  —\n"
        
        report += "\n━━━━━━━━━━━━━━━━━━\n"
        data_now = load_data()
        report += f"💰 *ТЕКУЩИЙ ОСТАТОК:*\n  $ {data_now['usd']:.2f}\n  ₽ {int(data_now['rub'])}"
        
        bot.send_message(chat_id, report, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ Ошибка при формировании отчёта. Проверьте даты.")

# ========== ОБРАБОТКА КНОПОК ОТЧЁТОВ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def handle_report_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    if call.data == "report_today":
        bot.edit_message_text("📅 Загружаю отчёт...", call.message.chat.id, call.message.message_id)
        send_today_report(call.message.chat.id)
        
    elif call.data == "report_single_day":
        bot.edit_message_text("📆 *Введите дату в формате:* `27.03`\n\nНапример: `27.03`", 
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        if not hasattr(bot, "waiting_for_day"):
            bot.waiting_for_day = {}
        bot.waiting_for_day[call.message.chat.id] = True
        
    elif call.data == "report_period":
        bot.edit_message_text("🗓️ *Введите начальную дату:* `27.03`", 
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        if not hasattr(bot, "waiting_for_period"):
            bot.waiting_for_period = {}
        bot.waiting_for_period[call.message.chat.id] = {"step": "start"}
    
    bot.answer_callback_query(call.id)

# ========== ОБРАБОТКА ВВОДА ДАТ ==========
@bot.message_handler(func=lambda m: hasattr(bot, "waiting_for_day") and m.chat.id in bot.waiting_for_day)
def handle_day_input(message):
    if not is_allowed(message.from_user.id):
        return
    
    date_input = message.text.strip()
    del bot.waiting_for_day[message.chat.id]
    send_single_day_report(message.chat.id, date_input)

@bot.message_handler(func=lambda m: hasattr(bot, "waiting_for_period") and m.chat.id in bot.waiting_for_period)
def handle_period_input(message):
    if not is_allowed(message.from_user.id):
        return
    
    user_state = bot.waiting_for_period[message.chat.id]
    date_input = message.text.strip()
    
    try:
        day, month = date_input.split('.')
        int(day), int(month)
        
        if user_state["step"] == "start":
            user_state["start_date"] = date_input
            user_state["step"] = "end"
            bot.reply_to(message, f"✅ Начальная дата: {date_input}\n\n📅 *Введите конечную дату:*", parse_mode='Markdown')
            
        elif user_state["step"] == "end":
            end_date = date_input
            start_date = user_state["start_date"]
            del bot.waiting_for_period[message.chat.id]
            send_period_report(message.chat.id, start_date, end_date)
    except:
        bot.reply_to(message, "❌ Неправильный формат. Используй: `27.03`", parse_mode='Markdown')
        if user_state["step"] == "start":
            del bot.waiting_for_period[message.chat.id]

# ========== ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ==========
@bot.message_handler(commands=['undo'])
def undo_last(message):
    if not is_admin(message.from_user.id):
        return
    
    data = load_data()
    if not data["transactions"]:
        bot.reply_to(message, "❌ Нет операций для отмены")
        return
    
    last = data["transactions"].pop()
    if last["sign"] == '+':
        if last["currency"] == "$":
            data["usd"] -= last["amount"]
        else:
            data["rub"] -= last["amount"]
    else:
        if last["currency"] == "$":
            data["usd"] += last["amount"]
        else:
            data["rub"] += last["amount"]
    
    save_data(data)
    bot.reply_to(message, f"✅ Отменено: {last['sign']}{last['amount']:.2f if last['currency'] == '$' else int(last['amount'])}{last['currency']} {last['comment']}\n💰 Остаток: $ {data['usd']:.2f} | ₽ {int(data['rub'])}")

@bot.message_handler(commands=['history'])
def history(message):
    if not is_allowed(message.from_user.id):
        return
    
    data = load_data()
    last_tx = data["transactions"][-15:]
    
    if not last_tx:
        bot.reply_to(message, "📋 История пуста")
        return
    
    text = "📋 *ПОСЛЕДНИЕ ОПЕРАЦИИ*\n━━━━━━━━━━━━━━━━━━\n\n"
    for tx in reversed(last_tx):
        date_part = tx["date"].split()[0][5:]
        time_part = tx["date"].split()[1][:5]
        sign = "➕" if tx["sign"] == '+' else "➖"
        if tx["currency"] == "$":
            text += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']}\n   📅 {date_part} {time_part} МСК\n\n"
        else:
            text += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']}\n   📅 {date_part} {time_part} МСК\n\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['today'])
def today_command(message):
    if not is_allowed(message.from_user.id):
        return
    send_today_report(message.chat.id)

@bot.message_handler(commands=['day'])
def day_command(message):
    if not is_allowed(message.from_user.id):
        return
    try:
        date_input = message.text.split()[1]
        send_single_day_report(message.chat.id, date_input)
    except:
        bot.reply_to(message, "❌ Напиши: /day 27.03")

# ========== ЗАПУСК ==========
print("🚀 Бот Алины запущен!")
print(f"👤 Админ: {ADMIN_ID}")
print("🕐 Московское время")
print("🔒 Приватный режим")

bot.infinity_polling()
