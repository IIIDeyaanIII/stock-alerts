"""
Stock price alert checker.
Reads config.json for the list of stocks + one-or-more target rules per stock,
fetches live prices, and sends a Telegram message EVERY TIME any target rule
is currently crossed (no suppression) - so while a stock stays past a target,
you'll get a fresh alert on every run until it moves back.
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


def normalize_rules(rule_value):
    """Accept either a single rule dict or a list of rule dicts."""
    if isinstance(rule_value, list):
        return rule_value
    return [rule_value]


def main():
    config = load_json(CONFIG_PATH, {"stocks": {}})
    state = load_json(STATE_PATH, {})

    stocks = config.get("stocks", {})
    if not stocks:
        print("No stocks configured in config.json. Nothing to do.")
        return

    state_changed = False

    for symbol, rule_value in stocks.items():
        rules = normalize_rules(rule_value)

        try:
            price = get_price(symbol)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            continue

        for rule in rules:
            target = rule.get("target")
            direction = rule.get("direction", "above")

            if target is None:
                print(f"Skipping a rule for {symbol}: no 'target' set")
                continue

            hit = (direction == "above" and price >= target) or (
                direction == "below" and price <= target
            )

            print(f"{symbol}: price={price} target={target} direction={direction} hit={hit}")

            if hit:
                if direction == "above":
                    emoji = "\U0001F534"  # red circle
                    arrow = "up to"
                else:
                    emoji = "\U0001F7E2"  # green circle
                    arrow = "down to"
                msg = (
                    f"{emoji} {symbol} is now {arrow} \u20b9{price:.2f}\n"
                    f"(target: {direction} \u20b9{target})"
                )
                send_telegram(msg)

        prev = state.get(symbol, {})
        if prev.get("last_price") != price:
            state[symbol] = {"last_price": price}
            state_changed = True

    if state_changed:
        save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
