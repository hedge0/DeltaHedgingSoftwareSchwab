import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants and Global Variables
config = {}

# Global variables for Tastytrade
session = None

async def main():
    """
    Main function to initialize the bot.
    """
    global session
    
    load_config()





    try:
        session = Session(login=config["TASTYTRADE_USERNAME"], password=config["TASTYTRADE_PASSWORD"], remember_me=True)
        print("Login successful.")
    except Exception as e:
        if "invalid_credentials" in str(e):
            print("Invalid login credentials. Please check your username and password.")
            return
        else:
            raise






    while True:
        stocks = {}
        options = {}

        positions = account.get_positions(session)



        for underlying_symbol in options:
            total_deltas = 0.0
            for option in options[underlying_symbol].values():
                total_deltas += (option["delta"] * option["quantity"]) * option["direction"]
            total_deltas = round(total_deltas * 100)

            total_shares = stocks[underlying_symbol]["quantity"] * stocks[underlying_symbol]["direction"]
            delta_imbalance = total_deltas + total_shares
            




            print(f"Underlying Symbol: {underlying_symbol}")
            print(f"Total Shares: {total_shares}")
            print(f"Total Deltas: {total_deltas}")
            print(f"Delta Imbalance: {delta_imbalance}")

            if delta_imbalance != 0:
                if delta_imbalance > 0:
                    print(f"Adjustment needed: Going short {delta_imbalance} shares to hedge the delta exposure.")
                else:
                    print(f"Adjustment needed: Going long {-1 * delta_imbalance} shares to hedge the delta exposure.")
            else:
                print("No adjustment needed. Delta is perfectly hedged with shares.")  
            print()

        await asyncio.sleep(config["HEDGING_FREQUENCY"])

















def load_config():
    """
    Load configuration from environment variables and validate them.
    
    Raises:
        ValueError: If any required environment variable is not set.
    """
    global config
    config = {
        "TASTYTRADE_USERNAME": os.getenv('TASTYTRADE_USERNAME'),
        "TASTYTRADE_PASSWORD": os.getenv('TASTYTRADE_PASSWORD'),
        "TASTYTRADE_ACCOUNT_NUMBER": os.getenv('TASTYTRADE_ACCOUNT_NUMBER'),
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
