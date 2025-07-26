# trading_logger.py

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path
import colorama # Import colorama for potential color support

# Initialize colorama
colorama.init()

# Custom Formatter for basic coloring
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT,
        'INFO': colorama.Fore.GREEN,
        'DEBUG': colorama.Fore.BLUE,
        'RESET': colorama.Style.RESET_ALL
    }

    def format(self, record):
        log_level = record.levelname
        color = self.COLORS.get(log_level, self.COLORS['RESET'])
        # Use a consistent base formatter for structure
        base_formatter = logging.Formatter('%(asctime)s | %(levelname)8s | %(name)15s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        formatted_message = base_formatter.format(record)
        return f"{color}{formatted_message}{self.COLORS['RESET']}"


# ========== ENHANCED LOGGER SETUP ==========
class TradingLogger:
    """Enhanced logger for trading bot with detailed process tracking"""

    def __init__(self, log_level: str = "INFO"):
        self.setup_logger(log_level)
        self.session_stats = {
            'signals_generated': 0,
            'signals_filtered': 0,
            'patterns_detected': 0,
            'websocket_messages': 0,
            'errors': 0
        }

    def setup_logger(self, log_level: str):
        """Setup enhanced logger with file and console output"""

        # Remove existing handlers to prevent duplicates if run multiple times
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Create logs directory
        Path("logs").mkdir(exist_ok=True)

        # Create handlers
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(ColoredFormatter()) # Use the custom colored formatter

        file_handler_daily = logging.FileHandler(
            f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler_daily.setLevel(getattr(logging, log_level.upper()))
        # Use basic formatter for file logs (no colors)
        file_handler_daily.setFormatter(logging.Formatter('%(asctime)s | %(levelname)8s | %(name)15s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))


        file_handler_signals = logging.FileHandler(
            f"logs/signals_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler_signals.setLevel(logging.INFO) # Signals usually INFO level
         # Use basic formatter for file logs (no colors)
        file_handler_signals.setFormatter(logging.Formatter('%(asctime)s | %(levelname)8s | %(name)15s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))


        # Add handlers to root logger
        logging.root.addHandler(console_handler)
        logging.root.addHandler(file_handler_daily)
        logging.root.addHandler(file_handler_signals)

        # Set root logger level
        logging.root.setLevel(getattr(logging, log_level.upper()))


        # Create specialized loggers
        self.main_logger = logging.getLogger("MAIN")
        self.data_logger = logging.getLogger("DATA")
        self.signal_logger = logging.getLogger("SIGNAL")
        self.websocket_logger = logging.getLogger("WEBSOCKET")
        self.pattern_logger = logging.getLogger("PATTERN")
        self.telegram_logger = logging.getLogger("TELEGRAM")


    def log_bot_start(self, pairs: List[str], timeframe: str):
        self.main_logger.info("=" * 80)
        self.main_logger.info("🚀 ENHANCED TRADING BOT - STARTING")
        self.main_logger.info("=" * 80)
        self.main_logger.info(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
        self.main_logger.info(f"⏰ Timeframe: {timeframe}")
        self.main_logger.info(f"💎 Pairs: {', '.join(pairs)}")
        self.main_logger.info(f"🕐 Session: {self.get_trading_session()}")
        self.main_logger.info("-" * 80)

    def log_data_initialization(self, pair: str, candles_loaded: int):
        self.data_logger.info(f"📊 {pair}: Loading historical data...")
        self.data_logger.info(f"✅ {pair}: {candles_loaded} candles loaded successfully")

    def log_websocket_connection(self, status: str, streams_count: int = 0):
        if status == "CONNECTED":
            self.websocket_logger.info("🔗 WebSocket connected successfully")
            if streams_count > 0:
                self.websocket_logger.info(f"📡 Subscribed to {streams_count} data streams")
        elif status == "DISCONNECTED":
            self.websocket_logger.warning("❌ WebSocket disconnected")
        elif status == "RECONNECTING":
            self.websocket_logger.info("🔄 Attempting to reconnect WebSocket...")
        elif status == "ERROR":
            self.websocket_logger.error("💥 WebSocket connection error")

    def log_candle_received(self, pair: str, candle_data: dict):
        self.websocket_logger.debug(
            f"📈 {pair}: New candle - "
            f"O:{candle_data.get('o', 'N/A'):.4f} H:{candle_data.get('h', 'N/A'):.4f} "
            f"L:{candle_data.get('l', 'N/A'):.4f} C:{candle_data.get('c', 'N/A'):.4f} "
            f"V:{candle_data.get('v', 'N/A'):.0f}"
        )
        self.session_stats['websocket_messages'] += 1

    def log_signal_analysis_start(self, pair: str, entry_price: float):
        self.signal_logger.info(f"🔍 {pair}: Starting signal analysis at ${entry_price:.4f}")

    def log_filter_result(self, pair: str, filter_name: str, result: bool, details: str = ""):
        status = "✅ PASS" if result else "❌ FAIL"
        detail_msg = f" ({details})" if details else ""
        self.signal_logger.debug(f"   🧪 {pair}: {filter_name} - {status}{detail_msg}")

    def log_pattern_detection(self, pair: str, pattern_type: str, detected: bool, details: dict = None):
        if detected:
            self.pattern_logger.info(f"🎯 {pair}: {pattern_type} pattern DETECTED!")
            if details:
                for key, value in details.items():
                    self.pattern_logger.info(f"   📊 {key}: {value}")
            self.session_stats['patterns_detected'] += 1
        else:
            self.pattern_logger.debug(f"   🔍 {pair}: {pattern_type} pattern not found")

    def log_technical_analysis(self, pair: str, indicators: dict):
        self.signal_logger.info(f"📊 {pair}: Technical Analysis:")
        for indicator, value in indicators.items():
            if isinstance(value, float):
                self.signal_logger.info(f"   📈 {indicator}: {value:.2f}")
            else:
                self.signal_logger.info(f"   📈 {indicator}: {value}")


    def log_signal_generated(self, signal_data: dict):
        pair = signal_data.get('pair', 'N/A')
        direction = signal_data.get('direction', 'N/A')
        strength = signal_data.get('strength', 'N/A')
        rr_ratio = signal_data.get('risk_reward', 'N/A')

        self.signal_logger.info("🚀" + "=" * 60)
        self.signal_logger.info(f"🎯 SIGNAL GENERATED: {pair} {direction}")
        self.signal_logger.info(f"   💪 Strength: {strength:.1f}★" if isinstance(strength, float) else f"   💪 Strength: {strength}")
        self.signal_logger.info(f"   💰 Entry: ${signal_data.get('entry_price', 'N/A'):.4f}" if isinstance(signal_data.get('entry_price'), float) else f"   💰 Entry: {signal_data.get('entry_price', 'N/A')}")
        self.signal_logger.info(f"   🛑 Stop Loss: ${signal_data.get('stop_loss', 'N/A'):.4f}" if isinstance(signal_data.get('stop_loss'), float) else f"   🛑 Stop Loss: {signal_data.get('stop_loss', 'N/A')}")
        self.signal_logger.info(f"   🎯 Take Profit: ${signal_data.get('take_profit', 'N/A'):.4f}" if isinstance(signal_data.get('take_profit'), float) else f"   🎯 Take Profit: {signal_data.get('take_profit', 'N/A')}")
        self.signal_logger.info(f"   📊 Risk:Reward: 1:{rr_ratio:.1f}" if isinstance(rr_ratio, float) else f"   📊 Risk:Reward: 1:{rr_ratio}")
        self.signal_logger.info(f"   🕐 Time: {datetime.now().strftime('%H:%M:%S WIB')}")
        self.signal_logger.info("🚀" + "=" * 60)

        self.session_stats['signals_generated'] += 1


    def log_signal_filtered(self, pair: str, reason: str, details: dict = None):
        self.signal_logger.info(f"🚫 {pair}: Signal FILTERED - {reason}")
        if details:
            for key, value in details.items():
                self.signal_logger.info(f"   📊 {key}: {value}")

        self.session_stats['signals_filtered'] += 1


    def log_telegram_notification(self, success: bool, pair: str, attempt: int = 1):
        if success:
            self.telegram_logger.info(f"📱 {pair}: Telegram notification sent successfully")
        else:
            self.telegram_logger.warning(f"⚠️ {pair}: Telegram notification failed (attempt {attempt})")

    def log_error(self, component: str, error_msg: str, pair: str = ""):
        pair_info = f"{pair}: " if pair else ""
        # Use the root logger for general errors
        logging.error(f"💥 {component} ERROR - {pair_info}{error_msg}")
        self.session_stats['errors'] += 1

    def log_session_stats(self):
        uptime = datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        self.main_logger.info("📊" + "=" * 50)
        self.main_logger.info("📊 SESSION STATISTICS")
        self.main_logger.info("📊" + "=" * 50)
        self.main_logger.info(f"⏱️  Uptime: {uptime}")
        self.main_logger.info(f"🚀 Signals Generated: {self.session_stats['signals_generated']}")
        self.main_logger.info(f"🚫 Signals Filtered: {self.session_stats['signals_filtered']}")
        self.main_logger.info(f"🎯 Patterns Detected: {self.session_stats['patterns_detected']}")
        self.main_logger.info(f"📡 WebSocket Messages: {self.session_stats['websocket_messages']}")
        self.main_logger.info(f"💥 Errors: {self.session_stats['errors']}")

        total_analysis = self.session_stats['signals_generated'] + self.session_stats['signals_filtered']
        if total_analysis > 0:
            efficiency = (self.session_stats['signals_generated'] / total_analysis) * 100
            self.main_logger.info(f"📈 Signal Efficiency: {efficiency:.1f}%")

        self.main_logger.info("📊" + "=" * 50)

    def get_trading_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        if 8 <= hour <= 12: return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19: return "SORE (London Active)"
        elif 20 <= hour <= 23: return "MALAM (NY Prime)"
        else: return "DINI HARI (Low Volume)"