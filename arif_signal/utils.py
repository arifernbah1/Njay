"""
Arif Signal Trading Bot - Utilities
Fungsi utilitas (ConfigManager, TimeUtils)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ConfigManager:
    """Manager untuk mengelola konfigurasi aplikasi"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load konfigurasi dari file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        return self.config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Simpan konfigurasi ke file"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        self.config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ambil nilai konfigurasi"""
        return self.config.get(key, default)

class TimeUtils:
    """Utility functions untuk operasi waktu"""
    
    @staticmethod
    def get_current_timestamp() -> datetime:
        """Dapatkan timestamp saat ini"""
        return datetime.now()
    
    @staticmethod
    def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp ke string"""
        return timestamp.strftime(format_str)
    
    @staticmethod
    def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """Parse string ke timestamp"""
        return datetime.strptime(timestamp_str, format_str)
    
    @staticmethod
    def add_minutes(timestamp: datetime, minutes: int) -> datetime:
        """Tambah menit ke timestamp"""
        return timestamp + timedelta(minutes=minutes)