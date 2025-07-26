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
import colorama
from datetime import datetime, timedelta
import numpy as np
import requests
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
            self.logger.log_error("MAIN", f"Bot error: {e}")
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.logger.main_logger.info("Stopping trading bot...")
        self.websocket_manager.stop()
        self.logger.log_session_stats()


# ========== ENTRY POINT ==========
if __name__ == '__main__':
    print("🤖 Starting Arif Signal Trading Bot...")
    print("=" * 50)
    
    # Instantiate and start the bot
    bot = TradingBot()
    bot.start()