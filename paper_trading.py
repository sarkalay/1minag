# paper_trading.py
import os
import json
import time
import requests
import re
import pandas as pd
import numpy as np
import math
import random
from datetime import datetime
import pytz
from dotenv import load_dotenv

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

class FullyAutonomous1HourPaperTrader:
    def __init__(self, real_bot=None):
        self.real_bot = real_bot
        self._initialize_paper_trader()
        
    def _initialize_paper_trader(self):
        """Initialize paper trading bot"""
        self.Fore = Fore
        self.Style = Style
        self.COLORAMA_AVAILABLE = COLORAMA_AVAILABLE
        self.thailand_tz = pytz.timezone('Asia/Bangkok')
        
        # API Keys (for AI decisions)
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY', "your_openrouter_api_key_here")
        
        # Paper Trading Settings
        self.monitoring_interval = 180  # 3 minutes
        self.paper_balance = 500.0
        self.available_budget = 500.0
        self.paper_positions = {}
        self.paper_history_file = "paper_trading_history.json"
        self.paper_history = self.load_paper_history()
        
        # Trading pairs
        self.available_pairs = ["BNBUSDT", "SOLUSDT", "AVAXUSDT"]
        self.max_concurrent_trades = 6
        self.max_position_size_percent = 10
        
        # Market data cache
        self.last_mtf = {}
        self.cycle_count = 0
        
        # Price history for realistic simulation
        self.price_history = {
            "BNBUSDT": [300],
            "SOLUSDT": [180], 
            "AVAXUSDT": [35]
        }
        
        self.print_color("🤖 PAPER TRADING BOT INITIALIZED!", self.Fore.CYAN + self.Style.BRIGHT)
        self.print_color(f"💰 Virtual Budget: ${self.paper_balance}", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color("🎯 NO TP/SL - AI MANUAL CLOSE ONLY", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color("⏰ MONITORING: 3 MINUTE INTERVAL", self.Fore.RED + self.Style.BRIGHT)

    # ===================================================================
    # 1. UTILITY FUNCTIONS
    # ===================================================================
    def print_color(self, text, color=""):
        if self.COLORAMA_AVAILABLE:
            print(f"{color}{text}")
        else:
            print(text)

    def get_thailand_time(self):
        return datetime.now(self.thailand_tz).strftime("%Y-%m-%d %H:%M:%S")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    # ===================================================================
    # 2. HISTORY MANAGEMENT
    # ===================================================================
    def load_paper_history(self):
        try:
            if os.path.exists(self.paper_history_file):
                with open(self.paper_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.print_color(f"📂 Loaded {len(data)} paper trades from history", self.Fore.GREEN)
                return data
        except Exception as e:
            self.print_color(f"❌ History load failed: {e}", self.Fore.YELLOW)
        return []

    def save_paper_history(self):
        try:
            with open(self.paper_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.paper_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.print_color(f"❌ History save failed: {e}", self.Fore.RED)

    def add_paper_trade_to_history(self, trade_data):
        trade_data['close_time'] = self.get_thailand_time()
        trade_data['trade_type'] = 'PAPER'
        self.paper_history.append(trade_data)
        if len(self.paper_history) > 200:
            self.paper_history = self.paper_history[-200:]
        self.save_paper_history()

    # ===================================================================
    # 3. TECHNICAL INDICATORS
    # ===================================================================
    def calculate_ema(self, data, period):
        if len(data) < period:
            return [None] * len(data)
        df = pd.Series(data)
        return df.ewm(span=period, adjust=False).mean().tolist()

    def calculate_rsi(self, data, period=14):
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
        if len(volumes) < window + 1:
            return False
        avg_vol = np.mean(volumes[-window-1:-1])
        current_vol = volumes[-1]
        return current_vol > avg_vol * 1.8

    def get_price_history(self, pair):
        """Generate realistic mock market data"""
        base_prices = {
            "BNBUSDT": 300,
            "SOLUSDT": 180, 
            "AVAXUSDT": 35
        }
        
        # Initialize or update price history
        if pair not in self.price_history:
            self.price_history[pair] = [base_prices.get(pair, 100)]
        
        current_prices = self.price_history[pair]
        last_price = current_prices[-1]
        
        # Simulate realistic price movement
        volatility = random.uniform(-2.0, 2.0)  # ±2% volatility
        new_price = last_price * (1 + volatility / 100)
        
        # Add to history (keep last 100 prices)
        current_prices.append(new_price)
        if len(current_prices) > 100:
            current_prices.pop(0)
        
        # Calculate technical indicators
        if len(current_prices) >= 21:
            ema9 = self.calculate_ema(current_prices, 9)[-1]
            ema21 = self.calculate_ema(current_prices, 21)[-1]
            rsi = self.calculate_rsi(current_prices, 14)[-1] if len(current_prices) >= 15 else 50
        else:
            ema9 = new_price * 1.01
            ema21 = new_price * 0.99
            rsi = 50
        
        # Determine trend and signals
        trend = "BULLISH" if ema9 > ema21 else "BEARISH"
        crossover = "GOLDEN" if len(current_prices) >= 2 and current_prices[-2] <= ema21 and new_price > ema21 else "DEATH" if len(current_prices) >= 2 and current_prices[-2] >= ema21 and new_price < ema21 else "NONE"
        
        # Mock volumes
        volumes = [random.uniform(1000, 10000) for _ in range(20)] + [random.uniform(5000, 20000)]
        vol_spike = self.calculate_volume_spike(volumes)
        
        return {
            'current_price': new_price,
            'price_change': ((new_price - last_price) / last_price * 100),
            'support_levels': [new_price * 0.97, new_price * 0.95],
            'resistance_levels': [new_price * 1.03, new_price * 1.05],
            'mtf_analysis': {
                '5m': {
                    'trend': trend,
                    'crossover': crossover,
                    'rsi': round(rsi, 1),
                    'vol_spike': vol_spike,
                    'support': new_price * 0.98,
                    'resistance': new_price * 1.02
                },
                '15m': {
                    'trend': trend,
                    'crossover': 'NONE',
                    'rsi': round(rsi + random.uniform(-5, 5), 1),
                    'vol_spike': False,
                    'support': new_price * 0.96,
                    'resistance': new_price * 1.04
                },
                '1h': {
                    'trend': "BULLISH" if rsi > 50 else "BEARISH",
                    'ema9': round(ema9, 4),
                    'ema21': round(ema21, 4),
                    'rsi': round(rsi, 1),
                    'support': new_price * 0.94,
                    'resistance': new_price * 1.06
                },
                '4h': {
                    'trend': "BULLISH",
                    'support': new_price * 0.92,
                    'resistance': new_price * 1.08
                }
            }
        }

    def get_current_price(self, pair):
        """Get current price from history"""
        if pair in self.price_history and self.price_history[pair]:
            return self.price_history[pair][-1]
        else:
            base_prices = {"BNBUSDT": 300, "SOLUSDT": 180, "AVAXUSDT": 35}
            return base_prices.get(pair, 100)

    # ===================================================================
    # 4. AI TRADING DECISIONS
    # ===================================================================
    def get_ai_trading_decision(self, pair, market_data):
        """Get AI trading decision from OpenRouter"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if not self.openrouter_key or self.openrouter_key == "your_openrouter_api_key_here":
                    return self.get_fallback_decision(market_data)

                current_price = market_data['current_price']
                mtf = market_data.get('mtf_analysis', {})
                
                # Create analysis text
                mtf_text = "MARKET ANALYSIS:\n"
                for tf in ['5m', '15m', '1h', '4h']:
                    if tf in mtf:
                        data = mtf[tf]
                        mtf_text += f"- {tf.upper()}: {data.get('trend', 'N/A')} | RSI: {data.get('rsi', 50)}"
                        if 'crossover' in data:
                            mtf_text += f" | Signal: {data['crossover']}"
                        if 'vol_spike' in data:
                            mtf_text += f" | Volume: {'SPIKE' if data['vol_spike'] else 'Normal'}"
                        mtf_text += "\n"

                prompt = f"""
                PAPER TRADING DECISION - ${self.available_budget:.2f} Budget

                {mtf_text}
                PAIR: {pair} | PRICE: ${current_price:.4f}

                RULES:
                - Only trade with clear trend alignment
                - Position size: 5-10% of budget
                - Leverage: 3-5x for paper trading
                - NO TP/SL - manual close only
                - Consider RSI, volume, and trend

                Return JSON:
                {{
                    "decision": "LONG" | "SHORT" | "HOLD",
                    "position_size_usd": number,
                    "entry_price": number,
                    "leverage": number,
                    "confidence": 0-100,
                    "reasoning": "Brief analysis"
                }}
                """

                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "deepseek/deepseek-chat-v3.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                }

                self.print_color(f"🧠 AI Analyzing {pair}...", self.Fore.MAGENTA)
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                       headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content'].strip()
                    return self.parse_ai_decision(ai_response, pair, current_price)
                else:
                    self.print_color(f"⚠️ AI API failed: {response.status_code}", self.Fore.YELLOW)
                    
            except Exception as e:
                self.print_color(f"⚠️ AI attempt {attempt+1} failed: {e}", self.Fore.YELLOW)
                if attempt == max_retries - 1:
                    return self.get_fallback_decision(market_data)
                time.sleep(1)
                
        return self.get_fallback_decision(market_data)

    def parse_ai_decision(self, ai_response, pair, current_price):
        """Parse AI response"""
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "decision": data.get('decision', 'HOLD').upper(),
                    "position_size_usd": float(data.get('position_size_usd', 0)),
                    "entry_price": float(data.get('entry_price', current_price)),
                    "leverage": max(3, min(5, int(data.get('leverage', 3)))),
                    "confidence": float(data.get('confidence', 50)),
                    "reasoning": data.get('reasoning', 'AI Analysis')
                }
        except Exception as e:
            self.print_color(f"❌ AI parse failed: {e}", self.Fore.RED)
        return self.get_fallback_decision({'current_price': current_price})

    def get_fallback_decision(self, market_data):
        """Fallback decision when AI is unavailable"""
        current_price = market_data['current_price']
        mtf = market_data.get('mtf_analysis', {})
        
        # Simple technical analysis
        bullish_signals = 0
        h1_data = mtf.get('1h', {})
        m5_data = mtf.get('5m', {})
        
        if h1_data.get('trend') == 'BULLISH':
            bullish_signals += 1
        if m5_data.get('crossover') == 'GOLDEN':
            bullish_signals += 1
        if h1_data.get('rsi', 50) < 40:
            bullish_signals += 1
            
        if bullish_signals >= 2:
            return {
                "decision": "LONG",
                "position_size_usd": 25,
                "entry_price": current_price,
                "leverage": 3,
                "confidence": 60,
                "reasoning": f"Fallback: Bullish signals ({bullish_signals}/3)"
            }
        else:
            return {
                "decision": "HOLD",
                "position_size_usd": 0,
                "entry_price": current_price,
                "leverage": 3,
                "confidence": 40,
                "reasoning": "Fallback: Waiting for clear signals"
            }

    # ===================================================================
    # 5. TRADE EXECUTION
    # ===================================================================
    def paper_execute_trade(self, pair, ai_decision):
        """Execute paper trade"""
        try:
            if len(self.paper_positions) >= self.max_concurrent_trades:
                self.print_color(f"🚫 Max trades reached: {self.max_concurrent_trades}", self.Fore.RED)
                return False

            size_usd = ai_decision['position_size_usd']
            if size_usd > self.available_budget:
                self.print_color(f"🚫 Insufficient budget: ${size_usd:.2f} > ${self.available_budget:.2f}", self.Fore.RED)
                return False

            if size_usd < 10:  # Minimum trade size
                self.print_color(f"🚫 Trade too small: ${size_usd:.2f}", self.Fore.RED)
                return False

            entry_price = ai_decision['entry_price']
            leverage = ai_decision['leverage']
            direction = ai_decision['decision']
            confidence = ai_decision['confidence']

            # Calculate quantity
            notional_value = size_usd * leverage
            quantity = notional_value / entry_price
            quantity = round(quantity, 6)

            trade = {
                'pair': pair,
                'direction': direction,
                'entry_price': entry_price,
                'entry_time': time.time(),
                'quantity': quantity,
                'position_size_usd': size_usd,
                'leverage': leverage,
                'status': 'ACTIVE',
                'ai_reason': ai_decision.get('reasoning', 'AI Decision'),
                'confidence': confidence
            }

            self.paper_positions[pair] = trade
            self.available_budget -= size_usd

            # Display trade execution
            direction_color = self.Fore.GREEN if direction == 'LONG' else self.Fore.RED
            direction_icon = "🟢 LONG" if direction == 'LONG' else "🔴 SHORT"
            
            self.print_color(f"\n🎯 PAPER TRADE EXECUTED", self.Fore.CYAN + self.Style.BRIGHT)
            self.print_color("=" * 60, self.Fore.CYAN)
            self.print_color(f"{direction_icon} {pair}", direction_color + self.Style.BRIGHT)
            self.print_color(f"Size: ${size_usd:.2f} | Leverage: {leverage}x", self.Fore.WHITE)
            self.print_color(f"Entry: ${entry_price:.4f} | Qty: {quantity}", self.Fore.CYAN)
            self.print_color(f"Confidence: {confidence}%", self.Fore.YELLOW)
            self.print_color(f"Reason: {ai_decision.get('reasoning', 'AI Analysis')}", self.Fore.WHITE)
            self.print_color("=" * 60, self.Fore.CYAN)

            return True
            
        except Exception as e:
            self.print_color(f"❌ Trade execution failed: {e}", self.Fore.RED)
            return False

    # ===================================================================
    # 6. POSITION MANAGEMENT
    # ===================================================================
    def calculate_pnl_percent(self, entry, current, direction, leverage=1):
        """Calculate PnL percentage"""
        if direction == "LONG":
            return ((current - entry) / entry) * 100 * leverage
        else:
            return ((entry - current) / entry) * 100 * leverage

    def get_ai_close_decision(self, pair, trade):
        """AI decision for closing positions"""
        try:
            current_price = self.get_current_price(pair)
            pnl_percent = self.calculate_pnl_percent(
                trade['entry_price'], current_price, trade['direction'], trade['leverage']
            )
            duration = (time.time() - trade['entry_time']) / 60  # minutes

            # Smart closing logic
            should_close = False
            close_reason = "HOLD"
            
            # Profit taking
            if pnl_percent >= 8:  # Take profit at 8%
                should_close = True
                close_reason = "TAKE_PROFIT"
            elif pnl_percent >= 4 and duration > 30:  # Take partial profit after 30min
                should_close = True
                close_reason = "PARTIAL_PROFIT"
            # Stop loss
            elif pnl_percent <= -10:  # Stop loss at -10%
                should_close = True
                close_reason = "STOP_LOSS"
            elif pnl_percent <= -6 and duration > 20:  # Early stop if trending against
                should_close = True
                close_reason = "EARLY_STOP"
            # Time-based exits
            elif duration > 120:  # Close after 120 minutes max
                should_close = True
                close_reason = "MAX_TIME"
            elif abs(pnl_percent) < 2 and duration > 45:  # Close if flat after 45min
                should_close = True
                close_reason = "NO_MOVEMENT"

            return {
                "should_close": should_close,
                "close_reason": close_reason,
                "confidence": 80 if should_close else 30,
                "reasoning": f"PnL: {pnl_percent:.1f}%, Duration: {duration:.1f}min"
            }
            
        except Exception as e:
            return {"should_close": False, "close_reason": "ERROR", "confidence": 0, "reasoning": str(e)}

    def paper_close_trade_immediately(self, pair, trade, close_reason):
        """Close paper trade"""
        try:
            current_price = self.get_current_price(pair)
            pnl_percent = self.calculate_pnl_percent(
                trade['entry_price'], current_price, trade['direction'], trade['leverage']
            )
            pnl_usd = (pnl_percent / 100) * trade['position_size_usd']

            # Update budget
            self.available_budget += trade['position_size_usd'] + pnl_usd
            if self.available_budget > self.paper_balance:
                self.paper_balance = self.available_budget

            # Create history record
            duration_min = round((time.time() - trade['entry_time']) / 60, 1)
            
            history_entry = {
                'pair': pair,
                'direction': trade['direction'],
                'entry_price': trade['entry_price'],
                'exit_price': current_price,
                'entry_time': datetime.fromtimestamp(trade['entry_time']).strftime("%Y-%m-%d %H:%M:%S"),
                'close_time': self.get_thailand_time(),
                'duration_min': duration_min,
                'pnl_percent': round(pnl_percent, 2),
                'pnl_usd': round(pnl_usd, 2),
                'position_size_usd': trade['position_size_usd'],
                'leverage': trade['leverage'],
                'close_reason': close_reason,
                'ai_reason': trade['ai_reason'],
                'confidence': trade['confidence']
            }

            self.add_paper_trade_to_history(history_entry)

            # Display closing info
            color = self.Fore.GREEN if pnl_percent > 0 else self.Fore.RED
            self.print_color(f"\n📝 POSITION CLOSED", color + self.Style.BRIGHT)
            self.print_color("=" * 50, color)
            self.print_color(f"Pair: {pair} | {trade['direction']}", self.Fore.WHITE)
            self.print_color(f"PnL: {pnl_percent:+.2f}% (${pnl_usd:+.2f})", color)
            self.print_color(f"Reason: {close_reason}", self.Fore.YELLOW)
            self.print_color(f"Duration: {duration_min} min", self.Fore.CYAN)
            self.print_color(f"New Balance: ${self.available_budget:.2f}", self.Fore.GREEN)
            self.print_color("=" * 50, color)

            # Remove from active positions
            del self.paper_positions[pair]
            return True
            
        except Exception as e:
            self.print_color(f"❌ Close failed: {e}", self.Fore.RED)
            return False

    def monitor_paper_positions(self):
        """Monitor and manage open positions"""
        closed = []
        for pair, trade in list(self.paper_positions.items()):
            if trade['status'] != 'ACTIVE':
                continue

            decision = self.get_ai_close_decision(pair, trade)
            if decision.get("should_close"):
                reason = f"AI_CLOSE: {decision['close_reason']} - {decision['reasoning']}"
                self.print_color(f"🤖 AI Decision: CLOSE {pair} - {decision['close_reason']}", self.Fore.YELLOW)
                self.print_color(f"💭 Reason: {decision['reasoning']}", self.Fore.CYAN)
                self.paper_close_trade_immediately(pair, trade, reason)
                closed.append(pair)
                time.sleep(1)  # Small delay between closes

        return closed

    # ===================================================================
    # 7. DASHBOARD & DISPLAY
    # ===================================================================
    def display_dashboard(self):
        """Display trading dashboard"""
        self.clear_screen()
        now = self.get_thailand_time()
        
        print(f"{self.Fore.CYAN + self.Style.BRIGHT}🤖 PAPER TRADING BOT DASHBOARD{self.Style.RESET_ALL}")
        print(f"{self.Fore.CYAN}═" * 60)
        print(f"🕐 Time: {now}")
        print(f"💰 Balance: ${self.paper_balance:.2f} | 💵 Available: ${self.available_budget:.2f}")
        print(f"📊 Active Trades: {len(self.paper_positions)}/{self.max_concurrent_trades}")
        print(f"📈 Total Trades: {len(self.paper_history)}")
        print(f"{self.Fore.CYAN}═" * 60)

        # Active Positions
        if self.paper_positions:
            print(f"\n{self.Fore.MAGENTA}📈 ACTIVE POSITIONS:{self.Style.RESET_ALL}")
            total_unrealized = 0
            
            for pair, trade in self.paper_positions.items():
                current_price = self.get_current_price(pair)
                pnl_percent = self.calculate_pnl_percent(
                    trade['entry_price'], current_price, trade['direction'], trade['leverage']
                )
                pnl_usd = (pnl_percent / 100) * trade['position_size_usd']
                total_unrealized += pnl_usd
                duration = round((time.time() - trade['entry_time']) / 60, 1)
                
                color = self.Fore.GREEN if pnl_percent > 0 else self.Fore.RED
                direction_icon = "🟢" if trade['direction'] == 'LONG' else "🔴"
                
                print(f"  {direction_icon} {pair:10} {trade['direction']:6} | Size: ${trade['position_size_usd']:6.2f}")
                print(f"     Entry: ${trade['entry_price']:.4f} → Current: ${current_price:.4f}")
                print(f"     PnL: {color}{pnl_percent:+.2f}% (${pnl_usd:+.2f}){self.Style.RESET_ALL} | {duration:4.1f} min | {trade['leverage']}x")
                print(f"     Confidence: {trade['confidence']}%")
                print()
            
            total_color = self.Fore.GREEN if total_unrealized >= 0 else self.Fore.RED
            print(f"  📊 Total Unrealized P&L: {total_color}${total_unrealized:+.2f}{self.Style.RESET_ALL}")
        else:
            print(f"\n{self.Fore.YELLOW}📭 No active positions{self.Style.RESET_ALL}")

        # Recent Trade History
        if self.paper_history:
            print(f"\n{self.Fore.YELLOW}📋 RECENT TRADES (Last 5):{self.Style.RESET_ALL}")
            for trade in self.paper_history[-5:]:
                color = self.Fore.GREEN if trade['pnl_percent'] > 0 else self.Fore.RED
                direction_icon = "🟢" if trade['direction'] == 'LONG' else "🔴"
                print(f"  {direction_icon} {trade['pair']:10} {trade['direction']:6} | {trade['pnl_percent']:+.2f}% | {trade['close_reason'][:20]}")

        print(f"\n{self.Fore.CYAN}═" * 60)
        print(f"⏰ Next analysis in {self.monitoring_interval} seconds...")
        print(f"{self.Fore.CYAN}═" * 60)

    # ===================================================================
    # 8. TRADING CYCLE
    # ===================================================================
    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        try:
            # Display dashboard
            self.display_dashboard()
            
            # Monitor and close positions
            closed_positions = self.monitor_paper_positions()
            if closed_positions:
                self.print_color(f"🔔 Closed {len(closed_positions)} position(s)", self.Fore.CYAN)

            # Look for new entry opportunities
            if self.available_budget > 50 and len(self.paper_positions) < self.max_concurrent_trades:
                self.print_color(f"\n🔍 Scanning {len(self.available_pairs)} pairs for opportunities...", self.Fore.BLUE)
                
                for pair in self.available_pairs:
                    if pair in self.paper_positions:
                        continue  # Skip if already have position
                        
                    try:
                        # Get market data
                        market_data = self.get_price_history(pair)
                        self.last_mtf = market_data.get('mtf_analysis', {})
                        
                        # Get AI decision
                        ai_decision = self.get_ai_trading_decision(pair, market_data)
                        
                        # Execute if valid signal
                        if (ai_decision['decision'] in ['LONG', 'SHORT'] and 
                            ai_decision['position_size_usd'] > 0 and 
                            ai_decision['confidence'] >= 60):
                            
                            self.print_color(f"🎯 Signal: {pair} {ai_decision['decision']} | Confidence: {ai_decision['confidence']}%", self.Fore.GREEN)
                            success = self.paper_execute_trade(pair, ai_decision)
                            if success:
                                time.sleep(2)  # Small delay between entries
                                
                    except Exception as e:
                        self.print_color(f"⚠️ Error analyzing {pair}: {e}", self.Fore.YELLOW)
                        continue
                        
        except Exception as e:
            self.print_color(f"❌ Trading cycle error: {e}", self.Fore.RED)

    # ===================================================================
    # 9. MAIN TRADING LOOP
    # ===================================================================
    def start_paper_trading(self):
        """Start the paper trading bot"""
        self.print_color("🚀 STARTING PAPER TRADING BOT...", self.Fore.MAGENTA + self.Style.BRIGHT)
        self.print_color("💰 VIRTUAL $500 PORTFOLIO", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color("🎯 NO TP/SL - AI MANUAL CLOSE ONLY", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color("⏰ 3 MINUTE MONITORING INTERVAL", self.Fore.RED + self.Style.BRIGHT)
        self.print_color("🛑 Press Ctrl+C to stop", self.Fore.CYAN + self.Style.BRIGHT)
        print()

        try:
            self.cycle_count = 0
            while True:
                self.cycle_count += 1
                self.print_color(f"\n🔄 TRADING CYCLE {self.cycle_count}", self.Fore.BLUE + self.Style.BRIGHT)
                self.print_color("═" * 40, self.Fore.BLUE)
                
                self.run_trading_cycle()
                
                self.print_color(f"⏳ Waiting {self.monitoring_interval} seconds for next cycle...", self.Fore.CYAN)
                time.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            self.print_color(f"\n🛑 TRADING STOPPED BY USER", self.Fore.RED + self.Style.BRIGHT)
            self.display_dashboard()
            
            # Show final stats
            if self.paper_history:
                total_pnl = sum(trade['pnl_usd'] for trade in self.paper_history)
                win_rate = len([t for t in self.paper_history if t['pnl_usd'] > 0]) / len(self.paper_history) * 100
                
                self.print_color(f"\n📊 FINAL STATISTICS", self.Fore.GREEN + self.Style.BRIGHT)
                self.print_color("═" * 40, self.Fore.GREEN)
                self.print_color(f"Total Trades: {len(self.paper_history)}", self.Fore.WHITE)
                self.print_color(f"Win Rate: {win_rate:.1f}%", self.Fore.GREEN if win_rate > 50 else self.Fore.YELLOW)
                self.print_color(f"Total P&L: ${total_pnl:+.2f}", self.Fore.GREEN if total_pnl > 0 else self.Fore.RED)
                self.print_color(f"Final Balance: ${self.paper_balance:.2f}", self.Fore.CYAN)
            
            self.print_color(f"💾 History saved to: {self.paper_history_file}", self.Fore.YELLOW)

# Run the bot directly
if __name__ == "__main__":
    bot = FullyAutonomous1HourPaperTrader()
    bot.start_paper_trading()
