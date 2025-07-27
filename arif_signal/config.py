# config.py

import os
from dotenv import load_dotenv
from typing import Dict
from models import TradingConfig

# Load environment variables from .env file
load_dotenv()

class TradingMode:
    """Trading mode definitions"""
    SCALPING = "SCALPING"
    SWING = "SWING"

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

    # Dual Mode Configuration - Both modes run simultaneously
    DUAL_MODE_CONFIG = {
        TradingMode.SCALPING: {
            'timeframe': '15m',  # Changed from 5m to 15m
            'enabled': True,
            'min_strength': 2.5,
            'volume_multiplier': 1.2,
            'rsi_oversold': 20,
            'rsi_overbought': 80,
            'min_risk_reward': 1.2,
            'max_daily_signals': 8,
            'signal_cooldown': 5,
            'pattern_sensitivity': 0.8,
            'volume_threshold': 100000,
            'telegram_chat_id': os.getenv('SCALPING_CHAT_ID', TELEGRAM_CHAT_ID)  # Separate chat for scalping
        },
        TradingMode.SWING: {
            'timeframe': '1h',
            'enabled': True,
            'min_strength': 4.0,
            'volume_multiplier': 2.0,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'min_risk_reward': 2.0,
            'max_daily_signals': 3,
            'signal_cooldown': 30,
            'pattern_sensitivity': 0.6,
            'volume_threshold': 500000,
            'telegram_chat_id': os.getenv('SWING_CHAT_ID', TELEGRAM_CHAT_ID)  # Separate chat for swing
        }
    }

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
    def get_mode_config(cls, mode: str) -> dict:
        """Get configuration for specific trading mode"""
        return cls.DUAL_MODE_CONFIG.get(mode, cls.DUAL_MODE_CONFIG[TradingMode.SCALPING])

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
        print("   🔥 DUAL MODE ENABLED:")
        for mode, config in cls.DUAL_MODE_CONFIG.items():
            status = "✅" if config['enabled'] else "❌"
            print("      {} {} Mode: {}m TF, {} signals/day, {}min cooldown".format(
                status, mode, config['timeframe'], config['max_daily_signals'], config['signal_cooldown']
            ))