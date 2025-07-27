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
    """Handle telegram notifications for dual mode"""
    # Add logger parameter
    def __init__(self, logger: TradingLogger):
        # Accept logger
        self.logger = logger # Store logger
        self.token = ConfigManager.TELEGRAM_TOKEN
        self.chat_id = ConfigManager.TELEGRAM_CHAT_ID

    def send_signal(self, signal: SignalData, mode: str = "SCALPING") -> bool:
        """Send signal notification for specific mode"""
        message = self._create_message(signal, mode)
        # Pass pair and mode to _send_telegram for logging context
        return self._send_telegram(message, signal.pair, mode)

    def _create_message(self, signal: SignalData, mode: str = "SCALPING") -> str:
        """Create formatted signal message for specific mode"""
        # Quality indicators based on mode
        if mode == "SCALPING":
            if signal.strength >= 4.0:
                strength_emoji = "⚡⚡⚡"
                quality = "PREMIUM SCALPING"
            elif signal.strength >= 3.0:
                strength_emoji = "⚡⚡"
                quality = "HIGH SCALPING"
            elif signal.strength >= 2.5:
                strength_emoji = "⚡"
                quality = "GOOD SCALPING"
            else:
                strength_emoji = "🔸"
                quality = "STANDARD SCALPING"
        else:  # SWING mode
            if signal.strength >= 5.0:
                strength_emoji = "🔥🔥🔥"
                quality = "PREMIUM SWING"
            elif signal.strength >= 4.0:
                strength_emoji = "🔥🔥"
                quality = "HIGH SWING"
            elif signal.strength >= 3.5:
                strength_emoji = "🔥"
                quality = "GOOD SWING"
            else:
                strength_emoji = "📈"
                quality = "STANDARD SWING"

        direction_emoji = "🟢" if signal.direction == SignalType.BUY else "🔴"
        signal_text = "🚀 LONG" if signal.direction == SignalType.BUY else "🩸 SHORT"
        mode_emoji = "⚡" if mode == "SCALPING" else "📈"
        mode_text = "SCALPING" if mode == "SCALPING" else "SWING"

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
{strength_emoji} <b>{mode_text} SIGNAL</b> {mode_emoji}
{direction_emoji} 💎 <b>{signal.pair.replace('USDT', '/USDT')}</b>
📊 <b>Mode:</b> {mode_text}
📊 <b>Quality:</b> {quality} ({signal.strength:.1f}★)
🎯 <b>Setup:</b> Enhanced {mode_text} Pattern Detection
💰 <b>Entry:</b> ${signal.entry_price:.4f}
🛑 <b>Stop Loss:</b> ${signal.stop_loss:.4f} (-{stop_pct:.1f}%)
🎯 <b>Take Profit:</b> ${signal.take_profit:.4f} (+{tp_pct:.1f}%)
🎯 <b>Risk:Reward = 1:{signal.risk_reward:.1f}</b>
🕐 <b>Session:</b> {session}
🕐 <b>Time:</b> {wib_time}
<i>⚡ Dual Mode Signal System v3.0</i>
        """.strip()

    def _send_telegram(self, message: str, pair: str, mode: str = "SCALPING") -> bool:
        """Send message via Telegram API with mode-specific chat ID"""
        # Get mode-specific chat ID
        mode_config = ConfigManager.get_mode_config(mode)
        chat_id = mode_config.get('telegram_chat_id', self.chat_id)
        
        url = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        data = {
            'chat_id': chat_id,
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
        self.logger.log_error("NotificationService", "Telegram notification failed after 3 attempts for {} ({})".format(pair, mode), pair=pair)
        return False