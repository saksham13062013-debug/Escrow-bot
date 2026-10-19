# Professional Telegram MM Escrow Bot

Full-featured middleman escrow bot with **Web Admin Panel**, PostgreSQL support, multi-language, Crypto + INR deals, and group deal creation.

## Features

### Telegram Bot
- Create deals (Crypto or INR/UPI)
- English + Hindi languages
- Group deal creation (`/deal` in groups)
- Middleman sets payment details (crypto address or UPI ID) per deal
- Buyer confirm / Seller shipped / Dispute flow
- Full admin commands inside Telegram

### Web Admin Panel (Professional)
- Beautiful dashboard with live stats
- Manage all deals (set payment, confirm, release, refund, cancel, delete)
- User management (ban/unban)
- Settings (fee, wallets, UPI, maintenance mode)
- Login protected by `ADMIN_SECRET`

### Database
- SQLite for local testing
- **PostgreSQL** ready for Railway production

---

## Quick Start (Local)

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS
python main.py
```

- Bot runs via long polling
- Web panel: http://localhost:8080

---

## Deploy on Railway (Production)

### 1. Create Project
- Go to [railway.app](https://railway.app)
- New Project → Empty Project

### 2. Add PostgreSQL
- Click **+ New** → **Database** → **PostgreSQL**
- Copy the `DATABASE_URL` (it will look like `postgresql://...`)
- Change it to: `postgresql+asyncpg://...` (add `+asyncpg`)

### 3. Deploy Code
- Upload this folder or connect GitHub repo
- Or use Railway CLI

### 4. Environment Variables
Set these in Railway **Variables**:

| Variable        | Value                                      |
|-----------------|--------------------------------------------|
| `BOT_TOKEN`     | From @BotFather                            |
| `ADMIN_IDS`     | Your Telegram user ID                      |
| `ADMIN_SECRET`  | Strong password for web panel login        |
| `DATABASE_URL`  | `postgresql+asyncpg://...` (from step 2)   |
| `WEB_PORT`      | `8080` (or leave default)                  |

### 5. Generate Domain
- In the service → Settings → Networking → Generate Domain
- Your web panel will be at `https://xxx.up.railway.app`

---

## How Middleman Flow Works

1. User creates deal (Crypto or INR)
2. Admin gets notification
3. **Admin sets payment details** (crypto address or UPI ID) via Telegram or Web Panel
4. Both parties receive the payment instructions
5. Buyer pays → Admin confirms payment
6. Seller delivers → Buyer confirms
7. Admin releases funds (or refunds / resolves dispute)

---

## Group Deals

In any group where the bot is admin:

```
/deal 1500 USDT TRC20 Selling Instagram account
```

Or reply to a user message:

```
/deal 5000 INR (UPI) Website design work
```

---

## Admin Commands (Telegram)

| Command       | Description          |
|---------------|----------------------|
| `/stats`      | Quick stats          |
| `/deal <id>`  | View deal + actions  |
| `/ban <id>`   | Ban user             |
| `/unban <id>` | Unban user           |

---

## Security Notes

- Always change `ADMIN_SECRET`
- Use a dedicated wallet / UPI for escrow
- Keep transaction records outside the bot
- For high volume, enable Railway PostgreSQL backups


## Group + DM + Log Channel

- Works in **private chat (DM)** and **groups**
- Group command: `/deal amount currency description` (or reply to user)
- **Deals Log Channel**: set `LOG_CHANNEL_ID` in env
  - Create a private channel
  - Add the bot as admin
  - Get channel ID (forward a message to @userinfobot)
  - Put the ID in Railway variables / `.env`

Every deal event (created, payment set, confirmed, released, refunded, disputed, cancelled) is posted to the log channel.

**Important for groups:** In @BotFather → Bot Settings → Group Privacy → **Turn off** so the bot can read group messages.

## Escrower Role + /verify

### Admin
- Admin Panel → **Manage Escrowers** / **Add Escrower**
- Or send: user_id and optional deal limit

### Escrower
Set your addresses:
```
/myaddress TXyz...your_usdt_address
/myaddress USDT_TRC20 TXyz...
/myaddress   (list your addresses)
/removeaddress 3
```

### Anyone (DM or Group)
```
/verify TXyz...address
```
- Match → ✅ VERIFIED ADDRESS + escrower name  
- No match → 🚨 NOT VERIFIED — POSSIBLE SCAM

## Force Join Group

Set in `.env` / Railway:
```
ESCROW_GROUP_ID=-100xxxxxxxxxx
ESCROW_GROUP_LINK=https://t.me/+InviteHash
```
Bot must be admin in that group. Users who are not members cannot use /start or Create Deal.

## UPI + Crypto Verify
Escrowers can register both:
```
/myaddress USDT_TRC20 TXyz...
/myaddress UPI name@okaxis
```
Users check with:
```
/verify TXyz...
/verify name@okaxis
```
