# data_ws.py

import ccxt
import json
import time
import websocket
import threading
import sys
import ssl
from collections import deque, defaultdict
from typing import List, Optional, Tuple

# Import classes from other files
from models import CandleData, SignalData, SignalType
from utils import TimeUtils
from analysis import TechnicalAnalyzer, PatternDetector
from processor import SignalProcessor
from notifications import NotificationService
from config import ConfigManager

# ========== DATA MANAGER ==========
class DataManager:
    """Manage market data storage and retrieval"""

    def __init__(self, maxlen: int = 200, logger: Optional['TradingLogger'] = None):
        self.logger = logger
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
            self.exchange = None  # Use None if initialization fails

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
                for _ in range(100):  # Add 100 dummy candles
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
                time.sleep(0.1)  # Use actual time module

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

    def __init__(self, data_manager: DataManager, signal_processor: SignalProcessor,
                 notification_service: NotificationService, logger: Optional['TradingLogger'] = None):
        self.data_manager = data_manager
        self.signal_processor = signal_processor
        self.notification_service = notification_service
        self.logger = logger
        self.is_running = True
        self.ws = None
        self.ws_thread = None

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
                sslopt={"cert_reqs": ssl.CERT_NONE}  # Add sslopt for potential cert issues
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
                self._connect()  # Recursive call to reconnect

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
            if len(candle_history) < 30:  # Minimum history length for TA/patterns
                # Optionally log that not enough history is available
                if self.logger: self.logger.websocket_logger.debug(f"📈 {pair}: Not enough history ({len(candle_history)}) to process signal.")
                return

            # Process signal - SignalProcessor handles its own logging
            signal = self.signal_processor.process_signal(pair, candle, candle_history)

            if signal:
                # Send notification - NotificationService handles its own logging
                if self.notification_service.send_signal(signal):
                    pass  # Logging is done within NotificationService
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
            self._connect()  # Recursive call to reconnect

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
            if self.logger: self.logger.log_websocket_connection("CONNECTED", len(streams))  # Re-log connected status with stream count
            else: logging.info(f"Subscribed to {len(streams)} streams")
        except Exception as e:
            # Use logger for errors, fallback if logger is None
            if self.logger: self.logger.log_error("WebSocketManager", f"Failed to send subscription message: {e}")
            else: logging.error(f"Failed to send subscription message: {e}")