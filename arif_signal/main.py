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
    """Main trading bot application with dual mode support"""
    def __init__(self):
        # Initialize enhanced logger first
        # This assumes TradingLogger is imported from trading_logger.py
        self.logger = TradingLogger(log_level=ConfigManager.LOG_LEVEL)
        
        # Initialize components, passing the logger instance
        # These assume the classes are imported from their respective files.
        # For example, DataManager is imported from data_ws.py
        self.data_manager = DataManager(logger=self.logger)
        self.analyzer = TechnicalAnalyzer(logger=self.logger)  # Pass logger to analyzer
        self.detector = PatternDetector(self.analyzer, logger=self.logger)  # Pass logger to detector
        self.signal_processor = SignalProcessor(
            self.analyzer, self.detector, self.logger  # Pass logger to processor
        )
        self.notification_service = NotificationService(logger=self.logger)  # Pass logger to notification service
        self.websocket_manager = WebSocketManager(
            self.data_manager, self.signal_processor, self.notification_service, logger=self.logger  # Pass logger to websocket manager
        )

    def start(self):
        """Start the trading bot with dual mode"""
        try:
            # Log bot startup using the logger with dual mode info
            self.logger.log_bot_start(
                ConfigManager.TIER1_PAIRS, 
                "DUAL MODE (15m + 1h)",
                dual_mode=True
            )
            
            # Initialize data (logging is handled within DataManager's initialize_data)
            self.data_manager.initialize_data()
            
            # Start WebSocket (logging is handled within WebSocketManager)
            # The WebSocketManager.start() method itself logs connection status
            self.websocket_manager.start()
            
            # The main thread will stay alive as long as the WebSocket thread is running
            # In a real application, you might use a more robust way to keep the main thread alive
            # or manage the lifecycle of the WebSocket thread.
            # For a simple script, a loop or just letting the WebSocket thread keep it alive is common.
            # You might add a loop here if the WebSocket thread doesn't keep the main thread alive
            # or if you need to perform other tasks in the main thread.
            # Example:
            # while self.websocket_manager.is_running:
            #     time.sleep(1)
            
        except KeyboardInterrupt:
            self.logger.main_logger.info("Bot stopped by user")  # Use logger
        except Exception as e:
            self.logger.log_error("MAIN", "Bot error: {}".format(e))  # Use logger
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
        self.logger.main_logger.info("Stopping trading bot...")  # Use logger
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

    def run(self):
        """Main application loop with mode-specific logging"""
        self.logger.log_info("MainApp", "Starting Arif Signal System", mode="SYSTEM")
        
        # Log initial mode
        self.logger.log_mode_switch("INIT", self.current_mode, "System startup")
        
        while True:
            try:
                # Check for mode switch
                new_mode = self.check_mode_switch()
                if new_mode and new_mode != self.current_mode:
                    self.logger.log_mode_switch(self.current_mode, new_mode, "Market condition change")
                    self.current_mode = new_mode
                
                # Process signals for current mode
                signals = self.process_signals_for_mode(self.current_mode)
                
                # Log mode performance
                if signals:
                    self.log_mode_performance()
                
                # Sleep based on mode
                if self.current_mode == "SCALPING":
                    time.sleep(15)  # 15 seconds for scalping
                else:
                    time.sleep(60)  # 1 minute for swing
                    
            except KeyboardInterrupt:
                self.logger.log_info("MainApp", "Shutting down gracefully", mode="SYSTEM")
                break
            except Exception as e:
                self.logger.log_error("MainApp", f"Error in main loop: {str(e)}", mode="SYSTEM")
                time.sleep(30)
    
    def check_mode_switch(self) -> str:
        """Check if mode should be switched based on market conditions"""
        try:
            # Simple market condition check (can be enhanced)
            current_hour = datetime.now().hour
            
            # Scalping mode during active hours (8 AM - 8 PM)
            if 8 <= current_hour <= 20:
                return "SCALPING"
            else:
                return "SWING"
                
        except Exception as e:
            self.logger.log_error("MainApp", f"Error checking mode switch: {str(e)}", mode="SYSTEM")
            return self.current_mode
    
    def process_signals_for_mode(self, mode: str) -> List[SignalData]:
        """Process signals for specific mode with mode-specific logging"""
        signals = []
        
        try:
            self.logger.log_info("MainApp", f"Processing signals for {mode} mode", mode=mode)
            
            for pair in self.pairs:
                try:
                    # Get candles based on mode
                    if mode == "SCALPING":
                        candles = self.data_manager.get_candles(pair, "15m", 100)
                    else:  # SWING mode
                        candles = self.data_manager.get_candles(pair, "1h", 200)
                    
                    if not candles:
                        self.logger.log_error("MainApp", f"No candles for {pair}", pair=pair, mode=mode)
                        continue
                    
                    # Process signal with mode-specific logging
                    signal = self.signal_processor.process_signal(candles, pair, mode)
                    
                    if signal:
                        signals.append(signal)
                        self.logger.log_info("MainApp", f"Signal generated for {pair}", pair=pair, mode=mode)
                    
                except Exception as e:
                    self.logger.log_error("MainApp", f"Error processing {pair}: {str(e)}", pair=pair, mode=mode)
                    continue
            
            # Log mode summary
            if signals:
                self.logger.log_info("MainApp", f"Generated {len(signals)} signals for {mode} mode", mode=mode)
            else:
                self.logger.log_info("MainApp", f"No signals generated for {mode} mode", mode=mode)
                
        except Exception as e:
            self.logger.log_error("MainApp", f"Error in process_signals_for_mode: {str(e)}", mode=mode)
        
        return signals
    
    def log_mode_performance(self):
        """Log performance statistics for current mode"""
        try:
            # Calculate basic stats (can be enhanced with actual performance tracking)
            stats = {
                'total_signals': len(self.signal_processor.daily_signal_count_scalping) if self.current_mode == "SCALPING" else len(self.signal_processor.daily_signal_count_swing),
                'win_rate': 0.65,  # Placeholder
                'avg_risk_reward': 2.1,  # Placeholder
                'total_pnl': 0.0  # Placeholder
            }
            
            self.logger.log_mode_performance(self.current_mode, stats)
            
        except Exception as e:
            self.logger.log_error("MainApp", f"Error logging mode performance: {str(e)}", mode=self.current_mode)


# ========== ENTRY POINT ==========
if __name__ == '__main__':
    print("🤖 Starting Arif Signal Trading Bot...")
    print("=" * 50)
    
    # Instantiate and start the bot
    bot = TradingBot()
    bot.start()