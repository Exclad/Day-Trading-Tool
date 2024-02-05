# Forex Data Analysis Tool

Welcome to the Day Trading Tool! This tool is designed to assist traders in analyzing data for making informed decisions. It provides features such as fetching historical candle data, calculating risk amounts, and determining take profit key levels.

## Prerequisites

Before running the tool, ensure you have the following installed on your system:

- [Python](https://www.python.org/downloads/): The tool is written in Python, so you'll need Python installed.


## Installation

### Step 1: Download the Code
Download the code by clicking on the "Code" button and selecting "Download ZIP". Extract the contents to your desired location.

### Step 2: Install Dependencies
Open a terminal (Command Prompt or PowerShell on Windows, Terminal on macOS/Linux) and navigate to the directory where you extracted the code.

Run the following command to install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. **API Key and Account ID:**
    - Open the `config.ini` file.
    - Replace `YOUR_API_KEY` and `YOUR_ACCOUNT_ID` with your OANDA API key and account ID.
    - To get your Oanda API Key, head over to [Oanda](https://hub.oanda.com/). Ensure that you're on the right account (Demo or Live). Click the "Tools" near the top left and click "API". It should then ask you to generate a API key.
    - Your account ID is your Oanda's Account Number. It should look something like 123-456-12345678-123

2. **Favorites List:**
    - If you want to use a list of favorite instruments, create or edit the `favorites.txt` file in the project directory. You should also be able to edit the file in the GUI.

## Usage

1. **Run the Script:**
    ```bash
    python exclad_daytrading_tool.py
    ```
    - This will launch the Forex Data Analysis Tool GUI.

2. **Enter Inputs:**
    - Select the category, instrument, direction, and enter the required information.
    - Click "Fetch Data" to analyze historical candle data.

3. **View Results:**
    - The tool will display key levels and information based on the entered data.

## Additional Information

- **Risk Amount Calculator:**
    - The tool provides a risk amount calculator that helps you determine the risk amount based on your NAV.

- **Stop Loss Calculator:**
    - Use the stop loss calculator to calculate stop losses based on swing high/low and direction.
