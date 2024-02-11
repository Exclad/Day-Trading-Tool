import requests
import os
import configparser
from datetime import datetime, timedelta, timezone
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox, Frame, Radiobutton, OptionMenu, Checkbutton, BooleanVar, Toplevel, Scrollbar, Canvas, CHECKBUTTON
import tkinter as tk
from tkinter import ttk, Text
import tkinter.font as tkFont

global_favorites_button = None


# Function to fetch candle data
def fetch_candle_data(api_key, account_id, instrument, start_date, end_date):
    endpoint = f"https://api-fxtrade.oanda.com/v3/instruments/{instrument}/candles"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "price": "M",
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "granularity": "D",
    }

    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"API request error: {response.status_code} - {response.text}")

    data = response.json()
    if not data["candles"]:
        raise Exception(f"No data returned for the period {start_date.date()} to {end_date.date()}.")

    high_prices = [float(candle["mid"]["h"]) for candle in data["candles"]]
    low_prices = [float(candle["mid"]["l"]) for candle in data["candles"]]
    close_prices = [float(candle["mid"]["c"]) for candle in data["candles"]]
    return max(high_prices), min(low_prices), close_prices[-1] if close_prices else None

# Function to read configuration file
def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['oanda']['api_key'], config['oanda']['account_id']

# Function to adjust for weekends
def adjust_for_weekend(date):
    while date.weekday() > 4:  # Adjust if Saturday (5) or Sunday (6)
        date -= timedelta(days=1)
    return date

# Function to get the range for the previous year
def get_previous_year_range(current_date):
    previous_year = current_date.year - 1
    start_of_previous_year = datetime(previous_year, 1, 1, tzinfo=timezone.utc)
    end_of_previous_year = datetime(previous_year, 12, 31, tzinfo=timezone.utc)
    return start_of_previous_year, end_of_previous_year

# Function to filter prices based on entry price
def filter_prices_based_on_entry(direction, entry_price, price_data, two_to_one_price=None):
    if direction == "LONG":
        filtered_data = {k: v for k, v in price_data.items() if v >= entry_price}
    elif direction == "SHORT":
        filtered_data = {k: v for k, v in price_data.items() if v <= entry_price}
    else:
        filtered_data = price_data

    # If two_to_one_price is provided, add it to the filtered_data
    if two_to_one_price is not None:
        filtered_data["Your 2:1 price"] = two_to_one_price

    return filtered_data

# Function to format the forex pair input
def format_forex_pair(pair):
    formatted = pair.upper().replace("/", "_").replace("-", "_")
    return formatted if "_" in formatted else formatted[:3] + "_" + formatted[3:]


# Function to fetch data and update GUI
def fetch_data():
    try:
        # Check if the loading process is already active
        if getattr(fetch_data, 'loading', False):
            messagebox.showinfo("Info", "Data is already being fetched. Please wait.")
            return

        # Set loading flag to True
        fetch_data.loading = True

        # Display loading message and show progress bar
        result_label.config(text="Fetching data, please wait...")
        progress_bar = ttk.Progressbar(result_frame, mode='indeterminate')
        progress_bar.pack(pady=5)
        progress_bar.start()

        root.update_idletasks()  # Force update to show the loading message

        # Schedule the fetch_data function to be called after a short delay
        root.after(100, lambda: perform_data_fetch(progress_bar))

    except Exception as e:
        messagebox.showerror("Error", str(e))

