#!/usr/bin/env python3
"""
Arif Signal Trading Bot - Internal Start Script
===============================================

This script allows running the bot from within the arif_signal directory.
It sets up the Python path correctly and starts the main application.

Usage:
    cd arif_signal
    python start.py
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point for running from arif_signal directory"""
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
        # Import and run the main app
        from main import ArifSignalApp
        app = ArifSignalApp()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure you have installed all dependencies:")
        print("   pip install requests websocket-client python-dotenv psutil")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()