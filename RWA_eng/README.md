```markdown
---
## 📊 **TokenizeLocal: Updated Technical Documentation**

---

### 🔍 General Description

**TokenizeLocal** is a platform for tokenizing local businesses, enabling users to purchase digital tokens representing a stake in a real business.

Each token entitles the holder to **monthly dividends**, proportional to the company’s revenue.

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

### 🔄 Main Data Flow

    [User] -->|/start| [Role Selection: User / Company]
    -->|User| [Registration / Login]
    --> [View Companies]
    --> [Buy Tokens]
    --> [Check Balance and Dividends]

    [Company] --> [Enter INN]
    --> [Verification via Checko API]
    --> [Token Issuance in DB]
    --> [Monthly Revenue Update]
    --> [Dividend Payout]

    [Data] --> [Stored in database.sqlite]
    --> [Can be viewed via records_check.py]

---

### 3. Technical Implementation

#### 3.1. **Database System (SQLite)**

All data is stored in `blockchain/database.sqlite`.  
Tables are created on first launch via the `_initialize_tables()` method.

##### Tables:

| Name | Fields |
|------|--------|
| `businesses` | `inn` (PRIMARY KEY), `name` |
| `token_issuances` | `business_inn` (PRIMARY KEY), `amount`, `issued_at` |
| `users` | `id`, `name`, `email` (UNIQUE), `password` |
| `user_tokens` | `id`, `email`, `business_inn`, `tokens` (UNIQUE: email + business_inn) |
| `dividend_history` | `id`, `business_inn`, `distribution_date`, `total_revenue`, `dividend_pool`, `token_price` |

> ⚠️ **Note**: In the current implementation, passwords are stored in plain text. For production, `bcrypt` hashing is recommended.

---

#### 3.2. **Key Classes**

| Class | Responsibility |
|------|----------------|
| `UserManager` | Registration, authentication, email validation |
| `DBManager` | CRUD operations: businesses, tokens, balances, dividends |
| `FinancialAPIClient` | Company verification by INN via Checko API |
| `TelegramBotHandler` | Command, state, role, and help handling |

---

### 4. How the System Works

#### 4.1. Data Flow

    main[main.py] --> role{Role: user / company?}
    role -- user --> auth[Authentication via UserManager]
    auth --> companies[List of companies from get_all_issuances()]
    companies --> buy[Buy tokens via add_user_tokens()]
    buy --> balance[Display balance via get_user_tokens()]

    role -- company --> checko[Verification via Checko API]
    checko --> issue[Token issuance via issue_tokens()]
    issue --> update[Monthly revenue update]
    update --> dividends[distribute_dividends() → dividend payout]

---

### 5. Company Workflow

1. Company starts the bot and selects the **"Company"** role.
2. Enters **INN** (10 or 12 digits).
3. Bot verifies the company via **Checko API**.
4. If status is **"Active"**, the company can **issue tokens**.
5. Token amount is **not limited by revenue** (initially), but the logic is in place.
6. Company can **update revenue monthly** and trigger `distribute_dividends()`.

---

### 6. User Workflow

1. User selects the **"User"** role.
2. Registers (name, email, password) or logs in.
3. Views the list of companies.
4. Buys tokens from one or more companies.
5. Views balance and dividend history.

> ✅ **Important**: User email is `user_id@telegram.local` to avoid dependency on manual input.

---

### 7. Dividend Mechanism

```python
def distribute_dividends(self, inn: str, revenue: float, dividend_percentage: float = 0.1):
    dividend_pool = revenue * dividend_percentage
    total_tokens = token_issuances[inn]
    for user_email, tokens in user_tokens:
        user_share = tokens / total_tokens
        user_dividend = user_share * dividend_pool
        # Record to history
