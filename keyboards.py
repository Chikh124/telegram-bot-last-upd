from aiogram import types


# Функція для створення головного меню на основі мови користувача
from aiogram import types


def main_menu_keyboard(language='uk'):
    # Логування для перевірки мови, з якою викликається функція
    print(f"Мова при створенні клавіатури: {language}")

    if language == 'uk':
        keyboard = [
            [types.KeyboardButton(text="📝 Реєстрація команди")],
            [types.KeyboardButton(text="👥 Приєднатися до команди")],
            [types.KeyboardButton(text="👥 Переглянути команду")],
            [types.KeyboardButton(text="📝 Створити тікет")],
            [types.KeyboardButton(text="👁 Переглянути тікети")],
            [types.KeyboardButton(text="ℹ️ FAQ")],
            [types.KeyboardButton(text="📜 Правила турніру")],
            [types.KeyboardButton(text="📆 Розклад матчів")],
            [types.KeyboardButton(text="💳 Оплатити участь")]
        ]
    else:
        keyboard = [
            [types.KeyboardButton(text="📝 Регистрация команды")],
            [types.KeyboardButton(text="👥 Присоединиться к команде")],
            [types.KeyboardButton(text="👥 Просмотреть команду")],
            [types.KeyboardButton(text="📝 Создать тикет")],
            [types.KeyboardButton(text="👁 Просмотреть тикеты")],
            [types.KeyboardButton(text="ℹ️ FAQ")],
            [types.KeyboardButton(text="📜 Правила турнира")],
            [types.KeyboardButton(text="📆 Расписание матчей")],
            [types.KeyboardButton(text="💳 Оплатить участие")]
        ]

    # Логування для перевірки створеної клавіатури
    print(f"Клавіатура створена для мови: {language}")

    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)



# Функція для створення клавіатури з опціями для команди
def team_options_keyboard(language='uk'):
    if language == 'uk':
        keyboard = [
            [types.InlineKeyboardButton(text="Редагувати назву", callback_data="edit_team_name")],
            [types.InlineKeyboardButton(text="Видалити команду", callback_data="delete_team")]
        ]
    else:
        keyboard = [
            [types.InlineKeyboardButton(text="Редактировать название", callback_data="edit_team_name")],
            [types.InlineKeyboardButton(text="Удалить команду", callback_data="delete_team")]
        ]

    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)
