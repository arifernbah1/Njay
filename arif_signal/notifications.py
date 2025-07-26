# notifications.py

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import classes from other files
from models import SignalData, SignalType
from utils import ConfigManager, TimeUtils

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