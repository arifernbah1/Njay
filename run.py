#!/usr/bin/env python3
"""
Arif Signal Trading Bot - Main Entry Point
==========================================

This is a signal generator bot that provides trading signals for:
- SCALPING mode (15m timeframe)
- SWING mode (1h timeframe)

Features:
- Parallel dual mode execution
- Swing pre-setup system
- Telegram notifications
- Health monitoring
- Comprehensive error handling
- Specialized trading logger

Usage:
    python run.py

Requirements:
    pip install requests websocket-client python-dotenv psutil
"""

import sys
import os

# Add the arif_signal directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'arif_signal'))

try:
    from arif_signal.main import ArifSignalApp
    
    def main():
        """Main entry point"""
        print("🚀 Starting Arif Signal Trading System...")
        print("=" * 60)
        print("📊 Signal Generator Bot")
        print("⚡ SCALPING Mode: Active (15s cycle)")
        print("📈 SWING Mode: Active (60s cycle)")
        print("🔄 Both modes running simultaneously!")
        print("🏥 Health Monitoring: Active (5min cycle)")
        print("📱 Telegram Notifications: Enabled")
        print("🛡️ Error Handling: Comprehensive")
        print("📝 Logging: Specialized Trading Logger")
        print("=" * 60)
        
        try:
            # Create and run the app
            app = ArifSignalApp()
            app.run()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Critical error: {str(e)}")
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("💡 Make sure you have installed all dependencies:")
    print("   pip install requests websocket-client python-dotenv psutil")
    print("💡 Make sure you're running from the correct directory")
    sys.exit(1)