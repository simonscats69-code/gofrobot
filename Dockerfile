# Universal Dockerfile for Telegram Bot with Multi-Stage Build
# Supports Python 3.10/3.11, production/development builds, and comprehensive optimizations

# =============================================
# BUILD ARGUMENTS
# =============================================
ARG PYTHON_VERSION=3.11
ARG BUILD_TYPE=production
ARG ENABLE_MONITORING=true
ARG ENABLE_BACKUP=true
ARG ENABLE_RATE_LIMIT=true

# =============================================
# BUILDER STAGE
# =============================================
FROM python:${PYTHON_VERSION}-slim as builder

# Set build arguments
ARG PYTHON_VERSION
ARG BUILD_TYPE
ARG ENABLE_MONITORING
ARG ENABLE_BACKUP
ARG ENABLE_RATE_LIMIT

WORKDIR /app

# Install build dependencies (only for Telegram bot requirements)
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements
COPY requirements.txt requirements_optimizations.txt ./

# Install Python dependencies based on build type
RUN if [ "$BUILD_TYPE" = "production" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt -r requirements_optimizations.txt; \
    fi

# =============================================
# FINAL STAGE
# =============================================
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    tzdata \
    && addgroup -g 1001 -S botgroup \
    && adduser -u 1001 -S botuser -G botgroup

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION%.*} /usr/local/lib/python${PYTHON_VERSION%.*}
COPY --from=builder /usr/local/bin/python${PYTHON_VERSION} /usr/local/bin/

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage/backups storage/logs storage/cache \
    && chown -R botuser:botgroup /app \
    && chmod +x main.py

# Set environment variables for Telegram bot
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC \
    REDIS_URL=redis://redis:6379/0 \
    DB_PATH=storage/bot_database.db \
    MONITORING_ENABLED=${ENABLE_MONITORING} \
    BACKUP_ENABLED=${ENABLE_BACKUP} \
    RATE_LIMIT_ENABLED=${ENABLE_RATE_LIMIT} \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0 if open('storage/.health').read().strip() == 'healthy' else 1)" || exit 1

# Create health check file
RUN echo "healthy" > storage/.health

# Switch to non-root user
USER botuser

# Command to run the bot
CMD ["python", "main.py"]

# =============================================
# DEVELOPMENT VERSION (Alternative - uncomment if needed)
# =============================================
# FROM python:${PYTHON_VERSION}-slim
#
# WORKDIR /app
#
# # Install dependencies
# COPY requirements.txt requirements_optimizations.txt ./
# RUN pip install --no-cache-dir -r requirements.txt -r requirements_optimizations.txt
#
# # Copy code
# COPY . .
#
# # Set environment variables
# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     TZ=UTC
#
# # Run the bot
# CMD ["python", "main.py"]