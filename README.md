# Stock Price Alerts → Telegram (Free, Cloud-Only)

Checks stock prices every 15 minutes during NSE market hours and sends you
a Telegram message the moment a stock hits a price you set. Runs entirely
on GitHub's free servers — nothing needs to run on your computer.

## One-time setup (~10 minutes)

### 1. Create a Telegram bot
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, give it a name and username (e.g. `mystockalerts_bot`).
3. BotFather will give you a **bot token** — looks like `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Save it.
4. Now search for **your new bot's username** in Telegram and send it any message, e.g. "hi" (this "activates" it so it's allowed to message you back).

### 2. Get your chat ID
1. In your browser, go to:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   (replace `<YOUR_TOKEN>` with the token from step 1)
2. You'll see JSON containing `"chat":{"id":123456789,...}` — that number is your **chat ID**. Save it.

### 3. Create a GitHub repo
1. Go to github.com → New repository (can be Public or Private, both are free) → e.g. `stock-alerts`.
2. Upload all the files from this project (`check_stocks.py`, `config.json`, `state.json`, `requirements.txt`, and the `.github/workflows/stock-alert.yml` folder), keeping the folder structure intact.
   - Easiest way: on the repo page, click "Add file" → "Upload files", drag everything in (make sure `.github/workflows/stock-alert.yml` ends up at that exact path).

### 4. Add your secrets
1. In your repo: **Settings → Secrets and variables → Actions → New repository secret**
2. Add:
   - `TELEGRAM_BOT_TOKEN` = the token from step 1
   - `TELEGRAM_CHAT_ID` = the chat ID from step 2

### 5. Test it
1. Go to the **Actions** tab in your repo → click "Stock Price Alerts" → **Run workflow** (manual trigger button).
2. Check the run logs to confirm it fetched a price. If HDFC Bank's current price already meets your target in `config.json`, you should get a Telegram message immediately.

That's it — from here it runs automatically every 15 minutes during market hours, for free, forever.

## Adding / changing stocks

Just edit `config.json` in GitHub (click the file → pencil/edit icon → commit changes). No coding required.

```json
{
  "stocks": {
    "HDFCBANK.NS": { "target": 1700, "direction": "above" },
    "RELIANCE.NS":  { "target": 2800, "direction": "below" },
    "TCS.NS":       { "target": 4000, "direction": "above" }
  }
}
```

- **Symbol format**: NSE stocks use `.NS` suffix (e.g. `HDFCBANK.NS`, `INFY.NS`, `TATASTEEL.NS`). BSE stocks use `.BO`.
- **`direction: "above"`** → alerts when price rises to/above the target.
- **`direction: "below"`** → alerts when price falls to/below the target.
- You can add as many stocks as you like — just add more entries.

## How the "don't spam me" logic works

Once a target is hit, you get exactly **one** notification, and it won't
repeat every 15 minutes. If the price later moves back past the target
(e.g. drops back below an "above" target), it silently resets — so if it
crosses again later, you'll get a fresh alert. This state is tracked in
`state.json`, which the workflow updates automatically on every run.

## Notes
- Prices come from Yahoo Finance (free, no API key needed) via the `yfinance` library. There can occasionally be a short delay (usually under a few minutes) — it's not tick-by-tick real-time, but plenty accurate for target-price alerts.
- The schedule covers roughly 9:00am–3:30pm IST, Mon–Fri. Edit the `cron` lines in `.github/workflows/stock-alert.yml` if you want a different window or frequency.
- GitHub Actions free tier gives 2,000 minutes/month for private repos (unlimited for public repos) — this job takes well under a minute per run, so you're nowhere close to any limit.