def perform_data_fetch(progress_bar):
    try:
        instrument = format_forex_pair(pair_var.get())
        direction = direction_var.get().upper()
        entry_price = float(entry_price_var.get())
        two_to_one_price_str = two_to_one_price_var.get()
        two_to_one_price = float(two_to_one_price_str) if two_to_one_price_str else None

        utc_now = datetime.now(timezone.utc) - timedelta(hours=8)  # Adjust for Singapore Time (GMT+8)
        yesterday = adjust_for_weekend(utc_now - timedelta(days=1))
        two_days_ago = adjust_for_weekend(yesterday - timedelta(days=1))
        three_days_ago = adjust_for_weekend(two_days_ago - timedelta(days=1))
        start_of_previous_year, end_of_previous_year = get_previous_year_range(utc_now)

        # Fetching data
        yest_high, yest_low, yest_close = fetch_candle_data(api_key, account_id, instrument, yesterday, yesterday)
        two_days_high, two_days_low, _ = fetch_candle_data(api_key, account_id, instrument, two_days_ago, two_days_ago)
        three_days_high, three_days_low, _ = fetch_candle_data(api_key, account_id, instrument, three_days_ago,
                                                               three_days_ago)
        one_year_high, one_year_low, _ = fetch_candle_data(api_key, account_id, instrument, start_of_previous_year,
                                                           end_of_previous_year)

        price_data = {
            "Close of previous day": yest_close,
            "2 days ago High": two_days_high,
            "2 days ago Low": two_days_low,
            "3 days ago High": three_days_high,
            "3 days ago Low": three_days_low,
            "Previous Year High": one_year_high,
            "Previous Year Low": one_year_low,
        }

        # Call filter_prices_based_on_entry with two_to_one_price
        filtered_price_data = filter_prices_based_on_entry(direction, entry_price, price_data, two_to_one_price)
        sorted_keys = sorted(filtered_price_data, key=filtered_price_data.get, reverse=(direction == "SHORT"))

        # Stop and hide the progress bar
        progress_bar.stop()
        progress_bar.pack_forget()

        # Display the results
        result_text = "\n".join([f"{key}: {filtered_price_data[key]}" for key in sorted_keys])
        result_label.config(text=result_text)

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        # Reset loading flag
        fetch_data.loading = False
def clear_inputs():
    direction_var.set("LONG")
    entry_price_var.set("")
    two_to_one_price_var.set("")  # Clear the 2:1 price field
    result_label.config(text="")

def fetch_instruments(api_key, account_id, category):
    # Logic to fetch instruments based on category
    # For now, we'll use mock data. Replace this with actual API requests as needed.

    forex_pairs = sorted([
        'AUD_CAD', 'AUD_CHF', 'AUD_HKD', 'AUD_JPY', 'AUD_NZD', 'AUD_SGD', 'AUD_USD',
        'CAD_CHF', 'CAD_HKD', 'CAD_JPY', 'CAD_SGD',
        'CHF_HKD', 'CHF_JPY', 'CHF_ZAR',
        'EUR_AUD', 'EUR_CAD', 'EUR_CHF', 'EUR_CZK', 'EUR_DKK', 'EUR_GBP', 'EUR_HKD',
        'EUR_HUF', 'EUR_JPY', 'EUR_NOK', 'EUR_NZD', 'EUR_PLN', 'EUR_SEK', 'EUR_SGD',
        'EUR_TRY', 'EUR_USD', 'EUR_ZAR',
        'GBP_AUD', 'GBP_CAD', 'GBP_CHF', 'GBP_HKD', 'GBP_JPY', 'GBP_NZD', 'GBP_PLN',
        'GBP_SGD', 'GBP_USD', 'GBP_ZAR',
        'HKD_JPY',
        'NZD_CAD', 'NZD_CHF', 'NZD_HKD', 'NZD_JPY', 'NZD_SGD', 'NZD_USD',
        'SGD_CHF', 'SGD_JPY',
        'USD_CAD', 'USD_CHF', 'USD_CNH', 'USD_CZK', 'USD_DKK', 'USD_HKD', 'USD_HUF',
        'USD_JPY', 'USD_MXN', 'USD_NOK', 'USD_PLN', 'USD_SEK', 'USD_SGD', 'USD_THB',
        'USD_TRY', 'USD_ZAR'
    ])

    indices = sorted([
        'AU200_AUD', 'CH20_CHF', 'CN50_USD', 'DE10YB_EUR', 'DE30_EUR', 'ESPIX_EUR',
        'EU50_EUR', 'FR40_EUR', 'HK33_HKD', 'JP225Y_JPY', 'JP225_USD', 'NAS100_USD',
        'NL25_EUR', 'SG30_SGD', 'SPX500_USD', 'UK10YB_GBP', 'UK100_GBP', 'US2000_USD',
        'US30_USD'
    ])

    commodities = sorted([
        'BCO_USD', 'BCH_USD', 'BTC_USD', 'CORN_USD', 'ETH_USD', 'LTC_USD', 'NATGAS_USD',
        'SOYBN_USD', 'SUGAR_USD', 'WHEAT_USD', 'WTI_CO_USD', 'XAG_AUD', 'XAG_CAD',
        'XAG_CHF', 'XAG_EUR', 'XAG_GBP', 'XAG_HKD', 'XAG_JPY', 'XAG_NZD', 'XAG_SGD',
        'XAG_USD', 'XAU_AUD', 'XAU_CAD', 'XAU_CHF', 'XAU_EUR', 'XAU_GBP', 'XAU_HKD',
        'XAU_JPY', 'XAU_NZD', 'XAU_SGD', 'XAU_USD', 'XAU_XAG', 'XCU_USD', 'XPD_USD',
        'XPT_USD'
    ])

    if category == "Forex":
        return forex_pairs
    elif category == "Indices":
        return indices
    elif category == "Commodities":
        return commodities
    else:
        return []


