# utils.py

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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