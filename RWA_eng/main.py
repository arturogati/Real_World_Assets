"""
TokenizeLocal Console App — Mirror version of the Telegram bot
"""

import os
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Initialize
logger = Logger("TokenizeLocalConsole")
CHECKO_API_KEY = "yCEWUepinagwBCn3"  # Replace with .env loading
db = DBManager()
user_manager = UserManager()

# Global session state
current_user_email = None
current_role = None  # "user" or "company"


def get_help_text(role: str) -> str:
    """Returns help message based on current role"""
    if role == "company":
        return """
💼 You are in **Company Mode**.

Available commands:
4. Issue Tokens
8. Help
9. Exit

💡 To restart, enter 0
        """.strip()
    else:
        return """
👤 You are in **User Mode**.

Available commands:
1. Login as User
2. Register as User
5. List Companies
6. Buy Tokens
7. My Balance
8. Help
9. Exit

💡 To restart, enter 0
        """.strip()


def show_help():
    """Displays help based on current role"""
    role = current_role or "user"
    print(get_help_text(role))


def reset_session():
    """Resets the session (like /start)"""
    global current_user_email, current_role
    current_user_email = None
    current_role = None
    print("\n🔄 Session reset. You can start fresh.")


def login_user():
    """User login"""
    global current_user_email, current_role
    print("\n🔐 Login as User")
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()

    if user_manager.authenticate_user(email, password):
        current_user_email = email
        current_role = "user"
        print(f"[INFO] Login successful for {email}")
        show_help()
    else:
        print("[ERROR] Invalid email or password.")


def register_user():
    """User registration"""
    global current_user_email, current_role
    print("\n📝 Register New User")
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        user_manager.register_user(name, email, password)
        current_user_email = email
        current_role = "user"
        print(f"[INFO] Registration successful! Welcome, {name}!")
        show_help()
    except UserAlreadyExists:
        print("[ERROR] User with this email already exists.")
    except InvalidEmail:
        print("[ERROR] Invalid email format.")
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")


def company_mode():
    """Company mode: issue tokens"""
    print("\n🏢 Company Mode")
    inn = input("Enter company INN: ").strip()

    if len(inn) not in (10, 12) or not inn.isdigit():
        print("[ERROR] Invalid INN format. Must be 10 or 12 digits.")
        return

    try:
        api_client = FinancialAPIClient(CHECKO_API_KEY)
        company_info = api_client.get_company_info(inn)

        if company_info.get("status") != "Действует":
            print(f"[ERROR] Company is not active. Status: {company_info['status']}")
            return

        print(f"[INFO] Company found: {company_info['name']}")

        amount_input = input("How many tokens to issue? ").strip()
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        db.register_or_update_business(inn, company_info["name"])
        db.issue_tokens(inn, amount)
        print(f"[INFO] ✅ Successfully issued {amount} tokens for '{company_info['name']}'")

    except Exception as e:
        print(f"[ERROR] Token issuance failed: {e}")


def show_companies():
    """Show list of available companies"""
    print("\n📋 Available Companies:")
    companies = db.get_all_issuances()
    if not companies:
        print("No companies available.")
        return

    for idx, (inn, name, amount, _) in enumerate(companies):
        print(f"{idx+1}. {name} (INN: {inn}) — Tokens available: {amount or 0}")


def buy_tokens():
    """Buy tokens as a user"""
    if not current_user_email:
        print("[ERROR] Please log in as a user first.")
        return

    print("\n🛒 Buy Tokens")
    show_companies()
    choice = input("Choose company number: ").strip()
    amount_input = input("How many tokens to buy? ").strip()

    try:
        company_num = int(choice)
        amount = float(amount_input)

        if company_num <= 0 or amount <= 0:
            raise ValueError("Numbers must be positive")

        companies = db.get_all_issuances()
        if company_num > len(companies):
            raise ValueError("No such company")

        inn, name, available, _ = companies[company_num - 1]
        if available is None or amount > available:
            raise ValueError(f"Not enough tokens. Available: {available or 0}")

        db.issue_tokens(inn, -amount)
        db.add_user_tokens(email=current_user_email, business_inn=inn, amount=amount)

        user_tokens = db.get_user_tokens(current_user_email)
        current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

        print(f"\n✅ Successfully bought {amount} tokens of '{name}'")
        print(f"Your current balance: {current_amount} tokens")

    except ValueError as e:
        print(f"[ERROR] Input error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def show_balance():
    """Show user's token balance"""
    if not current_user_email:
        print("[ERROR] Please log in first.")
        return

    print("\n💰 Your Balance:")
    tokens = db.get_user_tokens(current_user_email)
    if not tokens:
        print("You have no tokens yet.")
        return
    for row in tokens:
        inn, name, token_count = row
        print(f"- {name}: {token_count} tokens")


def run_full_demo():
    """Main application loop"""
    print("=== 🌐 TokenizeLocal Console App ===")
    show_help()

    while True:
        try:
            choice = input("\nEnter your choice (0-9): ").strip()

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
                print("[INFO] You have selected Company Mode.")
                show_help()

            elif choice == "4":
                if current_role == "company":
                    company_mode()
                else:
                    print("[ERROR] Please select Company Mode first (command 3).")

            elif choice == "5":
                show_companies()

            elif choice == "6":
                buy_tokens()

            elif choice == "7":
                show_balance()

            elif choice == "8":
                show_help()

            elif choice == "9":
                print("👋 Exiting TokenizeLocal...")
                break

            else:
                print("[ERROR] Invalid choice. Enter 0-9.")

        except KeyboardInterrupt:
            print("\n\n👋 Program interrupted by user.")
            break
        except Exception as e:
            print(f"[CRITICAL] Unexpected error: {e}")


if __name__ == "__main__":
    run_full_demo()
