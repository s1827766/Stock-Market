from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from stock import MeanReversionBot   # your class file

symbol = "DIS"

bot = MeanReversionBot(symbol=symbol, paper=True)

data_client = StockHistoricalDataClient(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY")
)

request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Day,
    start=datetime.now() - timedelta(days=200),
    end=datetime.now()
)

bars = data_client.get_stock_bars(request)

for bar in bars[symbol]:
    bot.add_price(bar.close)

print("Decision:", bot.trade_decision())
print("Shares held:", bot.shares_held)