def update_instruments_dropdown(*args):
    selected_category = category_var.get()
    use_favorites = favorites_var.get()

    if use_favorites:
        category_combobox.set("Favorites")  # Set category to "Favorites"
        category_combobox['state'] = 'readonly'
        instruments = read_favorite_instruments()
        instrument_combobox['values'] = instruments
        if instruments:
            pair_var.set(instruments[0])
    else:
        category_combobox['state'] = 'normal'
        categories = ["Forex", "Indices", "Commodities"]
        category_combobox['values'] = categories

        if not selected_category or selected_category not in categories:
            # If no category is selected or an invalid category is chosen, default to "Forex"
            selected_category = "Forex"
            category_combobox.set(selected_category)

        instruments = fetch_instruments(api_key, account_id, selected_category)
        instrument_combobox['values'] = instruments

        if instruments:
            pair_var.set(instruments[0])
        else:
            pair_var.set("Forex")

def fetch_all_instruments(api_key, account_id):
    endpoint = f"https://api-fxtrade.oanda.com/v3/accounts/{account_id}/instruments"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()
        instruments = [instrument['name'] for instrument in data['instruments']]
        return instruments
    else:
        raise Exception(f"API request error: {response.status_code} - {response.text}")

# Function to check and create the favorites button
def check_create_favorites_button():
    global global_favorites_button
    if global_favorites_button is None:
        if not os.path.exists("favorites.txt"):
            global_favorites_button = ttk.Button(frame, text="Create Favorites List", command=create_favorites)
        else:
            global_favorites_button = ttk.Button(frame, text="Edit Favorites List", command=edit_favorites)
        global_favorites_button.pack(pady=5)
    else:
        if not os.path.exists("favorites.txt"):
            global_favorites_button.config(text="Create Favorites List", command=create_favorites)
        else:
            global_favorites_button.config(text="Edit Favorites List", command=edit_favorites)



def read_favorite_instruments(file_name='favorites.txt'):
    try:
        with open(file_name, 'r') as file:
            favorites = file.read().splitlines()
        return [instrument.strip() for instrument in favorites if instrument.strip()]
    except FileNotFoundError:
        messagebox.showwarning("Warning", f"Favorites file '{file_name}' not found.")
        return []

# Function to create or edit favorites
def create_favorites():
    try:
        all_instruments = fetch_all_instruments(api_key, account_id)
        show_favorites_window("create", all_instruments)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def edit_favorites():
    try:
        all_instruments = fetch_all_instruments(api_key, account_id)
        show_favorites_window("edit", all_instruments)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Function to fetch account summary (including NAV)
