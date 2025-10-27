# notifications.py

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

# Import classes from other files
from models import SignalData, SignalType
from utils import TimeUtils
from config import ConfigManager

# ========== NOTIFICATION SERVICE ==========
class NotificationService:
    """Telegram notification service for trading alerts"""
    
    def __init__(self, bot_token: str, chat_id: str, trading_logger):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = trading_logger
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_swing_setup_alert(self, setup_data: Dict, mode: str = "SWING"):
        """Send swing setup alert to Telegram"""
        try:
            # Format message for swing setup
            message = self._format_swing_setup_message(setup_data)
            
            # Send to Telegram
            success = self._send_telegram_message(message, "SWING_SETUP")
            
            if success:
                self.logger.log_trading_alert(
                    "TELEGRAM_SENT",
                    f"Swing setup alert sent to Telegram for {setup_data.get('pair', 'N/A')}",
                    pair=setup_data.get('pair'),
                    mode=mode
                )
            else:
                self.logger.log_trading_alert(
                    "TELEGRAM_FAILED",
                    f"Failed to send swing setup alert to Telegram",
                    pair=setup_data.get('pair'),
                    mode=mode,
                    priority="HIGH"
                )
            
            return success
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error sending swing setup alert: {str(e)}",
                pair=setup_data.get('pair'),
                mode=mode,
                priority="CRITICAL"
            )
            return False
    
    def send_signal_alert(self, signal_data: Dict, mode: str = "SCALPING"):
        """Send trading signal alert to Telegram"""
        try:
            # Format message for signal
            message = self._format_signal_message(signal_data)
            
            # Send to Telegram
            success = self._send_telegram_message(message, "SIGNAL")
            
            if success:
                self.logger.log_trading_alert(
                    "TELEGRAM_SENT",
                    f"Signal alert sent to Telegram for {signal_data.get('pair', 'N/A')}",
                    pair=signal_data.get('pair'),
                    mode=mode
                )
            else:
                self.logger.log_trading_alert(
                    "TELEGRAM_FAILED",
                    f"Failed to send signal alert to Telegram",
                    pair=signal_data.get('pair'),
                    mode=mode,
                    priority="HIGH"
                )
            
            return success
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error sending signal alert: {str(e)}",
                pair=signal_data.get('pair'),
                mode=mode,
                priority="CRITICAL"
            )
            return False
    
    def send_setup_triggered_alert(self, setup_data: Dict, entry_price: float, mode: str = "SWING"):
        """Send alert when swing setup is triggered"""
        try:
            # Format message for setup trigger
            message = self._format_setup_triggered_message(setup_data, entry_price)
            
            # Send to Telegram
            success = self._send_telegram_message(message, "SETUP_TRIGGERED")
            
            if success:
                self.logger.log_trading_alert(
                    "TELEGRAM_SENT",
                    f"Setup triggered alert sent to Telegram for {setup_data.get('pair', 'N/A')}",
                    pair=setup_data.get('pair'),
                    mode=mode
                )
            else:
                self.logger.log_trading_alert(
                    "TELEGRAM_FAILED",
                    f"Failed to send setup triggered alert to Telegram",
                    pair=setup_data.get('pair'),
                    mode=mode,
                    priority="HIGH"
                )
            
            return success
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error sending setup triggered alert: {str(e)}",
                pair=setup_data.get('pair'),
                mode=mode,
                priority="CRITICAL"
            )
            return False
    
    def _format_swing_setup_message(self, setup_data: Dict) -> str:
        """Format swing setup message for Telegram"""
        try:
            pair = setup_data.get('pair', 'N/A')
            setup_type = setup_data.get('setup_type', 'N/A')
            confidence = setup_data.get('confidence', 0) * 100
            strength = setup_data.get('setup_strength', 0)
            entry_min, entry_max = setup_data.get('entry_zone', (0, 0))
            stop_loss = setup_data.get('stop_loss', 0)
            take_profits = setup_data.get('take_profit', [])
            risk_reward = setup_data.get('risk_reward', 0)
            market_structure = setup_data.get('market_structure', 'N/A')
            notes = setup_data.get('notes', '')
            
            message = f"""
🎯 <b>SWING SETUP CREATED</b>

💎 <b>Pair:</b> {pair}
📊 <b>Type:</b> {setup_type}
⏰ <b>Timeframe:</b> 1h
🕐 <b>Created:</b> {datetime.now().strftime('%H:%M:%S WIB')}

📈 <b>Market Structure:</b> {market_structure}
🎯 <b>Confidence:</b> {confidence:.1f}%
💪 <b>Strength:</b> {strength:.1f}/5.0
📊 <b>Risk/Reward:</b> 1:{risk_reward:.1f}

💰 <b>Entry Zone:</b> ${entry_min:,.2f} - ${entry_max:,.2f}
🛑 <b>Stop Loss:</b> ${stop_loss:,.2f}

🎯 <b>Take Profit Targets:</b>
"""
            
            for i, tp in enumerate(take_profits, 1):
                message += f"   TP{i}: ${tp:,.2f}\n"
            
            message += f"""
📝 <b>Notes:</b> {notes}

⚠️ <i>Setup is ACTIVE - Waiting for price to enter entry zone...</i>
"""
            
            return message.strip()
            
        except Exception as e:
            return f"Error formatting swing setup message: {str(e)}"
    
    def _format_signal_message(self, signal_data: Dict) -> str:
        """Format signal message for Telegram"""
        try:
            pair = signal_data.get('pair', 'N/A')
            direction = signal_data.get('direction', 'N/A')
            entry_price = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            take_profit = signal_data.get('take_profit', 0)
            strength = signal_data.get('strength', 0)
            risk_reward = signal_data.get('risk_reward', 0)
            pattern = signal_data.get('pattern', 'N/A')
            mode = signal_data.get('mode', 'N/A')
            
            # Emoji for direction
            direction_emoji = "🟢" if direction == "BUY" else "🔴"
            mode_emoji = "⚡" if mode == "SCALPING" else "📈"
            
            message = f"""
{mode_emoji} <b>{mode} SIGNAL</b>

{direction_emoji} <b>Direction:</b> {direction}
💎 <b>Pair:</b> {pair}
📊 <b>Pattern:</b> {pattern}
🕐 <b>Time:</b> {datetime.now().strftime('%H:%M:%S WIB')}

💰 <b>Entry Price:</b> ${entry_price:,.2f}
🛑 <b>Stop Loss:</b> ${stop_loss:,.2f}
🎯 <b>Take Profit:</b> ${take_profit:,.2f}

💪 <b>Strength:</b> {strength:.1f}/5.0
📊 <b>Risk/Reward:</b> 1:{risk_reward:.1f}

🚀 <i>Signal ready for execution!</i>
"""
            
            return message.strip()
            
        except Exception as e:
            return f"Error formatting signal message: {str(e)}"
    
    def _format_setup_triggered_message(self, setup_data: Dict, entry_price: float) -> str:
        """Format setup triggered message for Telegram"""
        try:
            pair = setup_data.get('pair', 'N/A')
            setup_type = setup_data.get('setup_type', 'N/A')
            direction = "BUY" if setup_type in ["BREAKOUT", "REVERSAL"] else "SELL"
            
            # Emoji for direction
            direction_emoji = "🟢" if direction == "BUY" else "🔴"
            
            message = f"""
🎯 <b>SWING SETUP TRIGGERED!</b>

{direction_emoji} <b>Direction:</b> {direction}
💎 <b>Pair:</b> {pair}
📊 <b>Setup Type:</b> {setup_type}
🕐 <b>Triggered:</b> {datetime.now().strftime('%H:%M:%S WIB')}

💰 <b>Entry Price:</b> ${entry_price:,.2f}
🛑 <b>Stop Loss:</b> ${setup_data.get('stop_loss', 0):,.2f}

🎯 <b>Take Profit Targets:</b>
"""
            
            for i, tp in enumerate(setup_data.get('take_profit', []), 1):
                message += f"   TP{i}: ${tp:,.2f}\n"
            
            message += f"""
📊 <b>Risk/Reward:</b> 1:{setup_data.get('risk_reward', 0):.1f}

🚀 <i>Setup executed - Signal generated!</i>
"""
            
            return message.strip()
            
        except Exception as e:
            return f"Error formatting setup triggered message: {str(e)}"
    
    def _send_telegram_message(self, message: str, message_type: str) -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return True
                else:
                    self.logger.log_trading_alert(
                        "TELEGRAM_ERROR",
                        f"Telegram API error: {result.get('description', 'Unknown error')}",
                        priority="HIGH"
                    )
                    return False
            else:
                self.logger.log_trading_alert(
                    "TELEGRAM_ERROR",
                    f"HTTP error {response.status_code}: {response.text}",
                    priority="HIGH"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.log_trading_alert(
                "TELEGRAM_ERROR",
                f"Network error: {str(e)}",
                priority="HIGH"
            )
            return False
        except Exception as e:
            self.logger.log_trading_alert(
                "TELEGRAM_ERROR",
                f"Unexpected error: {str(e)}",
                priority="HIGH"
            )
            return False
    
    def send_system_alert(self, alert_type: str, message: str, priority: str = "MEDIUM"):
        """Send system alert to Telegram"""
        try:
            # Format system message
            formatted_message = f"""
🤖 <b>SYSTEM ALERT</b>

📊 <b>Type:</b> {alert_type}
🕐 <b>Time:</b> {datetime.now().strftime('%H:%M:%S WIB')}
⚠️ <b>Priority:</b> {priority}

📝 <b>Message:</b>
{message}
"""
            
            # Send to Telegram
            success = self._send_telegram_message(formatted_message, "SYSTEM")
            
            if success:
                self.logger.log_trading_alert(
                    "TELEGRAM_SENT",
                    f"System alert sent to Telegram: {alert_type}",
                    priority=priority
                )
            else:
                self.logger.log_trading_alert(
                    "TELEGRAM_FAILED",
                    f"Failed to send system alert to Telegram",
                    priority="HIGH"
                )
            
            return success
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error sending system alert: {str(e)}",
                priority="CRITICAL"
            )
            return False