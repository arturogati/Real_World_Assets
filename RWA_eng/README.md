
---

## 📊 **TokenizeLocal: Updated Technical Documentation**

---

### 🔍 Overview

**TokenizeLocal** is a platform for tokenizing local businesses, allowing users to purchase digital tokens representing a share in a real business.

Each token grants the right to **monthly dividends**, proportional to the company's revenue.

---

### 🧠 Core System Components

    A[Telegram Bot] --> B[TelegramBotHandler]
    B --> C[DBManager]
    C --> D[(SQLite database.sqlite)]
    B --> E[FinancialAPIClient]
    E --> F[Checko API]
    B --> G[UserManager]
    B --> H[Logger]


---

### 🔄 Data Flow


    [User] -->|/start| [Role Selection: User / Company]
    -->|User| [Registration / Login]
    --> [View Companies]
    --> [Purchase Tokens]
    --> [View Balance & Dividends]

    [Company] --> [Enter Tax ID (INN)]
    --> [Verification via Checko API]
    --> [Token Issuance in DB]
    --> [Monthly Revenue Update]
    --> [Dividend Payout]

    [Data] --> [Stored in database.sqlite]
    --> [Viewable via records_check.py]


---

### 3. Technical Implementation

#### 3.1. **Database System (SQLite)**

All data is stored in `blockchain/database.sqlite`.  
Tables are created on first launch via `_initialize_tables()`.

##### Tables:

| Name | Fields |
|--------|------|
| `businesses` | `inn` (PRIMARY KEY), `name` |
| `token_issuances` | `business_inn` (PRIMARY KEY), `amount`, `issued_at` |
| `users` | `id`, `name`, `email` (UNIQUE), `password` |
| `user_tokens` | `id`, `email`, `business_inn`, `tokens` (UNIQUE: email + business_inn) |
| `dividend_history` | `id`, `business_inn`, `distribution_date`, `total_revenue`, `dividend_pool`, `token_price` |

> ⚠️ **Note**: In the current implementation, passwords are stored in plaintext. For production, use `bcrypt`.

---

#### 3.2. **Key Classes**

| Class | Responsibility |
|------|----------------|
| `UserManager` | Registration, authentication, email validation |
| `DBManager` | CRUD operations: companies, tokens, balances, dividends |
| `FinancialAPIClient` | Company verification via Checko API using Tax ID (INN) |
| `TelegramBotHandler` | Command handling, state management, role-based prompts |

---

### 4. How the System Works

#### 4.1. Data Flow


    main[main.py] --> role{Role: user / company?}
    role -- user --> auth[Authentication via UserManager]
    auth --> companies[Company list from get_all_issuances()]
    companies --> buy[Token purchase via add_user_tokens()]
    buy --> balance[Balance display via get_user_tokens()]

    role -- company --> checko[Verification via Checko API]
    checko --> issue[Token issuance via issue_tokens()]
    issue --> update[Monthly revenue update]
    update --> dividends[distribute_dividends() → dividend payout]


---

### 5. Company Workflow

1. The company launches the bot and selects the **"Company"** role.
2. Enters its **Tax ID (INN)** (10 or 12 digits).
3. The bot verifies the company via **Checko API**.
4. If the status is **"Active"**, the company can **issue tokens**.
5. The number of tokens is **not limited by revenue** (initially), but logic is in place.
6. The company can **update revenue monthly** and trigger `distribute_dividends()`.

---

### 6. User Workflow

1. The user selects the **"User"** role.
2. Registers (name, email, password) or logs in.
3. Views the list of companies.
4. Purchases tokens from one or multiple companies.
5. Checks balance and dividend history.

> ✅ **Important**: The user's email is `user_id@telegram.local` to avoid manual input.

---

### 7. Dividend Mechanism

```python
def distribute_dividends(self, inn: str, revenue: float, dividend_percentage: float = 0.1):
    dividend_pool = revenue * dividend_percentage
    total_tokens = token_issuances[inn]
    for user_email, tokens in user_tokens:
        user_share = tokens / total_tokens
        user_dividend = user_share * dividend_pool
        # Record in history
```

- Dividends are paid in **nominal units (e.g., $)**.
- Planned support for **USDT, USDC**.

---

### 8. Scaling Plan

