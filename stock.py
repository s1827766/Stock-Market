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
    Mean reversion bot that supports multiple stocks.
    Uses IEX data to avoid SIP subscription issues.
    Loads real Alpaca positions at startup.
    """

    def __init__(
        self,
        symbol,
        history=20,
        limit=0.005,     
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

        # Load existing position from Alpaca
        try:
            position = self.trading_client.get_open_position(self.symbol)
            self.shares_held = int(position.qty)
        except Exception:
            self.shares_held = 0

        # Data client
        self.data_client = StockHistoricalDataClient(
            self.api_key,
            self.secret_key
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
        
        print(f"{self.symbol} deviation: {deviation:.4f}")
        
        # BUY
        if deviation < -self.limit and self.shares_held < self.max_shares:
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

    def load_recent_prices(self, days=200):
        request = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            feed=DataFeed.IEX
        )

        bars = self.data_client.get_stock_bars(request)

        for bar in bars[self.symbol]:
            self.add_price(bar.close)


if __name__ == "__main__":
    # Add as many symbols as you want
    symbols = ["DIS", "IVZ", "MSFT", "WMT"]

    for symbol in symbols:
        print(f"\n=== Running bot for {symbol} ===")

        bot = MeanReversionBot(symbol=symbol, paper=True)

        bot.load_recent_prices(days=200)

        decision = bot.trade_decision()
        print(decision)
        print(f"Shares held: {bot.shares_held}")
