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
from trading_logger import TradingLogger

import logging

# ========== DATA MANAGER ==========
class DataManager:
    """Manage market data storage and retrieval for dual mode"""
    # Add logger parameter
    def __init__(self, maxlen: int = 200, logger: Optional[TradingLogger] = None):
        self.logger = logger # Store logger
        # Separate data storage for each mode
        self.live_data_scalping = defaultdict(lambda: deque(maxlen=maxlen))  # 15m data
        self.live_data_swing = defaultdict(lambda: deque(maxlen=maxlen))     # 1h data
        
        # Use try-except for ccxt initialization in case of environment issues
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'},
            })
        except Exception as e:
            # Use logger for errors, fallback to standard logging if logger is None
            if self.logger:
                self.logger.log_error("DataManager", "Failed to initialize ccxt: {}. Data fetching will be simulated.".format(e))
            else:
                logging.error("Failed to initialize ccxt: {}. Data fetching will be simulated.".format(e))
            self.exchange = None # Use None if initialization fails

    def add_candle(self, pair: str, candle: CandleData, mode: str = "SCALPING"):
        """Add new candle data for specific mode"""
        if mode == "SCALPING":
            self.live_data_scalping[pair].append(candle)
        else:
            self.live_data_swing[pair].append(candle)

    def get_candles(self, pair: str, mode: str = "SCALPING") -> List[CandleData]:
        """Get candle history for pair and mode"""
        if mode == "SCALPING":
            return list(self.live_data_scalping[pair])
        else:
            return list(self.live_data_swing[pair])

    def initialize_data(self):
        """Load initial historical data for both modes with logging"""
        # Use logger for info messages, fallback to standard logging if logger is None
        if self.logger:
            self.logger.data_logger.info("Loading historical data for dual mode...")
        else:
            logging.info("Loading historical data for dual mode...")

        if not self.exchange:
            # Use logger for warnings, fallback if logger is None
            if self.logger:
                self.logger.data_logger.warning("ccxt not initialized. Simulating data loading for dual mode.")
            else:
                logging.warning("ccxt not initialized. Simulating data loading for dual mode.")
            
            # Simulate adding some dummy data if ccxt failed for both modes
            for pair in ConfigManager.TIER1_PAIRS:
                # Scalping mode data (5m)
                for _ in range(100):
                    dummy_candle_scalping = CandleData(
                        timestamp=int(time.time() * 1000), 
                        open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0
                    )
                    self.add_candle(pair, dummy_candle_scalping, "SCALPING")
                
                # Swing mode data (1h)
                for _ in range(100):
                    dummy_candle_swing = CandleData(
                        timestamp=int(time.time() * 1000), 
                        open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0
                    )
                    self.add_candle(pair, dummy_candle_swing, "SWING")
                
                # Use logger for data initialization success, fallback if logger is None
                if self.logger:
                    self.logger.log_data_initialization(pair, 200)  # 100 for each mode
                else:
                    logging.info("✅ {}: 200 simulated candles loaded (100 scalping + 100 swing)".format(pair))
            return

        # Load real data for both modes
        for pair in ConfigManager.TIER1_PAIRS:
            try:
                ccxt_pair = ConfigManager.get_binance_symbol(pair)
                
                # Load Scalping data (5m)
                ohlcv_scalping = self.exchange.fetch_ohlcv(
                    ccxt_pair, 
                    ConfigManager.get_mode_config("SCALPING")['timeframe'], 
                    limit=100, 
                    params={'recvWindow': 5000}
                )
                for candle in ohlcv_scalping:
                    candle_data = CandleData(
                        timestamp=candle[0],
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5])
                    )
                    self.add_candle(pair, candle_data, "SCALPING")
                
                # Load Swing data (1h)
                ohlcv_swing = self.exchange.fetch_ohlcv(
                    ccxt_pair, 
                    ConfigManager.get_mode_config("SWING")['timeframe'], 
                    limit=100, 
                    params={'recvWindow': 5000}
                )
                for candle in ohlcv_swing:
                    candle_data = CandleData(
                        timestamp=candle[0],
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5])
                    )
                    self.add_candle(pair, candle_data, "SWING")
                
                # Use logger for data initialization success, fallback if logger is None
                if self.logger:
                    self.logger.log_data_initialization(pair, len(ohlcv_scalping) + len(ohlcv_swing))
                else:
                    logging.info("✅ {}: {} candles loaded ({} scalping + {} swing)".format(
                        pair, len(ohlcv_scalping) + len(ohlcv_swing), 
                        len(ohlcv_scalping), len(ohlcv_swing)
                    ))
                
                time.sleep(0.1) # Use actual time module
                
            except Exception as e:
                # Use logger for errors, fallback if logger is None
                if self.logger:
                    self.logger.log_error("DataManager", "Error loading data: {}".format(e), pair=pair)
                else:
                    logging.error("Error loading data for {}: {}. Simulating data for this pair.".format(pair, e))
                
                # Simulate adding some dummy data for the failed pair
                for _ in range(100):
                    dummy_candle = CandleData(
                        timestamp=int(time.time() * 1000), 
                        open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0
                    )
                    self.add_candle(pair, dummy_candle, "SCALPING")
                    self.add_candle(pair, dummy_candle, "SWING")
                
                # Use logger for simulated data loading after error, fallback if logger is None
                if self.logger:
                    self.logger.data_logger.info("✅ {}: 200 simulated candles loaded after error (100 scalping + 100 swing)".format(pair))
                else:
                    logging.info("✅ {}: 200 simulated candles loaded after error (100 scalping + 100 swing)".format(pair))


