# data_ws.py

import ccxt
import json
import time
import websocket
import threading
import sys # Import sys for fallback logger
import ssl # Needed for websocket.run_forever sslopt
from collections import deque, defaultdict
from typing import List, Optional, Tuple # List, Optional already imported in previous blocks, need Tuple for TA simulation

# Import classes from models.py, utils.py, processor.py, notifications.py, and trading_logger.py (Simulated)
# from models import CandleData, SignalData, SignalType # Gagal
# from utils import ConfigManager, TimeUtils # Gagal
# from processor import EnhancedSignalProcessor # Gagal
# from notifications import NotificationService # Gagal
# from trading_logger import TradingLogger # Gagal


# --- Simulate TradingLogger ---
# This is a minimal simulation just enough to prevent NameError if logger methods are called.
# The full TradingLogger class would reside in trading_logger.py
import logging # Import logging for fallback
class TradingLogger:
    def __init__(self, *args, **kwargs):
        # Use the root logger for simulation purposes
        self._logger = logging.getLogger("SIMULATED_LOGGER")
        # Configure simulation logger to output to console
        if not self._logger.handlers:
             handler = logging.StreamHandler(sys.stdout)
             formatter = logging.Formatter('%(asctime)s | SIM_LOG | %(message)s')
             handler.setFormatter(formatter)
             self._logger.addHandler(handler)
             self._logger.setLevel(logging.INFO) # Default level for simulation

    def log_bot_start(self, *args, **kwargs): self._logger.info("SIM_LOG: Bot start (simulated)")
    def log_data_initialization(self, pair: str, candles_loaded: int): self._logger.info(f"SIM_LOG: Data init ({pair}): {candles_loaded} candles loaded (simulated)")
    def log_websocket_connection(self, status: str, streams_count: int = 0):
        if status == "CONNECTED":
            self._logger.info("🔗 WebSocket connected successfully")
            if streams_count > 0:
                self._logger.info(f"📡 Subscribed to {streams_count} data streams")
        elif status == "DISCONNECTED": self._logger.warning("❌ WebSocket disconnected (simulated)")
        elif status == "RECONNECTING": self._logger.info("🔄 Attempting to reconnect WS (simulated)")
        elif status == "ERROR": self._logger.error("💥 WebSocket connection error (simulated)")

    def log_candle_received(self, pair: str, candle_data: dict): self._logger.debug(f"SIM_LOG: Candle received ({pair}) (simulated)")
    def log_signal_analysis_start(self, pair: str, entry_price: float): self._logger.info(f"SIM_LOG: Signal analysis start ({pair} @ {entry_price:.4f}) (simulated)")
    def log_filter_result(self, pair: str, filter_name: str, result: bool, details: str = ""): self._logger.debug(f"SIM_LOG: Filter result ({pair} - {filter_name}: {result}) (simulated) {details}")
    def log_pattern_detection(self, pair: str, pattern_type: str, detected: bool, details: dict = None):
        if detected: self._logger.info(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} DETECTED!) (simulated)")
        else: self._logger.debug(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} not found) (simulated)")
    def log_technical_analysis(self, pair: str, indicators: dict): self._logger.info(f"SIM_LOG: TA ({pair}) (simulated) {indicators}")
    def log_signal_generated(self, signal_data: dict): self._logger.info(f"SIM_LOG: Signal generated ({signal_data['pair']} - {signal_data['direction']}) (simulated)")
    def log_signal_filtered(self, pair: str, reason: str, details: dict = None): self._logger.info(f"SIM_LOG: Signal filtered ({pair} - {reason}) (simulated) {details}")
    def log_telegram_notification(self, success: bool, pair: str, attempt: int = 1):
         if success: self._logger.info(f"SIM_LOG: Telegram notification sent ({pair}) (simulated)")
         else: self._logger.warning(f"SIM_LOG: Telegram notification failed ({pair} - attempt {attempt}) (simulated)")
    def log_error(self, component: str, error_msg: str, pair: str = ""): self._logger.error(f"SIM_LOG: ERROR in {component} - {pair}{error_msg}")
    def log_session_stats(self): self._logger.info("SIM_LOG: Session stats (simulated)")

    @property
    def main_logger(self): return self._logger
    @property
    def data_logger(self): return self._logger
    @property
    def signal_logger(self): return self._logger
    @property
    def websocket_logger(self): return self._logger
    @property
    def pattern_logger(self): return self._logger
    @property
    def telegram_logger(self): return self._logger

    def get_trading_session(self) -> str: return "Simulated Session"
    def get_wib_time_string(self) -> str: return "Simulated WIB Time"
    def is_good_trading_time(self) -> bool: return True # Needed by SignalProcessor simulation


