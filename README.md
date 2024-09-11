# Delta Hedging Bot in Python

## Overview

The Delta Hedging Bot is a Python-based trading bot that automates delta hedging of a Tastytrade Brokerage Account's option positions. It integrates with the Tastytrade API to track positions, calculate delta imbalances between shares and options, and adjust hedging strategies in real time. The bot uses asyncio for asynchronous execution and Numba to accelerate critical calculations.

## Key Features

- **Delta Hedging:** Automatically calculates and adjusts delta imbalances between options and shares to maintain a neutral position.
- **Implied Volatility Calculation:** Uses the Barone-Adesi Whaley model to calculate implied volatility for American-style options.
- **Asynchronous Execution:** Leverages asyncio for non-blocking streaming of real-time option quotes and position data.
- **Tastytrade API Integration:** Fetches live option chains, manages accounts, and executes buy/sell orders through the Tastytrade API.

## Prerequisites

- Tastytrade account credentials
- FRED API key

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/hedge0/DeltaHedgingSoftware.git
    cd DeltaHedgingSoftware
    ```

2. Create a `.env` file in the root directory and add the required environment variables:
    ```env
    TASTYTRADE_USERNAME=your_tastytrade_username
    TASTYTRADE_PASSWORD=your_tastytrade_password
    TASTYTRADE_ACCOUNT_NUMBER=your_tastytrade_account_number
    FRED_API_KEY=your_fred_api_key
    HEDGING_FREQUENCY=your_hedging_frequency_in_seconds
    DRY_RUN=true_or_false
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. To run the app:
    ```bash
    python app.py
    ```

### Usage

- The bot will automatically log in to your Tastytrade account, fetch the latest positions, and begin calculating delta imbalances.
- The bot will hedge delta exposure by buying or selling shares as needed.
- You can configure the bot to perform a dry run (where no real trades are executed) by setting `DRY_RUN` to `True` in the `.env` file.

### Configuration

Edit the `.env` file to adjust your configuration:

- `TASTYTRADE_USERNAME`: Your Tastytrade account username.
- `TASTYTRADE_PASSWORD`: Your Tastytrade account password.
- `TASTYTRADE_ACCOUNT_NUMBER`: Your Tastytrade account number.
- `FRED_API_KEY`: Your FRED API key to fetch the risk-free rate.
- `HEDGING_FREQUENCY`: The frequency (in seconds) at which the bot checks for delta imbalances and updates hedging positions.
- `DRY_RUN`: Set to `True` to prevent real trades (useful for testing), or `False` for live trading.

## Contributing

Contributions are welcome! If you encounter any issues or want to enhance the functionality, feel free to open a pull request or submit an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
