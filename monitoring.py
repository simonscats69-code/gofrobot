"""
Monitoring and metrics system for the bot
"""
import time
import logging
from typing import Dict, Any
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from config import MONITORING

logger = logging.getLogger(__name__)

# Initialize metrics
if MONITORING["prometheus_enabled"]:
    # Counters
    REQUESTS_TOTAL = Counter(
        'bot_requests_total',
        'Total number of requests',
        ['handler', 'status']
    )

    MESSAGES_RECEIVED = Counter(
        'bot_messages_received_total',
        'Total messages received',
        ['chat_type']
    )

    COMMANDS_EXECUTED = Counter(
        'bot_commands_executed_total',
        'Total commands executed',
        ['command_name']
    )

    ERRORS_TOTAL = Counter(
        'bot_errors_total',
        'Total errors encountered',
        ['error_type']
    )

    # Gauges
    ACTIVE_USERS = Gauge(
        'bot_active_users',
        'Number of active users'
    )

    CACHE_SIZE = Gauge(
        'bot_cache_size',
        'Current cache size',
        ['cache_type']
    )

    DATABASE_CONNECTIONS = Gauge(
        'bot_database_connections',
        'Current database connections'
    )

    # Histograms
    REQUEST_DURATION = Histogram(
        'bot_request_duration_seconds',
        'Request processing duration',
        ['handler']
    )

    def init_prometheus():
        """Initialize Prometheus metrics server"""
        try:
            start_http_server(MONITORING["prometheus_port"])
            logger.info(f"📊 Prometheus metrics server started on port {MONITORING['prometheus_port']}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")

    def shutdown_prometheus():
        """Shutdown Prometheus metrics server"""
        # Prometheus server doesn't have a clean shutdown method
        logger.info("Prometheus metrics server shutdown")
else:
    # Dummy implementations when Prometheus is disabled
    def init_prometheus():
        logger.info("Prometheus metrics disabled in config")

    def shutdown_prometheus():
        pass

    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

    REQUESTS_TOTAL = DummyMetric()
    MESSAGES_RECEIVED = DummyMetric()
    COMMANDS_EXECUTED = DummyMetric()
    ERRORS_TOTAL = DummyMetric()
    ACTIVE_USERS = DummyMetric()
    CACHE_SIZE = DummyMetric()
    DATABASE_CONNECTIONS = DummyMetric()
    REQUEST_DURATION = DummyMetric()

class BotMonitor:
    """Bot monitoring and health check system"""

    def __init__(self):
        self.start_time = time.time()
        self.last_health_check = time.time()
        self.request_count = 0
        self.error_count = 0
        self.uptime = 0

    def update_metrics(self):
        """Update monitoring metrics"""
        self.uptime = time.time() - self.start_time

        # Update active users (this would be connected to actual user tracking)
        ACTIVE_USERS.set(10)  # Placeholder

        # Update request count
        REQUESTS_TOTAL.labels(handler="total", status="success").inc(self.request_count)
        ERRORS_TOTAL.labels(error_type="total").inc(self.error_count)

    def get_health_status(self) -> Dict[str, Any]:
        """Get bot health status"""
        return {
            "status": "healthy",
            "uptime_seconds": self.uptime,
            "requests_processed": self.request_count,
            "errors_encountered": self.error_count,
            "timestamp": time.time(),
            "memory_usage": self._get_memory_usage()
        }

    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        import psutil
        import os

        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()

            return {
                "rss_mb": mem_info.rss / 1024 / 1024,
                "vms_mb": mem_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except:
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0
            }

    def log_request(self, handler_name: str, duration: float, success: bool = True):
        """Log a request for monitoring"""
        self.request_count += 1

        REQUESTS_TOTAL.labels(handler=handler_name, status="success" if success else "error").inc()
        REQUEST_DURATION.labels(handler=handler_name).observe(duration)

        if not success:
            self.error_count += 1

    def log_command(self, command_name: str):
        """Log command execution"""
        COMMANDS_EXECUTED.labels(command_name=command_name).inc()

    def log_message(self, chat_type: str):
        """Log received message"""
        MESSAGES_RECEIVED.labels(chat_type=chat_type).inc()

    def log_error(self, error_type: str):
        """Log an error"""
        self.error_count += 1
        ERRORS_TOTAL.labels(error_type=error_type).inc()

    def update_cache_metrics(self, local_size: int, redis_connected: bool):
        """Update cache metrics"""
        CACHE_SIZE.labels(cache_type="local").set(local_size)
        CACHE_SIZE.labels(cache_type="redis").set(1 if redis_connected else 0)

    def update_db_metrics(self, connections: int):
        """Update database connection metrics"""
        DATABASE_CONNECTIONS.set(connections)

# Global monitor instance
bot_monitor = BotMonitor()

def init_monitoring():
    """Initialize monitoring system"""
    init_prometheus()
    logger.info("📊 Monitoring system initialized")

def shutdown_monitoring():
    """Shutdown monitoring system"""
    shutdown_prometheus()
    logger.info("📊 Monitoring system shutdown")

# Health check endpoint (would be used with web framework)
async def health_check():
    """Health check endpoint"""
    status = bot_monitor.get_health_status()
    return {
        "status": status["status"],
        "uptime": status["uptime_seconds"],
        "requests": status["requests_processed"],
        "errors": status["errors_encountered"],
        "memory": status["memory_usage"]
    }