# --- End Simulate TradingLogger ---


# --- Simulate Imports from other files needed by DataManager and WebSocketManager ---
from dataclasses import dataclass
from datetime import datetime, timedelta # timedelta needed by TimeUtils
import numpy as np # Needed by TechnicalAnalyzer
import requests # Needed by NotificationService
import json # Needed by NotificationService

@dataclass
class CandleData:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    @property
    def body_size(self) -> float: return abs(self.close - self.open)
    @property
    def upper_wick(self) -> float: return self.high - max(self.open, self.close)
    @property
    def lower_wick(self) -> float: return min(self.open, self.close) - self.low

@dataclass
class TradingConfig: # Needed by ConfigManager simulation
    min_strength: float
    volume_multiplier: float
    rsi_oversold: int
    rsi_overbought: int
    min_risk_reward: float
    priority: int
    max_daily_signals: int


@dataclass
class SignalData: # Needed by SignalProcessor and NotificationService simulation
    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    strength: float
    risk_reward: float
    timestamp: datetime

class SignalType: # Needed by SignalProcessor simulation
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    BUY = "BUY"
    SELL = "SELL"

class ConfigManager: # Needed by DataManager, WebSocketManager, SignalProcessor, NotificationService simulations
    TIER1_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT'
    ]
    TIMEFRAME = '15m'
    MIN_VOLUME_USDT = 500000
    TELEGRAM_TOKEN = 'ISI_TOKEN_KAMU'
    TELEGRAM_CHAT_ID = 'ISI_CHAT_ID_KAMU'
    SIGNAL_COOLDOWN_MINUTES = 30 # Needed by SignalProcessor simulation
    CONFIGS = { # Dummy config needed by get_config
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
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])


class TimeUtils: # Needed by SignalProcessor simulation
    WIB_OFFSET = 7
    @classmethod
    def get_wib_hour(cls) -> int: return (datetime.utcnow().hour + cls.WIB_OFFSET) % 24
    @classmethod
    def get_wib_time_string(cls) -> str: wib_time = datetime.utcnow() + timedelta(hours=cls.WIB_OFFSET); return wib_time.strftime('%H:%M:%S WIB')
    @classmethod
    def is_good_trading_time(cls) -> bool: hour = cls.get_wib_hour(); return (8 <= hour <= 12) or (15 <= hour <= 19) or (20 <= hour <= 23)
    @classmethod
    def get_trading_session(cls) -> str:
        hour = cls.get_wib_hour()
        if 8 <= hour <= 12: return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19: return "SORE (London Active)"
        elif 20 <= hour <= 23: return "MALAM (NY Prime)"
        elif 1 <= hour <= 7: return "DINI HARI (Low Volume)"
        else: return "TRANSISI"

class TechnicalAnalyzer: # Needed by SignalProcessor simulation
    def __init__(self, logger: Optional[TradingLogger] = None): self.logger = logger
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1: return 50.0
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    def find_support_resistance(self, candles: List[CandleData], lookback: int = 20) -> Tuple[List[float], List[float]]:
        if len(candles) < lookback * 2: return [], []
        highs = [c.high for c in candles[-lookback*2:]]
        lows = [c.low for c in candles[-lookback*2:]]
        resistance_levels = [h for i, h in enumerate(highs) if i >= lookback and i < len(highs) - lookback and h == max(highs[i-lookback:i+lookback+1])]
        support_levels = [l for i, l in enumerate(lows) if i >= lookback and i < len(lows) - lookback and l == min(lows[i-lookback:i+lookback+1])]
        return (sorted(list(set(support_levels)))[:5], sorted(list(set(resistance_levels)), reverse=True)[:5])

class PatternDetector: # Needed by SignalProcessor simulation
    def __init__(self, analyzer: TechnicalAnalyzer, logger: Optional[TradingLogger] = None):
        self.analyzer = analyzer
        self.logger = logger
    def detect_sweep(self, candles: List[CandleData], pair: str) -> Tuple[bool, Optional[str]]: return False, None # Simulated
    def detect_engulfing(self, candles: List[CandleData], direction: str) -> bool: return False # Simulated
    def _get_higher_timeframe_trend(self, pair: str) -> str: return "NEUTRAL" # Simulated


