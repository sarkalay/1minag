# indicators.py
import pandas as pd
import numpy as np

def calculate_ema(self, data, period):
    """Calculate Exponential Moving Average"""
    if len(data) < period:
        return [None] * len(data)
    df = pd.Series(data)
    return df.ewm(span=period, adjust=False).mean().tolist()

def calculate_rsi(self, data, period=14):
    """Calculate Relative Strength Index"""
    if len(data) < period + 1:
        return [50] * len(data)
    df = pd.Series(data)
    delta = df.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50).tolist()

def calculate_volume_spike(self, volumes, window=10):
    """Calculate if current volume is a spike"""
    if len(volumes) < window + 1:
        return False
    avg_vol = np.mean(volumes[-window-1:-1])
    current_vol = volumes[-1]
    return current_vol > avg_vol * 1.8

def get_price_history(self, pair, limit=50):
    """Multi-Timeframe Analysis with EMA, RSI, Volume"""
    try:
        if not self.binance:
            return self._get_mock_mtf_data(pair)

        intervals = {
            '5m': (Client.KLINE_INTERVAL_5MINUTE, 50),
            '15m': (Client.KLINE_INTERVAL_15MINUTE, 50),
            '1h': (Client.KLINE_INTERVAL_1HOUR, 50),
            '4h': (Client.KLINE_INTERVAL_4HOUR, 30),
            '1d': (Client.KLINE_INTERVAL_1DAY, 30)
        }

        mtf = {}
        current_price = self.get_current_price(pair)

        for name, (interval, lim) in intervals.items():
            klines = self.binance.futures_klines(symbol=pair, interval=interval, limit=lim)
            if not klines:
                continue

            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            ema9 = self.calculate_ema(closes, 9)
            ema21 = self.calculate_ema(closes, 21)
            rsi = self.calculate_rsi(closes, 14)[-1] if len(closes) > 14 else 50

            crossover = 'NONE'
            if len(ema9) >= 2 and len(ema21) >= 2:
                if ema9[-2] < ema21[-2] and ema9[-1] > ema21[-1]:
                    crossover = 'GOLDEN'
                elif ema9[-2] > ema21[-2] and ema9[-1] < ema21[-1]:
                    crossover = 'DEATH'

            vol_spike = self.calculate_volume_spike(volumes)

            mtf[name] = {
                'current_price': closes[-1],
                'change_1h': ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) > 1 else 0,
                'ema9': round(ema9[-1], 6) if ema9[-1] else 0,
                'ema21': round(ema21[-1], 6) if ema21[-1] else 0,
                'trend': 'BULLISH' if ema9[-1] > ema21[-1] else 'BEARISH',
                'crossover': crossover,
                'rsi': round(rsi, 1),
                'vol_spike': vol_spike,
                'support': round(min(lows[-10:]), 6),
                'resistance': round(max(highs[-10:]), 6)
            }

        main = mtf.get('1h', {})
        return {
            'current_price': current_price,
            'price_change': main.get('change_1h', 0),
            'support_levels': [mtf['1h']['support'], mtf['4h']['support']] if '4h' in mtf else [],
            'resistance_levels': [mtf['1h']['resistance'], mtf['4h']['resistance']] if '4h' in mtf else [],
            'mtf_analysis': mtf
        }

    except Exception as e:
        self.print_color(f"❌ MTF Analysis error: {e}", self.Fore.RED)
        return {
            'current_price': self.get_current_price(pair),
            'price_change': 0,
            'support_levels': [],
            'resistance_levels': [],
            'mtf_analysis': {}
        }

def _get_mock_mtf_data(self, pair):
    price = self.get_current_price(pair)
    return {
        'current_price': price,
        'price_change': 1.2,
        'support_levels': [price * 0.97, price * 0.95],
        'resistance_levels': [price * 1.03, price * 1.05],
        'mtf_analysis': {
            '5m': {'trend': 'BULLISH', 'crossover': 'GOLDEN', 'rsi': 68, 'vol_spike': True},
            '15m': {'trend': 'BULLISH', 'crossover': 'NONE', 'rsi': 62},
            '1h': {'trend': 'BULLISH', 'ema9': price*1.01, 'ema21': price*1.00},
            '4h': {'trend': 'BULLISH'},
            '1d': {'support': price*0.92, 'resistance': price*1.08}
        }
    }

def get_current_price(self, pair):
    try:
        if self.binance:
            ticker = self.binance.futures_symbol_ticker(symbol=pair)
            return float(ticker['price'])
        else:
            # Mock prices for paper trading
            mock_prices = {
                "BNBUSDT": 300,
                "SOLUSDT": 180, 
                "AVAXUSDT": 35
            }
            return mock_prices.get(pair, 100)
    except:
        return 100

# Attach to class
from core import FullyAutonomous1HourAITrader

for func in [calculate_ema, calculate_rsi, calculate_volume_spike, get_price_history, _get_mock_mtf_data, get_current_price]:
    setattr(FullyAutonomous1HourAITrader, func.__name__, func)
