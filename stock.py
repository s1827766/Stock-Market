from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class MeanReversionBot:
    """
    Mean reversion stock trading bot using Alpaca API.
    Loads API keys from environment variables for safety.
    """

    def __init__(
        self,
        symbol='DIS',
        history=100,
        limit=0.02,
        max_shares=100,
        daily_trade_limit=5,
        cooldown_hours=24,
        paper=True
    ):
        self.symbol = symbol
        self.history = history
        self.limit = limit
        self.max_shares = max_shares
        self.daily_trade_limit = daily_trade_limit
        self.cooldown_hours = cooldown_hours
        self.paper = paper

        self.prices = []
        self.shares_held = 0
        self.last_trade_time = None
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()

        # Load API keys from .env
        self.api_key = os.getenv("API_KEY")
        self.secret_key = os.getenv("API_SECRET")

        if not self.api_key or not self.secret_key:
            raise ValueError("Missing API_KEY or API_SECRET in .env file")

        base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"

        self.trading_client = TradingClient(
            self.api_key,
            self.secret_key,
            paper=paper,
            url_override=base_url
        )

    def add_price(self, price):
        self.prices.append(price)
        today = datetime.now().date()
        if self.last_reset_date != today:
            self.daily_trades = 0
            self.last_reset_date = today

    def can_trade(self):
        if self.daily_trades >= self.daily_trade_limit:
            return False
        if self.last_trade_time:
            if datetime.now() - self.last_trade_time < timedelta(hours=self.cooldown_hours):
                return False
        return True

    def execute_trade(self, side, qty):
        order_request = MarketOrderRequest(
            symbol=self.symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        return self.trading_client.submit_order(order_request)

    def trade_decision(self):
        if len(self.prices) < self.history:
            return "Not enough data"
        if not self.can_trade():
            return "Throttled or daily limit reached"

        mean_price = sum(self.prices[-self.history:]) / self.history
        current_price = self.prices[-1]
        deviation = (current_price - mean_price) / mean_price

        if deviation < -self.limit and self.shares_held == 0:
            try:
                order = self.execute_trade(OrderSide.BUY, self.max_shares)
                self.shares_held = self.max_shares
                self.last_trade_time = datetime.now()
                self.daily_trades += 1
                return f"BUY {self.max_shares} shares - Order ID: {order.id}"
            except Exception as e:
                return f"BUY failed: {str(e)}"

        elif deviation > self.limit and self.shares_held > 0:
            try:
                order = self.execute_trade(OrderSide.SELL, self.shares_held)
                sold = self.shares_held
                self.shares_held = 0
                self.last_trade_time = datetime.now()
                self.daily_trades += 1
                return f"SELL {sold} shares - Order ID: {order.id}"
            except Exception as e:
                return f"SELL failed: {str(e)}"

        return "HOLD (price near mean)"


if __name__ == "__main__":
    symbol = "DIS"
    bot = MeanReversionBot(symbol=symbol, paper=True)

    data_client = StockHistoricalDataClient(bot.api_key, bot.secret_key)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime.now() - timedelta(days=120),
        end=datetime.now()
    )

    bars = data_client.get_stock_bars(request)

    for bar in bars[symbol]:
        bot.add_price(bar.close)

    decision = bot.trade_decision()
    print(decision)
    print(f"Shares held: {bot.shares_held}")