# Simulate EnhancedSignalProcessor (needs TechnicalAnalyzer, PatternDetector, defaultdict, threading, logging, List, Optional, Tuple, CandleData, SignalData, TimeUtils, ConfigManager, SignalType, TradingLogger)
class EnhancedSignalProcessor:
    def __init__(self, analyzer: TechnicalAnalyzer, detector: PatternDetector, logger: TradingLogger):
        self.analyzer = analyzer
        self.detector = detector
        self.logger = logger
        self.daily_signal_count = defaultdict(int)
        self.last_signals = {}
        self.processing_lock = threading.Lock()
    def calculate_strength(self, candles: List[CandleData], pair: str) -> float: return 3.0 # Simulated
    def calculate_risk_reward(self, entry_price: float, direction: str, candles: List[CandleData]) -> Tuple[float, float, float]: return 1.5, entry_price*0.98, entry_price*1.02 # Simulated
    def process_signal(self, pair: str, candle: CandleData, candle_history: List[CandleData]) -> Optional[SignalData]:
        # Minimal simulation for process_signal to avoid errors when called
        if self.logger: self.logger.log_signal_analysis_start(pair, candle.close)
        # Simulate some checks and potentially return a dummy signal
        if len(candle_history) > 50: # Arbitrary condition to simulate a signal
             dummy_signal = SignalData(pair=pair, direction=SignalType.BUY, entry_price=candle.close, stop_loss=candle.close*0.98, take_profit=candle.close*1.04, strength=4.0, risk_reward=2.0, timestamp=datetime.utcnow())
             if self.logger: self.logger.log_signal_generated(dummy_signal.__dict__) # Log generated signal
             return dummy_signal
        else:
             if self.logger: self.logger.log_signal_filtered(pair, "Simulated filter condition") # Log filtered signal
             return None


# Simulate NotificationService (needs SignalData, ConfigManager, TimeUtils, logging, requests, json, time, SignalType, TradingLogger)
class NotificationService:
    def __init__(self, logger: TradingLogger):
        self.logger = logger
        self.token = 'ISI_TOKEN_KAMU'
        self.chat_id = 'ISI_CHAT_ID_KAMU'
    def send_signal(self, signal: SignalData) -> bool:
        # Simulate sending, log with logger
        if self.logger: self.logger.log_telegram_notification(True, signal.pair)
        return True # Simulate success


# --- End Simulate Imports ---


# ========== DATA MANAGER ==========
class DataManager:
    """Manage market data storage and retrieval"""

    # Add logger parameter
    def __init__(self, maxlen: int = 200, logger: Optional[TradingLogger] = None):
        self.logger = logger # Store logger
        self.live_data = defaultdict(lambda: deque(maxlen=maxlen))
        # Use try-except for ccxt initialization in case of environment issues
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'},
            })
        except Exception as e:
            # Use logger for errors, fallback to standard logging if logger is None
            if self.logger: self.logger.log_error("DataManager", f"Failed to initialize ccxt: {e}. Data fetching will be simulated.")
            else: logging.error(f"Failed to initialize ccxt: {e}. Data fetching will be simulated.")
            self.exchange = None # Use None if initialization fails


    def add_candle(self, pair: str, candle: CandleData):
        """Add new candle data"""
        self.live_data[pair].append(candle)

    def get_candles(self, pair: str) -> List[CandleData]:
        """Get candle history for pair"""
        return list(self.live_data[pair])

    def initialize_data(self):
        """Load initial historical data with logging"""
        # Use logger for info messages, fallback to standard logging if logger is None
        if self.logger: self.logger.data_logger.info("Loading historical data...")
        else: logging.info("Loading historical data...")

        if not self.exchange:
             # Use logger for warnings, fallback if logger is None
             if self.logger: self.logger.data_logger.warning("ccxt not initialized. Simulating data loading.")
             else: logging.warning("ccxt not initialized. Simulating data loading.")
             # Simulate adding some dummy data if ccxt failed
             for pair in ConfigManager.TIER1_PAIRS:
                 dummy_candle = CandleData(timestamp=int(time.time() * 1000), open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0)
                 for _ in range(100): # Add 100 dummy candles
                     self.add_candle(pair, dummy_candle)
                 # Use logger for data initialization success, fallback if logger is None
                 if self.logger: self.logger.log_data_initialization(pair, 100)
                 else: logging.info(f"✅ {pair}: 100 simulated candles loaded")
             return


        for pair in ConfigManager.TIER1_PAIRS:
            try:
                ccxt_pair = pair.replace('USDT', '/USDT')
                # Add timeout to fetch_ohlcv call
                ohlcv = self.exchange.fetch_ohlcv(ccxt_pair, ConfigManager.TIMEFRAME, limit=100, params={'recvWindow': 5000})

                for candle in ohlcv:
                    candle_data = CandleData(
                        timestamp=candle[0],
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5])
                    )
                    self.add_candle(pair, candle_data)

                # Use logger for data initialization success, fallback if logger is None
                if self.logger: self.logger.log_data_initialization(pair, len(ohlcv))
                else: logging.info(f"✅ {pair}: {len(ohlcv)} candles loaded")
                time.sleep(0.1) # Use actual time module

            except Exception as e:
                # Use logger for errors, fallback if logger is None
                if self.logger: self.logger.log_error("DataManager", f"Error loading data: {e}", pair=pair)
                else: logging.error(f"Error loading data for {pair}: {e}. Simulating data for this pair.")
                # Simulate adding some dummy data for the failed pair
                dummy_candle = CandleData(timestamp=int(time.time() * 1000), open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0)
                for _ in range(100):
                    self.add_candle(pair, dummy_candle)
                # Use logger for simulated data loading after error, fallback if logger is None
                if self.logger: self.logger.data_logger.info(f"✅ {pair}: 100 simulated candles loaded after error")
                else: logging.info(f"✅ {pair}: 100 simulated candles loaded after error")


