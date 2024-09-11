import asyncio
from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fredapi import Fred
from tastytrade import DXLinkStreamer, Equity, InstrumentType, NewOrder, OptionType, OrderAction, OrderTimeInForce, OrderType, PriceEffect, Session, Account
from tastytrade.order import *
from tastytrade.instruments import get_option_chain
from tastytrade.utils import TastytradeError
from tastytrade.dxfeed import EventType
from models import calculate_delta, calculate_implied_volatility_baw

# Load environment variables from .env file
load_dotenv()

# Constants and Global Variables
config = {}
risk_free_rate = 0.0
options_chains = {}

# Global variables for Tastytrade
session = None
account = None

async def main():
    """
    Main function to initialize the bot.
    """
    global session, account, risk_free_rate, options_chains
    
    precompile_numba_functions()
    load_config()

    try:
        fred = Fred(api_key=config["FRED_API_KEY"])
        sofr_data = fred.get_series('SOFR')
        risk_free_rate = (sofr_data.iloc[-1] / 100)
    except Exception as e:
        print("FRED API Error", f"Invalid FRED API Key: {str(e)}")
        return

    try:
        session = Session(login=config["TASTYTRADE_USERNAME"], password=config["TASTYTRADE_PASSWORD"], remember_me=True)
        print("Login successful.")
    except TastytradeError as e:
        if "invalid_credentials" in str(e):
            print("Invalid login credentials. Please check your username and password.")
            return
        else:
            raise

    try:
        account = Account.get_account(session, config["TASTYTRADE_ACCOUNT_NUMBER"])
    except TastytradeError as e:
        if "invalid_account_number" in str(e):
            print("Invalid account number. Please check your account number.")
            return
        else:
            raise  

    while True:
        stocks = {}
        options = {}

        positions = account.get_positions(session)

        for position in positions:
            if position.instrument_type == InstrumentType.EQUITY and position.quantity != 0:
                mid_price = await stream_raw_quotes(session, [position.underlying_symbol])
                stocks[position.underlying_symbol] = {
                    "quantity": int(position.quantity),
                    "price": mid_price,
                    "direction": 1 if position.quantity_direction == "Long" else -1
                }

            elif position.instrument_type == InstrumentType.EQUITY_OPTION and position.quantity != 0 and position.underlying_symbol not in options_chains:
                chain = get_option_chain(session, position.underlying_symbol)
                options_chains[position.underlying_symbol] = chain

        for position in positions:
            if position.instrument_type == InstrumentType.EQUITY_OPTION and position.quantity != 0:
                if position.underlying_symbol not in options:
                    options[position.underlying_symbol] = {}

                if position.underlying_symbol not in stocks:
                    mid_price = await stream_raw_quotes(session, [position.underlying_symbol])
                    stocks[position.underlying_symbol] = {
                        "quantity": 0,
                        "price": mid_price,
                        "direction": 1
                    }

                position_parsed = parse_option_symbol(position.symbol)
                exp_date = datetime.strptime(position_parsed["expiration_date"], '%Y-%m-%d').date()
                chain_data = options_chains[position.underlying_symbol][exp_date]

                for option in chain_data:
                    if option.symbol == position.symbol:
                        position_parsed["option_type"] = "calls" if option.option_type == OptionType.CALL else "puts"
                        position_parsed["strike"] = float(option.strike_price)
                        position_parsed["streamer_symbol"] = option.streamer_symbol

                position_parsed["price"] = await stream_raw_quotes(session, [position_parsed["streamer_symbol"]])
                position_parsed["quantity"] = float(position.quantity)
                position_parsed["direction"] = 1 if position.quantity_direction == "Long" else -1

                current_time = datetime.now()
                expiration_time =datetime.combine(datetime.strptime(position_parsed["expiration_date"], '%Y-%m-%d'), datetime.min.time()) + timedelta(hours=16)
                T = (expiration_time - current_time).total_seconds() / (365.25 * 24 * 3600)
                position_parsed["sigma"] = calculate_implied_volatility_baw(position_parsed["price"], stocks[position.underlying_symbol]["price"], position_parsed["strike"], risk_free_rate, T, option_type=position_parsed["option_type"])

                position_parsed["delta"] = (calculate_delta(stocks[position.underlying_symbol]["price"], position_parsed["strike"], T, risk_free_rate, position_parsed["sigma"], option_type=position_parsed["option_type"]))
                options[position.underlying_symbol][position.symbol] = position_parsed

        for underlying_symbol in options:
            total_deltas = 0.0
            for option in options[underlying_symbol].values():
                total_deltas += (option["delta"] * option["quantity"]) * option["direction"]
            total_deltas = round(total_deltas * 100)

            total_shares = stocks[underlying_symbol]["quantity"] * stocks[underlying_symbol]["direction"]
            delta_imbalance = total_deltas + total_shares
            
            for option in options[underlying_symbol].values():
                if option["sigma"] <= 0.005:
                    delta_imbalance = 0

            print(f"Underlying Symbol: {underlying_symbol}")
            print(f"Total Shares: {total_shares}")
            print(f"Total Deltas: {total_deltas}")
            print(f"Delta Imbalance: {delta_imbalance}")

            if delta_imbalance != 0:
                if delta_imbalance > 0:
                    print(f"Adjustment needed: Going short {delta_imbalance} shares to hedge the delta exposure.")

                    symbol = Equity.get_equity(session, underlying_symbol)
                    leg = symbol.build_leg(Decimal(delta_imbalance), OrderAction.SELL_TO_OPEN)

                    order = NewOrder(
                        time_in_force=OrderTimeInForce.DAY,
                        order_type=OrderType.MARKET,
                        legs=[leg],
                        price_effect=PriceEffect.CREDIT
                    )

                    try:
                        response = account.place_order(session, order, dry_run=config["DRY_RUN"])
                        print(response)
                    except TastytradeError as e:
                        print(f"Order placement failed: {e}")
                else:
                    print(f"Adjustment needed: Going long {-1 * delta_imbalance} shares to hedge the delta exposure.")
                    
                    symbol = Equity.get_equity(session, underlying_symbol)
                    leg = symbol.build_leg(Decimal(-1 * delta_imbalance), OrderAction.BUY_TO_OPEN)

                    order = NewOrder(
                        time_in_force=OrderTimeInForce.DAY,
                        order_type=OrderType.MARKET,
                        legs=[leg],
                        price_effect=PriceEffect.DEBIT
                    )

                    try:
                        response = account.place_order(session, order, dry_run=config["DRY_RUN"])
                        print(response)
                    except TastytradeError as e:
                        print(f"Order placement failed: {e}")
            else:
                print("No adjustment needed. Delta is perfectly hedged with shares.")  
            print()

        await asyncio.sleep(config["HEDGING_FREQUENCY"])

