# config.py

import os
from dotenv import load_dotenv
from typing import Dict
from models import TradingConfig

# Load environment variables from .env file
load_dotenv()

class ConfigManager:
    """Centralized configuration management with environment variables"""

    # Trading pairs - Added 2 more stable pairs (10 total)
    TIER1_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'XRPUSDT',
        'UNIUSDT', 'DOGEUSDT'
    ]

    # Symbol mapping for Binance API (some pairs have different symbols)
    SYMBOL_MAPPING = {
        'BTCUSDT': 'BTC/USDT',
        'ETHUSDT': 'ETH/USDT', 
        'BNBUSDT': 'BNB/USDT',
        'SOLUSDT': 'SOL/USDT',
        'ADAUSDT': 'ADA/USDT',
        'AVAXUSDT': 'AVAX/USDT',
        'LINKUSDT': 'LINK/USDT',  # Chainlink - very stable
        'XRPUSDT': 'XRP/USDT',    # Ripple - high volume and stable
        'UNIUSDT': 'UNI/USDT',    # Uniswap - DEX leader, very stable
        'DOGEUSDT': 'DOGE/USDT'   # Dogecoin - meme coin but high volume
    }

    # Environment variables with defaults
    TIMEFRAME = os.getenv('TIMEFRAME', '15m')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    MIN_VOLUME_USDT = int(os.getenv('MIN_VOLUME_USDT', '200000'))
    SIGNAL_COOLDOWN_MINUTES = int(os.getenv('SIGNAL_COOLDOWN_MINUTES', '15'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Trading configurations for each pair - Relaxed for more signals
    CONFIGS: Dict[str, TradingConfig] = {
        'BTCUSDT': TradingConfig(3.5, 1.8, 25, 75, 1.8, 1, 4),  # Relaxed quality, max 4/day
        'ETHUSDT': TradingConfig(3.4, 1.7, 25, 75, 1.8, 1, 4),  # Relaxed quality, max 4/day
        'BNBUSDT': TradingConfig(3.3, 1.6, 28, 72, 1.7, 2, 3),  # Relaxed quality, max 3/day
        'SOLUSDT': TradingConfig(3.3, 1.6, 28, 72, 1.7, 2, 3),  # Relaxed quality, max 3/day
        'ADAUSDT': TradingConfig(3.2, 1.5, 30, 70, 1.6, 3, 2),  # Relaxed quality, max 2/day
        'AVAXUSDT': TradingConfig(3.3, 1.6, 28, 72, 1.7, 2, 3), # Relaxed quality, max 3/day
        'LINKUSDT': TradingConfig(3.2, 1.5, 30, 70, 1.6, 2, 3), # Relaxed quality, max 3/day
        'XRPUSDT': TradingConfig(3.1, 1.4, 32, 68, 1.5, 3, 2),  # Relaxed quality, max 2/day
        'UNIUSDT': TradingConfig(3.2, 1.5, 30, 70, 1.6, 2, 3),  # Relaxed quality, max 3/day
        'DOGEUSDT': TradingConfig(3.0, 1.3, 35, 65, 1.4, 3, 2)  # Relaxed quality, max 2/day
    }

    @classmethod
    def get_config(cls, pair: str) -> TradingConfig:
        """Get trading config for a specific pair"""
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])

    @classmethod
    def get_binance_symbol(cls, pair: str) -> str:
        """Get the correct Binance symbol for a trading pair"""
        return cls.SYMBOL_MAPPING.get(pair, pair.replace('USDT', '/USDT'))

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Missing required environment variables: {}".format(', '.join(missing_vars)))
            print("Please check your .env file and ensure all required variables are set.")
            return False
        
        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("🔧 Current Configuration:")
        print("   📊 Timeframe: {}".format(cls.TIMEFRAME))
        print("   💰 Min Volume: ${:,}".format(cls.MIN_VOLUME_USDT))
        print("   ⏰ Cooldown: {} minutes".format(cls.SIGNAL_COOLDOWN_MINUTES))
        print("   📝 Log Level: {}".format(cls.LOG_LEVEL))
        print("   📱 Telegram: {}".format('✅ Configured' if cls.TELEGRAM_TOKEN else '❌ Not configured'))
        print("   🎯 Trading Pairs: {} pairs".format(len(cls.TIER1_PAIRS)))
        print("   📋 Symbol Mapping:")
        for pair, symbol in cls.SYMBOL_MAPPING.items():
            print("      {} → {}".format(pair, symbol))
        print("   💡 Premium Pairs: LINK, XRP, UNI, DOGE - All very stable!")
        print("   🚀 Total: 10 pairs ready for trading!")