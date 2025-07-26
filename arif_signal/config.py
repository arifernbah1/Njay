# config.py

import os
from dotenv import load_dotenv
from typing import Dict
from models import TradingConfig

# Load environment variables from .env file
load_dotenv()

class ConfigManager:
    """Centralized configuration management with environment variables"""

    # Trading pairs
    TIER1_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT'
    ]

    # Environment variables with defaults
    TIMEFRAME = os.getenv('TIMEFRAME', '15m')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    MIN_VOLUME_USDT = int(os.getenv('MIN_VOLUME_USDT', '500000'))
    SIGNAL_COOLDOWN_MINUTES = int(os.getenv('SIGNAL_COOLDOWN_MINUTES', '30'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Trading configurations for each pair
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

    @classmethod
    def get_config(cls, pair: str) -> TradingConfig:
        """Get trading config for a specific pair"""
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file and ensure all required variables are set.")
            return False
        
        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("🔧 Current Configuration:")
        print(f"   📊 Timeframe: {cls.TIMEFRAME}")
        print(f"   💰 Min Volume: ${cls.MIN_VOLUME_USDT:,}")
        print(f"   ⏰ Cooldown: {cls.SIGNAL_COOLDOWN_MINUTES} minutes")
        print(f"   📝 Log Level: {cls.LOG_LEVEL}")
        print(f"   📱 Telegram: {'✅ Configured' if cls.TELEGRAM_TOKEN else '❌ Not configured'}")
        print(f"   🎯 Trading Pairs: {len(cls.TIER1_PAIRS)} pairs")