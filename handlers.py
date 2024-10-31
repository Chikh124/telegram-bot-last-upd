import asyncio

from aiogram import Dispatcher, types, F, Bot
from aiogram.fsm.context import FSMContext
from database import (
    add_user, check_user_team, create_team, join_team, update_steam_profile,
    get_team_members, create_ticket, get_admin_ids, get_open_tickets,
    add_ticket_response, get_user_id_by_ticket, cursor, conn, get_schedule,
    get_matches, add_match_to_db, delete_match, get_teams_with_members, delete_team,
    update_payment_status, check_payment_status, get_db_connection, set_user_language,
    get_user_language, update_ticket_description
)
from states import RegistrationStates
from keyboards import main_menu_keyboard, team_options_keyboard
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import bot, dp  # Імпортуємо bot та dp з файлу bot.py




# Обробка відповіді адміністратора на тікет


async def cmd_reply_ticket(message: types.Message, bot: Bot, state: FSMContext):
    if message.from_user.id in get_admin_ids():
        try:
            parts = message.text.split(maxsplit=2)  # /reply <ticket_id> <відповідь>
            if len(parts) < 3:
                await message.answer("Неправильний формат. Використовуйте: /reply <ticket_id> <відповідь>")
                return

            ticket_id = int(parts[1])  # Отримуємо ticket_id
            response = parts[2].strip()  # Отримуємо відповідь

            user_id = get_user_id_by_ticket(ticket_id)  # Отримуємо user_id користувача, який створив тікет

            if user_id:
                # Отримуємо мову користувача, який створив тікет
                # Отримуємо мову користувача, який створив тікет
                user_language = get_user_language(user_id)
                print(f"Мова користувача з ID {user_id}: {user_language}")

                # Додаємо відповідь до тікета
                add_ticket_response(ticket_id, message.from_user.id, response)

                # Створюємо клавіатуру з кнопкою "Продовжити спілкування" і "Закрити тікет"
                continue_text = "Продовжити спілкування" if user_language == 'uk' else "Продолжить общение"
                close_text = "Закрити тікет" if user_language == 'uk' else "Закрыть тикет"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=continue_text, callback_data=f"continue_{ticket_id}")],
                        [InlineKeyboardButton(text=close_text, callback_data=f"close_{ticket_id}")]
                    ]
                )

                # Відправляємо повідомлення користувачу з клавіатурою на його мові
                if user_language == 'uk':
                    await bot.send_message(user_id, f"Адміністратор відповів на ваш тікет #{ticket_id}: {response}",
                                           reply_markup=keyboard)
                else:
                    await bot.send_message(user_id, f"Администратор ответил на ваш тикет #{ticket_id}: {response}",
                                           reply_markup=keyboard)

                # Повідомлення адміністратору
                await message.answer(f"Відповідь на тікет #{ticket_id} надіслано.")
            else:
                await message.answer(f"Тікет з ID {ticket_id} не знайдено.")
        except (IndexError, ValueError) as e:
            await message.answer("Неправильний формат. Використовуйте: /reply <ticket_id> <відповідь>")
    else:
        await message.answer("У вас немає прав для відповіді на тікети.")



# Обробник команди /start
async def cmd_start(message: types.Message):
    # Отримуємо інформацію про користувача
    user = message.from_user

    # Викликаємо функцію додавання користувача
    add_user(user)
    # Створюємо інлайн-кнопки для вибору мови
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Українська 🇺🇦", callback_data="lang_uk")],
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")]
        ]
    )
    await message.answer("Привіт! Оберіть мову спілкування/Привет! Выберите язык общения:", reply_markup=keyboard)



async def send_main_menu(message: types.Message, user_id: int):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(user_id, db)
    print(f"Мова при створенні клавіатури після оновлення: {user_language}")  # Логування для перевірки мови

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    # Відправляємо повідомлення з відповідним текстом та меню
    if user_language == 'uk':
        welcome_text = "Вітаємо на турнірі з RUST! Оберіть одну з опцій:"
    else:
        welcome_text = "Добро пожаловать на турнир по RUST! Выберите один из вариантов:"

    print(f"Викликаємо клавіатуру з мовою після збереження: {user_language}")  # Додаємо логування перед викликом клавіатури

    await message.answer(welcome_text, reply_markup=main_menu_keyboard(user_language))