| Direction | Implementation |
|-----------|-----------|
| REST API | FastAPI / Flask |
| GUI Interface | Streamlit / React |
| DAO Governance | Voting via DB or Snapshot |
| Secondary Token Market | Resale between users |
| Blockchain Integration | web3.py + smart contracts |
| Oracles | Pyth Network / Chainlink |
| USDT / USDC Support | For dividend stability |
| Automated Dividend Payouts | Cron or Airflow |
| Password Hashing | bcrypt / passlib |
| Transaction History | `dividend_history` table |

---

### 9. Global Business Verification APIs

| Country | Identifier | API |
|-------|--------------|-----|
| Russia | INN | Checko |
| USA | EIN | Dun & Bradstreet |
| EU | VAT ID | VIES |
| Global | Company ID | OpenCorporates |

> ✅ Only **Checko (Russia)** is supported initially.

---

### 10. Multi-Currency Support

| Supported Currencies | Description |
|----------------------|--------|
| RUB | Russian Ruble |
| USD | US Dollar |
| EUR | Euro |
| USDT | Stablecoin (TRC20, ERC20) |
| USDC | Stablecoin (ERC20) |
| ETH | Ethereum |
| BTC | Bitcoin |

> ✅ Initially, only RUB and USD are supported.

---

### 11. Current Status

| Feature | Status |
|--------|-----------|
| Registration / Login | ✅ |
| Token Issuance | ✅ |
| Token Purchase | ✅ |
| Balance & History | ✅ |
| Dividends | ✅ |
| Company Verification | ✅ (Checko) |
| Roles (User/Company) | ✅ |
| Dynamic Prompts | ✅ |
| SQLite Storage | ✅ |

---

### 12. Telegram Bot User Guide

#### 📱 Getting Started

1. Open Telegram and search for `@TokenizeLocalBot`.
2. Click **"Start"** or type `/start`.

---

#### 🔀 Role Selection

The bot will prompt you to choose:
- **👤 User** — for purchasing tokens.
- **🏢 Company** — for issuing tokens.

> 💡 After selection, the bot shows **role-specific commands**.

---

#### 🧑‍💼 "User" Mode

| Command | Action |
|--------|--------|
| `/register` | Register: enter name, email, and password separated by spaces |
| `/login` | Login: enter email and password separated by spaces |
| `/companies` | View all companies and available tokens |
| `/buy` | Buy tokens: select company number and quantity |
| `/balance` | View current token holdings |
| `/dividends` | View dividend history |
| `/help` | Command help |

---

#### 🏢 "Company" Mode

| Command | Action |
|--------|--------|
| `/issue_tokens` | Issue tokens: enter Tax ID (INN) and quantity |
| `/help` | Command help |
| `/start` | Restart |

> 💡 To restart, type `/start`.

---

#### 💬 Usage Examples

**Registration:**
```
/register
Ivan Petrov user@example.com 123456
```

**Login:**
```
/login
user@example.com 123456
```

**Token Issuance:**
```
/issue_tokens
7802348846
1000
```

**Token Purchase:**
```
/buy
1 50
```

---

#### ⚠️ Important Notes

- **User tokens are isolated** — `user_id@telegram.local` is used.
- **Prompts adapt to roles** — companies only see `/issue_tokens` and `/help`.
- **Error `Can't parse entities`** — fixed by removing `parse_mode="Markdown"`.
- **Passwords are stored in plaintext** — for demo. Use hashing in production.
- **Dividend formula:**
  ```
  Dividend per token = (Revenue × 10%) / Total tokens
  ```

---

### 13. Technical Acceptance Criteria (TAC)

| # | Criterion | Completion Sign |
|---|---------|------------------|
| 1 | Company Registration | ✔️ Ability to register via Tax ID (INN) |
| 2 | Company Verification via API | ✔️ Successful API request and status retrieval |
| 3 | Token Issuance by Company | ✔️ Tokens recorded in `token_issuances` |
| 4 | Balance Update After Purchase | ✔️ `user_tokens` updated |
| 5 | Balance View | ✔️ `/balance` command works correctly |
| 6 | Dynamic Prompts | ✔️ Different commands for different roles |
| 7 | Token Purchase | ✔️ Tokens deducted from company, credited to user |
| 8 | Dividend Payout | ✔️ `distribute_dividends()` updates history |
| 9 | Event Logging | ✔️ All actions logged via `Logger` |
| 10 | Email Security | ✔️ Uses `user_id@telegram.local` |

---

### ✅ Current Status & Launch Plan

- **Prototype**: Fully functional
- **API**: Checko (Russia)
- **Features**: Registration, issuance, purchase, balance, dividends
- **Beta Version**: Ready for launch within **1 month**
- **Target Audience**: 10 companies, 100 investors

---
