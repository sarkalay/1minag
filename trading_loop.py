# trading_loop.py
import time
import os

def display_dashboard(self):
    """Display trading dashboard WITH learning progress"""
    self.print_color(f"\n🤖 AI TRADING DASHBOARD - {self.get_thailand_time()}", self.Fore.CYAN + self.Style.BRIGHT)
    self.print_color("=" * 90, self.Fore.CYAN)
    self.print_color(f"🎯 MODE: NO TP/SL - AI MANUAL CLOSE ONLY", self.Fore.YELLOW + self.Style.BRIGHT)
    self.print_color(f"⏰ MONITORING: 3 MINUTE INTERVAL", self.Fore.RED + self.Style.BRIGHT)
    
    # === MTF SUMMARY ===
    if hasattr(self, 'last_mtf') and self.last_mtf:
        self.print_color(" MULTI-TIMEFRAME SUMMARY", self.Fore.MAGENTA + self.Style.BRIGHT)
        for tf, data in self.last_mtf.items():
            color = self.Fore.GREEN if data.get('trend') == 'BULLISH' else self.Fore.RED
            signal = f" | {data.get('crossover', '')}" if 'crossover' in data else ""
            rsi_text = f" | RSI: {data.get('rsi', 50)}" if 'rsi' in data else ""
            vol_text = f" | Vol: {'SPIKE' if data.get('vol_spike') else 'Normal'}" if 'vol_spike' in data else ""
            self.print_color(f"  {tf.upper()}: {data.get('trend', 'N/A')}{signal}{rsi_text}{vol_text}", color)
        self.print_color("   " + "-" * 60, self.Fore.CYAN)
    
    # 🧠 Add learning stats
    try:
        from learn_script import SelfLearningAITrader
        if hasattr(self, 'mistakes_history'):
            total_lessons = len(self.mistakes_history)
            if total_lessons > 0:
                self.print_color(f"🧠 AI HAS LEARNED FROM {total_lessons} MISTAKES", self.Fore.MAGENTA + self.Style.BRIGHT)
    except:
        pass
    
    active_count = 0
    total_unrealized = 0
    
    for pair, trade in self.ai_opened_trades.items():
        if trade['status'] == 'ACTIVE':
            active_count += 1
            current_price = self.get_current_price(pair)
            
            direction_icon = "🟢 LONG" if trade['direction'] == 'LONG' else "🔴 SHORT"
            
            if trade['direction'] == 'LONG':
                unrealized_pnl = (current_price - trade['entry_price']) * trade['quantity']
            else:
                unrealized_pnl = (trade['entry_price'] - current_price) * trade['quantity']
                
            total_unrealized += unrealized_pnl
            pnl_color = self.Fore.GREEN + self.Style.BRIGHT if unrealized_pnl >= 0 else self.Fore.RED + self.Style.BRIGHT
            
            self.print_color(f"{direction_icon} {pair}", self.Fore.WHITE + self.Style.BRIGHT)
            self.print_color(f"   Size: ${trade['position_size_usd']:.2f} | Leverage: {trade['leverage']}x ⚡", self.Fore.WHITE)
            self.print_color(f"   Entry: ${trade['entry_price']:.4f} | Current: ${current_price:.4f}", self.Fore.WHITE)
            self.print_color(f"   P&L: ${unrealized_pnl:.2f}", pnl_color)
            self.print_color(f"   🎯 NO TP/SL - AI Monitoring Every 3min", self.Fore.YELLOW)
            self.print_color("   " + "-" * 60, self.Fore.CYAN)
    
    if active_count == 0:
        self.print_color("No active positions", self.Fore.YELLOW)
    else:
        total_color = self.Fore.GREEN + self.Style.BRIGHT if total_unrealized >= 0 else self.Fore.RED + self.Style.BRIGHT
        self.print_color(f"📊 Active Positions: {active_count}/{self.max_concurrent_trades} | Total Unrealized P&L: ${total_unrealized:.2f}", total_color)