# ========== WEBSOCKET MANAGER ==========
class WebSocketManager:
    """Handle WebSocket connections and data streaming"""

    # Add logger parameter
    def __init__(self, data_manager: DataManager, signal_processor: EnhancedSignalProcessor,
                 notification_service: NotificationService, logger: Optional[TradingLogger] = None):
        self.data_manager = data_manager
        self.signal_processor = signal_processor
        self.notification_service = notification_service
        self.logger = logger # Store logger
        self.is_running = True
        self.ws = None
        self.ws_thread = None # Keep track of the thread

    def start(self):
        """Start WebSocket connection"""
        # Run the WebSocket connection in a separate thread to avoid blocking
        self.ws_thread = threading.Thread(target=self._connect)
        self.ws_thread.start()


    def stop(self):
        """Stop WebSocket connection"""
        self.is_running = False
        if self.ws:
            # Use logger for info messages, fallback if logger is None
            if self.logger: self.logger.websocket_logger.info("Stopping WebSocket connection...")
            else: logging.info("Stopping WebSocket connection...")
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
             # Use logger for info messages, fallback if logger is None
             if self.logger: self.logger.websocket_logger.info("Joining WebSocket thread...")
             else: logging.info("Joining WebSocket thread...")
             self.ws_thread.join(timeout=5)
             if self.ws_thread.is_alive():
                 # Use logger for warnings, fallback if logger is None
                 if self.logger: self.logger.websocket_logger.warning("WebSocket thread did not terminate cleanly.")
                 else: logging.warning("WebSocket thread did not terminate cleanly.")


    def _connect(self):
        """Establish WebSocket connection with logging"""
        try:
            # Use fstream for futures
            ws_url = "wss://fstream.binance.com/ws"

            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            # run_forever will block, so it's called in a separate thread
            self.ws.run_forever(
                ping_interval=30,  # Send a ping every 30 seconds
                ping_timeout=10,   # Timeout if pong is not received within 10 seconds
                sslopt={"cert_reqs": ssl.CERT_NONE} # Add sslopt for potential cert issues
            )

        except Exception as e:
            # Use logger for errors, fallback if logger is None
            if self.logger: self.logger.log_error("WebSocketManager", f"Connection error in thread: {e}")
            else: logging.error(f"WebSocket connection error in thread: {e}")
            if self.is_running:
                # Use logger for reconnection attempt, fallback if logger is None
                if self.logger: self.logger.log_websocket_connection("RECONNECTING")
                else: logging.info("Attempting to reconnect in 5 seconds...")
                time.sleep(5)
                self._connect() # Recursive call to reconnect

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages with logging"""
        try:
            data = json.loads(message)

            # Handle different message types (e.g., subscription confirmation)
            if 'result' in data or 'id' in data:
                 # Use logger for info messages, fallback if logger is None
                 if self.logger: self.logger.websocket_logger.info(f"WebSocket message: {data}")
                 else: logging.info(f"WebSocket message: {data}")
                 return

            if 'e' in data and data['e'] == 'kline' and 'k' in data:
                kline = data['k']
                pair = kline['s']

                # Only process closed candles
                if kline['x']:  # Candle closed (x = true)
                    candle_data = CandleData(
                        timestamp=int(kline['t']),
                        open=float(kline['o']),
                        high=float(kline['h']),
                        low=float(kline['l']),
                        close=float(kline['c']),
                        volume=float(kline['v'])
                    )
                    # Log incoming candle data using the logger
                    if self.logger: self.logger.log_candle_received(pair, kline)
                    # Process the candle in a separate thread to avoid blocking the WebSocket thread
                    threading.Thread(target=self._process_candle, args=(pair, candle_data)).start()


        except Exception as e:
            # Log the message content if parsing fails for debugging
            # Use logger for errors, fallback if logger is None
            if self.logger: self.logger.log_error("WebSocketManager", f"Message processing error: {e}. Message: {message[:200]}...")
            else: logging.error(f"WebSocket message processing error: {e}. Message: {message[:200]}...")


    def _process_candle(self, pair: str, candle: CandleData):
        """Process new candle data (intended to run in a thread) with logging"""
        try:
            # Add to data manager (DataManager handles its own logging)
            self.data_manager.add_candle(pair, candle)

            # Get candle history
            candle_history = self.data_manager.get_candles(pair)

            # Ensure enough history is available before processing signal
            if len(candle_history) < 30: # Minimum history length for TA/patterns
                # Optionally log that not enough history is available
                if self.logger: self.logger.websocket_logger.debug(f"📈 {pair}: Not enough history ({len(candle_history)}) to process signal.")
                return

            # Process signal - SignalProcessor handles its own logging
            signal = self.signal_processor.process_signal(pair, candle, candle_history)

            if signal:
                # Send notification - NotificationService handles its own logging
                if self.notification_service.send_signal(signal):
                    pass # Logging is done within NotificationService
                else:
                     # Use logger for warnings if sending fails after retries, fallback if logger is None
                     if self.logger: self.logger.telegram_logger.warning(f"Failed to send signal notification for {pair} after retries.")
                     else: logging.warning(f"Failed to send signal notification for {pair} after retries.")


        except Exception as e:
            # Log errors during candle processing
            # Use logger for errors, fallback if logger is None
            if self.logger: self.logger.log_error("WebSocketManager", f"Error processing candle: {e}", pair=pair)
            else: logging.error(f"Error processing candle for {pair} in thread: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket errors with logging"""
        # Check if the error is just None or an empty string, which can happen on clean close
        if error is not None and str(error).strip() != '':
            # Use logger to indicate a WebSocket error occurred
            if self.logger: self.logger.log_websocket_connection("ERROR")
            else: logging.error(f"WebSocket error: {error}")


    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close events with logging"""
        # Use logger for info messages, fallback if logger is None
        if self.logger: self.logger.websocket_logger.info(f"WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")
        else: logging.info(f"WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")

        if self.is_running:
            # Use logger for reconnection attempt, fallback if logger is None
            if self.logger: self.logger.log_websocket_connection("RECONNECTING")
            else: logging.info("Reconnecting in 5 seconds...")
            time.sleep(5)
            self._connect() # Recursive call to reconnect

    def _on_open(self, ws):
        """Handle WebSocket open events with logging"""
        # Use logger to indicate successful connection
        if self.logger: self.logger.log_websocket_connection("CONNECTED")
        else: logging.info("WebSocket connected!")

        streams = [f"{pair.lower()}@kline_{ConfigManager.TIMEFRAME}" for pair in ConfigManager.TIER1_PAIRS]
        subscribe_message = {"method": "SUBSCRIBE", "params": streams, "id": 1}

        try:
            ws.send(json.dumps(subscribe_message))
            # Use logger to confirm subscription
            if self.logger: self.logger.log_websocket_connection("CONNECTED", len(streams)) # Re-log connected status with stream count
            else: logging.info(f"Subscribed to {len(streams)} streams")
        except Exception as e:
            # Use logger for errors, fallback if logger is None
            if self.logger: self.logger.log_error("WebSocketManager", f"Failed to send subscription message: {e}")
            else: logging.error(f"Failed to send subscription message: {e}")