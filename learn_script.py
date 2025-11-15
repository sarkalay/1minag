# learn_script.py - ADVANCED LEARNING WITH STOP_LOSS & LOSS ANALYSIS
import os
import json
import time
from datetime import datetime

class SelfLearningAITrader:
    def __init__(self):
        # Mistake history storage
        self.mistakes_history_file = "ai_trading_mistakes.json"
        self.mistakes_history = self.load_mistakes_history()
        
        # Advanced learning patterns with confidence
        self.learned_patterns = {}
        
        # Performance tracking
        self.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'common_mistakes': {},
            'improvement_areas': [],
            'learning_effectiveness': 0.5,
            'recent_trades': 0,
            'old_trades': 0
        }
        
        # Learning config
        self.learning_config = {
            'min_mistakes_for_blocking': 3,
            'confidence_threshold': 0.7,
            'pattern_decay_days': 30,
            'recent_mistake_weight': 2.0,
            'adaptive_learning_rate': 0.1,
            'max_blocking_percentage': 0.3
        }
        
        self.learning_effectiveness_history = []
    
    def print_color(self, text, color=""):
        print(text)
    
    def load_mistakes_history(self):
        try:
            if os.path.exists(self.mistakes_history_file):
                with open(self.mistakes_history_file, 'r') as f:
                    mistakes = json.load(f)
                cutoff_time = time.time() - (90 * 24 * 60 * 60)
                recent_mistakes = [m for m in mistakes if m.get('timestamp', 0) > cutoff_time]
                return recent_mistakes
            return []
        except Exception as e:
            print(f"Error loading mistakes: {e}")
            return []
    
    def save_mistakes_history(self):
        try:
            with open(self.mistakes_history_file, 'w') as f:
                json.dump(self.mistakes_history, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    # ========================================
    # 1. CORE: ANALYZE WHY A TRADE LOST
    # ========================================
    def analyze_trade_mistake(self, trade_data):
        """Analyze losing trade and extract lesson + avoidance strategy"""
        try:
            pnl = trade_data.get("pnl", 0)
            if pnl >= 0:
                return None  # No mistake if profitable
            
            direction = trade_data["direction"]
            entry_price = trade_data["entry_price"]
            exit_price = trade_data["exit_price"]
            close_reason = trade_data.get("close_reason", "")
            pair = trade_data["pair"]
            leverage = trade_data.get("leverage", 1)
            ai_reasoning = trade_data.get("ai_reasoning", "").lower()

            # === MISTAKE TYPE DETECTION ===
            mistake_type = "Unknown loss"
            lesson = "Review entry conditions"
            avoidance = "Require stronger confirmation"

            # 1. STOP_LOSS HIT
            if "STOP_LOSS" in close_reason:
                if direction == "LONG":
                    mistake_type = "LONG stopped out"
                    lesson = f"Avoid LONG when price is near resistance or in downtrend"
                    avoidance = "Wait for 4H/1D bullish confirmation or breakout above resistance"
                else:  # SHORT
                    mistake_type = "SHORT stopped out"
                    lesson = f"Avoid SHORT when price is near support or in uptrend"
                    avoidance = "Wait for 4H/1D bearish confirmation or breakdown below support"

            # 2. WRONG DIRECTION (NO STOP_LOSS)
            elif direction == "LONG" and exit_price < entry_price:
                mistake_type = "LONG closed in loss"
                lesson = "Avoid LONG in bearish higher timeframe"
                avoidance = "Require 4H/1D uptrend + volume before LONG"
            elif direction == "SHORT" and exit_price > entry_price:
                mistake_type = "SHORT closed in loss"
                lesson = "Avoid SHORT in bullish higher timeframe"
                avoidance = "Require 4H/1D downtrend + volume before SHORT"

            # 3. HIGH LEVERAGE MISTAKE
            if leverage >= 8 and abs(pnl) > 3:
                mistake_type += f" (High leverage {leverage}x)"
                lesson += " | High leverage increases risk"
                avoidance += " | Use max 5x in volatile conditions"

            # 4. FALLBACK REASONING (AI WAS UNSURE)
            if "fallback" in ai_reasoning:
                mistake_type += " (Fallback decision)"
                lesson += " | AI was uncertain"
                avoidance += " | Skip trade if confidence < 70%"

            return {
                "mistake_type": mistake_type.strip(),
                "lesson_learned": lesson.strip(),
                "avoidance_strategy": avoidance.strip(),
                "trade_data": trade_data,
                "pnl": pnl
            }

        except Exception as e:
            print(f"Analysis error: {e}")
            return None

    # ========================================
    # 2. LEARN FROM MISTAKE
    # ========================================
    def learn_from_mistake(self, trade_data):
        try:
            mistake_analysis = self.analyze_trade_mistake(trade_data)
            if not mistake_analysis:
                return

            mistake_analysis['timestamp'] = time.time()
            mistake_analysis['learning_effectiveness'] = self.performance_stats.get('learning_effectiveness', 0.5)

            self.mistakes_history.append(mistake_analysis)
            self.performance_stats['losing_trades'] += 1
            mtype = mistake_analysis['mistake_type']
            self.performance_stats['common_mistakes'][mtype] = self.performance_stats['common_mistakes'].get(mtype, 0) + 1

            self.save_mistakes_history()
            self.update_learned_patterns(mistake_analysis)

            self.measure_learning_effectiveness()
            self.adaptive_learning_adjustment()

            self.print_color(f"AI LEARNING: {mistake_analysis['lesson_learned']}", "YELLOW")
            self.print_color(f"AVOIDANCE: {mistake_analysis['avoidance_strategy']}", "CYAN")
            self.print_color(f"Learning Effectiveness: {(self.performance_stats.get('learning_effectiveness', 0.5)*100):.1f}%", "MAGENTA")

        except Exception as e:
            print(f"Learning error: {e}")

    # ========================================
    # 3. UPDATE LEARNED PATTERNS
    # ========================================
    def update_learned_patterns(self, mistake_analysis):
        try:
            mtype = mistake_analysis['mistake_type']
            trade = mistake_analysis['trade_data']

            if mtype not in self.learned_patterns:
                self.learned_patterns[mtype] = {
                    'occurrences': 0,
                    'total_loss': 0,
                    'avoidance_strategies': [],
                    'last_occurrence': None,
                    'pairs_affected': set(),
                    'avg_leverage': 0,
                    'first_occurrence': time.time(),
                    'confidence_history': []
                }

            p = self.learned_patterns[mtype]
            p['occurrences'] += 1
            p['total_loss'] += abs(trade.get('pnl', 0))
            p['last_occurrence'] = time.time()
            p['pairs_affected'].add(trade.get('pair'))

            # Update avg leverage
            lev = trade.get('leverage', 1)
            if p['occurrences'] == 1:
                p['avg_leverage'] = lev
            else:
                p['avg_leverage'] = (p['avg_leverage'] * (p['occurrences'] - 1) + lev) / p['occurrences']

            strategy = mistake_analysis['avoidance_strategy']
            if strategy not in p['avoidance_strategies']:
                p['avoidance_strategies'].append(strategy)

            conf = self.calculate_pattern_confidence(mtype)
            p['confidence_history'].append({
                'timestamp': time.time(),
                'confidence': conf,
                'occurrences': p['occurrences']
            })

        except Exception as e:
            print(f"Pattern update error: {e}")

    # ========================================
    # 4. CALCULATE CONFIDENCE
    # ========================================
    def calculate_pattern_confidence(self, mistake_type):
        try:
            if mistake_type not in self.learned_patterns:
                return 0.0
            p = self.learned_patterns[mistake_type]
            occ = p['occurrences']
            total = max(1, self.performance_stats['total_trades'])

            base = min(occ / self.learning_config['min_mistakes_for_blocking'], 1.0)
            days_ago = (time.time() - p['last_occurrence']) / 86400
            decay = max(0, 1 - days_ago / self.learning_config['pattern_decay_days'])
            base *= decay

            eff = self.performance_stats.get('learning_effectiveness', 0.5)
            final = base * (0.5 + eff * 0.5)
            return min(final, 1.0)
        except:
            return 0.0

    # ========================================
    # 5. SHOULD AVOID TRADE?
    # ========================================
    def should_avoid_trade(self, ai_decision, market_data):
        try:
            if not self.mistakes_history:
                return False

            total_blocked = len([m for m in self.mistakes_history if m.get('was_blocked', False)])
            rate = total_blocked / max(1, self.performance_stats['total_trades'])
            if rate > self.learning_config['max_blocking_percentage']:
                return False

            decision = ai_decision["decision"]
            reasoning = ai_decision["reasoning"].lower()
            leverage = ai_decision.get("leverage", 1)

            for mtype, data in self.learned_patterns.items():
                conf = self.calculate_pattern_confidence(mtype)
                if conf >= self.learning_config['confidence_threshold']:
                    if self.matches_mistake_pattern(ai_decision, market_data, mtype):
                        self.print_color(f"LEARNING: Blocking '{mtype}' (Confidence: {conf:.1%})", "RED")
                        self.track_blocking_decision(mtype, ai_decision, market_data)
                        return True
            return False
        except:
            return False

    def matches_mistake_pattern(self, ai_decision, market_data, mistake_type):
        """Check if current trade matches a known mistake pattern"""
        try:
            direction = ai_decision["decision"]
            reasoning = ai_decision["reasoning"].lower()
            leverage = ai_decision.get("leverage", 1)

            if "stopped out" in mistake_type:
                if "LONG" in mistake_type and direction == "LONG":
                    return True
                if "SHORT" in mistake_type and direction == "SHORT":
                    return True
            if leverage >= 8 and "high leverage" in mistake_type.lower():
                return True
            if "fallback" in mistake_type.lower() and "fallback" in reasoning:
                return True
            return False
        except:
            return False

    def track_blocking_decision(self, mistake_type, ai_decision, market_data):
        record = {
            'timestamp': time.time(),
            'mistake_type': mistake_type,
            'ai_decision': ai_decision,
            'market_data': market_data,
            'was_blocked': True
        }
        self.mistakes_history.append(record)
        self.save_mistakes_history()

    # ========================================
    # 6. MEASURE & ADJUST LEARNING
    # ========================================
    def measure_learning_effectiveness(self):
        try:
            if len(self.mistakes_history) < 10:
                self.performance_stats['learning_effectiveness'] = 0.5
                return 0.5

            recent_cutoff = time.time() - (30 * 24 * 60 * 60)
            old_cutoff = time.time() - (60 * 24 * 60 * 60)

            recent_mistakes = [m for m in self.mistakes_history if m.get('timestamp', 0) > recent_cutoff]
            old_mistakes = [m for m in self.mistakes_history if old_cutoff < m.get('timestamp', 0) <= recent_cutoff]

            recent_rate = len(recent_mistakes) / max(1, getattr(self, 'recent_trades', 1))
            old_rate = len(old_mistakes) / max(1, getattr(self, 'old_trades', 1))

            effectiveness = max(0, 1 - (recent_rate / max(old_rate, 0.1)))
            self.performance_stats['learning_effectiveness'] = effectiveness
            return effectiveness
        except:
            return 0.5

    def adaptive_learning_adjustment(self):
        try:
            eff = self.performance_stats.get('learning_effectiveness', 0.5)
            if eff > 0.7:
                self.learning_config['confidence_threshold'] = max(0.5, self.learning_config['confidence_threshold'] - 0.05)
            elif eff < 0.3:
                self.learning_config['confidence_threshold'] = min(0.9, self.learning_config['confidence_threshold'] + 0.05)

            total = self.performance_stats['total_trades']
            if total > 100:
                self.learning_config['min_mistakes_for_blocking'] = max(2, 3 - (total // 100))

            self.print_color(f"LEARNING ADJUSTED: Threshold={self.learning_config['confidence_threshold']:.2f}, Eff={eff:.1%}", "MAGENTA")
        except:
            pass

    # ========================================
    # 7. GET LEARNING PROMPT
    # ========================================
    def get_learning_enhanced_prompt(self, pair, market_data):
        try:
            if not self.mistakes_history:
                return "No learning data yet."

            section = "\nSMART LEARNING INSIGHTS:\n"
            high_conf = []
            for mtype, data in self.learned_patterns.items():
                conf = self.calculate_pattern_confidence(mtype)
                if conf > 0.6:
                    high_conf.append((mtype, conf))
            if high_conf:
                section += "HIGH CONFIDENCE WARNINGS:\n"
                for m, c in sorted(high_conf, key=lambda x: x[1], reverse=True)[:3]:
                    section += f"- {m} ({c:.0%})\n"

            recent = self.mistakes_history[-2:]
            if recent:
                section += "\nRECENT LESSONS:\n"
                for m in recent:
                    if 'lesson_learned' in m:
                        section += f"- {m['lesson_learned']}\n"

            eff = self.performance_stats.get('learning_effectiveness', 0.5)
            section += f"\nLEARNING EFFECTIVENESS: {eff:.0%} "
            section += "Excellent" if eff > 0.7 else "Good" if eff > 0.5 else "Needs Work"
            section += f"\nTotal Mistakes Learned: {len(self.mistakes_history)}"
            return section
        except:
            return "Learning in progress..."

    # ========================================
    # 8. SHOW PROGRESS - ALWAYS SHOW, EVEN IF NO MISTAKES
    # ========================================
    def show_advanced_learning_progress(self):
        try:
            total_mistakes = len(self.mistakes_history)
            total_trades = self.performance_stats.get('total_trades', 0)
            win_rate = (self.performance_stats.get('winning_trades', 0) / max(1, total_trades)) * 100
            eff = self.performance_stats.get('learning_effectiveness', 0.5)

            self.print_color(f"\nADVANCED LEARNING REPORT", "CYAN")
            self.print_color("=" * 70, "CYAN")

            # ALWAYS SHOW BASIC STATS
            self.print_color(f"Total Trades: {total_trades}", "WHITE")
            self.print_color(f"Win Rate: {win_rate:.1f}%", "GREEN" if win_rate > 60 else "YELLOW")
            self.print_color(f"Total Mistakes Learned: {total_mistakes}", "WHITE")

            # IF NO MISTAKES YET → SHOW OBSERVATION MODE
            if total_mistakes == 0:
                self.print_color("LEARNING: No mistakes yet. AI is in observation mode.", "GRAY")
                self.print_color("Waiting for first loss to begin learning...", "YELLOW")
                self.print_color(f"Current Effectiveness: {eff:.0%} (Neutral)", "WHITE")
            else:
                # FULL REPORT
                self.print_color(f"Learning Effectiveness: {eff:.1%}", "GREEN" if eff > 0.6 else "YELLOW")
                self.print_color(f"Confidence Threshold: {self.learning_config['confidence_threshold']:.2f}", "WHITE")
                self.print_color(f"Active Patterns: {len(self.learned_patterns)}", "WHITE")

                # HIGH CONFIDENCE PATTERNS
                high_conf = [(p, self.calculate_pattern_confidence(p), d['occurrences'])
                            for p, d in self.learned_patterns.items() if self.calculate_pattern_confidence(p) > 0.5]
                if high_conf:
                    self.print_color(f"\nHIGH-CONFIDENCE PATTERNS:", "YELLOW")
                    for p, c, o in sorted(high_conf, key=lambda x: x[1], reverse=True)[:5]:
                        self.print_color(f"  {p}: {c:.0%} ({o} times)", "WHITE")
                else:
                    self.print_color(f"\nNo high-confidence patterns yet.", "GRAY")

                # BLOCKING STATS
                blocked = len([m for m in self.mistakes_history if m.get('was_blocked')])
                block_rate = (blocked / max(1, total_trades)) * 100
                self.print_color(f"\nBLOCKING: {block_rate:.1f}% of trades blocked", "MAGENTA")

        except Exception as e:
            print(f"Progress error: {e}")
