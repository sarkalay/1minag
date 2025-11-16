# ai_close.py
import requests
import re
import json
import time

def get_ai_close_decision(self, pair, trade):
    """Ask AI whether to close this position based on market conditions"""
    try:
        current_price = self.get_current_price(pair)
        market_data = self.get_price_history(pair)
        current_pnl = self.calculate_current_pnl(trade, current_price)
        
        prompt = f"""
        SHOULD WE CLOSE THIS POSITION? (3MINUTE MONITORING)
        
        CURRENT ACTIVE TRADE:
        - Pair: {pair}
        - Direction: {trade['direction']}
        - Entry Price: ${trade['entry_price']:.4f}
        - Current Price: ${current_price:.4f}
        - PnL: {current_pnl:.2f}%
        - Position Size: ${trade['position_size_usd']:.2f}
        - Leverage: {trade['leverage']}x
        - Trade Age: {(time.time() - trade['entry_time']) / 60:.1f} minutes
        
        MARKET CONDITIONS:
        - 1H Change: {market_data.get('price_change', 0):.2f}%
        - Support: {market_data.get('support_levels', [])}
        - Resistance: {market_data.get('resistance_levels', [])}
        - Current Trend: {'BULLISH' if market_data.get('price_change', 0) > 0 else 'BEARISH'}
        
        Should we CLOSE this position now?
        Consider:
        - Profit/loss situation
        - Trend changes and momentum
        - Technical indicators
        - Market sentiment
        - Risk management
        - Time in trade
        
        Return JSON:
        {{
            "should_close": true/false,
            "close_reason": "TAKE_PROFIT" | "STOP_LOSS" | "TREND_REVERSAL" | "TIME_EXIT" | "MARKET_CONDITION",
            "confidence": 0-100,
            "reasoning": "Detailed technical analysis for close decision"
        }}
        """
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Fully Autonomous AI Trader"
        }
        
        data = {
            "model": "deepseek/deepseek-chat-v3.1",
            "messages": [
                {"role": "system", "content": "You are an AI trader monitoring active positions every 3 minute. Decide whether to close positions based on current market conditions, technical analysis, and risk management. Provide clear reasoning for your close decisions."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Parse AI response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                close_decision = json.loads(json_str)
                return close_decision
                
        return {"should_close": False, "close_reason": "AI_UNAVAILABLE", "confidence": 0, "reasoning": "AI analysis failed"}
        
    except Exception as e:
        self.print_color(f"❌ AI close decision error: {e}", self.Fore.RED)
        return {"should_close": False, "close_reason": "ERROR", "confidence": 0, "reasoning": f"Error: {e}"}

def monitor_positions(self):
    """Monitor positions and ask AI when to close (NO TP/SL)"""
    try:
        closed_trades = []
        for pair, trade in list(self.ai_opened_trades.items()):
            if trade['status'] != 'ACTIVE':
                continue
            
            # NEW: Ask AI whether to close this position (for positions without TP/SL)
            if not trade.get('has_tp_sl', True):
                self.print_color(f"🔍 Asking AI whether to close {pair}...", self.Fore.BLUE)
                close_decision = self.get_ai_close_decision(pair, trade)
                
                if close_decision.get("should_close", False):
                    close_reason = close_decision.get("close_reason", "AI_DECISION")
                    confidence = close_decision.get("confidence", 0)
                    reasoning = close_decision.get("reasoning", "No reason provided")
                    
                    # 🆕 Use AI's ACTUAL reasoning for closing
                    full_close_reason = f"AI_CLOSE: {close_reason} - {reasoning}"
                    
                    self.print_color(f"🎯 AI Decision: CLOSE {pair}", self.Fore.YELLOW + self.Style.BRIGHT)
                    self.print_color(f"📝 AI Reasoning: {reasoning}", self.Fore.WHITE)
                    self.print_color(f"💡 Confidence: {confidence}% | Close Reason: {close_reason}", self.Fore.CYAN)
                    
                    # 🆕 Pass AI's actual reasoning to close function
                    success = self.close_trade_immediately(pair, trade, full_close_reason)
                    if success:
                        closed_trades.append(pair)
                else:
                    # Show AI's decision to hold with reasoning
                    if close_decision.get('confidence', 0) > 0:
                        reasoning = close_decision.get('reasoning', 'No reason provided')
                        self.print_color(f"🔍 AI wants to HOLD {pair} (Confidence: {close_decision.get('confidence', 0)}%)", self.Fore.GREEN)
                        self.print_color(f"📝 Hold Reasoning: {reasoning}", self.Fore.WHITE)
                
        return closed_trades
                
    except Exception as e:
        self.print_color(f"❌ Monitoring error: {e}", self.Fore.RED)
        return []

# Attach to class
from core import FullyAutonomous1HourAITrader

for func in [get_ai_close_decision, monitor_positions]:
    setattr(FullyAutonomous1HourAITrader, func.__name__, func)
