"""
TokenizeLocal Console App — зеркальная версия Telegram-бота
"""

import os
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Инициализация
logger = Logger("TokenizeLocalConsole")
checko_api_key = "yCEWUepinagwBCn3"  # или загрузите из .env
db = DBManager()
user_manager = UserManager()

# Глобальные переменные состояния
current_user_email = None
current_role = None  # "user" или "company"


def get_help_text(role: str):
    """Возвращает подсказку в зависимости от роли"""
    if role == "company":
        return """
💼 Вы в режиме компании.

Доступные команды:
4. Выпустить токены
8. Помощь
9. Выход

💡 Чтобы начать сначала — введите 0
        """.strip()
    else:
        return """
👤 Вы в режиме пользователя.

Доступные команды:
1. Войти как пользователь
2. Зарегистрироваться как пользователь
5. Список компаний
6. Купить токены
7. Мой баланс
8. Помощь
9. Выход

💡 Чтобы начать сначала — введите 0
        """.strip()


def show_help():
    """Показывает подсказку в зависимости от роли"""
    role = current_role or "user"
    print(get_help_text(role))


def reset_session():
    """Сбрасывает сессию (аналог /start)"""
    global current_user_email, current_role
    current_user_email = None
    current_role = None
    print("\n🔄 Сессия сброшена. Вы можете начать сначала.")


def login_user():
    """Вход пользователя"""
    global current_user_email, current_role
    print("\n🔐 Вход как пользователь")
    email = input("Введите email: ").strip()
    password = input("Введите пароль: ").strip()

    if user_manager.authenticate_user(email, password):
        current_user_email = email
        current_role = "user"
        print(f"[INFO] Вход выполнен успешно для {email}")
        show_help()
    else:
        print("[ERROR] Неверный email или пароль.")


def register_user():
    """Регистрация пользователя"""
    global current_user_email, current_role
    print("\n📝 Регистрация нового пользователя")
    name = input("Имя: ").strip()
    email = input("Email: ").strip()
    password = input("Пароль: ").strip()

    try:
        user_manager.register_user(name, email, password)
        current_user_email = email
        current_role = "user"
        print(f"[INFO] Регистрация успешна! Добро пожаловать, {name}!")
        show_help()
    except UserAlreadyExists:
        print("[ERROR] Пользователь с таким email уже существует.")
    except InvalidEmail:
        print("[ERROR] Некорректный email.")
    except Exception as e:
        print(f"[ERROR] Ошибка регистрации: {e}")


def company_mode():
    """Режим компании: выпуск токенов"""
    print("\n🏢 Режим компании")
    inn = input("Введите ИНН компании: ").strip()

    if len(inn) not in (10, 12) or not inn.isdigit():
        print("[ERROR] Неверный формат ИНН. Должно быть 10 или 12 цифр.")
        return

    try:
        api_client = FinancialAPIClient(checko_api_key)
        company_info = api_client.get_company_info(inn)

        if company_info.get("status") != "Действует":
            print(f"[ERROR] Компания не действует. Статус: {company_info['status']}")
            return

        print(f"[INFO] Компания найдена: {company_info['name']}")

        amount_input = input("Сколько токенов выпустить? ").strip()
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Количество должно быть положительным.")

        db.register_or_update_business(inn, company_info["name"])
        db.issue_tokens(inn, amount)
        print(f"[INFO] ✅ Успешно выпущено {amount} токенов для компании '{company_info['name']}'")

    except Exception as e:
        print(f"[ERROR] Ошибка выпуска токенов: {e}")


def show_companies():
    """Показать список компаний"""
    print("\n📋 Доступные компании:")
    companies = db.get_all_issuances()
    if not companies:
        print("Нет доступных компаний.")
        return

    for idx, (inn, name, amount, _) in enumerate(companies):
        print(f"{idx+1}. {name} (ИНН: {inn}) — доступно токенов: {amount or 0}")


def buy_tokens():
    """Покупка токенов пользователем"""
    if not current_user_email:
        print("[ERROR] Сначала войдите как пользователь.")
        return

    print("\n🛒 Покупка токенов")
    show_companies()
    choice = input("Выберите номер компании: ").strip()
    amount_input = input("Сколько токенов хотите купить? ").strip()

    try:
        company_num = int(choice)
        amount = float(amount_input)

        if company_num <= 0 or amount <= 0:
            raise ValueError("Числа должны быть положительными")

        companies = db.get_all_issuances()
        if company_num > len(companies):
            raise ValueError("Компании с таким номером не существует")

        inn, name, available, _ = companies[company_num - 1]
        if available is None or amount > available:
            raise ValueError(f"Недостаточно токенов. Доступно: {available or 0}")

        db.issue_tokens(inn, -amount)
        db.add_user_tokens(email=current_user_email, business_inn=inn, amount=amount)

        user_tokens = db.get_user_tokens(current_user_email)
        current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

        print(f"\n✅ Успешно куплено {amount} токенов компании '{name}'")
        print(f"Ваш текущий баланс: {current_amount} токенов")

    except ValueError as e:
        print(f"[ERROR] Ошибка ввода: {e}")
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")


def show_balance():
    """Показать баланс пользователя"""
    if not current_user_email:
        print("[ERROR] Сначала войдите как пользователь.")
        return

    print("\n💰 Ваш баланс:")
    tokens = db.get_user_tokens(current_user_email)
    if not tokens:
        print("У вас пока нет токенов.")
        return
    for row in tokens:
        inn, name, token_count = row
        print(f"- {name}: {token_count} токенов")


def run_full_demo():
    """Основной цикл приложения"""
    print("=== 🌐 TokenizeLocal Console App ===")
    show_help()

    while True:
        try:
            choice = input("\nВыберите действие (введите номер): ").strip()

            if choice == "0":
                reset_session()
                show_help()

            elif choice == "1":
                login_user()

            elif choice == "2":
                register_user()

            elif choice == "3":
                global current_role
                current_role = "company"
                print("[INFO] Вы выбрали режим компании.")
                show_help()

            elif choice == "4":
                if current_role == "company":
                    company_mode()
                else:
                    print("[ERROR] Выберите роль компании (команда 3).")

            elif choice == "5":
                show_companies()

            elif choice == "6":
                buy_tokens()

            elif choice == "7":
                show_balance()

            elif choice == "8":
                show_help()

            elif choice == "9":
                print("👋 Выход из TokenizeLocal...")
                break

            else:
                print("[ERROR] Неверный выбор. Введите 0-9.")

        except KeyboardInterrupt:
            print("\n\n👋 Программа завершена пользователем.")
            break
        except Exception as e:
            print(f"[CRITICAL] Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    run_full_demo()