def show_trade_history(self, limit=15):
    """Show trading history"""
    if not self.real_trade_history:
        self.print_color("No trade history found", self.Fore.YELLOW)
        return
    
    self.print_color(f"\n📊 TRADING HISTORY (Last {min(limit, len(self.real_trade_history))} trades)", self.Fore.CYAN + self.Style.BRIGHT)
    self.print_color("=" * 120, self.Fore.CYAN)
    
    recent_trades = self.real_trade_history[-limit:]
    for i, trade in enumerate(reversed(recent_trades)):
        pnl = trade.get('pnl', 0)
        pnl_color = self.Fore.GREEN + self.Style.BRIGHT if pnl > 0 else self.Fore.RED + self.Style.BRIGHT if pnl < 0 else self.Fore.YELLOW
        direction_icon = "🟢 LONG" if trade['direction'] == 'LONG' else "🔴 SHORT"
        position_size = trade.get('position_size_usd', 0)
        leverage = trade.get('leverage', 1)
        
        self.print_color(f"{i+1:2d}. {direction_icon} {trade['pair']} | Size: ${position_size:.2f} | Leverage: {leverage}x | P&L: ${pnl:.2f}", pnl_color)
        self.print_color(f"     Entry: ${trade.get('entry_price', 0):.4f} | Exit: ${trade.get('exit_price', 0):.4f} | {trade.get('close_reason', 'N/A')}", self.Fore.YELLOW)

def show_trading_stats(self):
    """Show trading statistics"""
    if self.real_total_trades == 0:
        return
        
    win_rate = (self.real_winning_trades / self.real_total_trades) * 100
    avg_trade = self.real_total_pnl / self.real_total_trades
    
    self.print_color(f"\n📈 TRADING STATISTICS", self.Fore.GREEN + self.Style.BRIGHT)
    self.print_color("=" * 60, self.Fore.GREEN)
    self.print_color(f"Total Trades: {self.real_total_trades} | Winning Trades: {self.real_winning_trades}", self.Fore.WHITE)
    self.print_color(f"Win Rate: {win_rate:.1f}%", self.Fore.GREEN + self.Style.BRIGHT if win_rate > 50 else self.Fore.YELLOW)
    self.print_color(f"Total P&L: ${self.real_total_pnl:.2f}", self.Fore.GREEN + self.Style.BRIGHT if self.real_total_pnl > 0 else self.Fore.RED + self.Style.BRIGHT)
    self.print_color(f"Average P&L per Trade: ${avg_trade:.2f}", self.Fore.WHITE)
    self.print_color(f"Available Budget: ${self.available_budget:.2f}", self.Fore.CYAN + self.Style.BRIGHT)

def show_advanced_learning_progress(self):
    """Display learning progress every 3 cycles"""
    try:
        from learn_script import SelfLearningAITrader
        if hasattr(self, 'mistakes_history'):
            total_lessons = len(self.mistakes_history)
            if total_lessons > 0:
                self.print_color(f"\n🧠 AI LEARNING PROGRESS (Cycle {getattr(self, 'cycle_count', 0)})", self.Fore.MAGENTA + self.Style.BRIGHT)
                self.print_color("=" * 50, self.Fore.MAGENTA)
                self.print_color(f"📚 Total Lessons Learned: {total_lessons}", self.Fore.CYAN)
                
                # Show recent mistakes patterns
                recent_mistakes = self.mistakes_history[-5:] if len(self.mistakes_history) >= 5 else self.mistakes_history
                if recent_mistakes:
                    self.print_color(f"🔄 Recent Patterns:", self.Fore.YELLOW)
                    for i, mistake in enumerate(reversed(recent_mistakes)):
                        reason = mistake.get('reason', 'Unknown pattern')
                        self.print_color(f"   {i+1}. {reason}", self.Fore.WHITE)
                
                # Show improvement stats
                if hasattr(self, 'performance_stats'):
                    total_trades = self.performance_stats.get('total_trades', 0)
                    winning_trades = self.performance_stats.get('winning_trades', 0)
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                    self.print_color(f"📈 Current Win Rate: {win_rate:.1f}%", self.Fore.GREEN)
                    
                # Show learned patterns count
                if hasattr(self, 'learned_patterns'):
                    pattern_count = len(self.learned_patterns)
                    self.print_color(f"🎯 Patterns Memorized: {pattern_count}", self.Fore.BLUE)
            else:
                self.print_color(f"\n🧠 AI is collecting learning data... (No mistakes yet)", self.Fore.YELLOW)
    except:
        self.print_color(f"\n🧠 Learning module not available", self.Fore.YELLOW)

