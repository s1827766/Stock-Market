from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed


class MeanReversionBot:
    """
    A simple mean reversion trading bot using Alpaca.
    Uses IEX data (free) to avoid SIP subscription errors.
    """

    def __init__(
        self,
        symbol="DIS",
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

        self.prices = []
        self.shares_held = 0
        self.daily_trades = 0
        self.last_trade_time = None
        self.last_reset_date = datetime.now().date()

        # Load keys
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY")

        # Trading client
        self.trading_client = TradingClient(
            self.api_key,
            self.secret_key,
            paper=paper
        )

        # Data client (IEX feed to avoid SIP errors)
        self.data_client = StockHistoricalDataClient(
            self.api_key,
            self.secret_key,
            feed=DataFeed.IEX
        )

    def add_price(self, price):
        self.prices.append(price)

        # Reset daily trade count at midnight
        today = datetime.now().date()
        if today != self.last_reset_date:
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
        order = MarketOrderRequest(
            symbol=self.symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        return self.trading_client.submit_order(order)

    def trade_decision(self):
        if len(self.prices) < self.history:
            return "Not enough data"

        if not self.can_trade():
            return "Trade cooldown or daily limit reached"

        mean_price = sum(self.prices[-self.history:]) / self.history
        current_price = self.prices[-1]
        deviation = (current_price - mean_price) / mean_price

        # BUY
        if deviation < -self.limit and self.shares_held == 0:
            try:
                order = self.execute_trade(OrderSide.BUY, self.max_shares)
                self.shares_held = self.max_shares
                self.daily_trades += 1
                self.last_trade_time = datetime.now()
                return f"BUY {self.max_shares} shares (Order ID: {order.id})"
            except Exception as e:
                return f"BUY failed: {e}"

        # SELL
        if deviation > self.limit and self.shares_held > 0:
            try:
                order = self.execute_trade(OrderSide.SELL, self.shares_held)
                sold = self.shares_held
                self.shares_held = 0
                self.daily_trades += 1
                self.last_trade_time = datetime.now()
                return f"SELL {sold} shares (Order ID: {order.id})"
            except Exception as e:
                return f"SELL failed: {e}"

        return "HOLD"

    def load_recent_prices(self, days=120):
        request = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=days),
            end=datetime.now()
        )

        bars = self.data_client.get_stock_bars(request)
        for bar in bars[self.symbol]:
            self.add_price(bar.close)


if __name__ == "__main__":
    bot = MeanReversionBot(symbol="DIS", paper=True)
    bot.load_recent_prices()

    decision = bot.trade_decision()
    print(decision)
    print(f"Shares held: {bot.shares_held}")