async def stream_raw_quotes(session, ticker_list):
    """
    Stream live quotes for the underlying asset and return the mid price.

    Args:
        session (Session): The Tastytrade session object.
        ticker_list (list): A list of ticker symbols to subscribe to for streaming quotes.

    Returns:
        float: The mid price calculated as the average of bid and ask prices.
    """
    async with DXLinkStreamer(session) as streamer:
        await streamer.subscribe(EventType.QUOTE, ticker_list)
        quote = await streamer.get_event(EventType.QUOTE)
        
        if hasattr(quote, 'bidPrice') and hasattr(quote, 'askPrice'):
            mid_price = float((quote.bidPrice + quote.askPrice) / 2)
            return mid_price
        else:
            raise ValueError("Quote does not contain bidPrice or askPrice")

def precompile_numba_functions():
    """
    Precompile Numba functions to improve performance.

    This method calls Numba-compiled functions with sample data to ensure they are precompiled,
    reducing latency during actual execution.
    """
    calculate_implied_volatility_baw(0.1, 100.0, 100.0, 0.01, 0.5, option_type='calls')

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
        "FRED_API_KEY": os.getenv('FRED_API_KEY'),
        "HEDGING_FREQUENCY": os.getenv('HEDGING_FREQUENCY'),
        "DRY_RUN": os.getenv('DRY_RUN', 'True').lower() in ['true', '1', 'yes']
    }

    for key, value in config.items():
        if value is None:
            raise ValueError(f"{key} environment variable not set")

    try:
        config["HEDGING_FREQUENCY"] = float(config["HEDGING_FREQUENCY"])
    except ValueError:
        raise ValueError("HEDGING_FREQUENCY environment variable must be a valid float")
        
def parse_option_symbol(symbol):
    """
    Parses an option symbol into its components, such as expiration date, option type, and strike price.
    
    Args:
        symbol (str): The full option symbol to be parsed (e.g., 'F 240913C00012500').
    
    Returns:
        dict: A dictionary containing the parsed details:
            - expiration_date (str): Expiration date in 'YYYY-MM-DD' format.
    
    Raises:
        ValueError: If the symbol format is incorrect.
    """
    parts = symbol.split()

    if len(parts) != 2:
        raise ValueError("The symbol format is incorrect.")

    option_details = parts[1]
    exp_date = option_details[:6]

    year = "20" + exp_date[:2]
    month = exp_date[2:4]
    day = exp_date[4:6]
    expiration_date = f"{year}-{month}-{day}"

    return {
        "expiration_date": expiration_date,
    }

if __name__ == "__main__":
    asyncio.run(main())
