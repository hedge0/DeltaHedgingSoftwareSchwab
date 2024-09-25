import nest_asyncio
nest_asyncio.apply()

import httpx
from schwab.auth import easy_client
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants and Global Variables
config = {}
session = None

async def main():
    """
    Main function to initialize the bot.
    """
    global session
    
    load_config()

    try:
        session = easy_client(
            token_path='token.json',
            api_key=config["SCHWAB_API_KEY"],
            app_secret=config["SCHWAB_SECRET"],
            callback_url=config["SCHWAB_CALLBACK_URL"],
            asyncio=True)
        print("Login successful.")
    except Exception as e:
        print("Login Failed", f"An error occurred: {str(e)}")
        return

    while True:
        stocks = {}
        options = {}
        streamers_tickers = {}
        deltas = {}

        try:
            resp = await session.get_account(config["SCHWAB_ACCOUNT_HASH"], fields=[session.Account.Fields.POSITIONS])
            assert resp.status_code == httpx.codes.OK

            account_data = resp.json()
            positions = account_data['securitiesAccount']['positions']

            for position in positions:
                asset_type = position["instrument"]["assetType"]

                if asset_type == "EQUITY":
                    symbol = position["instrument"]["symbol"]
                    stocks[symbol] = position

                elif asset_type == "OPTION":
                    underlying_symbol = position["instrument"]["underlyingSymbol"]
                    if underlying_symbol not in streamers_tickers:
                        options[underlying_symbol] = {}
                        streamers_tickers[underlying_symbol] = []
                    options[underlying_symbol][position["instrument"]["symbol"]] = position
                    streamers_tickers[underlying_symbol].append(position["instrument"]["symbol"])
        except Exception as e:
            print("Error fetching account positions:", f"An error occurred: {str(e)}")

        for ticker in options:
            total_deltas = 0.0

            if len(streamers_tickers[ticker]) != 0:
                try:
                    resp = await session.get_quotes(streamers_tickers[ticker])
                    assert resp.status_code == httpx.codes.OK

                    quote_data = resp.json()
                    for quote in quote_data:
                        quantity = float(options[ticker][quote]["longQuantity"]) - float(options[ticker][quote]["shortQuantity"])
                        delta = float(quote_data[quote]["quote"]["delta"]) * quantity * 100.0
                        total_deltas += delta
                except Exception as e:
                    print("Error fetching quotes:", f"An error occurred: {str(e)}")
            deltas[ticker] = round(total_deltas)





        print(stocks)
        print("")

        print(deltas)
        print("")






        await asyncio.sleep(config["HEDGING_FREQUENCY"])

def load_config():
    """
    Load configuration from environment variables and validate them.
    
    Raises:
        ValueError: If any required environment variable is not set.
    """
    global config
    config = {
        "SCHWAB_API_KEY": os.getenv('SCHWAB_API_KEY'),
        "SCHWAB_SECRET": os.getenv('SCHWAB_SECRET'),
        "SCHWAB_CALLBACK_URL": os.getenv('SCHWAB_CALLBACK_URL'),
        "SCHWAB_ACCOUNT_HASH": os.getenv('SCHWAB_ACCOUNT_HASH'),
        "HEDGING_FREQUENCY": os.getenv('HEDGING_FREQUENCY'),
    }

    for key, value in config.items():
        if value is None:
            raise ValueError(f"{key} environment variable not set")

    try:
        config["HEDGING_FREQUENCY"] = float(config["HEDGING_FREQUENCY"])
    except ValueError:
        raise ValueError("HEDGING_FREQUENCY environment variable must be a valid float")

if __name__ == "__main__":
    asyncio.run(main())
