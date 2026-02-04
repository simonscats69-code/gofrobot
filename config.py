"""
Configuration file for Gofrobot
Contains all constants, balance settings, and configuration parameters
"""

# Database Configuration
DB_CONFIG = {
    "name": "bot_database.db",
    "timeout": 60,
    "cache_ttl": 30,
    "max_cache_size": 100,
    "batch_save_interval": 5,
    "backup_keep": 5
}

# Admin Configuration
ADMIN_CONFIG = {
    "admin_ids": [5449121710],  # User IDs with admin privileges
    "maintenance_mode": False,  # Enable/disable maintenance mode
    "auto_repair_enabled": True,  # Enable automatic repair
    "backup_interval": 1800,  # Auto backup every 30 minutes (in seconds)
    "max_backup_files": 20,  # Maximum number of backup files to keep
    "diagnostic_interval": 300  # Diagnostic check every 5 minutes (in seconds)
}

# Game Balance Settings
BALANCE = {
    "UNIT_SCALE": 10.0,
    "DISPLAY_DECIMALS": 1,
    "GOFRA_EXP_PER_GRAM": 0.02,
    "MIN_GOFRA_EXP": 0.8,
    "GOFRA_SOFT_CAP": 500.0,
    "GOFRA_SOFT_CAP_MULT": 0.3,
    "CABLE_MM_PER_KG": 0.2,
    "MIN_CABLE_GAIN": 0.05,
    "CABLE_CHANCE_SMALL": 0.08,
    "PVP_GOFRA_MIN": 5.0,
    "PVP_GOFRA_MAX": 12.0,
    "PVP_CABLE_GAIN": 0.2,
    "PVP_CABLE_MULT": 0.02,
    "PVP_GOFRA_MULT": 0.0005,
}

# Gofra Levels Configuration
GOFRY_MM = {
    10.0: {"name": "Новая гофрошка", "emoji": "🆕", "min_grams": 30, "max_grams": 100, "atm_speed": 1.0},
    50.0: {"name": "Слегка разъезжена", "emoji": "🔄", "min_grams": 45, "max_grams": 120, "atm_speed": 1.1},
    150.0: {"name": "Рабочая гофрошка", "emoji": "⚙️", "min_grams": 60, "max_grams": 150, "atm_speed": 1.2},
    300.0: {"name": "Разъезжена хорошо", "emoji": "🔥", "min_grams": 80, "max_grams": 190, "atm_speed": 1.3},
    600.0: {"name": "Заезженная гофрошка", "emoji": "🏎️", "min_grams": 110, "max_grams": 250, "atm_speed": 1.4},
    1200.0: {"name": "Убитая гофрошка", "emoji": "💀", "min_grams": 150, "max_grams": 320, "atm_speed": 1.5},
    2500.0: {"name": "Легендарная гофрошка", "emoji": "👑", "min_grams": 200, "max_grams": 420, "atm_speed": 1.6},
    5000.0: {"name": "Царь-гофрошка", "emoji": "🐉", "min_grams": 270, "max_grams": 550, "atm_speed": 1.7},
    10000.0: {"name": "БОГ ГОФРОШКИ", "emoji": "👁️‍🗨️", "min_grams": 350, "max_grams": 700, "atm_speed": 1.8},
    20000.0: {"name": "ВСЕЛЕННАЯ ГОФРА", "emoji": "🌌", "min_grams": 450, "max_grams": 900, "atm_speed": 2.0},
}

# Game Constants
ATM_MAX = 12
ATM_BASE_TIME = 7200  # 2 hours in seconds

# Redis Configuration (if enabled)
REDIS_CONFIG = {
    "enabled": True,  # Включаем по умолчанию
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "cache_ttl": 3600,  # 1 час по умолчанию
    "connection_timeout": 5,  # 5 секунд таймаут
    "max_connections": 20  # Максимум 20 соединений
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "file": "storage/logs/bot_{date}.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "use_colorlog": True
}

# Rate Limiting
RATE_LIMITS = {
    "default": 30,  # 30 requests per minute
    "davka": 10,    # 10 davka actions per minute
    "pvp": 10,      # 10 PvP fights per hour
    "commands": 60  # 60 commands per minute
}

# Monitoring
MONITORING = {
    "prometheus_enabled": False,
    "prometheus_port": 8000,
    "health_check_path": "/health"
}

# Storage Configuration
STORAGE_DIR = "storage"
LOGS_DIR = "storage/logs"
BACKUP_DIR = "storage/backups"
CACHE_DIR = "storage/cache"

# Timing Configuration
TIMING_CONFIG = {
    "base_davka_cooldown": 7200,  # 2 hours in seconds
    "atm_regen_time": 600,        # 10 minutes in seconds
    "max_atm_count": 12,
    "precision_update_interval": 1,  # Update every second
    "countdown_update_interval": 1,  # Update countdown every second
    "max_countdown_messages": 100,   # Maximum active countdowns
    "time_precision": 2,             # Decimal places for time display
    "color_thresholds": {
        "ready": 0,
        "warning": 300,      # 5 minutes
        "danger": 60,        # 1 minute
        "critical": 10       # 10 seconds
    }
}
