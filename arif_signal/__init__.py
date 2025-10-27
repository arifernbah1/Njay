"""
Arif Signal Trading Bot Package
===============================

Advanced Signal Generator Bot with Parallel Dual Mode Execution
"""

__version__ = "2.0.0"
__author__ = "Arif Signal Team"
__description__ = "Advanced Trading Signal Generator with Health Monitoring"

# Import main classes for easy access
from .main import ArifSignalApp
from .trading_logger import TradingLogger
from .health_monitor import BotHealthMonitor
from .error_handler import ErrorHandler
from .notifications import NotificationService
from .swing_setup import SwingSetupManager

__all__ = [
    'ArifSignalApp',
    'TradingLogger', 
    'BotHealthMonitor',
    'ErrorHandler',
    'NotificationService',
    'SwingSetupManager'
]