def fetch_account_summary(api_key, account_id):
    endpoint = f"https://api-fxtrade.oanda.com/v3/accounts/{account_id}/summary"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("account", {}).get("balance", "N/A")
    else:
        raise Exception(f"API request error: {response.status_code} - {response.text}")


# Function to update NAV in the GUI
def update_nav_label():
    try:
        nav = fetch_account_summary(api_key, account_id)
        nav_label.config(text=f"Current NAV: {nav} SGD")

        # Calculate and update 3% risk amount
        risk_amount1 = 0.01 * float(nav)
        risk_amount2 = 0.02 * float(nav)
        risk_amount3 = 0.03 * float(nav)
        risk_label1.config(text=f"Your 1% risk amount is {risk_amount1:.2f} SGD")
        risk_label2.config(text=f"Your 2% risk amount is {risk_amount2:.2f} SGD")
        risk_label3.config(text=f"Your 3% risk amount is {risk_amount3:.2f} SGD")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Function to update 3% risk amount
def update_risk_amount():
    try:
        nav = fetch_account_summary(api_key, account_id)
        risk_amount1 = 0.01 * float(nav)
        risk_amount2 = 0.02 * float(nav)
        risk_amount3 = 0.03 * float(nav)
        risk_label1.config(text=f"Your 1% risk amount is {risk_amount1:.2f} SGD")
        risk_label2.config(text=f"Your 2% risk amount is {risk_amount2:.2f} SGD")
        risk_label3.config(text=f"Your 3% risk amount is {risk_amount3:.2f} SGD")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_favorites_window(mode, all_instruments):
    window = tk.Toplevel(root)
    window.title("Select Favorites")

    scrollbar = tk.Scrollbar(window)
    scrollbar.pack(side="right", fill="y")

    canvas = tk.Canvas(window, yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar.config(command=canvas.yview)

    frame_instruments = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame_instruments, anchor="nw")

    checkboxes = {}
    search_var = tk.StringVar()

    def update_favorites():
        favorites = [instrument for instrument, var in checkboxes.items() if var.get()]
        favorites.sort()  # Sort the favorites alphabetically
        with open("favorites.txt", "w") as file:
            for fav in favorites:
                file.write(f"{fav}\n")
        window.destroy()
        check_create_favorites_button()

    def update_instruments_list(*args):
        # Clear existing checkboxes
        for widget in frame_instruments.winfo_children():
            widget.destroy()

        search_text = search_var.get().lower()
        filtered_instruments = [instrument for instrument in all_instruments if search_text in instrument.lower()]

        for instrument in filtered_instruments:
            var = tk.BooleanVar(value=False)
            if mode == "edit" and os.path.exists("favorites.txt"):
                with open("favorites.txt", "r") as file:
                    if instrument in file.read().splitlines():
                        var.set(True)
            checkboxes[instrument] = var
            tk.Checkbutton(frame_instruments, text=instrument, variable=var).pack(anchor="w")

        frame_instruments.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    search_entry = tk.Entry(window, textvariable=search_var, width=30)
    search_entry.pack(pady=5)
    search_entry.bind("<KeyRelease>", update_instruments_list)

    update_instruments_list()

    ttk.Button(window, text="Submit", command=update_favorites).pack(pady=5)

def calculate_stop_losses(swing_price, direction):
    # Calculate stop losses based on direction
    percentages = [0.03, 0.3, 3]
    stop_losses = {}

    for percentage in percentages:
        key = f"{percentage}%"
        multiplier = -1 if direction == "LONG" else 1
        value = swing_price + (multiplier * swing_price * (percentage / 100))
        stop_losses[key] = value

    return stop_losses

