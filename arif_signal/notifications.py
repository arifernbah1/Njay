# notifications.py

import requests
import json
import sys # Import sys for fallback logger
import time # Needed for time.sleep
from datetime import datetime, timedelta # timedelta needed for TimeUtils
from typing import Dict, List, Optional, Tuple # Needed for simulated classes

# Import classes from models.py, utils.py, and trading_logger.py (Simulated)
# from models import SignalData, SignalType # Gagal
# from utils import ConfigManager, TimeUtils # Gagal
# from trading_logger import TradingLogger # Gagal


# --- Simulate TradingLogger ---
# This is a minimal simulation just enough to prevent NameError if logger methods are called.
# The full TradingLogger class would reside in trading_logger.py
import logging # Import logging for fallback
class TradingLogger:
    def __init__(self, *args, **kwargs):
        # Use the root logger for simulation purposes
        self._logger = logging.getLogger("SIMULATED_LOGGER")
        # Configure simulation logger to output to console
        if not self._logger.handlers:
             handler = logging.StreamHandler(sys.stdout)
             formatter = logging.Formatter('%(asctime)s | SIM_LOG | %(message)s')
             handler.setFormatter(formatter)
             self._logger.addHandler(handler)
             self._logger.setLevel(logging.INFO) # Default level for simulation

    def log_bot_start(self, *args, **kwargs): self._logger.info("SIM_LOG: Bot start (simulated)")
    def log_data_initialization(self, *args, **kwargs): self._logger.info(f"SIM_LOG: Data init (simulated) - {args[0]}")
    def log_websocket_connection(self, *args, **kwargs): self._logger.info(f"SIM_LOG: WS connection ({args[0]}) (simulated)")
    def log_candle_received(self, *args, **kwargs): self._logger.debug(f"SIM_LOG: Candle received ({args[0]}) (simulated)")
    def log_signal_analysis_start(self, pair: str, entry_price: float): self._logger.info(f"SIM_LOG: Signal analysis start ({pair} @ {entry_price:.4f}) (simulated)")
    def log_filter_result(self, pair: str, filter_name: str, result: bool, details: str = ""): self._logger.debug(f"SIM_LOG: Filter result ({pair} - {filter_name}: {result}) (simulated) {details}")
    def log_pattern_detection(self, pair: str, pattern_type: str, detected: bool, details: dict = None):
        if detected: self._logger.info(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} DETECTED!) (simulated)")
        else: self._logger.debug(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} not found) (simulated)")
    def log_technical_analysis(self, pair: str, indicators: dict): self._logger.info(f"SIM_LOG: TA ({pair}) (simulated) {indicators}")
    def log_signal_generated(self, signal_data: dict): self._logger.info(f"SIM_LOG: Signal generated ({signal_data['pair']} - {signal_data['direction']}) (simulated)")
    def log_signal_filtered(self, pair: str, reason: str, details: dict = None): self._logger.info(f"SIM_LOG: Signal filtered ({pair} - {reason}) (simulated) {details}")
    def log_telegram_notification(self, success: bool, pair: str, attempt: int = 1):
         if success: self._logger.info(f"SIM_LOG: Telegram notification sent ({pair}) (simulated)")
         else: self._logger.warning(f"SIM_LOG: Telegram notification failed ({pair} - attempt {attempt}) (simulated)")
    def log_error(self, component: str, error_msg: str, pair: str = ""): self._logger.error(f"SIM_LOG: ERROR in {component} - {pair}{error_msg}")
    def log_session_stats(self): self._logger.info("SIM_LOG: Session stats (simulated)")

    @property
    def main_logger(self): return self._logger
    @property
    def data_logger(self): return self._logger
    @property
    def signal_logger(self): return self._logger
    @property
    def websocket_logger(self): return self._logger
    @property
    def pattern_logger(self): return self._logger
    @property
    def telegram_logger(self): return self._logger

    def get_trading_session(self) -> str: return "Simulated Session"
    def get_wib_time_string(self) -> str: return "Simulated WIB Time"


# --- End Simulate TradingLogger ---


# --- Simulate Imports from other files needed by NotificationService ---
from dataclasses import dataclass
# datetime already imported

@dataclass
class SignalData:
    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    strength: float
    risk_reward: float
    timestamp: datetime

class SignalType:
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    BUY = "BUY"
    SELL = "SELL"

class ConfigManager:
    # Only include what's needed by notifications.py
    TELEGRAM_TOKEN = 'ISI_TOKEN_KAMU'
    TELEGRAM_CHAT_ID = 'ISI_CHAT_ID_KAMU'

