from aiogram.fsm.state import StatesGroup, State

class RegistrationStates(StatesGroup):
    waiting_for_team_name = State()
    waiting_for_steam_profile = State()
    waiting_for_invite_code = State()
    waiting_for_ticket_description = State()
    waiting_for_ticket_response = State()  # Додаємо новий стан для відповіді на тікет
    waiting_for_new_team_name = State()
