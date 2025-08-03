"""
TokenizeLocal Telegram Bot — final version
"""
import os
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Logger
logger = Logger("TokenizeLocalBot")

# Tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHECKO_API_KEY = os.getenv("CHECKO_API_KEY", "yCEWUepinagwBCn3")


class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = CHECKO_API_KEY
        self.user_states = {}

    def get_user_state(self, user_id: int) -> Dict:
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}, "help_shown": False}
        return self.user_states[user_id]

    def get_help_text(self, role: str) -> str:
        """Returns a help message depending on the role"""
        if role == "company":
            return (
                "💼 You are in company mode.\n"
                "Available commands:\n"
                "/issue_tokens — Issue tokens\n"
                "/help — Help\n"
                "💡 To restart, type /start"
            )
        else:
            return (
                "👤 You are in user mode.\n"
                "Available commands:\n"
                "/register — Register\n"
                "/login — Login\n"
                "/companies — List of companies\n"
                "/buy — Buy tokens\n"
                "/balance — My balance\n"
                "/dividends — My dividends\n"
                "/help — Help\n"
                "💡 To restart, type /start"
            )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /start — role selection"""
        keyboard = [
            [InlineKeyboardButton("👤 User", callback_data="role_user")],
            [InlineKeyboardButton("🏢 Company", callback_data="role_company")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Welcome to TokenizeLocal!\n"
            "Please select your role:",
            reply_markup=reply_markup
        )
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        user_state["role"] = None
        user_state["help_shown"] = False

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help — displays current help message"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        role = user_state.get("role", "user")
        help_text = self.get_help_text(role)
        await update.message.reply_text(help_text, parse_mode=None)

    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles role selection"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        user_state = self.get_user_state(user_id)

        if query.data == "role_user":
            user_state["role"] = "user"
            await query.edit_message_text("✅ You have selected user mode.")
        elif query.data == "role_company":
            user_state["role"] = "company"
            await query.edit_message_text("✅ You have selected company mode.")
        else:
            await query.edit_message_text("❌ Unknown role.")
            return

        # ✅ Always send help message
        help_text = self.get_help_text(user_state["role"])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_text,
            parse_mode=None  # 🔥 Key: Markdown removed
        )
        user_state["help_shown"] = True

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("❌ This command is only for users.")
            return
        await update.message.reply_text("Enter your name, email, and password separated by spaces\n"
                                        "Example: Ivan user@example.com 1234")
        user_state["awaiting_register"] = True

    async def login_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("❌ This command is only for users.")
            return
        await update.message.reply_text("Enter your email and password separated by a space")
        user_state["awaiting_login"] = True

    async def issue_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "company":
            await update.message.reply_text("❌ This command is only for companies.")
            return
        await update.message.reply_text("Enter the company INN (10 or 12 digits):")
        user_state["awaiting_inn"] = True

    async def process_inn_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        inn = update.message.text.strip()
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Invalid INN format.")
            return
        try:
            api_client = FinancialAPIClient(self.checko_api_key)
            company_info = api_client.get_company_info(inn)
            user_state["company_data"] = {"inn": inn, "name": company_info["name"]}
            await update.message.reply_text(f"✅ {company_info['name']}\n"
                                            f"Now enter the number of tokens:")
            user_state["awaiting_token_amount"] = True
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        amount_text = update.message.text.strip()
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            company_data = user_state.get("company_data")
            if not company_data:
                raise ValueError("Company data not found")
            db = DBManager()
            db.register_or_update_business(company_data["inn"], company_data["name"])
            db.issue_tokens(company_data["inn"], amount)
            await update.message.reply_text(f"✅ Issued {amount} tokens for {company_data['name']}!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            user_state.pop("awaiting_token_amount", None)
            user_state.pop("company_data", None)

    async def show_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("No companies available.")
            return
        response = "📋 Available companies:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} — {amount or 0} tokens\n"
        await update.message.reply_text(response)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            await update.message.reply_text("You have no tokens.")
            return
        response = "💰 Your balance:\n"
        for inn, name, amount in user_tokens:
            response += f"- {name}: {amount} tokens\n"
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("❌ This command is only for users.")
            return
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("❌ No companies available.")
            return
        response = "Select a company:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} ({amount or 0})\n"
        response += "\nEnter: NUMBER AMOUNT\nExample: 1 10"
        await update.message.reply_text(response)
        user_state["awaiting_purchase"] = True

    async def handle_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str):
        user_state = self.get_user_state(user_id)
        try:
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("Enter two values")
            company_num = int(parts[0]); amount = float(parts[1])
            if company_num <= 0 or amount <= 0:
                raise ValueError("Values must be positive")
            db = DBManager()
            companies = db.get_all_issuances()
            if company_num > len(companies):
                raise ValueError("Company not found")
            inn, name, available, _ = companies[company_num - 1]
            if available is None or amount > available:
                raise ValueError(f"Not enough tokens. Available: {available or 0}")
            email = f"{user_id}@telegram.local"
            db.issue_tokens(inn, -amount)
            db.add_user_tokens(email, inn, amount)
            current = next((t[2] for t in db.get_user_tokens(email) if t[0] == inn), 0)
            await update.message.reply_text(f"✅ Purchased {amount} tokens of {name}!\nBalance: {current}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            user_state.pop("awaiting_purchase", None)

    async def show_dividends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT d.business_inn, b.name, d.distribution_date, d.dividend_pool, d.token_price
            FROM dividend_history d
            JOIN businesses b ON d.business_inn = b.inn
            JOIN user_tokens u ON d.business_inn = u.business_inn
            WHERE u.email = ?
            ORDER BY d.distribution_date DESC
            LIMIT 5
        """, (email,))
        rows = cursor.fetchall()
        if not rows:
            await update.message.reply_text("You have not received any dividends.")
            return
        response = "📈 Your dividends:\n"
        for inn, name, date, pool, price in rows:
            tokens = next((t[2] for t in db.get_user_tokens(email) if t[0] == inn), 0)
            if tokens > 0:
                dividend = (tokens / db.get_token_stats(inn).get("total_issued", 1)) * pool
                response += f"🏢 {name}\n📅 {date[:10]}\n💸 {dividend:.2f}$\n"
        await update.message.reply_text(response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text.strip()
        try:
            if user_state.get("awaiting_register"):
                parts = text.split()
                if len(parts) < 3:
                    await update.message.reply_text("❌ Required: name email password")
                    return
                password = parts[-1]; email = parts[-2]; name = " ".join(parts[:-2])
                if "@" not in email:
                    await update.message.reply_text("❌ Invalid email")
                    return
                user_manager = UserManager()
                try:
                    user_manager.register_user(name, email, password)
                    await update.message.reply_text(f"✅ Registration successful, {name}!")
                    await self.show_companies(update, context)
                except UserAlreadyExists:
                    await update.message.reply_text("❌ User already exists.")
                except InvalidEmail:
                    await update.message.reply_text("❌ Invalid email.")
                finally:
                    user_state.pop("awaiting_register", None)
            elif user_state.get("awaiting_login"):
                parts = text.split()
                if len(parts) != 2:
                    await update.message.reply_text("❌ Enter email and password")
                    return
                email, password = parts
                user_manager = UserManager()
                if user_manager.authenticate_user(email, password):
                    await update.message.reply_text("✅ Login successful!")
                    await self.show_companies(update, context)
                else:
                    await update.message.reply_text("❌ Invalid email or password.")
                user_state.pop("awaiting_login", None)
            elif user_state.get("awaiting_inn"):
                await self.process_inn_input(update, context)
            elif user_state.get("awaiting_token_amount"):
                await self.process_token_amount(update, context)
            elif user_state.get("awaiting_purchase"):
                await self.handle_purchase(update, context, user_id, text)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    def setup_handlers(self, application):
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.handle_role_selection))
        application.add_handler(CommandHandler("register", self.register_user))
        application.add_handler(CommandHandler("login", self.login_user))
        application.add_handler(CommandHandler("issue_tokens", self.issue_tokens))
        application.add_handler(CommandHandler("companies", self.show_companies))
        application.add_handler(CommandHandler("buy", self.buy_tokens))
        application.add_handler(CommandHandler("balance", self.show_balance))
        application.add_handler(CommandHandler("dividends", self.show_dividends))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

def run_bot():
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    logger.log("✅ Bot started")
    application.run_polling()

if __name__ == "__main__":

    run_bot()
