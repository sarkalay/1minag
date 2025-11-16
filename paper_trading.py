# paper_trading.py
import os
import json
import time
from datetime import datetime
import pytz

class FullyAutonomous1HourPaperTrader:
    def __init__(self, real_bot):
        self.real_bot = real_bot
        self.Fore = real_bot.Fore
        self.Style = real_bot.Style
        self.COLORAMA_AVAILABLE = real_bot.COLORAMA_AVAILABLE
        self.thailand_tz = real_bot.thailand_tz

        # Paper Trading Settings
        self.monitoring_interval = 180  # 3 minutes
        self.paper_balance = 500.0
        self.available_budget = 500.0
        self.paper_positions = {}  # {pair: trade_data}
        self.paper_history_file = "paper_trading_history.json"
        self.paper_history = self.load_paper_history()
        self.available_pairs = real_bot.available_pairs.copy()
        self.max_concurrent_trades = 6
        self.max_position_size_percent = 10

        self.print_color("🤖 PAPER TRADER INITIALIZED | Budget: $500", self.Fore.CYAN + self.Style.BRIGHT)

    # ===================================================================
    # 1. HISTORY MANAGEMENT
    # ===================================================================
    def load_paper_history(self):
        try:
            if os.path.exists(self.paper_history_file):
                with open(self.paper_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.print_color(f"📂 Loaded {len(data)} paper trades from history.", self.Fore.GREEN)
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
    # 2. UTILS
    # ===================================================================
    def get_thailand_time(self):
        return datetime.now(self.thailand_tz).strftime("%Y-%m-%d %H:%M:%S")

    def print_color(self, text, color=""):
        if self.COLORAMA_AVAILABLE:
            print(f"{color}{text}{self.Style.RESET_ALL}")
        else:
            print(text)

    def calculate_pnl_percent(self, entry, exit, direction, leverage=1):
        if direction == "LONG":
            return ((exit - entry) / entry) * 100 * leverage
        else:
            return ((entry - exit) / entry) * 100 * leverage

    # ===================================================================
    # 3. PAPER EXECUTE TRADE
    # ===================================================================
    def paper_execute_trade(self, pair, ai_decision):
        try:
            if len(self.paper_positions) >= self.max_concurrent_trades:
                return False

            size_usd = ai_decision['position_size_usd']
            if size_usd > self.available_budget:
                size_usd = self.available_budget * 0.9

            if size_usd < 5:
                return False

            entry_price = ai_decision['entry_price']
            leverage = ai_decision['leverage']
            direction = "LONG" if "LONG" in ai_decision['decision'] else "SHORT"

            quantity = (size_usd * leverage) / entry_price
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
                'ai_reason': ai_decision.get('reasoning', 'AI Entry'),
                'confidence': ai_decision.get('confidence', 0)
            }

            self.paper_positions[pair] = trade
            self.available_budget -= size_usd

            self.print_color(f"📝 PAPER OPEN: {direction} {pair} | ${size_usd:.1f} | {leverage}x | Conf: {trade['confidence']}%", 
                           self.Fore.GREEN + self.Style.BRIGHT)
            self.print_color(f"📊 Entry: ${entry_price:.6f} | Qty: {quantity}", self.Fore.CYAN)

            return True
        except Exception as e:
            self.print_color(f"❌ Paper execute failed: {e}", self.Fore.RED)
            return False

    # ===================================================================
    # 4. PAPER CLOSE TRADE
    # ===================================================================
    def paper_close_trade_immediately(self, pair, trade, close_reason):
        try:
            current_price = self.real_bot.get_current_price(pair)
            pnl_percent = self.calculate_pnl_percent(
                trade['entry_price'], current_price, trade['direction'], trade['leverage']
            )
            pnl_usd = (pnl_percent / 100) * trade['position_size_usd']

            self.available_budget += trade['position_size_usd'] + pnl_usd
            if self.available_budget > self.paper_balance:
                self.paper_balance = self.available_budget

            close_time = self.get_thailand_time()
            duration_min = round((time.time() - trade['entry_time']) / 60, 1)

            history_entry = {
                'pair': pair,
                'direction': trade['direction'],
                'entry_price': trade['entry_price'],
                'exit_price': current_price,
                'entry_time': datetime.fromtimestamp(trade['entry_time'], self.thailand_tz).strftime("%Y-%m-%d %H:%M:%S"),
                'close_time': close_time,
                'duration_min': duration_min,
                'pnl_percent': round(pnl_percent, 2),
                'pnl_usd': round(pnl_usd, 2),
                'position_size_usd': trade['position_size_usd'],
                'leverage': trade['leverage'],
                'close_reason': close_reason,
                'ai_entry_reason': trade['ai_reason'],
                'confidence': trade['confidence']
            }

            self.add_paper_trade_to_history(history_entry)

            color = self.Fore.GREEN if pnl_percent > 0 else self.Fore.RED
            self.print_color(f"📝 PAPER CLOSE: {pair} | PnL: {pnl_percent:+.2f}% (${pnl_usd:+.2f})", 
                           color + self.Style.BRIGHT)
            self.print_color(f"📋 Reason: {close_reason}", self.Fore.YELLOW)
            self.print_color(f"⏱️ Duration: {duration_min} min | Balance: ${self.available_budget:.2f}", self.Fore.CYAN)

            del self.paper_positions[pair]
            return True
        except Exception as e:
            self.print_color(f"❌ Paper close failed: {e}", self.Fore.RED)
            return False

    # ===================================================================
    # 5. AI CLOSE DECISION (Uses Real Bot's AI)
    # ===================================================================
    def get_ai_close_decision(self, pair, trade):
        return self.real_bot.get_ai_close_decision(pair, trade)

    # ===================================================================
    # 6. MONITOR PAPER POSITIONS
    # ===================================================================
    def monitor_paper_positions(self):
        closed = []
        for pair, trade in list(self.paper_positions.items()):
            if trade['status'] != 'ACTIVE':
                continue

            decision = self.get_ai_close_decision(pair, trade)
            if decision.get("should_close"):
                thought = decision.get("ai_thought", "No AI thought.")
                reason = f"AI_CLOSE: {decision['close_reason']} | {thought[:100]}{'...' if len(thought)>100 else ''}"
                
                self.print_color(f"🎯 AI Decision: CLOSE {pair}", self.Fore.YELLOW + self.Style.BRIGHT)
                self.print_color(f"💭 AI Thought: {thought}", self.Fore.CYAN + self.Style.DIM)

                self.paper_close_trade_immediately(pair, trade, reason)
                closed.append(pair)

        return closed

    # ===================================================================
    # 7. DISPLAY PAPER DASHBOARD
    # ===================================================================
    def display_paper_dashboard(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        now = self.get_thailand_time()
        print(f"{self.Fore.CYAN + self.Style.BRIGHT}=== PAPER TRADER DASHBOARD ==={self.Style.RESET_ALL}")
        print(f"🕐 Time: {now} | 💰 Balance: ${self.paper_balance:.2f} | 💵 Available: ${self.available_budget:.2f}")
        print(f"📊 Active Trades: {len(self.paper_positions)} / {self.max_concurrent_trades}")
        print(f"📈 Total Paper Trades: {len(self.paper_history)}\n")

        if self.paper_positions:
            print(f"{self.Fore.MAGENTA}ACTIVE POSITIONS:{self.Style.RESET_ALL}")
            for pair, t in self.paper_positions.items():
                current_price = self.real_bot.get_current_price(pair)
                pnl = self.calculate_pnl_percent(t['entry_price'], current_price, t['direction'], t['leverage'])
                duration = round((time.time() - t['entry_time']) / 60, 1)
                color = self.Fore.GREEN if pnl > 0 else self.Fore.RED
                print(f"  {pair} | {t['direction']} | Entry: ${t['entry_price']:.4f} → ${current_price:.4f}")
                print(f"  PnL: {color}{pnl:+.2f}% (${pnl/100*t['position_size_usd']:+.2f}){self.Style.RESET_ALL} | {duration} min | {t['leverage']}x")
            print()

        if self.paper_history:
            print(f"{self.Fore.YELLOW}RECENT PAPER TRADES (Last 5):{self.Style.RESET_ALL}")
            for trade in self.paper_history[-5:]:
                color = self.Fore.GREEN if trade['pnl_percent'] > 0 else self.Fore.RED
                print(f"  {trade['pair']} | {trade['direction']} | {trade['pnl_percent']:+.2f}% | {trade['close_reason'][:30]}")
            print()

    # ===================================================================
    # 8. RUN ONE CYCLE
    # ===================================================================
    # paper_trading.py - run_paper_trading_cycle function ကို ပြင်ပါ
def run_paper_trading_cycle(self):
    self.display_paper_dashboard()

    # Monitor & Close
    self.monitor_paper_positions()

    # Entry Logic (Only if budget allows)
    if self.available_budget > 50 and len(self.paper_positions) < self.max_concurrent_trades:
        for pair in self.available_pairs:
            if pair in self.paper_positions:
                continue
            try:
                market_data = self.real_bot.get_price_history(pair)
                
                # Check if market data is valid
                if not market_data or 'current_price' not in market_data:
                    self.print_color(f"⚠️ Skipping {pair}: Invalid market data", self.Fore.YELLOW)
                    continue
                    
                ai_decision = self.real_bot.get_ai_trading_decision(pair, market_data)
                
                if ai_decision and ai_decision['decision'] in ['LONG', 'SHORT'] and ai_decision['confidence'] >= 65:
                    self.print_color(f"🎯 PAPER SIGNAL: {pair} {ai_decision['decision']} | Confidence: {ai_decision['confidence']}%", self.Fore.GREEN)
                    self.paper_execute_trade(pair, ai_decision)
                    time.sleep(1)  # Small delay between trades
                    
            except Exception as e:
                self.print_color(f"⚠️ Paper trading error for {pair}: {e}", self.Fore.YELLOW)
                continue

    # ===================================================================
    # 9. START PAPER TRADING
    # ===================================================================
    def start_paper_trading(self):
        self.print_color("🚀 STARTING PAPER TRADING MODE...", self.Fore.MAGENTA + self.Style.BRIGHT)
        self.print_color("🛑 Press Ctrl+C to stop.\n", self.Fore.YELLOW)

        try:
            cycle = 0
            while True:
                cycle += 1
                self.print_color(f"--- PAPER CYCLE {cycle} ---", self.Fore.BLUE + self.Style.DIM)
                self.run_paper_trading_cycle()
                time.sleep(self.monitoring_interval)
        except KeyboardInterrupt:
            self.print_color("\n🛑 PAPER TRADING STOPPED BY USER.", self.Fore.RED + self.Style.BRIGHT)
            self.display_paper_dashboard()
            print(f"💰 Final Balance: ${self.paper_balance:.2f}")
            print(f"💾 History saved to: {self.paper_history_file}")
