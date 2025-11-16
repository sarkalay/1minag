# ai_entry.py
import time
import re
import json
import requests

def get_ai_trading_decision(self, pair, market_data, current_trade=None):
    """AI makes COMPLETE trading decisions including REVERSE positions"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            if not self.openrouter_key:
                self.print_color("❌ OpenRouter API key missing!", self.Fore.RED)
                return self.get_improved_fallback_decision(pair, market_data)

            current_price = market_data.get('current_price', 0)
            mtf = market_data.get('mtf_analysis', {})

            # === MULTI-TIMEFRAME TEXT SUMMARY ===
            mtf_text = "MULTI-TIMEFRAME ANALYSIS:\n"
            for tf in ['5m', '15m', '1h', '4h', '1d']:
                if tf in mtf:
                    d = mtf[tf]
                    mtf_text += f"- {tf.upper()}: {d.get('trend', 'N/A')} | "
                    if 'crossover' in d:
                        mtf_text += f"Signal: {d['crossover']} | "
                    if 'rsi' in d:
                        mtf_text += f"RSI: {d['rsi']} | "
                    if 'vol_spike' in d:
                        mtf_text += f"Vol: {'SPIKE' if d['vol_spike'] else 'Normal'} | "
                    if 'support' in d and 'resistance' in d:
                        mtf_text += f"S/R: {d['support']:.4f}/{d['resistance']:.4f}"
                    mtf_text += "\n"

            # === TREND ALIGNMENT ===
            h1_trend = mtf.get('1h', {}).get('trend')
            h4_trend = mtf.get('4h', {}).get('trend')
            alignment = "STRONG" if h1_trend == h4_trend and h1_trend else "WEAK"

            # === REVERSE ANALYSIS ===
            reverse_analysis = ""
            if current_trade and self.allow_reverse_positions:
                pnl = self.calculate_current_pnl(current_trade, current_price)
                reverse_analysis = f"""
                EXISTING POSITION:
                - Direction: {current_trade['direction']}
                - Entry: ${current_trade['entry_price']:.4f}
                - PnL: {pnl:.2f}%
                - REVERSE if trend flipped?
                """

            # === LEARNING CONTEXT ===
            learning_context = ""
            try:
                from learn_script import SelfLearningAITrader
                if hasattr(self, 'get_learning_enhanced_prompt'):
                    learning_context = self.get_learning_enhanced_prompt(pair, market_data)
            except:
                pass

            # === FINAL PROMPT ===
            prompt = f"""
YOU ARE A PROFESSIONAL AI TRADER. Budget: ${self.available_budget:.2f}

{mtf_text}
TREND ALIGNMENT: {alignment}

1H TRADING PAIR: {pair}
Current Price: ${current_price:.6f}
{reverse_analysis}
{learning_context}

RULES:
- Only trade if 1H and 4H trend align
- Confirm entry with 15m crossover + volume spike
- RSI < 30 = oversold, > 70 = overbought
- Position size: 5-10% of budget ($50 min)
- Leverage: 5-10x based on volatility
- NO TP/SL - you will close manually

REVERSE POSITION STRATEGY (CRITICAL):
- Use "REVERSE_LONG"  → Close current SHORT + Open LONG immediately
- Use "REVERSE_SHORT" → Close current LONG  + Open SHORT immediately
- REVERSE only if ALL conditions met:
  1. Current PnL ≤ -2%
  2. 1H and 4H trend flipped (opposite to current position)
  3. 15m shows crossover in new direction
  4. Volume spike confirms momentum