# ========== WEBSOCKET MANAGER ==========
class WebSocketManager:
    """Handle WebSocket connections and data streaming for dual mode"""
    # Add logger parameter
    def __init__(self, data_manager: DataManager, signal_processor: EnhancedSignalProcessor, notification_service: NotificationService, logger: Optional[TradingLogger] = None):
        self.data_manager = data_manager
        self.signal_processor = signal_processor
        self.notification_service = notification_service
        self.logger = logger # Store logger
        self.is_running = True
        self.ws_scalping = None  # WebSocket for 5m data
        self.ws_swing = None     # WebSocket for 1h data
        self.ws_scalping_thread = None
        self.ws_swing_thread = None

    def start(self):
        """Start WebSocket connections for both modes"""
        # Start Scalping WebSocket (5m)
        self.ws_scalping_thread = threading.Thread(target=self._connect_scalping)
        self.ws_scalping_thread.start()
        
        # Start Swing WebSocket (1h)
        self.ws_swing_thread = threading.Thread(target=self._connect_swing)
        self.ws_swing_thread.start()

    def stop(self):
        """Stop WebSocket connections"""
        self.is_running = False
        
        if self.ws_scalping:
            if self.logger:
                self.logger.websocket_logger.info("Stopping Scalping WebSocket connection...")
            else:
                logging.info("Stopping Scalping WebSocket connection...")
            self.ws_scalping.close()
            
        if self.ws_swing:
            if self.logger:
                self.logger.websocket_logger.info("Stopping Swing WebSocket connection...")
            else:
                logging.info("Stopping Swing WebSocket connection...")
            self.ws_swing.close()
            
        # Join threads
        for thread_name, thread in [("Scalping", self.ws_scalping_thread), ("Swing", self.ws_swing_thread)]:
            if thread and thread.is_alive():
                if self.logger:
                    self.logger.websocket_logger.info("Joining {} WebSocket thread...".format(thread_name))
                else:
                    logging.info("Joining {} WebSocket thread...".format(thread_name))
                thread.join(timeout=5)
                if thread.is_alive():
                    if self.logger:
                        self.logger.websocket_logger.warning("{} WebSocket thread did not terminate cleanly.".format(thread_name))
                    else:
                        logging.warning("{} WebSocket thread did not terminate cleanly.".format(thread_name))

    def _connect_scalping(self):
        """Establish WebSocket connection for Scalping mode (15m)"""
        try:
            ws_url = "wss://fstream.binance.com/ws"
            self.ws_scalping = websocket.WebSocketApp(
                ws_url,
                on_message=lambda ws, msg: self._on_message_scalping(ws, msg),
                on_error=lambda ws, err: self._on_error(ws, err, "SCALPING"),
                on_close=lambda ws, code, msg: self._on_close(ws, code, msg, "SCALPING"),
                on_open=lambda ws: self._on_open_scalping(ws)
            )
            self.ws_scalping.run_forever(
                ping_interval=30,
                ping_timeout=10,
                sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        except Exception as e:
            if self.logger:
                self.logger.log_error("WebSocketManager", "Scalping connection error in thread: {}".format(e))
            else:
                logging.error("Scalping WebSocket connection error in thread: {}".format(e))
            if self.is_running:
                if self.logger:
                    self.logger.log_websocket_connection("RECONNECTING")
                else:
                    logging.info("Attempting to reconnect Scalping in 5 seconds...")
                time.sleep(5)
                self._connect_scalping()

    def _connect_swing(self):
        """Establish WebSocket connection for Swing mode (1h)"""
        try:
            ws_url = "wss://fstream.binance.com/ws"
            self.ws_swing = websocket.WebSocketApp(
                ws_url,
                on_message=lambda ws, msg: self._on_message_swing(ws, msg),
                on_error=lambda ws, err: self._on_error(ws, err, "SWING"),
                on_close=lambda ws, code, msg: self._on_close(ws, code, msg, "SWING"),
                on_open=lambda ws: self._on_open_swing(ws)
            )
            self.ws_swing.run_forever(
                ping_interval=30,
                ping_timeout=10,
                sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        except Exception as e:
            if self.logger:
                self.logger.log_error("WebSocketManager", "Swing connection error in thread: {}".format(e))
            else:
                logging.error("Swing WebSocket connection error in thread: {}".format(e))
            if self.is_running:
                if self.logger:
                    self.logger.log_websocket_connection("RECONNECTING")
                else:
                    logging.info("Attempting to reconnect Swing in 5 seconds...")
                time.sleep(5)
                self._connect_swing()

    def _on_message_scalping(self, ws, message):
        """Handle incoming WebSocket messages for Scalping mode"""
        self._process_message(message, "SCALPING")

    def _on_message_swing(self, ws, message):
        """Handle incoming WebSocket messages for Swing mode"""
        self._process_message(message, "SWING")

    def _process_message(self, message: str, mode: str):
        """Process WebSocket message for specific mode"""
        try:
            data = json.loads(message)
            
            # Handle different message types (e.g., subscription confirmation)
            if 'result' in data or 'id' in data:
                if self.logger:
                    self.logger.websocket_logger.info("WebSocket message ({}): {}".format(mode, data))
                else:
                    logging.info("WebSocket message ({}): {}".format(mode, data))
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
                    if self.logger:
                        self.logger.log_candle_received(pair, kline)
                    
                    # Process the candle in a separate thread to avoid blocking the WebSocket thread
                    threading.Thread(target=self._process_candle, args=(pair, candle_data, mode)).start()
                    
        except Exception as e:
            # Log the message content if parsing fails for debugging
            if self.logger:
                self.logger.log_error("WebSocketManager", "Message processing error ({}): {}. Message: {}...".format(mode, e, message[:200]))
            else:
                logging.error("WebSocket message processing error ({}): {}. Message: {}...".format(mode, e, message[:200]))

    def _process_candle(self, pair: str, candle: CandleData, mode: str):
        """Process new candle data for specific mode"""
        try:
            # Add to data manager
            self.data_manager.add_candle(pair, candle, mode)
            
            # Get candle history for this mode
            candle_history = self.data_manager.get_candles(pair, mode)
            
            # Ensure enough history is available before processing signal
            min_history = 30 if mode == "SCALPING" else 50  # Different requirements per mode
            if len(candle_history) < min_history:
                if self.logger:
                    self.logger.websocket_logger.debug("📈 {} ({}): Not enough history ({}) to process signal.".format(pair, mode, len(candle_history)))
                return
            
            # Process signal for this mode
            signal = self.signal_processor.process_signal(pair, candle, candle_history, mode)
            
            if signal:
                # Send notification
                if self.notification_service.send_signal(signal, mode):
                    pass  # Logging is done within NotificationService
                else:
                    if self.logger:
                        self.logger.telegram_logger.warning("Failed to send {} signal notification for {} after retries.".format(mode, pair))
                    else:
                        logging.warning("Failed to send {} signal notification for {} after retries.".format(mode, pair))
                        
        except Exception as e:
            if self.logger:
                self.logger.log_error("WebSocketManager", "Error processing {} candle: {}".format(mode, e), pair=pair)
            else:
                logging.error("Error processing {} candle for {} in thread: {}".format(mode, pair, e))

    def _on_error(self, ws, error, mode: str):
        """Handle WebSocket errors"""
        if error is not None and str(error).strip() != '':
            if self.logger:
                self.logger.log_websocket_connection("ERROR")
            else:
                logging.error("{} WebSocket error: {}".format(mode, error))

    def _on_close(self, ws, close_status_code, close_msg, mode: str):
        """Handle WebSocket close events"""
        if self.logger:
            self.logger.websocket_logger.info("{} WebSocket connection closed. Code: {}, Message: {}".format(mode, close_status_code, close_msg))
        else:
            logging.info("{} WebSocket connection closed. Code: {}, Message: {}".format(mode, close_status_code, close_msg))
        
        if self.is_running:
            if self.logger:
                self.logger.log_websocket_connection("RECONNECTING")
            else:
                logging.info("Reconnecting {} in 5 seconds...".format(mode))
            time.sleep(5)
            if mode == "SCALPING":
                self._connect_scalping()
            else:
                self._connect_swing()

    def _on_open_scalping(self, ws):
        """Handle WebSocket open events for Scalping mode"""
        if self.logger:
            self.logger.log_websocket_connection("CONNECTED")
        else:
            logging.info("Scalping WebSocket connected!")
        
        # Subscribe to 15m streams (changed from 5m)
        streams = ["{}@kline_15m".format(pair.lower()) for pair in ConfigManager.TIER1_PAIRS]
        subscribe_message = {"method": "SUBSCRIBE", "params": streams, "id": 1}
        
        try:
            ws.send(json.dumps(subscribe_message))
            if self.logger:
                self.logger.log_websocket_connection("CONNECTED", len(streams))
            else:
                logging.info("Subscribed to {} Scalping streams".format(len(streams)))
        except Exception as e:
            if self.logger:
                self.logger.log_error("WebSocketManager", "Failed to send Scalping subscription message: {}".format(e))
            else:
                logging.error("Failed to send Scalping subscription message: {}".format(e))

    def _on_open_swing(self, ws):
        """Handle WebSocket open events for Swing mode"""
        if self.logger:
            self.logger.log_websocket_connection("CONNECTED")
        else:
            logging.info("Swing WebSocket connected!")
        
        # Subscribe to 1h streams
        streams = ["{}@kline_1h".format(pair.lower()) for pair in ConfigManager.TIER1_PAIRS]
        subscribe_message = {"method": "SUBSCRIBE", "params": streams, "id": 2}
        
        try:
            ws.send(json.dumps(subscribe_message))
            if self.logger:
                self.logger.log_websocket_connection("CONNECTED", len(streams))
            else:
                logging.info("Subscribed to {} Swing streams".format(len(streams)))
        except Exception as e:
            if self.logger:
                self.logger.log_error("WebSocketManager", "Failed to send Swing subscription message: {}".format(e))
            else:
                logging.error("Failed to send Swing subscription message: {}".format(e))