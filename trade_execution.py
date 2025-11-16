# trade_execution.py
import time
import json

def calculate_quantity(self, pair, entry_price, position_size_usd, leverage):
    """Calculate quantity based on position size and leverage"""
    try:
        if entry_price <= 0:
            return None
            
        # Calculate notional value
        notional_value = position_size_usd * leverage
        
        # Calculate quantity
        quantity = notional_value / entry_price
        
        # Apply precision
        precision = self.quantity_precision.get(pair, 3)
        quantity = round(quantity, precision)
        
        if quantity <= 0:
            return None
            
        self.print_color(f"📊 Position: ${position_size_usd} | Leverage: {leverage}x | Notional: ${notional_value:.2f} | Quantity: {quantity}", self.Fore.CYAN)
        return quantity
        
    except Exception as e:
        self.print_color(f"❌ Quantity calculation failed: {e}", self.Fore.RED)
        return None

def can_open_new_position(self, pair, position_size_usd):
    """Check if new position can be opened"""
    if pair in self.ai_opened_trades:
        return False, "Position already exists"
    
    if len(self.ai_opened_trades) >= self.max_concurrent_trades:
        return False, f"Max concurrent trades reached ({self.max_concurrent_trades})"
        
    if position_size_usd > self.available_budget:
        return False, f"Insufficient budget: ${position_size_usd:.2f} > ${self.available_budget:.2f}"
        
    max_allowed = self.total_budget * self.max_position_size_percent / 100
    if position_size_usd > max_allowed:
        return False, f"Position size too large: ${position_size_usd:.2f} > ${max_allowed:.2f}"
        
    return True, "OK"