Return JSON:
{{
    "decision": "LONG" | "SHORT" | "HOLD" | "REVERSE_LONG" | "REVERSE_SHORT",
    "position_size_usd": number,
    "entry_price": number,
    "leverage": number,
    "confidence": 0-100,
    "reasoning": "MTF alignment + signal + risk"
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
                    {"role": "system", "content": "You are a fully autonomous AI trader with reverse position capability. You manually close positions based on market conditions - no TP/SL orders are set. Analyze when to enter AND when to exit based on technical analysis. Monitor every 3 minute."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 800
            }
            
            self.print_color(f"🧠 DeepSeek Analyzing {pair} with 3MIN monitoring...", self.Fore.MAGENTA + self.Style.BRIGHT)
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                return self.parse_ai_trading_decision(ai_response, pair, current_price, current_trade)
            else:
                self.print_color(f"⚠️ DeepSeek API attempt {attempt+1} failed: {response.status_code}", self.Fore.YELLOW)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                    
        except requests.exceptions.Timeout:
            self.print_color(f"⏰ DeepSeek timeout attempt {attempt+1}", self.Fore.YELLOW)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
                
        except Exception as e:
            self.print_color(f"❌ DeepSeek error attempt {attempt+1}: {e}", self.Fore.RED)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
    
    # All retries failed - use improved fallback
    self.print_color("🚨 All AI attempts failed, using improved fallback", self.Fore.RED)
    return self.get_improved_fallback_decision(pair, market_data)

def get_improved_fallback_decision(self, pair, market_data):
    """Better fallback that analyzes market conditions"""
    current_price = market_data['current_price']
    mtf = market_data.get('mtf_analysis', {})
    
    # Analyze multiple timeframes
    h1_data = mtf.get('1h', {})
    h4_data = mtf.get('4h', {})
    m15_data = mtf.get('15m', {})
    
    # Technical analysis based fallback
    bullish_signals = 0
    bearish_signals = 0
    
    # Check 1H trend
    if h1_data.get('trend') == 'BULLISH':
        bullish_signals += 1
    elif h1_data.get('trend') == 'BEARISH':
        bearish_signals += 1
    
    # Check 4H trend  
    if h4_data.get('trend') == 'BULLISH':
        bullish_signals += 1
    elif h4_data.get('trend') == 'BEARISH':
        bearish_signals += 1
    
    # Check RSI
    h1_rsi = h1_data.get('rsi', 50)
    if h1_rsi < 35:  # Oversold
        bullish_signals += 1
    elif h1_rsi > 65:  # Overbought
        bearish_signals += 1
    
    # Check crossover
    if m15_data.get('crossover') == 'GOLDEN':
        bullish_signals += 1
    elif m15_data.get('crossover') == 'DEATH':
        bearish_signals += 1
    
    # Make decision
    if bullish_signals >= 3 and bearish_signals <= 1:
        return {
            "decision": "LONG",
            "position_size_usd": 20,  # Smaller size for fallback
            "entry_price": current_price,
            "leverage": 5,
            "confidence": 60,
            "reasoning": f"Fallback: Bullish signals ({bullish_signals}/{bearish_signals}) - Trend + RSI + Crossover",
            "should_reverse": False
        }
    elif bearish_signals >= 3 and bullish_signals <= 1:
        return {
            "decision": "SHORT", 
            "position_size_usd": 20,
            "entry_price": current_price,
            "leverage": 5,
            "confidence": 60,
            "reasoning": f"Fallback: Bearish signals ({bearish_signals}/{bullish_signals}) - Trend + RSI + Crossover",
            "should_reverse": False
        }
    else:
        return {
            "decision": "HOLD",
            "position_size_usd": 0,
            "entry_price": current_price,
            "leverage": 5,
            "confidence": 40,
            "reasoning": f"Fallback: Mixed signals ({bullish_signals}/{bearish_signals}) - Waiting for clear direction",
            "should_reverse": False
        }

def parse_ai_trading_decision(self, ai_response, pair, current_price, current_trade=None):
    """Parse AI's trading decision including REVERSE positions"""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            decision_data = json.loads(json_str)
            
            decision = decision_data.get('decision', 'HOLD').upper()
            position_size_usd = float(decision_data.get('position_size_usd', 0))
            entry_price = float(decision_data.get('entry_price', 0))
            leverage = int(decision_data.get('leverage', 5))
            confidence = float(decision_data.get('confidence', 50))
            reasoning = decision_data.get('reasoning', 'AI Analysis')
            
            # Validate leverage
            if leverage < 5:
                leverage = 5
            elif leverage > 10:
                leverage = 10
                
            if entry_price <= 0:
                entry_price = current_price
                
            return {
                "decision": decision,
                "position_size_usd": position_size_usd,
                "entry_price": entry_price,
                "leverage": leverage,
                "confidence": confidence,
                "reasoning": reasoning,
                "should_reverse": decision.startswith('REVERSE_')
            }
        return self.get_improved_fallback_decision(pair, {'current_price': current_price})
    except Exception as e:
        self.print_color(f"❌ DeepSeek response parsing failed: {e}", self.Fore.RED)
        return self.get_improved_fallback_decision(pair, {'current_price': current_price})

def calculate_current_pnl(self, trade, current_price):
    """Calculate current PnL percentage"""
    try:
        if trade['direction'] == 'LONG':
            pnl_percent = ((current_price - trade['entry_price']) / trade['entry_price']) * 100 * trade['leverage']
        else:
            pnl_percent = ((trade['entry_price'] - current_price) / trade['entry_price']) * 100 * trade['leverage']
        return pnl_percent
    except:
        return 0

def get_ai_decision_with_learning(self, pair, market_data):
    """Get AI decision enhanced with learned lessons"""
    # First get normal AI decision
    ai_decision = self.get_ai_trading_decision(pair, market_data)
    
    # Check if this matches known mistake patterns
    try:
        from learn_script import SelfLearningAITrader
        if hasattr(self, 'should_avoid_trade') and self.should_avoid_trade(ai_decision, market_data):
            self.print_color(f"🧠 AI USING LEARNING: Blocking potential mistake for {pair}", self.Fore.YELLOW)
            return {
                "decision": "HOLD",
                "position_size_usd": 0,
                "entry_price": market_data['current_price'],
                "leverage": 5,
                "confidence": 0,
                "reasoning": f"Blocked - matches known error pattern",
                "should_reverse": False
            }
    except:
        pass
    
    # Add learning context to reasoning
    if ai_decision["decision"] != "HOLD" and hasattr(self, 'mistakes_history'):
        learning_context = f" | Applying lessons from {len(self.mistakes_history)} past mistakes"
        ai_decision["reasoning"] += learning_context
    
    return ai_decision

# Attach to class
from core import FullyAutonomous1HourAITrader

for func in [get_ai_trading_decision, parse_ai_trading_decision, get_improved_fallback_decision, 
             calculate_current_pnl, get_ai_decision_with_learning]:
    setattr(FullyAutonomous1HourAITrader, func.__name__, func)
