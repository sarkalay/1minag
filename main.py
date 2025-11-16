# main.py
import os
import sys
import time

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# main.py မှာ ဒီလိုထည့်ပါ
def main():
    try:
        # Import all modules
        import core
        import indicators
        import ai_entry
        import ai_close
        import trade_execution
        import trading_loop
        
        # Check if learning is available
        try:
            from learn_script import SelfLearningAITrader
            LEARN_SCRIPT_AVAILABLE = True
            print("✅ Learning module loaded successfully!")
        except ImportError as e:
            LEARN_SCRIPT_AVAILABLE = False
            print(f"❌ Learning module not available: {e}")
        
        # Create bot
        from core import FullyAutonomous1HourAITrader
        bot = FullyAutonomous1HourAITrader()
        
        # Ask user for mode selection
        print("\n" + "="*70)
        print("🤖 FULLY AUTONOMOUS 1-HOUR AI TRADER")
        print("="*70)
        print("1. 🎯 REAL TRADING (Live Binance Account)")
        print("2. 📝 PAPER TRADING (Virtual Simulation)")
        print("3. ❌ EXIT")
        
        choice = input("\nSelect mode (1-3): ").strip()
        
        if choice == "1":
            if bot.binance:
                print(f"\n🚀 STARTING REAL TRADING...")
                
                # Import and start real trading
                from trading_loop import start_real_trading
                start_real_trading(bot)
            else:
                print(f"\n❌ Binance connection failed. Switching to paper trading...")
                from paper_trading import FullyAutonomous1HourPaperTrader
                paper_bot = FullyAutonomous1HourPaperTrader(bot)
                paper_bot.start_paper_trading()
                
        elif choice == "2":
            print(f"\n📝 STARTING PAPER TRADING...")
            from paper_trading import FullyAutonomous1HourPaperTrader
            paper_bot = FullyAutonomous1HourPaperTrader(bot)
            paper_bot.start_paper_trading()
            
        elif choice == "3":
            print(f"\n👋 Exiting...")
            
        else:
            print(f"\n❌ Invalid choice. Exiting...")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Program stopped by user")
    except Exception as e:
        print(f"\n❌ Main execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