```

- Dividends are paid in **fiat units (e.g., $)**.
- Future support for **USDT, USDC** is planned.

---

### 8. Scaling Roadmap

| Direction | Implementation |
|---------|----------------|
| REST API | FastAPI / Flask |
| GUI Interface | Streamlit / React |
| DAO Governance | Voting in DB or via Snapshot |
| Secondary Token Market | Resale between users |
| Blockchain Integration | web3.py + smart contracts |
| Oracles | Pyth Network / Chainlink |
| USDT / USDC Support | For dividend stability |
| Automated Dividend Issuance | Via cron or Airflow |
| Password Hashing | bcrypt / passlib |
| Transaction History | `dividend_history` table |

---

### 9. Global API Support for Business Verification

| Country | Identifier | API |
|--------|------------|-----|
| Russia | INN | Checko |
| USA | EIN | Dun & Bradstreet |
| EU | VAT ID | VIES |
| Global | Company ID | OpenCorporates |

> ✅ Currently supports only **Checko (Russia)**.

---

### 10. Multi-Currency Support

| Supported Currencies | Description |
|----------------------|-----------|
| RUB | Russian Ruble |
| USD | US Dollar |
| EUR | Euro |
| USDT | Stablecoin (TRC20, ERC20) |
| USDC | Stablecoin (ERC20) |
| ETH | Ethereum |
| BTC | Bitcoin |

> ✅ At launch — only RUB and USD.

---

### 11. Current Status

| Feature | Status |
|--------|--------|
| Registration / Login | ✅ |
| Token Issuance | ✅ |
| Token Purchase | ✅ |
| Balance and History | ✅ |
| Dividends | ✅ |
| Company Verification | ✅ (Checko) |
| Roles (User/Company) | ✅ |
| Dynamic Help Messages | ✅ |
| SQLite Storage | ✅ |

---

### 12. Telegram Bot User Guide

#### 📱 How to Start

1. Open Telegram and find the bot `@TokenizeLocalBot`.
2. Click **"Start"** or type `/start`.

---

#### 🔀 Role Selection

The bot will prompt you to choose:
- **👤 User** — to buy tokens.
- **🏢 Company** — to issue tokens.

> 💡 After selection, the bot will show **relevant commands**.

---

#### 🧑‍💼 "User" Mode

| Command | Action |
|--------|--------|
| `/register` | Registration: enter name, email, and password separated by spaces |
| `/login` | Login: enter email and password separated by space |
| `/companies` | View all companies and available tokens |
| `/buy` | Buy tokens: enter number and quantity |
| `/balance` | View current token balance |
| `/dividends` | View dividend history |
| `/help` | Command help |

---

#### 🏢 "Company" Mode

| Command | Action |
|--------|--------|
| `/issue_tokens` | Issue tokens: enter INN and amount |
| `/help` | Command help |
| `/start` | Restart the bot |

> 💡 To restart at any time — type `/start`.

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

**Buying Tokens:**
```
/buy
1 50
```

---

#### ⚠️ Important Notes

- **All user tokens are isolated** — using `user_id@telegram.local`.
- **Help messages are role-specific** — companies only see `/issue_tokens` and `/help`.
- **Error `Can't parse entities`** — fixed by removing `parse_mode="Markdown"`.
- **Passwords are stored in plain text** — acceptable for demo. In production — must be hashed.
- **Dividends are calculated by the formula:**
  ```
  Dividend per token = (Revenue × 10%) / Total number of tokens
  ```

---

### 13. Technical Acceptance Criteria (TAC)

| № | Criterion | Completion Indicator |
|---|---------|------------------|
| 1 | Company Registration | ✔️ Ability to register via INN |
| 2 | Company Verification via API | ✔️ Successful request and status retrieval |
| 3 | Token Issuance by Company | ✔️ Tokens recorded in `token_issuances` |
| 4 | Balance Update After Purchase | ✔️ `user_tokens` updated correctly |
| 5 | Balance Viewing | ✔️ `/balance` command works properly |
| 6 | Dynamic Help Messages | ✔️ Different commands for different roles |
| 7 | Token Purchase | ✔️ Tokens deducted from company, credited to user |
| 8 | Dividend Payout | ✔️ `distribute_dividends()` updates history |
| 9 | Event Logging | ✔️ All actions logged via `Logger` |
| 10 | Email Security | ✔️ Uses `user_id@telegram.local` |

---

### ✅ Current Status and Launch Plan

- **Prototype**: Fully functional
- **API**: Checko (Russia), only companies with "Active" status and financial reports are allowed. Similar procedures planned for international companies via API.
- **Features**: registration, issuance, purchase, balance, dividends
- **Beta version**: Ready to launch within **1 month**
- **Target group**: 10 companies, 100 investors
---