# Optimized Dockerfile with multi-stage build for production
# For development, you can use the simple version below (commented out)

# =============================================
# PRODUCTION VERSION (Optimized)
# =============================================
# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =============================================
# Final stage
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    tzdata

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin/python3.11 /usr/local/bin/

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC

# Health check
HEALCHECK --interval=30s --timeout=3s \
    CMD python -c "import sys; sys.exit(0 if open('storage/.health').read() == 'healthy' else 1)" || exit 1

# Create health check file
RUN mkdir -p storage && echo "healthy" > storage/.health

# Expose Prometheus metrics port
EXPOSE 8000

# Command to run the bot
CMD ["python", "main.py"]

# =============================================
# DEVELOPMENT VERSION (Simple - uncomment if needed)
# =============================================
# FROM python:3.11-slim
#
# WORKDIR /app
#
# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
#
# # Copy code
# COPY . .
#
# # Run the bot
# CMD ["python", "main.py"]
