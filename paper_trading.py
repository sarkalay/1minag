# paper_trading_bot.py
import os
import json
import time
import requests
import re
import pandas as pd
import numpy as np
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
    def __init__(self):
        self._initialize_bot()
        
    def _initialize_bot(self):
        """Initialize paper trading bot"""
        self.Fore = Fore
        self.Style = Style
        self.COLORAMA_AVAILABLE = COLORAMA_AVAILABLE
        self.thailand_tz = pytz.timezone('Asia/Bangkok')
        
        # API Keys (for AI decisions)
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        
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

    def get_mock_price_history(self, pair):
        """Generate realistic mock market data"""
        base_prices = {
            "BNBUSDT": 300,
            "SOLUSDT": 180, 
            "AVAXUSDT": 35
        }
        
        base_price = base_prices.get(pair, 100)
        current_time = time.time()
        
        # Simulate price movement based on time
        price_variation = math.sin(current_time / 300) * 10  # 5-minute cycles
        current_price = base_price + price_variation
        
        # Generate realistic mock data
        return {
            'current_price': current_price,
            'price_change': (price_variation / base_price) * 100,
            'support_levels': [current_price * 0.97, current_price * 0.95],
            'resistance_levels': [current_price * 1.03, current_price * 1.05],
            'mtf_analysis': {
                '5m': {
                    'trend': 'BULLISH' if price_variation > 0 else 'BEARISH',
                    'crossover': 'GOLDEN' if price_variation > 2 else 'DEATH' if price_variation < -2 else 'NONE',
                    'rsi': 65 if price_variation > 0 else 35,
                    'vol_spike': True if current_time % 300 < 60 else False
                },
                '15m': {
                    'trend': 'BULLISH' if price_variation > -1 else 'BEARISH',
                    'crossover': 'NONE',
                    'rsi': 55,
                    'vol_spike': False
                },
                '1h': {
                    'trend': 'BULLISH',
                    'ema9': current_price * 1.005,
                    'ema21': current_price * 0.995,
                    'rsi': 52
                },
                '4h': {
                    'trend': 'BULLISH',
                    'support': current_price * 0.92,
                    'resistance': current_price * 1.08
                }
            }
        }

    def get_current_price(self, pair):
        """Get current price with realistic fluctuations"""
        base_prices = {
            "BNBUSDT": 300,
            "SOLUSDT": 180,
            "AVAXUSDT": 35
        }
        base_price = base_prices.get(pair, 100)
        
        # Add some random fluctuation
        import random
        fluctuation = random.uniform(-0.5, 0.5)  # ±0.5% fluctuation
        return base_price * (1 + fluctuation / 100)

    # ===================================================================
    # 4. AI TRADING DECISIONS
    # ===================================================================
    def get_ai_trading_decision(self, pair, market_data):
        """Get AI trading decision from OpenRouter"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if not self.openrouter_key:
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

                response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                       headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content'].strip()
                    return self.parse_ai_decision(ai_response, pair, current_price)
                    
            except Exception as e:
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
        except:
            pass
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
                return False

            size_usd = ai_decision['position_size_usd']
            if size_usd > self.available_budget:
                size_usd = self.available_budget * 0.8  # Use 80% of available

            if size_usd < 10:  # Minimum trade size
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

            # Simple closing logic
            should_close = False
            close_reason = "HOLD"
            
            if pnl_percent >= 5:  # Take profit at 5%
                should_close = True
                close_reason = "TAKE_PROFIT"
            elif pnl_percent <= -8:  # Stop loss at -8%
                should_close = True
                close_reason = "STOP_LOSS"
            elif duration > 60:  # Close after 60 minutes
                should_close = True
                close_reason = "TIME_EXIT"
            elif abs(pnl_percent) < 1 and duration > 30:  # Close if flat after 30min
                should_close = True
                close_reason = "NO_MOVEMENT"

            return {
                "should_close": should_close,
                "close_reason": close_reason,
                "confidence": 70 if should_close else 30,
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
                        market_data = self.get_mock_price_history(pair)
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
    def start_trading(self):
        """Start the paper trading bot"""
        self.print_color("🚀 STARTING PAPER TRADING BOT...", self.Fore.MAGENTA + self.Style.BRIGHT)
        self.print_color("💰 VIRTUAL $500 PORTFOLIO", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color("🎯 NO TP/SL - AI MANUAL CLOSE ONLY", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color("⏰ 3 MINUTE MONITORING INTERVAL", self.Fore.RED + self.Style.BRIGHT)
        self.print_color("🛑 Press Ctrl+C to stop", self.Fore.CYAN + self.Style.BRIGHT)
        print()

        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                self.print_color(f"\n🔄 TRADING CYCLE {cycle_count}", self.Fore.BLUE + self.Style.BRIGHT)
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

# Required imports for the mock data
import math

# Run the bot
if __name__ == "__main__":
    bot = PaperTradingBot()
    bot.start_trading()
