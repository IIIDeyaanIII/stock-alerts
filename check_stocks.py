"""
Stock price alert checker.
Reads config.json for the list of stocks + target prices,
fetches live prices, and sends a Telegram message when a target
is crossed. Keeps state.json so it only notifies once per crossing
(and resets automatically if price moves back the other way, so it
can alert you again next time it crosses).
"""

import json
import os
import sys
import requests
import yfinance as yf

CONFIG_PATH = "config.json"
STATE_PATH = "state.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": message})
    resp.raise_for_status()


def get_price(symbol):
    ticker = yf.Ticker(symbol)
    fast_info = ticker.fast_info
    price = fast_info.get("last_price") if isinstance(fast_info, dict) else fast_info.last_price
    if price is None:
        raise ValueError(f"No price returned for {symbol}")
    return float(price)


def main():
    config = load_json(CONFIG_PATH, {"stocks": {}})
    state = load_json(STATE_PATH, {})

    stocks = config.get("stocks", {})
    if not stocks:
        print("No stocks configured in config.json. Nothing to do.")
        return

    state_changed = False

    for symbol, rule in stocks.items():
        target = rule.get("target")
        direction = rule.get("direction", "above")  # "above" or "below"

        if target is None:
            print(f"Skipping {symbol}: no 'target' set in config.json")
            continue

        try:
            price = get_price(symbol)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            continue

        prev = state.get(symbol, {})
        was_notified = prev.get("notified", False)

        hit = (direction == "above" and price >= target) or (
            direction == "below" and price <= target
        )

        print(f"{symbol}: price={price} target={target} direction={direction} hit={hit}")

        if hit and not was_notified:
            arrow = "up to" if direction == "above" else "down to"
            msg = (
                f"\U0001F514 {symbol} is now {arrow} \u20b9{price:.2f}\n"
                f"(target: {direction} \u20b9{target})"
            )
            send_telegram(msg)
            state[symbol] = {"notified": True, "last_price": price}
            state_changed = True
        elif not hit and was_notified:
            # Price moved back past target -> reset so it can alert again later
            state[symbol] = {"notified": False, "last_price": price}
            state_changed = True
        else:
            if prev.get("last_price") != price:
                state.setdefault(symbol, {"notified": was_notified})
                state[symbol]["last_price"] = price
                state_changed = True

    if state_changed:
        save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
