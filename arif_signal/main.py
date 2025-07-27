# main.py

# --- Import classes from other files ---
from arif_signal.data_manager import DataManager
from arif_signal.processor import SignalProcessor
from arif_signal.config import ConfigManager
from arif_signal.trading_logger import TradingLogger, TradingSignal
from arif_signal.models import SignalData, SignalType
from datetime import datetime
import time
import sys

class ArifSignalApp:
    """Main application class with Trading Logger integration"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.pairs = self.config.get_pairs()
        self.current_mode = "SCALPING"  # Default mode
        
        # Initialize specialized Trading Logger
        self.trading_logger = TradingLogger("trading_logs")
        
        # Initialize components with trading logger
        self.data_manager = DataManager(self.trading_logger)
        self.signal_processor = SignalProcessor(self.trading_logger)
        
        # Log system startup
        self.trading_logger.log_trading_alert(
            "SYSTEM_START", 
            "Arif Signal Trading System initialized",
            priority="HIGH"
        )
    
    def run(self):
        """Main application loop with Trading Logger integration"""
        self.trading_logger.log_trading_alert(
            "SYSTEM_START", 
            f"Starting Arif Signal System in {self.current_mode} mode",
            priority="HIGH"
        )
        
        while True:
            try:
                # Check for mode switch
                new_mode = self.check_mode_switch()
                if new_mode and new_mode != self.current_mode:
                    self.trading_logger.log_trading_alert(
                        "MODE_SWITCH",
                        f"Switching from {self.current_mode} to {new_mode}",
                        priority="MEDIUM"
                    )
                    self.current_mode = new_mode
                
                # Process signals for current mode
                signals = self.process_signals_for_mode(self.current_mode)
                
                # Log performance summary
                if signals:
                    self.trading_logger.log_performance_summary(self.current_mode)
                
                # Sleep based on mode
                if self.current_mode == "SCALPING":
                    time.sleep(15)  # 15 seconds for scalping
                else:
                    time.sleep(60)  # 1 minute for swing
                    
            except KeyboardInterrupt:
                self.trading_logger.log_trading_alert(
                    "SYSTEM_SHUTDOWN",
                    "Shutting down gracefully",
                    priority="HIGH"
                )
                break
            except Exception as e:
                self.trading_logger.log_trading_alert(
                    "ERROR",
                    f"Error in main loop: {str(e)}",
                    priority="CRITICAL"
                )
                time.sleep(30)
    
    def check_mode_switch(self) -> str:
        """Check if mode should be switched based on market conditions"""
        try:
            # Simple market condition check (can be enhanced)
            current_hour = datetime.now().hour
            
            # Scalping mode during active hours (8 AM - 8 PM)
            if 8 <= current_hour <= 20:
                return "SCALPING"
            else:
                return "SWING"
                
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error checking mode switch: {str(e)}",
                priority="HIGH"
            )
            return self.current_mode
    
    def process_signals_for_mode(self, mode: str) -> list:
        """Process signals for specific mode with Trading Logger"""
        signals = []
        
        try:
            self.trading_logger.log_trading_alert(
                "PROCESSING",
                f"Processing signals for {mode} mode",
                mode=mode
            )
            
            for pair in self.pairs:
                try:
                    # Get candles based on mode
                    if mode == "SCALPING":
                        candles = self.data_manager.get_candles(pair, "15m", 100)
                    else:  # SWING mode
                        candles = self.data_manager.get_candles(pair, "1h", 200)
                    
                    if not candles:
                        self.trading_logger.log_trading_alert(
                            "DATA_ERROR",
                            f"No candles for {pair}",
                            pair=pair,
                            mode=mode
                        )
                        continue
                    
                    # Process signal with Trading Logger
                    signal = self.signal_processor.process_signal(candles, pair, mode)
                    
                    if signal:
                        # Convert to TradingSignal format
                        trading_signal = TradingSignal(
                            pair=signal.pair,
                            direction=signal.direction,
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            strength=signal.strength,
                            risk_reward=signal.risk_reward,
                            mode=mode,
                            timestamp=signal.timestamp,
                            pattern=self._get_signal_pattern(signal),
                            volume_ratio=self._get_volume_ratio(candles),
                            rsi=self._get_rsi(candles),
                            trend=self._get_trend(candles)
                        )
                        
                        # Log with Trading Logger
                        self.trading_logger.log_trading_signal(trading_signal)
                        
                        signals.append(signal)
                        
                        self.trading_logger.log_trading_alert(
                            "SIGNAL_GENERATED",
                            f"Signal generated for {pair}",
                            pair=pair,
                            mode=mode
                        )
                    
                except Exception as e:
                    self.trading_logger.log_trading_alert(
                        "ERROR",
                        f"Error processing {pair}: {str(e)}",
                        pair=pair,
                        mode=mode,
                        priority="HIGH"
                    )
                    continue
            
            # Log mode summary
            if signals:
                self.trading_logger.log_trading_alert(
                    "SUMMARY",
                    f"Generated {len(signals)} signals for {mode} mode",
                    mode=mode
                )
            else:
                self.trading_logger.log_trading_alert(
                    "SUMMARY",
                    f"No signals generated for {mode} mode",
                    mode=mode
                )
                
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error in process_signals_for_mode: {str(e)}",
                mode=mode,
                priority="CRITICAL"
            )
        
        return signals
    
    def _get_signal_pattern(self, signal: SignalData) -> str:
        """Extract pattern from signal (placeholder)"""
        return "Sweep"  # Placeholder
    
    def _get_volume_ratio(self, candles: list) -> float:
        """Calculate volume ratio (placeholder)"""
        if len(candles) < 10:
            return 1.0
        current_volume = candles[-1].volume
        avg_volume = sum(c.volume for c in candles[-10:]) / 10
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def _get_rsi(self, candles: list) -> float:
        """Calculate RSI (placeholder)"""
        return 50.0  # Placeholder
    
    def _get_trend(self, candles: list) -> str:
        """Determine trend (placeholder)"""
        if len(candles) < 20:
            return "NEUTRAL"
        sma_20 = sum(c.close for c in candles[-20:]) / 20
        current_price = candles[-1].close
        return "BULLISH" if current_price > sma_20 else "BEARISH"

# ========== ENTRY POINT ==========
if __name__ == '__main__':
    print("🤖 Starting Arif Signal Trading Bot with Trading Logger...")
    print("=" * 60)
    print("📊 Trading Logger: Specialized logging for trading analysis")
    print("⚡ Mode: Dual Mode (Scalping + Swing)")
    print("📁 Logs: trading_logs/ directory")
    print("=" * 60)
    
    try:
        # Instantiate and run the app
        app = ArifSignalApp()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)