def execute_ai_trade(self, pair, ai_decision):
    """Execute trade WITHOUT TP/SL orders - AI will close manually"""
    try:
        decision = ai_decision["decision"]
        position_size_usd = ai_decision["position_size_usd"]
        entry_price = ai_decision["entry_price"]
        leverage = ai_decision["leverage"]
        confidence = ai_decision["confidence"]
        reasoning = ai_decision["reasoning"]
        
        # NEW: Handle reverse positions
        if decision.startswith('REVERSE_'):
            if pair in self.ai_opened_trades:
                current_trade = self.ai_opened_trades[pair]
                return self.execute_reverse_position(pair, ai_decision, current_trade)
            else:
                self.print_color(f"❌ Cannot reverse: No active position for {pair}", self.Fore.RED)
                return False
        
        if decision == "HOLD" or position_size_usd <= 0:
            self.print_color(f"🟡 DeepSeek decides to HOLD {pair}", self.Fore.YELLOW)
            return False
        
        # Check if we can open position (skip if reversing)
        if pair in self.ai_opened_trades and not decision.startswith('REVERSE_'):
            self.print_color(f"🚫 Cannot open {pair}: Position already exists", self.Fore.RED)
            return False
        
        if len(self.ai_opened_trades) >= self.max_concurrent_trades and pair not in self.ai_opened_trades:
            self.print_color(f"🚫 Cannot open {pair}: Max concurrent trades reached", self.Fore.RED)
            return False
            
        if position_size_usd > self.available_budget:
            self.print_color(f"🚫 Cannot open {pair}: Insufficient budget", self.Fore.RED)
            return False
        
        # Calculate quantity
        quantity = self.calculate_quantity(pair, entry_price, position_size_usd, leverage)
        if quantity is None:
            return False
        
        # Display AI trade decision (NO TP/SL)
        direction_color = self.Fore.GREEN + self.Style.BRIGHT if decision == 'LONG' else self.Fore.RED + self.Style.BRIGHT
        direction_icon = "🟢 LONG" if decision == 'LONG' else "🔴 SHORT"
        
        self.print_color(f"\n🤖 DEEPSEEK TRADE EXECUTION (NO TP/SL)", self.Fore.CYAN + self.Style.BRIGHT)
        self.print_color("=" * 80, self.Fore.CYAN)
        self.print_color(f"{direction_icon} {pair}", direction_color)
        self.print_color(f"POSITION SIZE: ${position_size_usd:.2f}", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color(f"LEVERAGE: {leverage}x ⚡", self.Fore.RED + self.Style.BRIGHT)
        self.print_color(f"ENTRY PRICE: ${entry_price:.4f}", self.Fore.WHITE)
        self.print_color(f"QUANTITY: {quantity}", self.Fore.CYAN)
        self.print_color(f"🎯 NO TP/SL SET - AI WILL CLOSE MANUALLY BASED ON MARKET", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color(f"CONFIDENCE: {confidence}%", self.Fore.YELLOW + self.Style.BRIGHT)
        self.print_color(f"REASONING: {reasoning}", self.Fore.WHITE)
        self.print_color("=" * 80, self.Fore.CYAN)
        
        # Execute live trade WITHOUT TP/SL orders
        if self.binance:
            entry_side = 'BUY' if decision == 'LONG' else 'SELL'
            
            # Set leverage
            try:
                self.binance.futures_change_leverage(symbol=pair, leverage=leverage)
            except Exception as e:
                self.print_color(f"⚠️ Leverage change failed: {e}", self.Fore.YELLOW)
            
            # Execute order ONLY - no TP/SL orders
            order = self.binance.futures_create_order(
                symbol=pair,
                side=entry_side,
                type='MARKET',
                quantity=quantity
            )
            
            # ❌❌❌ NO TP/SL ORDERS CREATED ❌❌❌
        
        # Update budget and track trade
        self.available_budget -= position_size_usd
        
        self.ai_opened_trades[pair] = {
            "pair": pair,
            "direction": decision,
            "entry_price": entry_price,
            "quantity": quantity,
            "position_size_usd": position_size_usd,
            "leverage": leverage,
            "entry_time": time.time(),
            "status": 'ACTIVE',
            'ai_confidence': confidence,
            'ai_reasoning': reasoning,
            'entry_time_th': self.get_thailand_time(),
            'has_tp_sl': False  # NEW: Mark as no TP/SL
        }
        
        self.print_color(f"✅ TRADE EXECUTED (NO TP/SL): {pair} {decision} | Leverage: {leverage}x", self.Fore.GREEN + self.Style.BRIGHT)
        self.print_color(f"📊 AI will monitor and close manually based on market conditions", self.Fore.BLUE)
        return True
        
    except Exception as e:
        self.print_color(f"❌ Trade execution failed: {e}", self.Fore.RED)
        return False

def execute_reverse_position(self, pair, ai_decision, current_trade):
    """Execute reverse position - CLOSE CURRENT, THEN ASK AI BEFORE OPENING REVERSE"""
    try:
        self.print_color(f"🔄 ATTEMPTING REVERSE POSITION FOR {pair}", self.Fore.YELLOW + self.Style.BRIGHT)
        
        # 1. First close the current losing position
        close_success = self.close_trade_immediately(pair, current_trade, "REVERSE_POSITION")
        
        if close_success:
            # 2. Wait a moment for position to close
            time.sleep(2)
            
            # 3. Verify position is actually removed
            if pair in self.ai_opened_trades:
                self.print_color(f"⚠️  Position still exists after close, forcing removal...", self.Fore.RED)
                del self.ai_opened_trades[pair]
            
            # 4. 🆕 ASK AI AGAIN BEFORE OPENING REVERSE POSITION
            self.print_color(f"🔍 Asking AI to confirm reverse position for {pair}...", self.Fore.BLUE)
            market_data = self.get_price_history(pair)
            
            # Get fresh AI decision after closing
            new_ai_decision = self.get_ai_trading_decision(pair, market_data, None)
            
            # Check if AI still wants to open reverse position
            if new_ai_decision["decision"] in ["LONG", "SHORT"] and new_ai_decision["position_size_usd"] > 0:
                # 🎯 Calculate correct reverse direction
                current_direction = current_trade['direction']
                if current_direction == "LONG":
                    correct_reverse_direction = "SHORT"
                else:
                    correct_reverse_direction = "LONG"
                
                self.print_color(f"✅ AI CONFIRMED: Opening {correct_reverse_direction} {pair}", self.Fore.CYAN + self.Style.BRIGHT)
                
                # Use the new AI decision but ensure correct direction
                reverse_decision = new_ai_decision.copy()
                reverse_decision["decision"] = correct_reverse_direction
                
                # Execute the reverse trade
                return self.execute_ai_trade(pair, reverse_decision)
            else:
                self.print_color(f"🔄 AI changed mind, not opening reverse position for {pair}", self.Fore.YELLOW)
                self.print_color(f"📝 AI Decision: {new_ai_decision['decision']} | Reason: {new_ai_decision['reasoning']}", self.Fore.WHITE)
                return False
        else:
            self.print_color(f"❌ Reverse position failed: Could not close current trade", self.Fore.RED)
            return False
            
    except Exception as e:
        self.print_color(f"❌ Reverse position execution failed: {e}", self.Fore.RED)
        return False

def close_trade_immediately(self, pair, trade, close_reason="AI_DECISION"):
    """Close trade immediately at market price with AI reasoning"""
    try:
        if self.binance:
            # Cancel any existing orders first
            try:
                open_orders = self.binance.futures_get_open_orders(symbol=pair)
                for order in open_orders:
                    if order['reduceOnly']:
                        self.binance.futures_cancel_order(symbol=pair, orderId=order['orderId'])
            except Exception as e:
                self.print_color(f"⚠️ Order cancel warning: {e}", self.Fore.YELLOW)
            
            # Close position with market order
            close_side = 'SELL' if trade['direction'] == 'LONG' else 'BUY'
            order = self.binance.futures_create_order(
                symbol=pair,
                side=close_side,
                type='MARKET',
                quantity=abs(trade['quantity']),
                reduceOnly=True
            )
            
            # Calculate final PnL
            current_price = self.get_current_price(pair)
            if trade['direction'] == 'LONG':
                pnl = (current_price - trade['entry_price']) * trade['quantity']
            else:
                pnl = (trade['entry_price'] - current_price) * trade['quantity']
            
            # 🆕 Update trade record with AI's actual reasoning
            trade['status'] = 'CLOSED'
            trade['exit_price'] = current_price
            trade['pnl'] = pnl
            trade['close_reason'] = close_reason  # 🆕 Use AI's actual reason
            trade['close_time'] = self.get_thailand_time()
            
            # Return budget
            self.available_budget += trade['position_size_usd'] + pnl
            
            self.add_trade_to_history(trade.copy())
            
            # 🆕 Better closing message
            pnl_color = self.Fore.GREEN if pnl > 0 else self.Fore.RED
            self.print_color(f"✅ Position closed | {pair} | P&L: ${pnl:.2f} | Reason: {close_reason}", pnl_color)
            
            # Remove from active positions after closing
            if pair in self.ai_opened_trades:
                del self.ai_opened_trades[pair]
            
            return True
        else:
            # Paper trading close
            current_price = self.get_current_price(pair)
            if trade['direction'] == 'LONG':
                pnl = (current_price - trade['entry_price']) * trade['quantity']
            else:
                pnl = (trade['entry_price'] - current_price) * trade['quantity']
            
            trade['status'] = 'CLOSED'
            trade['exit_price'] = current_price
            trade['pnl'] = pnl
            trade['close_reason'] = close_reason  # 🆕 Use AI's actual reason
            trade['close_time'] = self.get_thailand_time()
            
            self.available_budget += trade['position_size_usd'] + pnl
            self.add_trade_to_history(trade.copy())
            
            # 🆕 Better closing message
            pnl_color = self.Fore.GREEN if pnl > 0 else self.Fore.RED
            self.print_color(f"✅ Position closed | {pair} | P&L: ${pnl:.2f} | Reason: {close_reason}", pnl_color)
            
            # Remove from active positions after closing
            if pair in self.ai_opened_trades:
                del self.ai_opened_trades[pair]
            
            return True
            
    except Exception as e:
        self.print_color(f"❌ Immediate close failed: {e}", self.Fore.RED)
        return False

# Attach to class
from core import FullyAutonomous1HourAITrader

for func in [calculate_quantity, can_open_new_position, execute_ai_trade, 
             execute_reverse_position, close_trade_immediately]:
    setattr(FullyAutonomous1HourAITrader, func.__name__, func)