# Обробник кнопки "📝 Реєстрація команди"
async def cmd_register_team(message: types.Message, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    try:
        # Отримуємо мову користувача
        user_language = get_user_language(message.from_user.id, db)

        # Перевіряємо, чи користувач вже в команді
        user_team = check_user_team(message.from_user.id)

        if user_team:
            if user_language == 'uk':
                await message.answer(f"Ви вже зареєстровані в команді {user_team}.")
            else:
                await message.answer(f"Вы уже зарегистрированы в команде {user_team}.")
        else:
            if user_language == 'uk':
                await message.answer("Введіть назву вашої команди:")
            else:
                await message.answer("Введите название вашей команды:")
            await state.set_state(RegistrationStates.waiting_for_team_name)

    except Exception as e:
        print(f"Сталася помилка: {e}")
        await message.answer("Виникла помилка. Спробуйте ще раз.")

    finally:
        # Закриваємо з'єднання з базою даних після використання
        db.close()


# Обробка введення назви команди
async def process_team_name(message: types.Message, state: FSMContext):
    team_name = message.text.strip()

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    try:
        # Отримуємо мову користувача
        user_language = get_user_language(message.from_user.id, db)  # Передаємо ідентифікатор та з'єднання

        # Створюємо команду
        invite_code = create_team(message.from_user.id, team_name)

        if user_language == 'uk':
            await message.answer(f"Команда '{team_name}' створена! Код запрошення: {invite_code}")
        else:
            await message.answer(f"Команда '{team_name}' создана! Код приглашения: {invite_code}")

        # Після введення назви команди запитуємо Steam профіль
        if user_language == 'uk':
            await message.answer("Будь ласка, введіть ваш Steam профіль (посилання):")
        else:
            await message.answer("Пожалуйста, введите ваш Steam профиль (ссылка):")

        await state.set_state(RegistrationStates.waiting_for_steam_profile)

    except Exception as e:
        print(f"Сталася помилка: {e}")
        await message.answer("Виникла помилка. Спробуйте ще раз.")

    finally:
        # Закриваємо з'єднання з базою даних
        db.close()




# Обробка введення Steam профілю
async def process_steam_profile(message: types.Message, state: FSMContext):
    steam_profile = message.text.strip()

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    try:
        # Оновлюємо Steam профіль у базі даних
        update_steam_profile(message.from_user.id, steam_profile)

        # Отримуємо мову користувача
        user_language = get_user_language(message.from_user.id, db)

        # Виводимо повідомлення залежно від мови
        if user_language == 'uk':
            await message.answer("Ваш Steam профіль успішно збережено!")
        else:
            await message.answer("Ваш Steam профиль успешно сохранён!")

        await state.clear()  # Завершуємо стан

    except Exception as e:
        print(f"Сталася помилка: {e}")
        await message.answer("Виникла помилка. Спробуйте ще раз.")

    finally:
        # Закриваємо з'єднання з базою даних
        db.close()






# Обробник кнопки "👥 Приєднатися до команди"
async def cmd_join_team(message: types.Message, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    # Спочатку перевіряємо, чи користувач вже в команді
    if check_user_team(message.from_user.id):
        if user_language == 'uk':
            await message.answer("Ви вже в команді.")
        else:
            await message.answer("Вы уже в команде.")
    else:
        if user_language == 'uk':
            await message.answer("Введіть код запрошення від капітана команди:")
        else:
            await message.answer("Введите код приглашения от капитана команды:")

        await state.set_state(RegistrationStates.waiting_for_invite_code)


# Обробка введення коду запрошення
async def process_invite_code(message: types.Message, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    invite_code = message.text.strip()
    result, captain_id = join_team(message.from_user.id, invite_code)

    if result == True:
        if user_language == 'uk':
            await message.answer("Ви успішно приєдналися до команди!")
        else:
            await message.answer("Вы успешно присоединились к команде!")

        # Після приєднання запитуємо Steam профіль
        if user_language == 'uk':
            await message.answer("Будь ласка, введіть ваш Steam профіль (посилання):")
        else:
            await message.answer("Пожалуйста, введите ваш Steam профиль (ссылка):")

        await state.set_state(RegistrationStates.waiting_for_steam_profile)  # Переходимо в стан очікування профілю

        # Надсилаємо повідомлення капітану про нового гравця
        captain_message = f"До вашої команди приєднався гравець: {message.from_user.first_name} (@{message.from_user.username})" if user_language == 'uk' else f"К вашей команде присоединился игрок: {message.from_user.first_name} (@{message.from_user.username})"
        try:
            await bot.send_message(captain_id, captain_message)
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення капітану: {e}")

    elif result == False:
        if user_language == 'uk':
            await message.answer("Команда вже заповнена.")
        else:
            await message.answer("Команда уже заполнена.")
    else:
        if user_language == 'uk':
            await message.answer("Невірний код запрошення. Спробуйте ще раз.")
        else:
            await message.answer("Неверный код приглашения. Попробуйте еще раз.")


# Обробник кнопки "👥 Переглянути команду"
async def cmd_view_team(message: types.Message):
    user_id = message.from_user.id

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    try:
        # Отримуємо мову користувача, передаючи з'єднання до функції
        user_language = get_user_language(user_id, db)

        team_id = check_user_team(user_id)

        if team_id:
            # Отримуємо назву команди
            cursor.execute("SELECT team_name FROM teams WHERE team_id = ?", (team_id,))
            team_name = cursor.fetchone()

            if team_name:
                # Отримуємо учасників команди
                team_members = get_team_members(team_id)

                if team_members:
                    if user_language == 'uk':
                        response = f"У вашій команді '{team_name[0]}':\n"
                    else:
                        response = f"В вашей команде '{team_name[0]}':\n"

                    # Додаємо учасників до відповіді
                    for member in team_members:
                        response += f"- {member[1]} (@{member[0]}) - {member[2]}\n"

                    await message.answer(response, reply_markup=team_options_keyboard())
                else:
                    if user_language == 'uk':
                        await message.answer(f"У вашій команді '{team_name[0]}' немає учасників.")
                    else:
                        await message.answer(f"В вашей команде '{team_name[0]}' нет участников.")
            else:
                if user_language == 'uk':
                    await message.answer("Не вдалося знайти назву команди.")
                else:
                    await message.answer("Не удалось найти название команды.")
        else:
            if user_language == 'uk':
                await message.answer("Ви не зареєстровані в жодній команді.")
            else:
                await message.answer("Вы не зарегистрированы ни в одной команде.")

    finally:
        # Закриваємо з'єднання після того, як отримали всі потрібні дані
        db.close()



# Обробка створення тікета
async def cmd_create_ticket(message: types.Message, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    if user_language == 'uk':
        await message.answer("Будь ласка, опишіть вашу проблему:")
    else:
        await message.answer("Пожалуйста, опишите вашу проблему:")

    await state.set_state(RegistrationStates.waiting_for_ticket_description)


# Обробка опису тікета
import os

async def process_ticket_description(message: types.Message, state: FSMContext, bot: Bot):
    description = ""

    # Отримуємо нікнейм користувача або ставимо "unknown", якщо він відсутній
    username = message.from_user.username if message.from_user.username else "unknown"

    # Обробка медіа (фото або відео)
    if message.photo or message.video:
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = 'photo'
        elif message.video:
            file_id = message.video.file_id
            file_type = 'video'

        # Отримуємо файл і зберігаємо його з додаванням нікнейму до назви
        file = await bot.get_file(file_id)
        file_path = f"ticketdoc/ticket_{message.message_id}_{username}_{file_type}.{file.file_path.split('.')[-1]}"
        await bot.download_file(file.file_path, file_path)

        # Додаємо текст про отримане фото або відео
        description = f"Отримано {file_type}."

        # Якщо є текст разом із медіа
        if message.caption:
            description = message.caption

        # Надсилаємо фото або відео всім адміністраторам
        admin_ids = get_admin_ids()
        for admin_id in admin_ids:
            if file_type == 'photo':
                await bot.send_photo(admin_id, photo=file_id, caption=f"Новий тікет від {message.from_user.first_name} (@{username}): {description}")
            elif file_type == 'video':
                await bot.send_video(admin_id, video=file_id, caption=f"Новий тікет від {message.from_user.first_name} (@{username}): {description}")

    # Якщо немає фото або відео, але є текстове повідомлення
    if message.text and not message.photo and not message.video:
        description = message.text.strip()

    # Якщо тільки фото або відео без тексту
    if not description:
        description = "Отримано фото/відео."

    # Створюємо тікет
    ticket_id = create_ticket(message.from_user.id, description)

    # Отримуємо мову користувача
    db = get_db_connection()
    user_language = get_user_language(message.from_user.id, db)
    db.close()

    if user_language == 'uk':
        await message.answer(f"Тікет #{ticket_id} створено. Адміністратори скоро дадуть відповідь.")
    else:
        await message.answer(f"Тикет #{ticket_id} создан. Администраторы скоро дадут ответ.")

    # Надсилаємо повідомлення всім адміністраторам про новий тікет
    admin_ids = get_admin_ids()
    for admin_id in admin_ids:
        if user_language == 'uk':
            await bot.send_message(admin_id, f"Новий тікет #{ticket_id} від {message.from_user.first_name} (@{username}): {description}")
        else:
            await bot.send_message(admin_id, f"Новый тикет #{ticket_id} от {message.from_user.first_name} (@{username}): {description}")

    await state.clear()



# Обробник для перегляду тікетів
async def cmd_view_tickets(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    if message.from_user.id in get_admin_ids():
        tickets = get_open_tickets()  # Функція для отримання відкритих тікетів

        if tickets:
            response = "Активні тікети:\n" if user_language == 'uk' else "Активные тикеты:\n"

            for ticket in tickets:
                response += f"#{ticket[0]}: {ticket[2]} (від користувача {ticket[1]})\n" if user_language == 'uk' else f"#{ticket[0]}: {ticket[2]} (от пользователя {ticket[1]})\n"
            await message.answer(response)
        else:
            no_tickets_message = "Немає відкритих тікетів." if user_language == 'uk' else "Нет открытых тикетов."
            await message.answer(no_tickets_message)
    else:
        no_access_message = "У вас немає прав для перегляду тікетів." if user_language == 'uk' else "У вас нет прав для просмотра тикетов."
        await message.answer(no_access_message)




async def cmd_reply_ticket(message: types.Message, bot: Bot, state: FSMContext, user_language=None):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    if user_language is None:  # Якщо мова не п ередана, отримуємо її з бази даних
        user_language = get_user_language(message.from_user.id)

    if message.from_user.id in get_admin_ids():
        try:
            # Виводимо мову для перевірки
            print(f"Мова адміністратора або користувача: {user_language}")

            # Розбиваємо повідомлення на частини
            parts = message.text.split(maxsplit=2)  # /reply <ticket_id> <відповідь>
            if len(parts) < 3:
                if user_language == 'uk':
                    await message.answer("Неправильний формат. Використовуйте: /reply <ticket_id> <відповідь>")
                else:
                    await message.answer("Неправильный формат. Используйте: /reply <ticket_id> <ответ>")
                return

            ticket_id = int(parts[1])  # Отримуємо ticket_id
            response = parts[2].strip()  # Отримуємо відповідь

            # Зберігаємо активний тікет у стані
            await state.update_data(active_ticket_id=ticket_id)
            await state.set_state(RegistrationStates.waiting_for_ticket_response)

            current_state = await state.get_state()
            print(f"Стан користувача після відповіді адміністратора: {current_state}")

            # Отримуємо user_id користувача, який створив тікет
            user_id = get_user_id_by_ticket(ticket_id)
            print(f"Отримано user_id для тікета #{ticket_id}: {user_id}")

            if user_id:
                # Отримуємо мову користувача, якщо її немає
                if not user_language:
                    user_language = get_user_language(user_id)

                # Додаємо відповідь до тікета
                add_ticket_response(ticket_id, message.from_user.id, response)

                # Створюємо клавіатуру з двома кнопками: Продовжити спілкування та Закрити тікет
                continue_button = InlineKeyboardButton(text="Продовжити спілкування" if user_language == 'uk' else "Продолжить общение", callback_data=f"continue_{ticket_id}")
                close_button = InlineKeyboardButton(text="Закрити тікет" if user_language == 'uk' else "Закрыть тикет", callback_data=f"close_{ticket_id}")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[continue_button], [close_button]])

                # Відправляємо повідомлення користувачу з клавіатурою на його мові
                if user_language == 'uk':
                    await bot.send_message(user_id, f"Адміністратор відповів на ваш тікет #{ticket_id}: {response}",
                                           reply_markup=keyboard)
                else:
                    await bot.send_message(user_id, f"Администратор ответил на ваш тикет #{ticket_id}: {response}",
                                           reply_markup=keyboard)

                await message.answer(f"Відповідь на тікет #{ticket_id} надіслано." if user_language == 'uk' else f"Ответ на тикет #{ticket_id} отправлен.")
            else:
                await message.answer(f"Тікет з ID {ticket_id} не знайдено." if user_language == 'uk' else f"Тикет с ID {ticket_id} не найден.")
        except (IndexError, ValueError) as e:
            print(f"Помилка: {e}")  # Лог для помилки
            if user_language == 'uk':
                await message.answer("Неправильний формат. Використовуйте: /reply <ticket_id> <відповідь>")
            else:
                await message.answer("Неправильный формат. Используйте: /reply <ticket_id> <ответ>")
    else:
        if user_language == 'uk':
            await message.answer("У вас немає прав для відповіді на тікети.")
        else:
            await message.answer("У вас нет прав для ответа на тикеты.")




# Обробник для закриття тікета через команду /close (для адміністраторів)
async def cmd_close_ticket(message: types.Message):
    parts = message.text.split(maxsplit=1)  # /close <ticket_id>

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    if len(parts) == 2:
        try:
            ticket_id = int(parts[1])
            # Оновлюємо статус тікета на "closed"
            cursor.execute('UPDATE tickets SET status = ? WHERE ticket_id = ?', ('closed', ticket_id))
            conn.commit()

            async def cmd_close_ticket(message: types.Message):
                user_language = get_user_language(message.from_user.id)  # Отримуємо мову користувача
                parts = message.text.split(maxsplit=1)  # /close <ticket_id>

                if len(parts) == 2:
                    try:
                        ticket_id = int(parts[1])
                        # Оновлюємо статус тікета на "closed"
                        cursor.execute('UPDATE tickets SET status = ? WHERE ticket_id = ?', ('closed', ticket_id))
                        conn.commit()

                        if user_language == 'uk':
                            await message.answer(f"Тікет #{ticket_id} успішно закрито.")
                        else:
                            await message.answer(f"Тикет #{ticket_id} успешно закрыт.")
                    except ValueError:
                        if user_language == 'uk':
                            await message.answer("Неправильний формат. Використовуйте: /close <ticket_id>")
                        else:
                            await message.answer("Неправильный формат. Используйте: /close <ticket_id>")
                else:
                    if user_language == 'uk':
                        await message.answer("Неправильний формат. Використовуйте: /close <ticket_id>")
                    else:
                        await message.answer("Неправильный формат. Используйте: /close <ticket_id>")

            await message.answer(f"Тікет #{ticket_id} успішно закрито.")
        except ValueError:
            await message.answer("Неправильний формат. Використовуйте: /close <ticket_id>")
    else:
        await message.answer("Неправильний формат. Використовуйте: /close <ticket_id>")

# Обробник для закриття тікета через callback-кнопку (для користувача)

async def process_close_ticket(callback_query: types.CallbackQuery):
    ticket_id = int(callback_query.data.split('_')[1])  # Отримуємо ticket_id з callback_data

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)  # Використовуємо callback_query

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    # Оновлюємо статус тікета на "closed"
    cursor.execute('UPDATE tickets SET status = ? WHERE ticket_id = ?', ('closed', ticket_id))
    conn.commit()

    # Сповіщаємо користувача про закриття тікета
    if user_language == 'uk':
        await callback_query.message.answer(f"Тікет #{ticket_id} успішно закрито.")
    else:
        await callback_query.message.answer(f"Тикет #{ticket_id} успешно закрыт.")

    # Видаляємо клавіатуру після закриття тікета
    await callback_query.message.edit_reply_markup(reply_markup=None)



async def user_reply_to_ticket(message: types.Message, state: FSMContext, bot: Bot):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    data = await state.get_data()
    ticket_id = data.get('active_ticket_id')  # Отримуємо активний тікет із стану

    if ticket_id:
        response = message.text.strip()
        print(f"Відповідь користувача на тікет {ticket_id}: {response}")

        # Додаємо відповідь до тікета
        add_ticket_response(ticket_id, message.from_user.id, response)

        # Отримуємо мову користувача
        user_language = get_user_language(message.from_user.id)

        # Сповіщаємо всіх адміністраторів
        admin_ids = get_admin_ids()
        for admin_id in admin_ids:
            await bot.send_message(admin_id,
                                   f"Новий коментар до тікета #{ticket_id} від {message.from_user.first_name}: {response}")

        # Відповідь користувачу на його мові
        if user_language == 'uk':
            await message.answer(f"Ваш коментар до тікета #{ticket_id} надіслано.")
        else:
            await message.answer(f"Ваш комментар к тикету #{ticket_id} отправлен.")

        await state.clear()  # Очищуємо стан після завершення
    else:
        # Спочатку отримаємо мову користувача перед тим, як надсилати відповідь
        user_language = get_user_language(message.from_user.id)

        if user_language == 'uk':
            await message.answer("Немає активного тікета для продовження діалогу.")
        else:
            await message.answer("Нет активного тикета для продолжения диалога.")


async def process_continue(callback_query: types.CallbackQuery, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id,db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    ticket_id = int(callback_query.data.split('_')[1])  # Отримуємо ticket_id з callback_data

    # Отримуємо мову користувача
    user_language = get_user_language(callback_query.from_user.id)

    # Повідомляємо користувачу про продовження діалогу
    if user_language == 'uk':
        await callback_query.message.answer(f"Продовжіть спілкування по тікету #{ticket_id}. Введіть ваше повідомлення:")
    else:
        await callback_query.message.answer(f"Продолжите общение по тикету #{ticket_id}. Введите ваше сообщение:")

    # Зберігаємо активний тікет у стані для користувача
    await state.update_data(active_ticket_id=ticket_id)
    await state.set_state(RegistrationStates.waiting_for_ticket_response)



async def cmd_add_match(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    if message.from_user.id in get_admin_ids():
        try:
            # Очікуємо формат: /add_match <дата> <час>
            parts = message.text.split(maxsplit=2)
            if len(parts) != 3:
                user_language = get_user_language(message.from_user.id)
                if user_language == 'uk':
                    await message.answer("Неправильний формат. Використовуйте: /add_match <дата> <час> (наприклад, 2024-09-20 18:00)")
                else:
                    await message.answer("Неправильный формат. Используйте: /add_match <дата> <время> (например, 2024-09-20 18:00)")
                return

            match_date = parts[1].strip()
            match_time = parts[2].strip()

            # Додаємо матч у базу даних
            add_match_to_db(match_date, match_time)

            user_language = get_user_language(message.from_user.id)
            if user_language == 'uk':
                await message.answer(f"Матч на {match_date} о {match_time} успішно додано.")
            else:
                await message.answer(f"Матч на {match_date} в {match_time} успешно добавлен.")
        except Exception as e:
            await message.answer(f"Сталася помилка: {e}")
    else:
        user_language = get_user_language(message.from_user.id)
        if user_language == 'uk':
            await message.answer("У вас немає прав для додавання матчів.")
        else:
            await message.answer("У вас нет прав для добавления матчей.")


# Функція для додавання нового матчу
async def add_match(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    try:
        # Отримуємо мову користувача
        user_language = get_user_language(message.from_user.id)

        # Розділяємо повідомлення, щоб отримати дату та час
        match_date, match_time = message.text.split()[1:3]

        # Додаємо матч до бази даних
        cursor.execute("INSERT INTO matches (match_date, match_time) VALUES (?, ?)", (match_date, match_time))
        conn.commit()

        # Відповідь на основі мови користувача
        if user_language == 'uk':
            await message.answer(f"Матч заплановано на {match_date} о {match_time}.")
        else:
            await message.answer(f"Матч запланирован на {match_date} в {match_time}.")
    except Exception as e:
        if user_language == 'uk':
            await message.answer(f"Сталася помилка: {e}")
        else:
            await message.answer(f"Произошла ошибка: {e}")



async def cmd_view_schedule(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    # Отримуємо заплановані матчі
    matches = get_matches()

    # Формуємо відповідь залежно від наявності матчів та мови користувача
    if matches:
        response = "Заплановані матчі:\n" if user_language == 'uk' else "Запланированные матчи:\n"
        for match in matches:
            response += f"- {match[0]} о {match[1]}\n"
    else:
        response = "Наразі немає запланованих матчів." if user_language == 'uk' else "На данный момент нет запланированных матчей."

    # Відправляємо відповідь користувачу
    await message.answer(response)




async def cmd_view_schedule_button(message: types.Message):
    await cmd_view_schedule(message)


async def cmd_delete_match(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    # Отримуємо мову користувача
    user_language = get_user_language(message.from_user.id)

    if message.from_user.id in get_admin_ids():
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) != 2:
                if user_language == 'uk':
                    await message.answer("Неправильний формат. Використовуйте: /delete_match <match_id>")
                else:
                    await message.answer("Неправильный формат. Используйте: /delete_match <match_id>")
                return

            match_id = int(parts[1].strip())
            delete_match(match_id)

            if user_language == 'uk':
                await message.answer(f"Матч з ID {match_id} успішно видалено.")
            else:
                await message.answer(f"Матч с ID {match_id} успешно удалён.")
        except Exception as e:
            if user_language == 'uk':
                await message.answer(f"Сталася помилка: {e}")
            else:
                await message.answer(f"Произошла ошибка: {e}")
    else:
        if user_language == 'uk':
            await message.answer("У вас немає прав для видалення матчів.")
        else:
            await message.answer("У вас нет прав для удаления матчей.")




async def cmd_faq(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    try:
        # Вибираємо файл FAQ залежно від мови користувача
        if user_language == 'uk':
            faq_file = 'faq.txt'
        else:
            faq_file = 'faqru.txt'

        # Читаємо відповідний файл
        with open(faq_file, 'r', encoding='utf-8') as file:
            faq_text = file.read()

        # Відправляємо користувачу вміст файлу
        await message.answer(faq_text)
    except Exception as e:
        if user_language == 'uk':
            await message.answer(f"Сталася помилка при завантаженні FAQ: {e}")
        else:
            await message.answer(f"Произошла ошибка при загрузке FAQ: {e}")



async def cmd_rules(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    try:
        # Вибираємо файл правил залежно від мови користувача
        if user_language == 'uk':
            rules_file = "rules.txt"
        else:
            rules_file = "rulesru.txt"

        # Читаємо відповідний файл з правилами
        with open(rules_file, "r", encoding="utf-8") as file:
            rules = file.read()

        # Відправляємо користувачу правила
        await message.answer(rules)
    except Exception as e:
        if user_language == 'uk':
            await message.answer(f"Сталася помилка при завантаженні правил: {e}")
        else:
            await message.answer(f"Произошла ошибка при загрузке правил: {e}")




async def cmd_view_teams_with_members(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    if message.from_user.id in get_admin_ids():
        teams = get_teams_with_members()
        if teams:
            if user_language == 'uk':
                response = "Зареєстровані команди та їхні учасники:\n"
            else:
                response = "Зарегистрированные команды и их участники:\n"

            current_team = None
            for team in teams:
                team_name, username, first_name, last_name, steam_profile = team
                if team_name != current_team:
                    if current_team is not None:
                        response += "\n"  # Відділяємо команди між собою
                    response += f"\nКоманда: {team_name}\n"  # Виводимо назву команди
                    current_team = team_name
                response += f"  - @{username} ({first_name or ''} {last_name or ''}) - {steam_profile}\n"

            await message.answer(response)
        else:
            await message.answer("Немає зареєстрованих команд." if user_language == 'uk' else "Нет зарегистрированных команд.")
    else:
        await message.answer("У вас немає прав для перегляду команд." if user_language == 'uk' else "У вас нет прав для просмотра команд.")



# Обробник кнопки для редагування назви команди
async def process_edit_team_name(callback_query: types.CallbackQuery, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    user_language = get_user_language(callback_query.from_user.id)
    prompt = "Введіть нову назву вашої команди:" if user_language == 'uk' else "Введите новое название вашей команды:"
    await callback_query.message.answer(prompt)
    await state.set_state(RegistrationStates.waiting_for_new_team_name)



# Обробка нової назви команди
async def process_new_team_name(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    new_team_name = message.text.strip()

    # Оновлюємо назву команди в базі даних
    cursor.execute('UPDATE teams SET team_name = ? WHERE team_id = (SELECT team_id FROM users WHERE user_id = ?)', (new_team_name, message.from_user.id))
    conn.commit()

    confirmation = f"Назва команди успішно змінена на: {new_team_name}" if user_language == 'uk' else f"Название команды успешно изменено на: {new_team_name}"
    await message.answer(confirmation)
    await state.clear()


# Обробник для видалення команди
async def cmd_delete_team(message: types.Message, state: FSMContext):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    user_id = message.from_user.id
    team_id = check_user_team(user_id)

    if team_id:
        delete_team(team_id)
        if user_language == 'uk':
            await message.answer("Ваша команда видалена.Для продовження надішліть /start у чат.")
            await message.answer("Для продовження надішліть /start у чат.")
        else:
            await message.answer("Ваша команда удалена.Для продолжения отправьте /start в чат")
            await message.answer("Для продолжения отправьте /start в чат.")
        await state.clear()
    else:
        if user_language == 'uk':
            await message.answer("Ви не є капітаном жодної команди.")
        else:
            await message.answer("Вы не капитан ни одной команды.")



async def cmd_pay_participation(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    try:
        payment_status = check_payment_status(message.from_user.id)

        if payment_status == "Done":
            if user_language == 'uk':
                await message.answer("Ви вже оплатили вхід за турнір.")
            else:
                await message.answer("Вы уже оплатили участие в турнире.")
        else:
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="Оплатити за себе" if user_language == 'uk' else "Оплатить за себя", callback_data="pay_self"),
                    types.InlineKeyboardButton(text="Оплатити за команду" if user_language == 'uk' else "Оплатить за команду", callback_data="pay_team")
                ]
            ])
            await message.answer("Оберіть варіант оплати:" if user_language == 'uk' else "Выберите вариант оплаты:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Сталася помилка: {e}" if user_language == 'uk' else f"Произошла ошибка: {e}")

async def process_payment_for_self(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    if user_language == 'uk':
        await callback_query.message.answer("Оплатіть за участь. Ваші реквізити: https://send.monobank.ua/jar/example")
        await callback_query.message.answer("Після оплати завантажте скріншот.")
    else:
        await callback_query.message.answer("Оплатите участие. Ваши реквизиты: https://send.monobank.ua/jar/example")
        await callback_query.message.answer("После оплаты загрузите скриншот.")




async def process_payment_for_team(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    if user_language == 'uk':
        await callback_query.message.answer("Оплатіть за участь команди. Ваші реквізити: https://send.monobank.ua/jar/team-example")
        await callback_query.message.answer("Після оплати завантажте скріншот.")
    else:
        await callback_query.message.answer("Оплатите участие команды. Ваши реквизиты: https://send.monobank.ua/jar/team-example")
        await callback_query.message.answer("После оплаты загрузите скриншот.")


async def process_payment_screenshot(message: types.Message):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(message.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    try:
        # Створюємо клавіатуру з кнопками для підтвердження оплати, але тільки для адміністраторів
        approve_text = "Оплата прийшла" if user_language == 'uk' else "Оплата прошла"
        deny_text = "Оплата не прийшла" if user_language == 'uk' else "Оплата не прошла"
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text=approve_text, callback_data=f"payment_approved_{message.from_user.id}"),
                types.InlineKeyboardButton(text=deny_text, callback_data=f"payment_denied_{message.from_user.id}")
            ]
        ])

        if message.photo:
            photo = message.photo[-1].file_id

            admin_ids = get_admin_ids()  # Отримати список адміністраторів
            for admin_id in admin_ids:
                try:
                    await message.bot.send_photo(
                        admin_id,
                        photo=photo,
                        caption=f"Отримано скріншот від {message.from_user.username} для перевірки оплати." if user_language == 'uk' else f"Получен скриншот от {message.from_user.username} для проверки оплаты.",
                        reply_markup=keyboard  # Клавіатура тільки для адміністраторів
                    )
                except Exception as e:
                    await message.answer(f"Сталася помилка під час відправлення повідомлення адміністратору: {admin_id}. Помилка: {e}")

            # Користувачу надсилаємо тільки це повідомлення, без клавіатури
            await message.answer("Скріншот успішно надіслано на перевірку адміністратору." if user_language == 'uk' else "Скриншот успешно отправлен на проверку администратору.")
        else:
            await message.answer("Будь ласка, надішліть скріншот." if user_language == 'uk' else "Пожалуйста, отправьте скриншот.")

    except Exception as e:
        await message.answer(f"Сталася помилка: {e}" if user_language == 'uk' else f"Произошла ошибка: {e}")




async def process_payment_confirmation(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    user_id = callback_query.data.split('_')[2]

    update_payment_status(user_id, "Done")
    await callback_query.message.answer(f"Оплата від користувача {user_id} була підтверджена." if user_language == 'uk' else f"Оплата от пользователя {user_id} была подтверждена.")




async def process_payment_rejection(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    user_id = callback_query.data.split('_')[2]

    update_payment_status(user_id, "Failed")
    await callback_query.message.answer(f"Оплата від користувача {user_id} була відхилена." if user_language == 'uk' else f"Оплата от пользователя {user_id} была отклонена.")



async def process_payment_option(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    if callback_query.data == "pay_self":
        await callback_query.message.answer("Для оплати участі за себе, перейдіть за посиланням: [Ваша силка на банку або карту]" if user_language == 'uk' else "Для оплаты участия за себя, перейдите по ссылке: [Ваша ссылка на банк или карту]")
    elif callback_query.data == "pay_team":
        await callback_query.message.answer("Для оплати участі за команду, перейдіть за посиланням: [Ваша силка на банку або карту]" if user_language == 'uk' else "Для оплаты участия за команду, перейдите по ссылке: [Ваша ссылка на банк или карту]")

    await callback_query.answer()

# Обробник для підтвердження оплати
async def payment_approved(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача, передаючи з'єднання до функції
    user_language = get_user_language(callback_query.from_user.id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()


    user_id = callback_query.data.split('_')[-1]


    update_payment_status(user_id, "Done")

    confirmation_message = "Оплата пройшла успішно! Тепер ти можеш брати участь у турнірі. Не забудь приєднатися до нашого Discord: https://discord.gg/BfCzeXVEru" if user_language == 'uk' else "Оплата прошла успешно! Теперь ты можешь участвовать в турнире. Не забудь присоединиться к нашему Discord: https://discord.gg/BfCzeXVEru"
    await callback_query.bot.send_message(user_id, confirmation_message)

    await callback_query.message.answer("Оплата прийшла, статус змінено на 'Done'." if user_language == 'uk' else "Оплата прошла, статус изменен на 'Done'.")
    await callback_query.answer()


# Обробник для відмови в оплаті
async def payment_denied(callback_query: types.CallbackQuery):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо user_id з callback_data
    user_id = callback_query.data.split('_')[-1]

    # Отримуємо мову користувача з бази даних
    user_language = get_user_language(user_id, db)

    # Закриваємо з'єднання після того, як отримали мову користувача
    db.close()

    rejection_message = "Оплата не пройшла. Якщо ти впевнений у тому, що оплатив, відкрий тікет тут або в нашому Discord для допомоги: https://discord.gg/BfCzeXVEru" if user_language == 'uk' else "Оплата не прошла. Если ты уверен, что оплатил, открой тикет здесь или в нашем Discord для помощи: https://discord.gg/BfCzeXVEru"
    await callback_query.bot.send_message(user_id, rejection_message)

    await callback_query.message.answer("Оплата не пройшла, користувачу надіслано повідомлення." if user_language == 'uk' else "Оплата не прошла, пользователю отправлено сообщение.")
    await callback_query.answer()




async def process_language_choice(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    try:
        # Оновлюємо мову користувача в базі даних
        print(f"Оновлюємо мову користувача {user_id} на {lang}")
        set_user_language(user_id, lang)

        # Відправляємо підтвердження вибору мови
        if lang == 'uk':
            await callback_query.message.answer("Ви обрали українську мову.")
        else:
            await callback_query.message.answer("Вы выбрали русский язык.")

        # Після вибору мови показуємо головне меню
        await send_main_menu(callback_query.message, user_id)

    except Exception as e:
        print(f"Помилка при оновленні мови користувача: {e}")
        await callback_query.message.answer("Сталася помилка, спробуйте ще раз.")
    finally:
        # Закриваємо з'єднання з базою
        db.close()



async def send_main_menu(message: types.Message, user_id: int):
    # Отримуємо з'єднання з базою даних
    db = get_db_connection()

    # Отримуємо мову користувача
    user_language = get_user_language(user_id, db)

    # Закриваємо з'єднання з базою
    db.close()

    # Відправляємо повідомлення з відповідним текстом та меню
    if user_language == 'uk':
        welcome_text = "Вітаємо на турнірі з RUST! Оберіть одну з опцій:"
    else:
        welcome_text = "Добро пожаловать на турнир по RUST! Выберите один из вариантов:"

    # Передаємо мову користувача у функцію main_menu_keyboard
    await message.answer(welcome_text, reply_markup=main_menu_keyboard(user_language))


# Функція для реєстрації всіх обробників
def register_message_handlers(dp: Dispatcher):
    """Реєструємо хендлери для текстових повідомлень"""
    dp.message.register(cmd_start, F.text == "/start")

    # Реєстрація для українських команд
    dp.message.register(cmd_register_team, F.text == "📝 Реєстрація команди")
    dp.message.register(cmd_join_team, F.text == "👥 Приєднатися до команди")
    dp.message.register(cmd_view_team, F.text == "👥 Переглянути команду")
    dp.message.register(cmd_create_ticket, F.text == "📝 Створити тікет")
    dp.message.register(cmd_view_tickets, F.text == "👁 Переглянути тікети")
    dp.message.register(cmd_view_schedule_button, F.text == "📆 Розклад матчів")
    dp.message.register(cmd_view_schedule, F.text == "🗓 Розклад матчів")
    dp.message.register(cmd_faq, F.text == "ℹ️ FAQ")
    dp.message.register(cmd_rules, F.text == "📜 Правила турніру")
    dp.message.register(cmd_pay_participation, F.text == "💳 Оплатити участь")

    # Реєстрація для російських команд
    dp.message.register(cmd_register_team, F.text == "📝 Регистрация команды")
    dp.message.register(cmd_join_team, F.text == "👥 Присоединиться к команде")
    dp.message.register(cmd_view_team, F.text == "👥 Просмотреть команду")
    dp.message.register(cmd_create_ticket, F.text == "📝 Создать тикет")
    dp.message.register(cmd_view_tickets, F.text == "👁 Просмотреть тикеты")
    dp.message.register(cmd_view_schedule_button, F.text == "📆 Расписание матчей")
    dp.message.register(cmd_view_schedule, F.text == "🗓 Расписание матчей")
    dp.message.register(cmd_faq, F.text == "ℹ️ FAQ")
    dp.message.register(cmd_rules, F.text == "📜 Правила турнира")
    dp.message.register(cmd_pay_participation, F.text == "💳 Оплатить участие")

    # Інші хендлери без залежності від мови
    dp.message.register(process_team_name, RegistrationStates.waiting_for_team_name)
    dp.message.register(process_steam_profile, RegistrationStates.waiting_for_steam_profile)
    dp.message.register(process_invite_code, RegistrationStates.waiting_for_invite_code)
    dp.message.register(process_ticket_description, RegistrationStates.waiting_for_ticket_description)
    dp.message.register(cmd_reply_ticket, F.text.startswith("/reply"))
    dp.message.register(user_reply_to_ticket, RegistrationStates.waiting_for_ticket_response)
    dp.message.register(cmd_close_ticket, F.text.startswith("/close"))
    dp.message.register(cmd_add_match, F.text.startswith("/add_match"))
    dp.message.register(cmd_delete_match, F.text.startswith("/delete_match"))
    dp.message.register(cmd_view_teams_with_members, F.text.startswith("/view_teams"))
    dp.message.register(process_new_team_name, RegistrationStates.waiting_for_new_team_name)
    dp.message.register(process_payment_screenshot, F.content_type == types.ContentType.PHOTO)

def register_callback_handlers(dp: Dispatcher):
    """Реєструємо хендлери для callback даних"""
    dp.callback_query.register(process_continue, F.data.startswith('continue_'))
    dp.callback_query.register(process_close_ticket, F.data.startswith('close_'))
    dp.callback_query.register(process_edit_team_name, F.data == "edit_team_name")
    dp.callback_query.register(cmd_delete_team, F.data == "delete_team")
    dp.callback_query.register(process_payment_for_self, F.data == "pay_for_self")
    dp.callback_query.register(process_payment_for_team, F.data == "pay_for_team")
    dp.callback_query.register(process_payment_confirmation, F.data.startswith("payment_confirm_"))
    dp.callback_query.register(process_payment_rejection, F.data.startswith("payment_reject_"))
    dp.callback_query.register(process_payment_option, F.data.in_({"pay_self", "pay_team"}))
    dp.callback_query.register(payment_approved, lambda c: c.data.startswith('payment_approved'))
    dp.callback_query.register(payment_denied, lambda c: c.data.startswith('payment_denied'))
    dp.callback_query.register(process_language_choice, lambda c: c.data.startswith('lang_'))

def register_handlers(dp: Dispatcher):
    """Головна функція для реєстрації всіх хендлерів"""
    register_message_handlers(dp)
    register_callback_handlers(dp)






















