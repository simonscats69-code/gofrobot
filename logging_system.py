"""
Advanced logging system with JSON support and log rotation
"""
import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any
from config import LOGGING_CONFIG

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
            log_data["stack_trace"] = self.formatStack(record.stack_info) if record.stack_info else None

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'chat_id'):
            log_data['chat_id'] = record.chat_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        return json.dumps(log_data, ensure_ascii=False)

    def formatTime(self, record: logging.LogRecord) -> str:
        return datetime.fromtimestamp(record.created).isoformat()

    def formatException(self, exc_info: tuple) -> str:
        import traceback
        return "".join(traceback.format_exception(*exc_info)).strip()

    def formatStack(self, stack_info: str) -> str:
        return stack_info.strip() if stack_info else None

class LogRotator:
    """Log file rotation handler"""

    def __init__(self, log_dir: str, max_size: int, backup_count: int):
        self.log_dir = log_dir
        self.max_size = max_size
        self.backup_count = backup_count
        os.makedirs(log_dir, exist_ok=True)

    def should_rotate(self, log_file: str) -> bool:
        """Check if log file should be rotated"""
        try:
            return os.path.exists(log_file) and os.path.getsize(log_file) > self.max_size
        except:
            return False

    def rotate(self, log_file: str) -> str:
        """Rotate log files"""
        if not self.should_rotate(log_file):
            return log_file

        # Find existing backups
        base_name = os.path.basename(log_file)
        name, ext = os.path.splitext(base_name)
        existing_backups = []

        for f in os.listdir(self.log_dir):
            if f.startswith(name) and f != base_name:
                try:
                    existing_backups.append(int(f[len(name)+1:-len(ext)]))
                except:
                    pass

        if existing_backups:
            existing_backups.sort()
            # Remove oldest backups if we have too many
            while len(existing_backups) >= self.backup_count:
                oldest = existing_backups.pop(0)
                try:
                    os.remove(os.path.join(self.log_dir, f"{name}.{oldest}{ext}"))
                except:
                    pass
            # Rename existing backups
            for i, num in enumerate(reversed(existing_backups), 1):
                try:
                    os.rename(
                        os.path.join(self.log_dir, f"{name}.{num}{ext}"),
                        os.path.join(self.log_dir, f"{name}.{num + i}{ext}")
                    )
                except:
                    pass
            # Rename current log to backup
            try:
                os.rename(
                    log_file,
                    os.path.join(self.log_dir, f"{name}.1{ext}")
                )
            except:
                pass

        return log_file

def setup_advanced_logging() -> logging.Logger:
    """Setup advanced logging system with JSON and rotation"""
    log_dir = "storage/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create log file with date
    log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")

    # Initialize logger
    logger = logging.getLogger("gofrobot")
    logger.setLevel(getattr(logging, LOGGING_CONFIG["level"], logging.INFO))

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with color
    try:
        import colorlog
        console_format = '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
        logger.addHandler(console_handler)
    except ImportError:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    # File handler with JSON format and rotation
    file_rotator = LogRotator(
        log_dir,
        LOGGING_CONFIG["max_size"],
        LOGGING_CONFIG["backup_count"]
    )

    # Rotate logs if needed
    file_rotator.rotate(log_file)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Suppress verbose library logs
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)

    logger.info("📝 Advanced logging system initialized", extra={
        "component": "logging",
        "action": "initialize",
        "log_file": log_file,
        "level": LOGGING_CONFIG["level"]
    })

    return logger

def get_request_logger(user_id: int, chat_id: int, request_id: str) -> logging.Logger:
    """Get logger with request context"""
    logger = logging.getLogger("gofrobot.request")
    adapter = logging.LoggerAdapter(logger, {
        'user_id': user_id,
        'chat_id': chat_id,
        'request_id': request_id
    })
    return adapter

def log_performance(start_time: float, handler_name: str, user_id: int = None, success: bool = True):
    """Log performance metrics"""
    duration = time.time() - start_time
    logger = logging.getLogger("gofrobot.performance")

    extra = {
        "duration": duration,
        "handler": handler_name,
        "success": success
    }

    if user_id:
        extra["user_id"] = user_id

    if success:
        logger.info(f"✅ {handler_name} completed in {duration:.3f}s", extra=extra)
    else:
        logger.error(f"❌ {handler_name} failed after {duration:.3f}s", extra=extra)

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context"""
    logger = logging.getLogger("gofrobot.error")
    context = context or {}

    extra = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context
    }

    logger.error(f"Error: {str(error)}", extra=extra, exc_info=True)

# Initialize advanced logging
advanced_logger = setup_advanced_logging()