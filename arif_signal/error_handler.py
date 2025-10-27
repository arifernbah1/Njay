import traceback
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Error categories"""
    DATA_ERROR = "DATA_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    API_ERROR = "API_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    TELEGRAM_ERROR = "TELEGRAM_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

@dataclass
class ErrorInfo:
    """Error information structure"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    pair: Optional[str] = None
    mode: Optional[str] = None
    timestamp: datetime = None
    stack_trace: str = ""
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.context is None:
            self.context = {}

class ErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self, trading_logger, notification_service=None):
        self.logger = trading_logger
        self.notification_service = notification_service
        self.error_count = {}
        self.recovery_strategies = {}
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Initialize error tracking
        self._setup_error_tracking()
        self._setup_recovery_strategies()
    
    def _setup_error_tracking(self):
        """Setup error tracking counters"""
        for category in ErrorCategory:
            self.error_count[category.value] = 0
    
    def _setup_recovery_strategies(self):
        """Setup recovery strategies for different error types"""
        self.recovery_strategies = {
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.API_ERROR: self._handle_api_error,
            ErrorCategory.DATA_ERROR: self._handle_data_error,
            ErrorCategory.TELEGRAM_ERROR: self._handle_telegram_error,
            ErrorCategory.PROCESSING_ERROR: self._handle_processing_error,
            ErrorCategory.SYSTEM_ERROR: self._handle_system_error
        }
    
    def handle_error(self, error: Exception, component: str, 
                    category: ErrorCategory = ErrorCategory.SYSTEM_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    pair: str = None, mode: str = None,
                    context: Dict[str, Any] = None) -> bool:
        """Main error handling method"""
        try:
            # Create error info
            error_info = ErrorInfo(
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                component=component,
                pair=pair,
                mode=mode,
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            # Log error
            self._log_error(error_info)
            
            # Update error count
            self.error_count[category.value] += 1
            
            # Send Telegram alert for high/critical errors
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self._send_error_alert(error_info)
            
            # Execute recovery strategy
            recovery_success = self._execute_recovery_strategy(error_info)
            
            # Handle critical errors
            if severity == ErrorSeverity.CRITICAL:
                self._handle_critical_error(error_info)
            
            return recovery_success
            
        except Exception as e:
            # Fallback error handling
            print(f"Error in error handler: {str(e)}")
            return False
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with detailed information"""
        try:
            error_data = {
                "error_type": error_info.error_type,
                "error_message": error_info.error_message,
                "severity": error_info.severity.value,
                "category": error_info.category.value,
                "component": error_info.component,
                "pair": error_info.pair,
                "mode": error_info.mode,
                "timestamp": error_info.timestamp.isoformat(),
                "stack_trace": error_info.stack_trace,
                "context": error_info.context
            }
            
            # Log to trading logger
            self.logger.log_trading_alert(
                "ERROR",
                f"{error_info.category.value}: {error_info.error_message}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority=error_info.severity.value
            )
            
            # Log detailed error to file
            self.logger.log_error(
                error_info.component,
                f"Error: {error_info.error_message}",
                pair=error_info.pair,
                mode=error_info.mode,
                error_data=error_data
            )
            
        except Exception as e:
            print(f"Error logging error: {str(e)}")
    
    def _send_error_alert(self, error_info: ErrorInfo):
        """Send error alert to Telegram"""
        try:
            if self.notification_service:
                message = f"""
🚨 <b>ERROR ALERT</b>

📊 <b>Type:</b> {error_info.error_type}
⚠️ <b>Severity:</b> {error_info.severity.value}
📁 <b>Category:</b> {error_info.category.value}
🔧 <b>Component:</b> {error_info.component}
🕐 <b>Time:</b> {error_info.timestamp.strftime('%H:%M:%S WIB')}

💎 <b>Pair:</b> {error_info.pair or 'N/A'}
📊 <b>Mode:</b> {error_info.mode or 'N/A'}

📝 <b>Message:</b>
{error_info.error_message}

🔍 <b>Context:</b>
{self._format_context(error_info.context)}
"""
                
                self.notification_service.send_system_alert(
                    "ERROR_ALERT",
                    message,
                    error_info.severity.value
                )
                
        except Exception as e:
            print(f"Error sending error alert: {str(e)}")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for Telegram message"""
        if not context:
            return "No additional context"
        
        formatted = []
        for key, value in context.items():
            formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    def _execute_recovery_strategy(self, error_info: ErrorInfo) -> bool:
        """Execute appropriate recovery strategy"""
        try:
            recovery_func = self.recovery_strategies.get(error_info.category)
            if recovery_func:
                return recovery_func(error_info)
            else:
                # Default recovery
                return self._default_recovery(error_info)
                
        except Exception as e:
            print(f"Error in recovery strategy: {str(e)}")
            return False
    
    def _handle_network_error(self, error_info: ErrorInfo) -> bool:
        """Handle network errors with retry logic"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Attempting network error recovery for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Wait before retry
            time.sleep(self.retry_delay)
            
            # Log recovery attempt
            self.logger.log_trading_alert(
                "RECOVERY_ATTEMPT",
                f"Network recovery attempt completed",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"Network recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="HIGH"
            )
            return False
    
    def _handle_api_error(self, error_info: ErrorInfo) -> bool:
        """Handle API errors"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Handling API error for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Check if it's a rate limit error
            if "rate limit" in error_info.error_message.lower():
                # Wait longer for rate limit
                time.sleep(5)
                self.logger.log_trading_alert(
                    "RATE_LIMIT",
                    "Rate limit detected, waiting before retry",
                    pair=error_info.pair,
                    mode=error_info.mode
                )
            
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"API recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="HIGH"
            )
            return False
    
    def _handle_data_error(self, error_info: ErrorInfo) -> bool:
        """Handle data errors"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Handling data error for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Skip this pair for now
            if error_info.pair:
                self.logger.log_trading_alert(
                    "PAIR_SKIPPED",
                    f"Skipping {error_info.pair} due to data error",
                    pair=error_info.pair,
                    mode=error_info.mode
                )
            
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"Data recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="HIGH"
            )
            return False
    
    def _handle_telegram_error(self, error_info: ErrorInfo) -> bool:
        """Handle Telegram errors"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Handling Telegram error for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Telegram errors are not critical for trading
            # Just log and continue
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"Telegram recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="MEDIUM"
            )
            return False
    
    def _handle_processing_error(self, error_info: ErrorInfo) -> bool:
        """Handle processing errors"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Handling processing error for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Skip this processing cycle
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"Processing recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="HIGH"
            )
            return False
    
    def _handle_system_error(self, error_info: ErrorInfo) -> bool:
        """Handle system errors"""
        try:
            self.logger.log_trading_alert(
                "RECOVERY",
                f"Handling system error for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # System errors might require restart
            if error_info.severity == ErrorSeverity.CRITICAL:
                self.logger.log_trading_alert(
                    "SYSTEM_RESTART",
                    "Critical system error detected, restart recommended",
                    priority="CRITICAL"
                )
            
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "RECOVERY_FAILED",
                f"System recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="CRITICAL"
            )
            return False
    
    def _default_recovery(self, error_info: ErrorInfo) -> bool:
        """Default recovery strategy"""
        try:
            self.logger.log_trading_alert(
                "DEFAULT_RECOVERY",
                f"Using default recovery for {error_info.component}",
                pair=error_info.pair,
                mode=error_info.mode
            )
            
            # Simple wait and retry
            time.sleep(self.retry_delay)
            return True
            
        except Exception as e:
            self.logger.log_trading_alert(
                "DEFAULT_RECOVERY_FAILED",
                f"Default recovery failed: {str(e)}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="HIGH"
            )
            return False
    
    def _handle_critical_error(self, error_info: ErrorInfo):
        """Handle critical errors"""
        try:
            self.logger.log_trading_alert(
                "CRITICAL_ERROR",
                f"Critical error in {error_info.component}: {error_info.error_message}",
                pair=error_info.pair,
                mode=error_info.mode,
                priority="CRITICAL"
            )
            
            # Send critical alert to Telegram
            if self.notification_service:
                self.notification_service.send_system_alert(
                    "CRITICAL_ERROR",
                    f"Critical error detected in {error_info.component}. Manual intervention may be required.",
                    "CRITICAL"
                )
            
            # Log error statistics
            self._log_error_statistics()
            
        except Exception as e:
            print(f"Error handling critical error: {str(e)}")
    
    def _log_error_statistics(self):
        """Log error statistics"""
        try:
            stats = {
                "total_errors": sum(self.error_count.values()),
                "error_breakdown": self.error_count.copy(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.log_trading_alert(
                "ERROR_STATS",
                f"Error statistics: {stats}",
                priority="MEDIUM"
            )
            
        except Exception as e:
            print(f"Error logging statistics: {str(e)}")
    
    def get_error_count(self, category: ErrorCategory = None) -> Dict[str, int]:
        """Get error count for specific category or all"""
        if category:
            return {category.value: self.error_count.get(category.value, 0)}
        return self.error_count.copy()
    
    def reset_error_count(self, category: ErrorCategory = None):
        """Reset error count"""
        if category:
            self.error_count[category.value] = 0
        else:
            self._setup_error_tracking()
    
    def safe_execute(self, func: Callable, *args, component: str = "Unknown",
                    category: ErrorCategory = ErrorCategory.SYSTEM_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    pair: str = None, mode: str = None,
                    context: Dict[str, Any] = None, **kwargs) -> Any:
        """Safely execute function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, component, category, severity, pair, mode, context)
            return None