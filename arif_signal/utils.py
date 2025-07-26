# utils.py

import logging # Keep for fallback logging if logger is not provided
import sys # Keep for fallback logger setup if logger is not provided
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import classes from other files
from models import TradingConfig # Assuming TradingConfig is in models.py
# from trading_logger import TradingLogger # Assuming TradingLogger is in trading_logger.py

# --- Simulate TradingLogger if the import fails (for notebook execution) ---
# In a real project, you would remove this simulation.
try:
    from trading_logger import TradingLogger
except ImportError:
    class TradingLogger:
        def __init__(self, *args, **kwargs):
            self._logger = logging.getLogger("SIMULATED_LOGGER")
            if not self._logger.handlers:
                 handler = logging.StreamHandler(sys.stdout)
                 formatter = logging.Formatter('%(asctime)s | SIM_LOG | %(message)s')
                 handler.setFormatter(formatter)
                 self._logger.addHandler(handler)
                 self._logger.setLevel(logging.INFO)
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
        def log_signal_generated(self, signal_data: dict): self._logger.info(f"SIM_LOG: Signal generated ({signal_data.get('pair', 'N/A')} - {signal_data.get('direction', 'N/A')}) (simulated)")
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
        def is_good_trading_time(self) -> bool: return True


# ========== CONFIGURATION MANAGER ==========
class ConfigManager:
    """Centralized configuration management"""

    TIER1_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT'
    ]

    TIMEFRAME = '15m'
    TELEGRAM_TOKEN = 'ISI_TOKEN_KAMU'  # TODO: Move to environment variables
    TELEGRAM_CHAT_ID = 'ISI_CHAT_ID_KAMU'

    CONFIGS: Dict[str, TradingConfig] = { # Use imported TradingConfig
        'BTCUSDT': TradingConfig(4.0, 2.0, 25, 75, 2.0, 1, 4),
        'ETHUSDT': TradingConfig(3.8, 1.8, 28, 72, 2.0, 1, 4),
        'BNBUSDT': TradingConfig(3.5, 1.7, 30, 70, 1.8, 2, 3),
        'SOLUSDT': TradingConfig(3.6, 1.9, 27, 73, 1.8, 2, 3),
        'ADAUSDT': TradingConfig(3.2, 1.6, 30, 70, 1.5, 3, 2),
        'AVAXUSDT': TradingConfig(3.4, 1.8, 28, 72, 1.6, 2, 3),
        'MATICUSDT': TradingConfig(3.0, 1.5, 32, 68, 1.5, 3, 2),
        'DOTUSDT': TradingConfig(3.3, 1.7, 30, 70, 1.6, 3, 2)
    }

    MIN_VOLUME_USDT = 500000  # $500k minimum volume
    SIGNAL_COOLDOWN_MINUTES = 30

    # Add logger parameter (optional)
    def __init__(self, logger: Optional[TradingLogger] = None):
        self.logger = logger
        # No logging within __init__ for ConfigManager usually

    @classmethod
    def get_config(cls, pair: str) -> TradingConfig:
        """Get trading config for a specific pair"""
        # No logging needed in this specific method, it just returns data
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])


# ========== TIME UTILITIES ==========
class TimeUtils:
    """WIB time handling utilities"""

    WIB_OFFSET = 7  # UTC+7

    # Add logger parameter (optional)
    def __init__(self, logger: Optional[TradingLogger] = None):
        self.logger = logger
        # No logging within __init__ for TimeUtils usually

    @classmethod
    def get_wib_hour(cls) -> int:
        """Get current WIB hour"""
        return (datetime.utcnow().hour + cls.WIB_OFFSET) % 24

    @classmethod
    def get_wib_time_string(cls) -> str:
        """Get formatted WIB time string"""
        wib_time = datetime.utcnow() + timedelta(hours=cls.WIB_OFFSET)
        return wib_time.strftime('%H:%M:%S WIB')

    @classmethod
    def is_good_trading_time(cls) -> bool:
        """Check if current time is optimal for trading"""
        hour = cls.get_wib_hour()
        is_good = (8 <= hour <= 12) or (15 <= hour <= 19) or (20 <= hour <= 23)
        # Logging here is too verbose for every check, better in SignalProcessor
        return is_good

    @classmethod
    def get_trading_session(cls) -> str:
        """Get current trading session name"""
        hour = cls.get_wib_hour()

        if 8 <= hour <= 12:
            session = "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19:
            session = "SORE (London Active)"
        elif 20 <= hour <= 23:
            session = "MALAM (NY Prime)"
        elif 1 <= hour <= 7:
            session = "DINI HARI (Low Volume)"
        else:
            session = "TRANSISI"

        # Logging here is also verbose for every call
        return session