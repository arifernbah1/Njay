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

import logging

# ========== DATA MANAGER ==========
class DataManager:
    """Manage market data storage and retrieval"""

    def __init__(self, maxlen: int = 200, logger: Optional['TradingLogger'] = None):
        self.logger = logger
        self.live_data = defaultdict(lambda: deque(maxlen=maxlen))
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'},
            })
        except Exception as e:
            if self.logger: 
                self.logger.log_error("DataManager", "Failed to initialize ccxt: {}. Data fetching will be simulated.".format(e))
            else: 
                logging.error("Failed to initialize ccxt: {}. Data fetching will be simulated.".format(e))
            self.exchange = None

    def add_candle(self, pair: str, candle: CandleData):
        """Add new candle data"""
        self.live_data[pair].append(candle)

    def get_candles(self, pair: str) -> List[CandleData]:
        """Get candle history for pair"""
        return list(self.live_data[pair])

    def initialize_data(self):
        """Load initial historical data with logging"""
        if self.logger: 
            self.logger.data_logger.info("Loading historical data...")
        else: 
            logging.info("Loading historical data...")

        if not self.exchange:
            # Use logger for warnings, fallback if logger is None
            if self.logger:
                self.logger.data_logger.warning("ccxt not initialized. Loading realistic simulated data.")
            else:
                logging.warning("ccxt not initialized. Loading realistic simulated data.")
            
            # Simulate adding realistic data if ccxt failed
            for pair in ConfigManager.TIER1_PAIRS:
                # Generate realistic price data based on typical crypto prices
                base_price = 100.0
                if pair == 'BTCUSDT':
                    base_price = 50000.0
                elif pair == 'ETHUSDT':
                    base_price = 3000.0
                elif pair == 'BNBUSDT':
                    base_price = 300.0
                elif pair == 'SOLUSDT':
                    base_price = 100.0
                elif pair == 'ADAUSDT':
                    base_price = 0.5
                elif pair == 'AVAXUSDT':
                    base_price = 25.0
                elif pair == 'MATICUSDT':
                    base_price = 0.8
                elif pair == 'DOTUSDT':
                    base_price = 7.0
                
                # Generate 100 realistic candles with some variation
                for i in range(100):
                    # Simulate price movement
                    price_change = (i % 20 - 10) * 0.01  # Oscillating pattern
                    current_price = base_price * (1 + price_change)
                    
                    # Create realistic candle
                    open_price = current_price * (1 + (i % 5 - 2) * 0.005)
                    close_price = current_price * (1 + (i % 7 - 3) * 0.005)
                    high_price = max(open_price, close_price) * (1 + 0.01)
                    low_price = min(open_price, close_price) * (1 - 0.01)
                    volume = base_price * 1000 * (1 + (i % 10) * 0.1)  # Realistic volume
                    
                    realistic_candle = CandleData(
                        timestamp=int(time.time() * 1000) - (100 - i) * 15 * 60 * 1000,  # 15m intervals
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume
                    )
                    self.add_candle(pair, realistic_candle)
                
                # Use logger for data initialization success, fallback if logger is None
                if self.logger:
                    self.logger.log_data_initialization(pair, 100)
                else:
                    logging.info("✅ {}: 100 realistic simulated candles loaded".format(pair))
            return

        for pair in ConfigManager.TIER1_PAIRS:
            try:
                ccxt_pair = ConfigManager.get_binance_symbol(pair)
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

                if self.logger: 
                    self.logger.log_data_initialization(pair, len(ohlcv))
                else: 
                    logging.info("✅ {}: {} candles loaded".format(pair, len(ohlcv)))
                time.sleep(0.1)

            except Exception as e:
                # Use logger for errors, fallback if logger is None
                if self.logger:
                    self.logger.log_error("DataManager", "Error loading data: {}".format(e), pair=pair)
                else:
                    logging.error("Error loading data for {}: {}. Loading realistic simulated data for this pair.".format(pair, e))
                
                # Generate realistic simulated data for the failed pair
                base_price = 100.0
                if pair == 'BTCUSDT':
                    base_price = 50000.0
                elif pair == 'ETHUSDT':
                    base_price = 3000.0
                elif pair == 'BNBUSDT':
                    base_price = 300.0
                elif pair == 'SOLUSDT':
                    base_price = 100.0
                elif pair == 'ADAUSDT':
                    base_price = 0.5
                elif pair == 'AVAXUSDT':
                    base_price = 25.0
                elif pair == 'MATICUSDT':
                    base_price = 0.8
                elif pair == 'DOTUSDT':
                    base_price = 7.0
                
                # Generate 100 realistic candles with some variation
                for i in range(100):
                    # Simulate price movement
                    price_change = (i % 20 - 10) * 0.01  # Oscillating pattern
                    current_price = base_price * (1 + price_change)
                    
                    # Create realistic candle
                    open_price = current_price * (1 + (i % 5 - 2) * 0.005)
                    close_price = current_price * (1 + (i % 7 - 3) * 0.005)
                    high_price = max(open_price, close_price) * (1 + 0.01)
                    low_price = min(open_price, close_price) * (1 - 0.01)
                    volume = base_price * 1000 * (1 + (i % 10) * 0.1)  # Realistic volume
                    
                    realistic_candle = CandleData(
                        timestamp=int(time.time() * 1000) - (100 - i) * 15 * 60 * 1000,  # 15m intervals
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume
                    )
                    self.add_candle(pair, realistic_candle)
                
                # Use logger for simulated data loading after error, fallback if logger is None
                if self.logger:
                    self.logger.data_logger.info("✅ {}: 100 realistic simulated candles loaded after error".format(pair))
                else:
                    logging.info("✅ {}: 100 realistic simulated candles loaded after error".format(pair))


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
        self.ws_thread = threading.Thread(target=self._connect)
        self.ws_thread.start()

    def stop(self):
        """Stop WebSocket connection"""
        self.is_running = False
        if self.ws:
            if self.logger: 
                self.logger.websocket_logger.info("Stopping WebSocket connection...")
            else: 
                logging.info("Stopping WebSocket connection...")
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
            if self.logger: 
                self.logger.websocket_logger.info("Joining WebSocket thread...")
            else: 
                logging.info("Joining WebSocket thread...")
            self.ws_thread.join(timeout=5)
            if self.ws_thread.is_alive():
                if self.logger: 
                    self.logger.websocket_logger.warning("WebSocket thread did not terminate cleanly.")
                else: 
                    logging.warning("WebSocket thread did not terminate cleanly.")

    def _connect(self):
        """Establish WebSocket connection with logging"""
        try:
            ws_url = "wss://fstream.binance.com/ws"

            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            self.ws.run_forever(
                ping_interval=30,
                ping_timeout=10,
                sslopt={"cert_reqs": ssl.CERT_NONE}
            )

        except Exception as e:
            if self.logger: 
                self.logger.log_error("WebSocketManager", "Connection error in thread: {}".format(e))
            else: 
                logging.error("WebSocket connection error in thread: {}".format(e))
            if self.is_running:
                if self.logger: 
                    self.logger.log_websocket_connection("RECONNECTING")
                else: 
                    logging.info("Attempting to reconnect in 5 seconds...")
                time.sleep(5)
                self._connect()

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages with logging"""
        try:
            data = json.loads(message)

            if 'result' in data or 'id' in data:
                if self.logger: 
                    self.logger.websocket_logger.info("WebSocket message: {}".format(data))
                else: 
                    logging.info("WebSocket message: {}".format(data))
                return

            if 'e' in data and data['e'] == 'kline' and 'k' in data:
                kline = data['k']
                pair = kline['s']

                if kline['x']:  # Candle closed (x = true)
                    candle_data = CandleData(
                        timestamp=int(kline['t']),
                        open=float(kline['o']),
                        high=float(kline['h']),
                        low=float(kline['l']),
                        close=float(kline['c']),
                        volume=float(kline['v'])
                    )
                    if self.logger: 
                        self.logger.log_candle_received(pair, kline)
                    threading.Thread(target=self._process_candle, args=(pair, candle_data)).start()

        except Exception as e:
            if self.logger: 
                self.logger.log_error("WebSocketManager", "Message processing error: {}. Message: {}...".format(e, str(message)[:200]))
            else: 
                logging.error("WebSocket message processing error: {}. Message: {}...".format(e, str(message)[:200]))

    def _process_candle(self, pair: str, candle: CandleData):
        """Process new candle data (intended to run in a thread) with logging"""
        try:
            self.data_manager.add_candle(pair, candle)
            candle_history = self.data_manager.get_candles(pair)

            if len(candle_history) < 30:
                if self.logger: 
                    self.logger.websocket_logger.debug("📈 {}: Not enough history ({}) to process signal.".format(pair, len(candle_history)))
                return

            signal = self.signal_processor.process_signal(pair, candle, candle_history)

            if signal:
                if self.notification_service.send_signal(signal):
                    pass
                else:
                    if self.logger: 
                        self.logger.telegram_logger.warning("Failed to send signal notification for {} after retries.".format(pair))
                    else: 
                        logging.warning("Failed to send signal notification for {} after retries.".format(pair))

        except Exception as e:
            if self.logger: 
                self.logger.log_error("WebSocketManager", "Error processing candle: {}".format(e), pair=pair)
            else: 
                logging.error("Error processing candle for {} in thread: {}".format(pair, e))

    def _on_error(self, ws, error):
        """Handle WebSocket errors with logging"""
        if error is not None and str(error).strip() != '':
            if self.logger: 
                self.logger.log_websocket_connection("ERROR")
            else: 
                logging.error("WebSocket error: {}".format(error))

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close events with logging"""
        if self.logger: 
            self.logger.websocket_logger.info("WebSocket connection closed. Code: {}, Message: {}".format(close_status_code, close_msg))
        else: 
            logging.info("WebSocket connection closed. Code: {}, Message: {}".format(close_status_code, close_msg))

        if self.is_running:
            if self.logger: 
                self.logger.log_websocket_connection("RECONNECTING")
            else: 
                logging.info("Reconnecting in 5 seconds...")
            time.sleep(5)
            self._connect()

    def _on_open(self, ws):
        """Handle WebSocket open events with logging"""
        if self.logger: 
            self.logger.log_websocket_connection("CONNECTED")
        else: 
            logging.info("WebSocket connected!")

        streams = ["{}@kline_{}".format(pair.lower(), ConfigManager.TIMEFRAME) for pair in ConfigManager.TIER1_PAIRS]
        subscribe_message = {"method": "SUBSCRIBE", "params": streams, "id": 1}

        try:
            ws.send(json.dumps(subscribe_message))
            if self.logger: 
                self.logger.log_websocket_connection("CONNECTED", len(streams))
            else: 
                logging.info("Subscribed to {} streams".format(len(streams)))
        except Exception as e:
            if self.logger: 
                self.logger.log_error("WebSocketManager", "Failed to send subscription message: {}".format(e))
            else: 
                logging.error("Failed to send subscription message: {}".format(e))