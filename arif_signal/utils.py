# utils.py

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import classes from other files
from models import TradingConfig

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

    CONFIGS: Dict[str, TradingConfig] = {
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

    @classmethod
    def get_config(cls, pair: str) -> TradingConfig:
        """Get trading config for a specific pair"""
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])


# ========== TIME UTILITIES ==========
class TimeUtils:
    """Time utilities for trading sessions"""

    WIB_OFFSET = 7  # UTC+7

    @classmethod
    def get_wib_hour(cls) -> int:
        """Get current hour in WIB timezone"""
        return (datetime.utcnow().hour + cls.WIB_OFFSET) % 24

    @classmethod
    def get_wib_time_string(cls) -> str:
        """Get current time string in WIB timezone"""
        wib_time = datetime.utcnow() + timedelta(hours=cls.WIB_OFFSET)
        return wib_time.strftime('%H:%M:%S WIB')

    @classmethod
    def is_good_trading_time(cls) -> bool:
        """Check if current time is good for trading"""
        hour = cls.get_wib_hour()
        return (8 <= hour <= 12) or (15 <= hour <= 19) or (20 <= hour <= 23)

    @classmethod
    def get_trading_session(cls) -> str:
        """Get current trading session"""
        hour = cls.get_wib_hour()
        if 8 <= hour <= 12:
            return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19:
            return "SORE (London Active)"
        elif 20 <= hour <= 23:
            return "MALAM (NY Prime)"
        elif 1 <= hour <= 7:
            return "DINI HARI (Low Volume)"
        else:
            return "TRANSISI"