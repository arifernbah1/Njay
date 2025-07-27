# trading_logger.py

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path
try:
    import colorama # Import colorama for potential color support
except ImportError:
    colorama = None # Fallback if colorama is not available

# Initialize colorama if available
if colorama:
    colorama.init()

# Custom Formatter for basic coloring
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': colorama.Fore.YELLOW if colorama else '',
        'ERROR': colorama.Fore.RED if colorama else '',
        'CRITICAL': (colorama.Fore.RED + colorama.Style.BRIGHT) if colorama else '',
        'INFO': colorama.Fore.GREEN if colorama else '',
        'DEBUG': colorama.Fore.BLUE if colorama else '',
        'RESET': colorama.Style.RESET_ALL if colorama else ''
    }

    def format(self, record):
        log_level = record.levelname
        color = self.COLORS.get(log_level, self.COLORS['RESET'])
        # Use a consistent base formatter for structure
        base_formatter = logging.Formatter('%(asctime)s | %(levelname)8s | %(name)15s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        formatted_message = base_formatter.format(record)
        return "{}{}{}".format(color, formatted_message, self.COLORS['RESET'])


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
            "logs/trading_bot_{}.log".format(datetime.now().strftime('%Y%m%d')),
            encoding='utf-8'
        )
        file_handler_daily.setLevel(getattr(logging, log_level.upper()))
        # Use basic formatter for file logs (no colors)
        file_handler_daily.setFormatter(logging.Formatter('%(asctime)s | %(levelname)8s | %(name)15s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))


        file_handler_signals = logging.FileHandler(
            "logs/signals_{}.log".format(datetime.now().strftime('%Y%m%d')),
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
        self.main_logger.info("📅 Start Time: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')))
        self.main_logger.info("⏰ Timeframe: {}".format(timeframe))
        self.main_logger.info("💎 Pairs: {}".format(', '.join(pairs)))
        self.main_logger.info("🕐 Session: {}".format(self.get_trading_session()))
        self.main_logger.info("-" * 80)

    def log_data_initialization(self, pair: str, candles_loaded: int):
        self.data_logger.info("📊 {}: Loading historical data...".format(pair))
        self.data_logger.info("✅ {}: {} candles loaded successfully".format(pair, candles_loaded))

    def log_websocket_connection(self, status: str, streams_count: int = 0):
        if status == "CONNECTED":
            self.websocket_logger.info("🔗 WebSocket connected successfully")
            if streams_count > 0:
                self.websocket_logger.info("📡 Subscribed to {} data streams".format(streams_count))
        elif status == "DISCONNECTED":
            self.websocket_logger.warning("❌ WebSocket disconnected")
        elif status == "RECONNECTING":
            self.websocket_logger.info("🔄 Attempting to reconnect WebSocket...")
        elif status == "ERROR":
            self.websocket_logger.error("💥 WebSocket connection error")

    def log_candle_received(self, pair: str, candle_data: dict):
        self.websocket_logger.debug(
            "📈 {}: New candle - "
            "O:{:.4f} H:{:.4f} "
            "L:{:.4f} C:{:.4f} "
            "V:{:.0f}".format(
                pair,
                float(candle_data.get('o', 0)),
                float(candle_data.get('h', 0)),
                float(candle_data.get('l', 0)),
                float(candle_data.get('c', 0)),
                float(candle_data.get('v', 0))
            )
        )
        self.session_stats['websocket_messages'] += 1

    def log_signal_analysis_start(self, pair: str, entry_price: float):
        self.signal_logger.info("🔍 {}: Starting signal analysis at $ {:.4f}".format(pair, entry_price))

    def log_filter_result(self, pair: str, filter_name: str, result: bool, details: str = ""):
        status = "✅ PASS" if result else "❌ FAIL"
        detail_msg = " ({})".format(details) if details else ""
        self.signal_logger.debug("   🧪 {}: {} - {}{}".format(pair, filter_name, status, detail_msg))

    def log_pattern_detection(self, pair: str, pattern_type: str, detected: bool, details: dict = None):
        if detected:
            self.pattern_logger.info("🎯 {}: {} pattern DETECTED!".format(pair, pattern_type))
            if details:
                for key, value in details.items():
                    self.pattern_logger.info("   📊 {}: {}".format(key, value))
            self.session_stats['patterns_detected'] += 1
        else:
            self.pattern_logger.debug("   🔍 {}: {} pattern not found".format(pair, pattern_type))

    def log_technical_analysis(self, pair: str, indicators: dict):
        self.signal_logger.info("📊 {}: Technical Analysis:".format(pair))
        for indicator, value in indicators.items():
            if isinstance(value, float):
                self.signal_logger.info("   📈 {}: {:.2f}".format(indicator, value))
            else:
                self.signal_logger.info("   📈 {}: {}".format(indicator, value))


    def log_signal_generated(self, signal_data: dict):
        pair = signal_data.get('pair', 'N/A')
        direction = signal_data.get('direction', 'N/A')
        strength = signal_data.get('strength', 'N/A')
        rr_ratio = signal_data.get('risk_reward', 'N/A')

        self.signal_logger.info("🚀" + "=" * 60)
        self.signal_logger.info("🎯 SIGNAL GENERATED: {} {}".format(pair, direction))
        self.signal_logger.info("   💪 Strength: {:.1f}★".format(strength) if isinstance(strength, float) else "   💪 Strength: {}".format(strength))
        self.signal_logger.info("   💰 Entry: $ {:.4f}".format(signal_data.get('entry_price')) if isinstance(signal_data.get('entry_price'), float) else "   💰 Entry: {}".format(signal_data.get('entry_price', 'N/A')))
        self.signal_logger.info("   🛑 Stop Loss: $ {:.4f}".format(signal_data.get('stop_loss')) if isinstance(signal_data.get('stop_loss'), float) else "   🛑 Stop Loss: {}".format(signal_data.get('stop_loss', 'N/A')))
        self.signal_logger.info("   🎯 Take Profit: $ {:.4f}".format(signal_data.get('take_profit')) if isinstance(signal_data.get('take_profit'), float) else "   🎯 Take Profit: {}".format(signal_data.get('take_profit', 'N/A')))
        self.signal_logger.info("   📊 Risk:Reward: 1:{:.1f}".format(rr_ratio) if isinstance(rr_ratio, float) else "   📊 Risk:Reward: 1:{}".format(rr_ratio))
        self.signal_logger.info("   🕐 Time: {}".format(datetime.now().strftime('%H:%M:%S WIB')))
        self.signal_logger.info("🚀" + "=" * 60)

        self.session_stats['signals_generated'] += 1


    def log_signal_filtered(self, pair: str, reason: str, details: dict = None):
        self.signal_logger.info("🚫 {}: Signal FILTERED - {}".format(pair, reason))
        if details:
            for key, value in details.items():
                self.signal_logger.info("   📊 {}: {}".format(key, value))

        self.session_stats['signals_filtered'] += 1


    def log_telegram_notification(self, success: bool, pair: str, attempt: int = 1):
        if success:
            self.telegram_logger.info("📱 {}: Telegram notification sent successfully".format(pair))
        else:
            self.telegram_logger.warning("⚠️ {}: Telegram notification failed (attempt {})".format(pair, attempt))

    def log_error(self, component: str, error_msg: str, pair: str = ""):
        pair_info = "{}: ".format(pair) if pair else ""
        # Use the root logger for general errors
        logging.error("💥 {} ERROR - {}{}".format(component, pair_info, error_msg))
        self.session_stats['errors'] += 1

    def log_session_stats(self):
        uptime = datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        self.main_logger.info("📊" + "=" * 50)
        self.main_logger.info("📊 SESSION STATISTICS")
        self.main_logger.info("📊" + "=" * 50)
        self.main_logger.info("⏱️  Uptime: {}".format(uptime))
        self.main_logger.info("🚀 Signals Generated: {}".format(self.session_stats['signals_generated']))
        self.main_logger.info("🚫 Signals Filtered: {}".format(self.session_stats['signals_filtered']))
        self.main_logger.info("🎯 Patterns Detected: {}".format(self.session_stats['patterns_detected']))
        self.main_logger.info("📡 WebSocket Messages: {}".format(self.session_stats['websocket_messages']))
        self.main_logger.info("💥 Errors: {}".format(self.session_stats['errors']))

        total_analysis = self.session_stats['signals_generated'] + self.session_stats['signals_filtered']
        if total_analysis > 0:
            efficiency = (self.session_stats['signals_generated'] / total_analysis) * 100
            self.main_logger.info("📈 Signal Efficiency: {:.1f}%".format(efficiency))

        self.main_logger.info("📊" + "=" * 50)

    def get_trading_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        if 8 <= hour <= 12: return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19: return "SORE (London Active)"
        elif 20 <= hour <= 23: return "MALAM (NY Prime)"
        else: return "DINI HARI (Low Volume)"