def run_trading_cycle(self):
    """Run trading cycle with REVERSE position checking and AI manual close"""
    try:
        # First monitor and ask AI to close positions
        self.monitor_positions()
        self.display_dashboard()
        
        # Show stats periodically
        if hasattr(self, 'cycle_count') and self.cycle_count % 4 == 0:  # Every 4 cycles (5 minutes)
            self.show_trade_history(8)
            self.show_trading_stats()
        
        # 🧠 Show advanced learning progress every 3 cycles
        if hasattr(self, 'cycle_count') and self.cycle_count % 3 == 0:
            self.show_advanced_learning_progress()
        
        self.print_color(f"\n🔍 DEEPSEEK SCANNING {len(self.available_pairs)} PAIRS...", self.Fore.BLUE + self.Style.BRIGHT)
        
        qualified_signals = 0
        for pair in self.available_pairs:
            if self.available_budget > 100:
                market_data = self.get_price_history(pair)
                self.last_mtf = market_data.get('mtf_analysis', {})
                
                # Use learning-enhanced AI decision
                ai_decision = self.get_ai_decision_with_learning(pair, market_data)
                
                if ai_decision["decision"] != "HOLD" and ai_decision["position_size_usd"] > 0:
                    qualified_signals += 1
                    direction = ai_decision['decision']
                    leverage_info = f"Leverage: {ai_decision['leverage']}x"
                    
                    if direction.startswith('REVERSE_'):
                        self.print_color(f"🔄 REVERSE SIGNAL: {pair} {direction} | Size: ${ai_decision['position_size_usd']:.2f}", self.Fore.YELLOW + self.Style.BRIGHT)
                    else:
                        self.print_color(f"🎯 TRADE SIGNAL: {pair} {direction} | Size: ${ai_decision['position_size_usd']:.2f} | {leverage_info}", self.Fore.GREEN + self.Style.BRIGHT)
                    
                    success = self.execute_ai_trade(pair, ai_decision)
                    if success:
                        time.sleep(2)  # Reduced delay for faster 3min cycles
            
        if qualified_signals == 0:
            self.print_color("No qualified DeepSeek signals this cycle", self.Fore.YELLOW)
            
    except Exception as e:
        self.print_color(f"❌ Trading cycle error: {e}", self.Fore.RED)

def start_real_trading(self):
    """Start trading with REVERSE position feature and NO TP/SL"""
    self.print_color("🚀 STARTING AI TRADER WITH 3MINUTE MONITORING!", self.Fore.CYAN + self.Style.BRIGHT)
    self.print_color("💰 AI MANAGING $500 PORTFOLIO", self.Fore.GREEN + self.Style.BRIGHT)
    self.print_color("🔄 REVERSE POSITION: ENABLED (AI can flip losing positions)", self.Fore.MAGENTA + self.Style.BRIGHT)
    self.print_color("🎯 NO TP/SL - AI MANUAL CLOSE ONLY", self.Fore.YELLOW + self.Style.BRIGHT)
    self.print_color("⏰ MONITORING: 3 MINUTE INTERVAL", self.Fore.RED + self.Style.BRIGHT)
    self.print_color("⚡ LEVERAGE: 5x to 10x", self.Fore.RED + self.Style.BRIGHT)
    try:
        from learn_script import SelfLearningAITrader
        self.print_color("🧠 SELF-LEARNING AI: ENABLED", self.Fore.MAGENTA + self.Style.BRIGHT)
    except:
        pass
    
    self.cycle_count = 0
    while True:
        try:
            self.cycle_count += 1
            self.print_color(f"\n🔄 TRADING CYCLE {self.cycle_count} (3MIN INTERVAL)", self.Fore.CYAN + self.Style.BRIGHT)
            self.print_color("=" * 60, self.Fore.CYAN)
            self.run_trading_cycle()
            self.print_color(f"⏳ Next analysis in 3 minute...", self.Fore.BLUE)
            time.sleep(self.monitoring_interval)  # 3 minute
            
        except KeyboardInterrupt:
            self.print_color(f"\n🛑 TRADING STOPPED", self.Fore.RED + self.Style.BRIGHT)
            self.show_trade_history(15)
            self.show_trading_stats()
            break
        except Exception as e:
            self.print_color(f"❌ Main loop error: {e}", self.Fore.RED)
            time.sleep(self.monitoring_interval)

# Attach to class
from core import FullyAutonomous1HourAITrader

for func in [display_dashboard, show_trade_history, show_trading_stats, 
             show_advanced_learning_progress, run_trading_cycle, start_real_trading]:
    setattr(FullyAutonomous1HourAITrader, func.__name__, func)