def update_stop_losses():
    try:
        swing_price = float(swing_price_var.get())
        direction = stop_loss_direction_var.get()

        if not swing_price or not direction:
            messagebox.showwarning("Warning", "Please enter the Swing Price and select the Direction.")
            return

        stop_losses = calculate_stop_losses(swing_price, direction)

        # Display the stop losses
        stop_loss_text = "\n".join([f"{key} stop loss is {value:.6f} SGD" for key, value in stop_losses.items()])
        stop_loss_label.config(text=stop_loss_text)

    except ValueError:
        messagebox.showerror("Error", "Invalid input. Please enter a valid numeric value for Swing Price.")

def clear_stop_loss_inputs():
    swing_price_var.set("")  # Clear swing high/low input
    stop_loss_direction_var.set("LONG")  # Reset direction to LONG
    stop_loss_label.config(text="Calculated Stop Losses:")  # Clear the calculated stop losses


# GUI setup
root = tk.Tk()
root.title("Vijay's Day Trading Tool")
root.geometry("900x750")

style = ttk.Style()
font_large = tk.font.Font(family="Calibri", size=14)
font_medium = tk.font.Font(family="Calibri", size=12)
style.configure("TButton", padding=5, font=font_medium)
style.configure("TLabel", font=font_medium)
style.configure("TRadiobutton", font=font_medium)

# Header label for risk amount calculator
risk_header_label = ttk.Label(root, text="Risk Amount Calculator", font=('Calibri', 14, 'bold'))
risk_header_label.pack(side="top", anchor="nw", padx=10, pady=10)

# Create a label for displaying the NAV
nav_label = ttk.Label(root, text="Current NAV: N/A SGD", font=font_large)
nav_label.pack(anchor="nw", padx=10, pady=10)

# Label for displaying 3% risk amount
risk_label1 = ttk.Label(root, text="Your 1% risk amount is N/A SGD", font=font_medium)
risk_label1.pack(anchor="nw", padx=10, pady=10)

risk_label2 = ttk.Label(root, text="Your 2% risk amount is N/A SGD", font=font_medium)
risk_label2.pack(anchor="nw", padx=10, pady=10)

risk_label3 = ttk.Label(root, text="Your 3% risk amount is N/A SGD", font=font_medium)
risk_label3.pack(anchor="nw", padx=10, pady=10)

# Button to manually update NAV
ttk.Button(root, text="Update NAV", command=update_nav_label).pack(side="top", anchor="nw", padx=10)

# Create a separate frame for the stop loss calculator
stop_loss_frame = Frame(root)
stop_loss_frame.place(relx=0.98, rely=0, anchor="ne")

# Header label for stop loss calculator
stop_loss_header_label = ttk.Label(stop_loss_frame, text="Stop Loss Calculator", font=('Calibri', 14, 'bold'))
stop_loss_header_label.grid(row=0, column=0, columnspan=2, pady=10)

# Are you going long or short?
stop_loss_direction_label = ttk.Label(stop_loss_frame, text="Are you going long or short?", font=font_medium)
stop_loss_direction_label.grid(row=1, column=0, columnspan=2, pady=5)

# Direction selection for stop loss
stop_loss_direction_var = StringVar(value="LONG")
ttk.Radiobutton(stop_loss_frame, text="Long (-0.03%)", variable=stop_loss_direction_var, value="LONG").grid(row=2, column=0)
ttk.Radiobutton(stop_loss_frame, text="Short (+0.03%)", variable=stop_loss_direction_var, value="SHORT").grid(row=2, column=1)

# Swing high/low input
swing_price_label = ttk.Label(stop_loss_frame, text="Swing high/low", font=font_medium)
swing_price_label.grid(row=3, column=0, pady=5)
swing_price_var = StringVar()
swing_price_entry = ttk.Entry(stop_loss_frame, textvariable=swing_price_var, font=font_medium)
swing_price_entry.grid(row=3, column=1, pady=5)

# Calculate Stop Loss button
calculate_stop_losses_button = ttk.Button(stop_loss_frame, text="Calculate Stop Losses", command=update_stop_losses)
calculate_stop_losses_button.grid(row=4, column=0, columnspan=2, pady=5)

