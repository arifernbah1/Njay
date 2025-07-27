# main.py

# --- Import classes from other files ---
from trading_logger import TradingLogger
from models import CandleData, TradingConfig, SignalData, SignalType
from utils import TimeUtils
from analysis import TechnicalAnalyzer, PatternDetector
from processor import SignalProcessor
from notifications import NotificationService
from data_ws import DataManager, WebSocketManager
from config import ConfigManager

import logging
import sys
import threading
import time
from collections import defaultdict, deque
try:
    import colorama
except ImportError:
    colorama = None

from datetime import datetime, timedelta

try:
    import numpy as np
except ImportError:
    print("❌ numpy is required. Please install: pip install numpy")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests is required. Please install: pip install requests")
    sys.exit(1)

import json
import ssl
from typing import List, Optional, Tuple
from pathlib import Path

# ========== MAIN APPLICATION ==========
class TradingBot:
    """Main trading bot application"""

    def __init__(self):
        # Validate configuration first
        if not ConfigManager.validate_config():
            print("❌ Configuration validation failed. Please check your .env file.")
            sys.exit(1)

        # Print current configuration
        ConfigManager.print_config()

        # Initialize enhanced logger first
        self.logger = TradingLogger(log_level=ConfigManager.LOG_LEVEL)

        # Initialize components, passing the logger instance
        self.data_manager = DataManager(logger=self.logger)
        self.analyzer = TechnicalAnalyzer(logger=self.logger)
        self.detector = PatternDetector(self.analyzer, logger=self.logger)
        self.signal_processor = SignalProcessor(
            self.analyzer,
            self.detector,
            self.logger
        )
        self.notification_service = NotificationService(logger=self.logger)
        self.websocket_manager = WebSocketManager(
            self.data_manager,
            self.signal_processor,
            self.notification_service,
            logger=self.logger
        )

    def start(self):
        """Start the trading bot"""
        try:
            # Log bot startup using the logger
            self.logger.log_bot_start(
                ConfigManager.TIER1_PAIRS,
                ConfigManager.TIMEFRAME
            )

            # Send Telegram notification for bot start
            self._send_start_notification()

            # Initialize data
            self.data_manager.initialize_data()

            # Start WebSocket
            self.websocket_manager.start()

            # Keep main thread alive
            while self.websocket_manager.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.main_logger.info("Bot stopped by user")
            self.stop()
        except Exception as e:
            self.logger.log_error("MAIN", "Bot error: {}".format(e))
            self.stop()

    def _send_start_notification(self):
        """Send Telegram notification when bot starts"""
        try:
            # Create start message
            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')
            session = TimeUtils.get_trading_session()
            
            message = """
🤖 <b>ARIF SIGNAL BOT - STARTED</b>

✅ <b>Status:</b> Bot successfully started
🕐 <b>Start Time:</b> {}
📊 <b>Timeframe:</b> {}
🕐 <b>Session:</b> {}

💎 <b>Trading Pairs ({}):</b>
{}

💰 <b>Configuration:</b>
• Min Volume: ${:,}
• Cooldown: {} minutes
• Max Daily Signals: 1-2 per pair

🎯 <b>Strategy:</b> Conservative Development Mode
📱 <b>Notifications:</b> Active
🔗 <b>WebSocket:</b> Connecting...

<i>Bot is now monitoring for high-quality trading signals...</i>
            """.format(
                start_time, ConfigManager.TIMEFRAME, session,
                len(ConfigManager.TIER1_PAIRS), ', '.join(ConfigManager.TIER1_PAIRS),
                ConfigManager.MIN_VOLUME_USDT, ConfigManager.SIGNAL_COOLDOWN_MINUTES
            ).strip()

            # Send notification
            success = self.notification_service._send_telegram(message, "BOT_START")
            
            if success:
                self.logger.main_logger.info("✅ Start notification sent to Telegram")
            else:
                self.logger.main_logger.warning("⚠️ Failed to send start notification to Telegram")
                
        except Exception as e:
            self.logger.log_error("MAIN", "Error sending start notification: {}".format(e))

    def stop(self):
        """Stop the trading bot"""
        self.logger.main_logger.info("Stopping trading bot...")
        
        # Send stop notification
        self._send_stop_notification()
        
        self.websocket_manager.stop()
        self.logger.log_session_stats()

    def _send_stop_notification(self):
        """Send Telegram notification when bot stops"""
        try:
            stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')
            
            message = """
🛑 <b>ARIF SIGNAL BOT - STOPPED</b>

❌ <b>Status:</b> Bot stopped
🕐 <b>Stop Time:</b> {}

📊 <b>Session Summary:</b>
• Check logs for detailed statistics
• Review signal performance
• Restart when ready

<i>Bot has been safely stopped.</i>
            """.format(stop_time).strip()

            # Send notification
            success = self.notification_service._send_telegram(message, "BOT_STOP")
            
            if success:
                self.logger.main_logger.info("✅ Stop notification sent to Telegram")
            else:
                self.logger.main_logger.warning("⚠️ Failed to send stop notification to Telegram")
                
        except Exception as e:
            self.logger.log_error("MAIN", "Error sending stop notification: {}".format(e))


# ========== ENTRY POINT ==========
if __name__ == '__main__':
    print("🤖 Starting Arif Signal Trading Bot...")
    print("=" * 50)
    
    # Instantiate and start the bot
    bot = TradingBot()
    bot.start()