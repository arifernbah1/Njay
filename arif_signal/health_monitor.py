import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

class HealthStatus(Enum):
    """Health status levels"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"

class ComponentStatus(Enum):
    """Component status"""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    RESTARTING = "RESTARTING"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime

@dataclass
class BotMetrics:
    """Bot performance metrics"""
    uptime_seconds: int
    signals_generated: int
    signals_scalping: int
    signals_swing: int
    errors_count: int
    telegram_sent: int
    telegram_failed: int
    active_setups: int
    processing_time_avg: float
    timestamp: datetime

@dataclass
class ComponentHealth:
    """Individual component health"""
    name: str
    status: ComponentStatus
    last_check: datetime
    error_count: int
    response_time_ms: float
    is_critical: bool

@dataclass
class HealthReport:
    """Complete health report"""
    overall_status: HealthStatus
    system_metrics: SystemMetrics
    bot_metrics: BotMetrics
    components: Dict[str, ComponentHealth]
    alerts: List[str]
    recommendations: List[str]
    timestamp: datetime

class BotHealthMonitor:
    """Comprehensive bot health monitoring system"""
    
    def __init__(self, trading_logger, notification_service=None):
        self.logger = trading_logger
        self.notification_service = notification_service
        
        # Health tracking
        self.start_time = datetime.utcnow()
        self.last_health_check = None
        self.health_history = []
        self.max_history_size = 100
        
        # Metrics tracking
        self.signals_generated = 0
        self.signals_scalping = 0
        self.signals_swing = 0
        self.errors_count = 0
        self.telegram_sent = 0
        self.telegram_failed = 0
        self.processing_times = []
        
        # Component monitoring
        self.components = {
            "SCALPING_THREAD": ComponentHealth("SCALPING_THREAD", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True),
            "SWING_THREAD": ComponentHealth("SWING_THREAD", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True),
            "DATA_MANAGER": ComponentHealth("DATA_MANAGER", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True),
            "SIGNAL_PROCESSOR": ComponentHealth("SIGNAL_PROCESSOR", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True),
            "TELEGRAM_SERVICE": ComponentHealth("TELEGRAM_SERVICE", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, False),
            "ERROR_HANDLER": ComponentHealth("ERROR_HANDLER", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True),
            "SWING_SETUP_MANAGER": ComponentHealth("SWING_SETUP_MANAGER", ComponentStatus.RUNNING, datetime.utcnow(), 0, 0, True)
        }
        
        # Health thresholds
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "error_rate_warning": 0.1,  # 10% error rate
            "error_rate_critical": 0.3,  # 30% error rate
            "response_time_warning": 5000,  # 5 seconds
            "response_time_critical": 10000,  # 10 seconds
            "uptime_minimum": 3600  # 1 hour minimum
        }
        
        # Monitoring control
        self.monitoring_active = True
        self.monitor_thread = None
        
        # Start monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start health monitoring thread"""
        try:
            self.monitor_thread = threading.Thread(
                target=self._monitor_health_loop,
                name="HealthMonitor",
                daemon=True
            )
            self.monitor_thread.start()
            
            self.logger.log_trading_alert(
                "HEALTH_MONITOR_START",
                "Bot health monitoring system started",
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.log_trading_alert(
                "HEALTH_MONITOR_ERROR",
                f"Failed to start health monitoring: {str(e)}",
                priority="CRITICAL"
            )
    
    def _monitor_health_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_active:
            try:
                # Generate health report
                health_report = self.generate_health_report()
                
                # Check for critical issues
                if health_report.overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    self._handle_health_alert(health_report)
                
                # Log health status
                self._log_health_status(health_report)
                
                # Store in history
                self._store_health_history(health_report)
                
                # Wait before next check (5 minutes)
                time.sleep(300)
                
            except Exception as e:
                self.logger.log_trading_alert(
                    "HEALTH_MONITOR_ERROR",
                    f"Error in health monitoring loop: {str(e)}",
                    priority="HIGH"
                )
                time.sleep(60)  # Wait 1 minute before retry
    
    def generate_health_report(self) -> HealthReport:
        """Generate comprehensive health report"""
        try:
            # Get system metrics
            system_metrics = self._get_system_metrics()
            
            # Get bot metrics
            bot_metrics = self._get_bot_metrics()
            
            # Check component health
            self._check_component_health()
            
            # Determine overall status
            overall_status = self._determine_overall_status(system_metrics, bot_metrics)
            
            # Generate alerts and recommendations
            alerts, recommendations = self._generate_alerts_and_recommendations(
                system_metrics, bot_metrics, overall_status
            )
            
            # Create health report
            health_report = HealthReport(
                overall_status=overall_status,
                system_metrics=system_metrics,
                bot_metrics=bot_metrics,
                components=self.components.copy(),
                alerts=alerts,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
            self.last_health_check = health_report.timestamp
            return health_report
            
        except Exception as e:
            self.logger.log_trading_alert(
                "HEALTH_REPORT_ERROR",
                f"Error generating health report: {str(e)}",
                priority="HIGH"
            )
            
            # Return basic error report
            return HealthReport(
                overall_status=HealthStatus.CRITICAL,
                system_metrics=self._get_basic_system_metrics(),
                bot_metrics=self._get_basic_bot_metrics(),
                components=self.components.copy(),
                alerts=[f"Health report generation failed: {str(e)}"],
                recommendations=["Check system logs", "Restart health monitor"],
                timestamp=datetime.utcnow()
            )
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network usage
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_percent=disk_percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.log_trading_alert(
                "SYSTEM_METRICS_ERROR",
                f"Error getting system metrics: {str(e)}",
                priority="MEDIUM"
            )
            return self._get_basic_system_metrics()
    
    def _get_basic_system_metrics(self) -> SystemMetrics:
        """Get basic system metrics when detailed metrics fail"""
        return SystemMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_used_mb=0.0,
            memory_total_mb=0.0,
            disk_percent=0.0,
            network_sent_mb=0.0,
            network_recv_mb=0.0,
            timestamp=datetime.utcnow()
        )
    
    def _get_bot_metrics(self) -> BotMetrics:
        """Get bot performance metrics"""
        try:
            # Calculate uptime
            uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())
            
            # Calculate average processing time
            processing_time_avg = 0.0
            if self.processing_times:
                processing_time_avg = sum(self.processing_times) / len(self.processing_times)
            
            return BotMetrics(
                uptime_seconds=uptime_seconds,
                signals_generated=self.signals_generated,
                signals_scalping=self.signals_scalping,
                signals_swing=self.signals_swing,
                errors_count=self.errors_count,
                telegram_sent=self.telegram_sent,
                telegram_failed=self.telegram_failed,
                active_setups=self._get_active_setups_count(),
                processing_time_avg=processing_time_avg,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.log_trading_alert(
                "BOT_METRICS_ERROR",
                f"Error getting bot metrics: {str(e)}",
                priority="MEDIUM"
            )
            return self._get_basic_bot_metrics()
    
    def _get_basic_bot_metrics(self) -> BotMetrics:
        """Get basic bot metrics when detailed metrics fail"""
        return BotMetrics(
            uptime_seconds=0,
            signals_generated=0,
            signals_scalping=0,
            signals_swing=0,
            errors_count=0,
            telegram_sent=0,
            telegram_failed=0,
            active_setups=0,
            processing_time_avg=0.0,
            timestamp=datetime.utcnow()
        )
    
    def _get_active_setups_count(self) -> int:
        """Get count of active swing setups"""
        try:
            # This would need to be implemented based on your swing setup manager
            # For now, return 0
            return 0
        except Exception:
            return 0
    
    def _check_component_health(self):
        """Check health of individual components"""
        try:
            current_time = datetime.utcnow()
            
            # Update component timestamps
            for component_name in self.components:
                component = self.components[component_name]
                component.last_check = current_time
                
                # Check if component is responding (simplified check)
                if component.error_count > 10:
                    component.status = ComponentStatus.ERROR
                elif component.error_count > 5:
                    component.status = ComponentStatus.RESTARTING
                else:
                    component.status = ComponentStatus.RUNNING
                    
        except Exception as e:
            self.logger.log_trading_alert(
                "COMPONENT_HEALTH_ERROR",
                f"Error checking component health: {str(e)}",
                priority="MEDIUM"
            )
    
    def _determine_overall_status(self, system_metrics: SystemMetrics, bot_metrics: BotMetrics) -> HealthStatus:
        """Determine overall health status"""
        try:
            # Check critical system metrics
            if (system_metrics.cpu_percent > self.thresholds["cpu_critical"] or
                system_metrics.memory_percent > self.thresholds["memory_critical"] or
                system_metrics.disk_percent > self.thresholds["disk_critical"]):
                return HealthStatus.CRITICAL
            
            # Check warning thresholds
            if (system_metrics.cpu_percent > self.thresholds["cpu_warning"] or
                system_metrics.memory_percent > self.thresholds["memory_warning"] or
                system_metrics.disk_percent > self.thresholds["disk_warning"]):
                return HealthStatus.WARNING
            
            # Check bot-specific metrics
            if bot_metrics.uptime_seconds < self.thresholds["uptime_minimum"]:
                return HealthStatus.WARNING
            
            # Check error rate
            total_operations = bot_metrics.signals_generated + bot_metrics.telegram_sent
            if total_operations > 0:
                error_rate = bot_metrics.errors_count / total_operations
                if error_rate > self.thresholds["error_rate_critical"]:
                    return HealthStatus.CRITICAL
                elif error_rate > self.thresholds["error_rate_warning"]:
                    return HealthStatus.WARNING
            
            # Check component status
            critical_components_down = sum(
                1 for comp in self.components.values() 
                if comp.is_critical and comp.status == ComponentStatus.ERROR
            )
            
            if critical_components_down > 0:
                return HealthStatus.CRITICAL
            
            # All checks passed
            return HealthStatus.EXCELLENT
            
        except Exception as e:
            self.logger.log_trading_alert(
                "STATUS_DETERMINATION_ERROR",
                f"Error determining health status: {str(e)}",
                priority="MEDIUM"
            )
            return HealthStatus.WARNING
    
    def _generate_alerts_and_recommendations(self, system_metrics: SystemMetrics, 
                                           bot_metrics: BotMetrics, 
                                           overall_status: HealthStatus) -> tuple[List[str], List[str]]:
        """Generate alerts and recommendations based on health status"""
        alerts = []
        recommendations = []
        
        try:
            # System alerts
            if system_metrics.cpu_percent > self.thresholds["cpu_critical"]:
                alerts.append(f"CRITICAL: CPU usage at {system_metrics.cpu_percent:.1f}%")
                recommendations.append("Consider reducing bot load or upgrading hardware")
            
            elif system_metrics.cpu_percent > self.thresholds["cpu_warning"]:
                alerts.append(f"WARNING: CPU usage at {system_metrics.cpu_percent:.1f}%")
                recommendations.append("Monitor CPU usage closely")
            
            if system_metrics.memory_percent > self.thresholds["memory_critical"]:
                alerts.append(f"CRITICAL: Memory usage at {system_metrics.memory_percent:.1f}%")
                recommendations.append("Restart bot or increase system memory")
            
            elif system_metrics.memory_percent > self.thresholds["memory_warning"]:
                alerts.append(f"WARNING: Memory usage at {system_metrics.memory_percent:.1f}%")
                recommendations.append("Monitor memory usage and consider optimization")
            
            if system_metrics.disk_percent > self.thresholds["disk_critical"]:
                alerts.append(f"CRITICAL: Disk usage at {system_metrics.disk_percent:.1f}%")
                recommendations.append("Free up disk space immediately")
            
            elif system_metrics.disk_percent > self.thresholds["disk_warning"]:
                alerts.append(f"WARNING: Disk usage at {system_metrics.disk_percent:.1f}%")
                recommendations.append("Consider cleaning up log files")
            
            # Bot-specific alerts
            if bot_metrics.uptime_seconds < self.thresholds["uptime_minimum"]:
                alerts.append(f"WARNING: Bot uptime only {bot_metrics.uptime_seconds} seconds")
                recommendations.append("Monitor bot stability")
            
            # Component alerts
            for component_name, component in self.components.items():
                if component.status == ComponentStatus.ERROR and component.is_critical:
                    alerts.append(f"CRITICAL: {component_name} is in ERROR state")
                    recommendations.append(f"Restart {component_name}")
                elif component.status == ComponentStatus.ERROR:
                    alerts.append(f"WARNING: {component_name} is in ERROR state")
                    recommendations.append(f"Check {component_name} logs")
            
            # Performance alerts
            if bot_metrics.processing_time_avg > self.thresholds["response_time_critical"]:
                alerts.append(f"CRITICAL: Average processing time {bot_metrics.processing_time_avg:.0f}ms")
                recommendations.append("Optimize signal processing algorithms")
            
            elif bot_metrics.processing_time_avg > self.thresholds["response_time_warning"]:
                alerts.append(f"WARNING: Average processing time {bot_metrics.processing_time_avg:.0f}ms")
                recommendations.append("Monitor processing performance")
            
            # If no specific alerts, add general status
            if not alerts and overall_status == HealthStatus.EXCELLENT:
                alerts.append("All systems operating normally")
                recommendations.append("Continue monitoring")
            
        except Exception as e:
            alerts.append(f"Error generating alerts: {str(e)}")
            recommendations.append("Check health monitor logs")
        
        return alerts, recommendations
    
    def _handle_health_alert(self, health_report: HealthReport):
        """Handle health alerts by sending notifications"""
        try:
            if self.notification_service:
                # Create health alert message
                message = self._format_health_alert_message(health_report)
                
                # Send alert based on severity
                priority = "CRITICAL" if health_report.overall_status == HealthStatus.CRITICAL else "HIGH"
                
                self.notification_service.send_system_alert(
                    "HEALTH_ALERT",
                    message,
                    priority
                )
                
                self.logger.log_trading_alert(
                    "HEALTH_ALERT_SENT",
                    f"Health alert sent: {health_report.overall_status.value}",
                    priority=priority
                )
            
        except Exception as e:
            self.logger.log_trading_alert(
                "HEALTH_ALERT_ERROR",
                f"Error sending health alert: {str(e)}",
                priority="HIGH"
            )
    
    def _format_health_alert_message(self, health_report: HealthReport) -> str:
        """Format health alert message for Telegram"""
        try:
            status_emoji = {
                HealthStatus.EXCELLENT: "🟢",
                HealthStatus.GOOD: "🟡",
                HealthStatus.WARNING: "🟠",
                HealthStatus.CRITICAL: "🔴",
                HealthStatus.OFFLINE: "⚫"
            }
            
            message = f"""
🏥 <b>BOT HEALTH ALERT</b>

{status_emoji.get(health_report.overall_status, "❓")} <b>Status:</b> {health_report.overall_status.value}
🕐 <b>Time:</b> {health_report.timestamp.strftime('%H:%M:%S WIB')}
⏱️ <b>Uptime:</b> {health_report.bot_metrics.uptime_seconds // 3600}h {(health_report.bot_metrics.uptime_seconds % 3600) // 60}m

💻 <b>System Metrics:</b>
• CPU: {health_report.system_metrics.cpu_percent:.1f}%
• Memory: {health_report.system_metrics.memory_percent:.1f}% ({health_report.system_metrics.memory_used_mb:.0f}MB)
• Disk: {health_report.system_metrics.disk_percent:.1f}%

🤖 <b>Bot Metrics:</b>
• Signals: {health_report.bot_metrics.signals_generated} (S: {health_report.bot_metrics.signals_scalping}, W: {health_report.bot_metrics.signals_swing})
• Errors: {health_report.bot_metrics.errors_count}
• Telegram: {health_report.bot_metrics.telegram_sent} sent, {health_report.bot_metrics.telegram_failed} failed
• Processing: {health_report.bot_metrics.processing_time_avg:.0f}ms avg

🔧 <b>Component Status:</b>
"""
            
            for component_name, component in health_report.components.items():
                status_emoji = {
                    ComponentStatus.RUNNING: "🟢",
                    ComponentStatus.STOPPED: "🔴",
                    ComponentStatus.ERROR: "🔴",
                    ComponentStatus.RESTARTING: "🟡"
                }
                message += f"• {component_name}: {status_emoji.get(component.status, '❓')} {component.status.value}\n"
            
            if health_report.alerts:
                message += f"\n⚠️ <b>Alerts:</b>\n"
                for alert in health_report.alerts[:3]:  # Show first 3 alerts
                    message += f"• {alert}\n"
            
            if health_report.recommendations:
                message += f"\n💡 <b>Recommendations:</b>\n"
                for rec in health_report.recommendations[:3]:  # Show first 3 recommendations
                    message += f"• {rec}\n"
            
            return message.strip()
            
        except Exception as e:
            return f"Error formatting health alert: {str(e)}"
    
    def _log_health_status(self, health_report: HealthReport):
        """Log health status to trading logger"""
        try:
            health_data = {
                "overall_status": health_report.overall_status.value,
                "system_metrics": asdict(health_report.system_metrics),
                "bot_metrics": asdict(health_report.bot_metrics),
                "components": {name: asdict(comp) for name, comp in health_report.components.items()},
                "alerts": health_report.alerts,
                "recommendations": health_report.recommendations,
                "timestamp": health_report.timestamp.isoformat()
            }
            
            self.logger.log_system_health(health_data)
            
        except Exception as e:
            self.logger.log_trading_alert(
                "HEALTH_LOG_ERROR",
                f"Error logging health status: {str(e)}",
                priority="MEDIUM"
            )
    
    def _store_health_history(self, health_report: HealthReport):
        """Store health report in history"""
        try:
            self.health_history.append(health_report)
            
            # Keep only recent history
            if len(self.health_history) > self.max_history_size:
                self.health_history.pop(0)
                
        except Exception as e:
            self.logger.log_trading_alert(
                "HEALTH_HISTORY_ERROR",
                f"Error storing health history: {str(e)}",
                priority="LOW"
            )
    
    # Public methods for updating metrics
    def increment_signal(self, mode: str = "SCALPING"):
        """Increment signal counter"""
        self.signals_generated += 1
        if mode == "SCALPING":
            self.signals_scalping += 1
        elif mode == "SWING":
            self.signals_swing += 1
    
    def increment_error(self):
        """Increment error counter"""
        self.errors_count += 1
    
    def increment_telegram_sent(self):
        """Increment telegram sent counter"""
        self.telegram_sent += 1
    
    def increment_telegram_failed(self):
        """Increment telegram failed counter"""
        self.telegram_failed += 1
    
    def add_processing_time(self, processing_time_ms: float):
        """Add processing time measurement"""
        self.processing_times.append(processing_time_ms)
        
        # Keep only recent measurements
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
    
    def update_component_status(self, component_name: str, status: ComponentStatus, 
                              error_count: int = None, response_time_ms: float = None):
        """Update component status"""
        if component_name in self.components:
            component = self.components[component_name]
            component.status = status
            component.last_check = datetime.utcnow()
            
            if error_count is not None:
                component.error_count = error_count
            
            if response_time_ms is not None:
                component.response_time_ms = response_time_ms
    
    def get_health_report(self) -> Optional[HealthReport]:
        """Get current health report"""
        if self.last_health_check:
            return self.generate_health_report()
        return None
    
    def get_health_history(self) -> List[HealthReport]:
        """Get health history"""
        return self.health_history.copy()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get quick system status"""
        try:
            system_metrics = self._get_system_metrics()
            bot_metrics = self._get_bot_metrics()
            
            return {
                "status": "RUNNING" if self.monitoring_active else "STOPPED",
                "uptime_seconds": bot_metrics.uptime_seconds,
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "signals_generated": bot_metrics.signals_generated,
                "errors_count": bot_metrics.errors_count,
                "last_check": self.last_health_check.isoformat() if self.last_health_check else None
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.log_trading_alert(
            "HEALTH_MONITOR_STOP",
            "Bot health monitoring system stopped",
            priority="HIGH"
        )