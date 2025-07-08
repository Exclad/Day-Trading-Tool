# -*- coding: utf-8 -*-
import os
import sys
import requests
import oandapyV20
from dotenv import load_dotenv
# 1. ADDED: Import the datetime module for timestamps
from datetime import datetime
from oandapyV20.endpoints.accounts import AccountSummary
from oandapyV20.endpoints.trades import OpenTrades, TradeClose

# --- Load Environment Variables ---
load_dotenv() 

API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INSTRUMENT = os.getenv("OANDA_INSTRUMENT")

# --- Telegram Helper Function ---
def send_telegram(message: str):
    """Sends a message to your Telegram bot and handles potential errors."""
    if not BOT_TOKEN or not CHAT_ID:
        sys.__stdout__.write("[!] Telegram credentials not found in .env file.\n")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    
    try:
        requests.post(url, data=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        sys.__stdout__.write(f"[!] Critical Error: Failed to send Telegram message: {e}\n")

# --- Custom Logger to Redirect `print` to Console and Telegram ---
class TelegramLogger:
    """A custom logger that duplicates print statements to the console and Telegram."""
    def write(self, message):
        message = message.strip()
        if message:
            # 1. ADDED: Create a timestamp and prepend it to every message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            
            sys.__stdout__.write(formatted_message + "\n")
            send_telegram(formatted_message)

    def flush(self):
        pass

# --- Redirect `stdout` and `stderr` to our custom logger ---
sys.stdout = TelegramLogger()
sys.stderr = TelegramLogger()

# --- Main Application Logic ---
def main():
    """Main function to run the trading bot logic."""
    print("🤖 OANDA Trade Closer Bot: Script started.")

    # --- Connect to OANDA ---
    try:
        client = oandapyV20.API(access_token=API_KEY)
        request = AccountSummary(accountID=ACCOUNT_ID)
        client.request(request)
        print("✅ Successfully connected to OANDA demo account.")
    except Exception as e:
        print(f"❌ FATAL: Could not connect to OANDA. {e}")
        return

    # --- Get Open Trades ---
    try:
        trades_req = OpenTrades(accountID=ACCOUNT_ID)
        resp = client.request(trades_req)
        open_trades = resp.get("trades", [])

        if not open_trades:
            print("👍 No open trades found. Nothing to do. Script will now exit.")
            return

    except Exception as e:
        print(f"❌ FATAL: Could not retrieve open trades from OANDA. {e}")
        return

    # --- Process and Close Trades ---
    print(f"🔎 Found {len(open_trades)} open trade(s). Checking for '{INSTRUMENT}'.")
    nas100_trades_found = False
    for trade in open_trades:
        if trade.get("instrument") == INSTRUMENT:
            nas100_trades_found = True
            trade_id = trade['id']
            print(f"🎯 Found matching trade! Attempting to close Trade ID: {trade_id}...")
            
            try:
                close_req = TradeClose(accountID=ACCOUNT_ID, tradeID=trade_id)
                # 2. ADDED: Capture the response from the close request
                response = client.request(close_req)
                print(f"✅ Successfully closed trade {trade_id}.")
                
                # 2. ADDED: Get profit/loss from the response and print it
                # We use .get() with a default of {} or 'N/A' to prevent errors if the key doesn't exist
                pnl = response.get('orderFillTransaction', {}).get('pl', 'N/A')
                print(f"💰 P/L for trade {trade_id}: {pnl}")

            except Exception as e:
                print(f"❌ ERROR: Failed to close trade {trade_id}. Reason: {e}")

    if not nas100_trades_found:
        print(f"👍 No open trades for '{INSTRUMENT}' were found among the open positions.")

    print("🏁 OANDA Trade Closer Bot: Script finished.")


if __name__ == "__main__":
    main()