class TimeUtils:
    WIB_OFFSET = 7
    @classmethod
    def get_wib_time_string(cls) -> str:
        wib_time = datetime.utcnow() + timedelta(hours=cls.WIB_OFFSET)
        return wib_time.strftime('%H:%M:%S WIB')
    @classmethod
    def get_trading_session(cls) -> str:
        hour = (datetime.utcnow().hour + cls.WIB_OFFSET) % 24
        if 8 <= hour <= 12: return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19: return "SORE (London Active)"
        elif 20 <= hour <= 23: return "MALAM (NY Prime)"
        elif 1 <= hour <= 7: return "DINI HARI (Low Volume)"
        else: return "TRANSISI"

# --- End Simulate Imports ---


# ========== NOTIFICATION SERVICE ==========
class NotificationService:
    """Handle telegram notifications"""

    # Add logger parameter
    def __init__(self, logger: TradingLogger): # Accept logger
        self.logger = logger # Store logger
        self.token = ConfigManager.TELEGRAM_TOKEN
        self.chat_id = ConfigManager.TELEGRAM_CHAT_ID

    def send_signal(self, signal: SignalData) -> bool:
        """Send signal notification"""
        message = self._create_message(signal)
        # Pass pair to _send_telegram for logging context
        return self._send_telegram(message, signal.pair)

    def _create_message(self, signal: SignalData) -> str:
        """Create formatted signal message"""
        # Quality indicators
        if signal.strength >= 5.0:
            strength_emoji = "🔥🔥🔥"
            quality = "PREMIUM"
        elif signal.strength >= 4.0:
            strength_emoji = "🔥🔥"
            quality = "HIGH"
        elif signal.strength >= 3.5:
            strength_emoji = "🔥"
            quality = "GOOD"
        else:
            strength_emoji = "⚡"
            quality = "STANDARD"

        direction_emoji = "🟢" if signal.direction == SignalType.BUY else "🔴"
        signal_text = "🚀 LONG" if signal.direction == SignalType.BUY else "🩸 SHORT"

        # Calculate percentages
        if signal.direction == SignalType.BUY:
            stop_pct = ((signal.entry_price - signal.stop_loss) / signal.entry_price) * 100 if signal.entry_price != 0 else 0
            tp_pct = ((signal.take_profit - signal.entry_price) / signal.entry_price) * 100 if signal.entry_price != 0 else 0
        else:
            stop_pct = ((signal.stop_loss - signal.entry_price) / signal.entry_price) * 100 if signal.entry_price != 0 else 0
            tp_pct = ((signal.entry_price - signal.take_profit) / signal.entry_price) * 100 if signal.entry_price != 0 else 0

        session = TimeUtils.get_trading_session()
        wib_time = TimeUtils.get_wib_time_string()

        return f"""
{strength_emoji} <b>{signal_text} ENTRY</b> {direction_emoji}

💎 <b>{signal.pair.replace('USDT', '/USDT')}</b>
📊 <b>Quality:</b> {quality} ({signal.strength:.1f}★)
🎯 <b>Setup:</b> Enhanced Pattern Detection

💰 <b>Entry:</b> ${signal.entry_price:.4f}
🛑 <b>Stop Loss:</b> ${signal.stop_loss:.4f} (-{stop_pct:.1f}%)
🎯 <b>Take Profit:</b> ${signal.take_profit:.4f} (+{tp_pct:.1f}%)

🎯 <b>Risk:Reward = 1:{signal.risk_reward:.1f}</b>

🕐 <b>Session:</b> {session}
🕐 <b>Time:</b> {wib_time}
<i>⚡ Refactored Signal System v3.0</i>
        """.strip()

    def _send_telegram(self, message: str, pair: str) -> bool:
        """Send message via Telegram API with logging"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        # Use logger for notification attempts
        for attempt in range(3):
            try:
                response = requests.post(url, data=data, timeout=10)
                if response.status_code == 200:
                    # Log successful notification
                    self.logger.log_telegram_notification(True, pair)
                    return True
            except Exception as e:
                # Log failed attempt and error
                self.logger.log_telegram_notification(False, pair, attempt=attempt+1)
                self.logger.log_error("NotificationService", f"Telegram attempt {attempt + 1} failed: {e}", pair=pair)
                time.sleep(1)

        # Log final failure after retries
        self.logger.log_error("NotificationService", f"Telegram notification failed after 3 attempts for {pair}", pair=pair)
        return False