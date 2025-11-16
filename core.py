# core.py
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from learn_script import SelfLearningAITrader
    LEARN_SCRIPT_AVAILABLE = True
    print("✅ Learn script loaded successfully!")
except ImportError as e:
    print(f"❌ Learn script import failed: {e}")
    LEARN_SCRIPT_AVAILABLE = False

import requests
import json
import time
import re
import math
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from datetime import datetime
import pytz
import pandas as pd

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("Warning: Colorama not installed. Run: pip install colorama")

load_dotenv()

if not COLORAMA_AVAILABLE:
    class DummyColors:
        def __getattr__(self, name): return ''
    Fore = DummyColors()
    Back = DummyColors()
    Style = DummyColors()

# === CLASS DEFINITION ===
if LEARN_SCRIPT_AVAILABLE:
    class FullyAutonomous1HourAITrader(SelfLearningAITrader):
        def __init__(self):
            super().__init__()
            self._initialize_trading()
else:
    class FullyAutonomous1HourAITrader(object):
        def __init__(self):
            self.mistakes_history = []
            self.learned_patterns = {}
            self.performance_stats = {
                'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
                'common_mistakes': {}, 'improvement_areas': []
            }
            self._initialize_trading()

# === COMMON INITIALIZATION ===
def _initialize_trading(self):
    self.binance_api_key = os.getenv('BINANCE_API_KEY')
    self.binance_secret = os.getenv('BINANCE_SECRET_KEY')
    self.openrouter_key = os.getenv('OPENROUTER_API_KEY')

    self.Fore = Fore
    self.Back = Back
    self.Style = Style
    self.COLORAMA_AVAILABLE = COLORAMA_AVAILABLE
    self.thailand_tz = pytz.timezone('Asia/Bangkok')

    self.total_budget = 500
    self.available_budget = 500
    self.max_position_size_percent = 10
    self.max_concurrent_trades = 4
    self.available_pairs = ["BNBUSDT", "SOLUSDT", "AVAXUSDT"]
    self.ai_opened_trades = {}
    self.real_trade_history_file = "fully_autonomous_1hour_ai_trading_history.json"
    self.real_trade_history = self.load_real_trade_history()
    self.real_total_trades = 0
    self.real_winning_trades = 0
    self.real_total_pnl = 0.0
    self.quantity_precision = {}
    self.price_precision = {}
    self.allow_reverse_positions = True
    self.monitoring_interval = 180  # 3 minutes

    self.validate_api_keys()
    try:
        self.binance = Client(self.binance_api_key, self.binance_secret)
        self.print_color("🤖 FULLY AUTONOMOUS AI TRADER ACTIVATED!", self.Fore.CYAN + self.Style.BRIGHT)
        self.print_color(f"💰 TOTAL BUDGET: ${self.total_budget}", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color("🔄 REVERSE POSITION: ENABLED", self.Fore.MAGENTA + self.Style.BRIGHT)
        self.print_color("🎯 NO TP/SL - AI MANUAL CLOSE", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color("⏰ MONITORING: 3 MINUTE INTERVAL", self.Fore.RED + self.Style.BRIGHT)
        if LEARN_SCRIPT_AVAILABLE:
            self.print_color("🧠 SELF-LEARNING AI: ENABLED", self.Fore.MAGENTA + self.Style.BRIGHT)
    except Exception as e:
        self.print_color(f"❌ Binance init failed: {e}", self.Fore.RED)
        self.binance = None

    self.validate_config()
    if self.binance:
        self.setup_futures()
        self.load_symbol_precision()

# === ESSENTIAL METHODS ===
def load_real_trade_history(self):
    """Load trading history"""
    try:
        if os.path.exists(self.real_trade_history_file):
            with open(self.real_trade_history_file, 'r') as f:
                history = json.load(f)
                self.real_total_trades = len(history)
                self.real_winning_trades = len([t for t in history if t.get('pnl', 0) > 0])
                self.real_total_pnl = sum(t.get('pnl', 0) for t in history)
                return history
        return []
    except Exception as e:
        self.print_color(f"❌ Error loading trade history: {e}", self.Fore.RED)
        return []

def save_real_trade_history(self):
    """Save trading history"""
    try:
        with open(self.real_trade_history_file, 'w') as f:
            json.dump(self.real_trade_history, f, indent=2)
    except Exception as e:
        self.print_color(f"❌ Error saving trade history: {e}", self.Fore.RED)

def add_trade_to_history(self, trade_data):
    """Add trade to history WITH learning"""
    try:
        trade_data['close_time'] = self.get_thailand_time()
        trade_data['close_timestamp'] = time.time()
        trade_data['trade_type'] = 'REAL'
        self.real_trade_history.append(trade_data)
        
        # 🧠 Learn from this trade (especially if it's a loss)
        if LEARN_SCRIPT_AVAILABLE:
            self.learn_from_mistake(trade_data)
            self.adaptive_learning_adjustment()
        
        # Update performance stats
        self.performance_stats['total_trades'] += 1
        pnl = trade_data.get('pnl', 0)
        self.real_total_pnl += pnl
        if pnl > 0:
            self.real_winning_trades += 1
            self.performance_stats['winning_trades'] += 1
        else:
            self.performance_stats['losing_trades'] += 1
            
        if len(self.real_trade_history) > 200:
            self.real_trade_history = self.real_trade_history[-200:]
        self.save_real_trade_history()
        self.print_color(f"📝 Trade saved: {trade_data['pair']} {trade_data['direction']} P&L: ${pnl:.2f}", self.Fore.CYAN)
    except Exception as e:
        self.print_color(f"❌ Error adding trade to history: {e}", self.Fore.RED)

def get_thailand_time(self):
    now_utc = datetime.now(pytz.utc)
    thailand_time = now_utc.astimezone(self.thailand_tz)
    return thailand_time.strftime('%Y-%m-%d %H:%M:%S')

def print_color(self, text, color=""):
    if self.COLORAMA_AVAILABLE:
        print(f"{color}{text}")
    else:
        print(text)

def validate_config(self):
    if not all([self.binance_api_key, self.binance_secret, self.openrouter_key]):
        self.print_color("❌ Missing API keys!", self.Fore.RED)
        return False
    try:
        if self.binance:
            self.binance.futures_exchange_info()
            self.print_color("✅ Binance connection successful!", self.Fore.GREEN + self.Style.BRIGHT)
        else:
            self.print_color("📝 Binance client not available - Paper Trading only", self.Fore.YELLOW)
            return True
    except Exception as e:
        self.print_color(f"❌ Binance connection failed: {e}", self.Fore.RED)
        return False
    return True

def setup_futures(self):
    if not self.binance:
        return
        
    try:
        for pair in self.available_pairs:
            try:
                # Set initial leverage to 5x (AI can change later)
                self.binance.futures_change_leverage(symbol=pair, leverage=5)
                self.binance.futures_change_margin_type(symbol=pair, marginType='ISOLATED')
                self.print_color(f"✅ Leverage set for {pair}", self.Fore.GREEN)
            except Exception as e:
                self.print_color(f"⚠️ Leverage setup failed for {pair}: {e}", self.Fore.YELLOW)
        self.print_color("✅ Futures setup completed!", self.Fore.GREEN + self.Style.BRIGHT)
    except Exception as e:
        self.print_color(f"❌ Futures setup failed: {e}", self.Fore.RED)

def load_symbol_precision(self):
    if not self.binance:
        for pair in self.available_pairs:
            self.quantity_precision[pair] = 3
            self.price_precision[pair] = 4
        self.print_color("📝 Default precision set for paper trading", self.Fore.GREEN)
        return
        
    try:
        exchange_info = self.binance.futures_exchange_info()
        for symbol in exchange_info['symbols']:
            pair = symbol['symbol']
            if pair not in self.available_pairs:
                continue
            for f in symbol['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = f['stepSize']
                    qty_precision = len(step_size.split('.')[1].rstrip('0')) if '.' in step_size else 0
                    self.quantity_precision[pair] = qty_precision
                elif f['filterType'] == 'PRICE_FILTER':
                    tick_size = f['tickSize']
                    price_precision = len(tick_size.split('.')[1].rstrip('0')) if '.' in tick_size else 0
                    self.price_precision[pair] = price_precision
        self.print_color("✅ Symbol precision loaded", self.Fore.GREEN + self.Style.BRIGHT)
    except Exception as e:
        self.print_color(f"❌ Error loading symbol precision: {e}", self.Fore.RED)

def validate_api_keys(self):
    """Validate all API keys at startup"""
    issues = []
    
    if not self.binance_api_key or self.binance_api_key == "your_binance_api_key_here":
        issues.append("Binance API Key not configured")
    
    if not self.binance_secret or self.binance_secret == "your_binance_secret_key_here":
        issues.append("Binance Secret Key not configured")
        
    if not self.openrouter_key or self.openrouter_key == "your_openrouter_api_key_here":
        issues.append("OpenRouter API Key not configured - AI will use fallback decisions")
    
    if issues:
        self.print_color("🚨 CONFIGURATION ISSUES FOUND:", self.Fore.RED + self.Style.BRIGHT)
        for issue in issues:
            self.print_color(f"   ❌ {issue}", self.Fore.RED)
        
        if "OpenRouter" in str(issues):
            self.print_color("   💡 Without OpenRouter, AI will use technical analysis fallback only", self.Fore.YELLOW)
    
    return len(issues) == 0

def get_market_news_sentiment(self):
    """Get recent cryptocurrency news sentiment"""
    try:
        news_sources = [
            "CoinDesk", "Cointelegraph", "CryptoSlate", "Decrypt", "Binance Blog"
        ]
        return f"Monitoring: {', '.join(news_sources)}"
    except:
        return "General crypto market news monitoring"

# Attach all methods to the class
FullyAutonomous1HourAITrader._initialize_trading = _initialize_trading
FullyAutonomous1HourAITrader.load_real_trade_history = load_real_trade_history
FullyAutonomous1HourAITrader.save_real_trade_history = save_real_trade_history
FullyAutonomous1HourAITrader.add_trade_to_history = add_trade_to_history
FullyAutonomous1HourAITrader.get_thailand_time = get_thailand_time
FullyAutonomous1HourAITrader.print_color = print_color
FullyAutonomous1HourAITrader.validate_config = validate_config
FullyAutonomous1HourAITrader.setup_futures = setup_futures
FullyAutonomous1HourAITrader.load_symbol_precision = load_symbol_precision
FullyAutonomous1HourAITrader.validate_api_keys = validate_api_keys
FullyAutonomous1HourAITrader.get_market_news_sentiment = get_market_news_sentiment
