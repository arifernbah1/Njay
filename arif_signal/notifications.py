# notifications.py

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import classes from other files
from models import SignalData, SignalType
from utils import TimeUtils
from config import ConfigManager

# ========== NOTIFICATION SERVICE ==========
class NotificationService:
    """Handle telegram notifications"""

    def __init__(self, logger: 'TradingLogger'):
        self.logger = logger
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

        return """
{} <b>{} ENTRY</b> {}

💎 <b>{}</b>
📊 <b>Quality:</b> {} ({:.1f}★)
🎯 <b>Setup:</b> Enhanced Pattern Detection

💰 <b>Entry:</b> ${:.4f}
🛑 <b>Stop Loss:</b> ${:.4f} (-{:.1f}%)
🎯 <b>Take Profit:</b> ${:.4f} (+{:.1f}%)

🎯 <b>Risk:Reward = 1:{:.1f}</b>

🕐 <b>Session:</b> {}
🕐 <b>Time:</b> {}
<i>⚡ Refactored Signal System v3.0</i>
        """.format(
            strength_emoji, signal_text, direction_emoji,
            signal.pair.replace('USDT', '/USDT'),
            quality, signal.strength,
            signal.entry_price,
            signal.stop_loss, stop_pct,
            signal.take_profit, tp_pct,
            signal.risk_reward,
            session, wib_time
        ).strip()

    def _send_telegram(self, message: str, pair: str) -> bool:
        """Send message via Telegram API with logging"""
        url = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
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
                self.logger.log_error("NotificationService", "Telegram attempt {} failed: {}".format(attempt + 1, e), pair=pair)
                time.sleep(1)

        # Log final failure after retries
        self.logger.log_error("NotificationService", "Telegram notification failed after 3 attempts for {}".format(pair), pair=pair)
        return False