# Clear button for stop loss calculator
clear_stop_loss_button = ttk.Button(stop_loss_frame, text="Clear", command=clear_stop_loss_inputs)
clear_stop_loss_button.grid(row=5, column=0, columnspan=2, pady=5)

# Stop Loss label
stop_loss_label = ttk.Label(stop_loss_frame, text="Calculated Stop Losses:", font=font_medium)
stop_loss_label.grid(row=6, column=0, columnspan=2, pady=5)

frame = Frame(root, pady=10)
frame.place(relx=0.5, rely=0.385, anchor="center")  # Move the frame up

api_key, account_id = read_config()

pair_var = StringVar()
direction_var = StringVar(value="LONG")
entry_price_var = StringVar()
category_var = StringVar(value="Forex")
favorites_var = tk.BooleanVar(value=False)

# Header label for take profit key levels
take_profit_header_label = ttk.Label(frame, text="Take Profit Key Levels", font=('Calibri', 14, 'bold'))
take_profit_header_label.pack(anchor="nw", pady=5)

# Instruments dropdown
category_label = ttk.Label(frame, text="Category", font=font_medium)
category_label.pack(pady=5)
category_combobox = ttk.Combobox(frame, textvariable=category_var, values=["Forex", "Indices", "Commodities"], font=font_medium)
category_combobox.pack(pady=5)

# Pair dropdown
pair_label = ttk.Label(frame, text="Instrument", font=font_medium)
pair_label.pack(pady=5)
instrument_combobox = ttk.Combobox(frame, textvariable=pair_var, font=font_medium)
instrument_combobox.pack(pady=5)

# Favorites
favorites_frame = ttk.Frame(frame)
favorites_frame.pack(pady=5)

favorites_label = ttk.Label(favorites_frame, text="Use Favorites", font=font_medium)
favorites_label.pack(side="left")

favorites_checkbutton = ttk.Checkbutton(favorites_frame, variable=favorites_var, command=update_instruments_dropdown)
favorites_checkbutton.pack(side="left")

# Update UI elements based on saved favorites
check_create_favorites_button()

# Direction selection
direction_label = ttk.Label(frame, text="Direction", font=font_medium)
direction_label.pack(pady=5)
ttk.Radiobutton(frame, text="Long", variable=direction_var, value="LONG").pack()
ttk.Radiobutton(frame, text="Short", variable=direction_var, value="SHORT").pack()

# Entry price
entry_price_label = ttk.Label(frame, text="Entry Price", font=font_medium)
entry_price_label.pack(pady=5)
entry_price_entry = ttk.Entry(frame, textvariable=entry_price_var, font=font_medium)
entry_price_entry.pack(pady=5)

# 2:1 price input
two_to_one_price_var = StringVar()
two_to_one_price_label = ttk.Label(frame, text="Your 2:1 price", font=font_medium)
two_to_one_price_label.pack(pady=5)
two_to_one_price_entry = ttk.Entry(frame, textvariable=two_to_one_price_var, font=font_medium)
two_to_one_price_entry.pack(pady=5)

# Fetch data button
fetch_button = ttk.Button(frame, text="Fetch Data", command=fetch_data)
fetch_button.pack(pady=5)

# Clear button
clear_button = ttk.Button(frame, text="Clear", command=clear_inputs)
clear_button.pack(pady=5)

# Create a separate frame for the result label
result_frame = Frame(root, pady=10)
result_frame.pack(side="bottom", anchor="n", pady=5)  # Adjust side and anchor as needed

# Result label
result_label = ttk.Label(result_frame, text="", font=('Calibri', 11), justify="left")
result_label.pack(pady=5)

# Update UI elements based on saved favorites
category_var.trace("w", update_instruments_dropdown)
favorites_var.trace("w", update_instruments_dropdown)
update_instruments_dropdown()

root.mainloop()
