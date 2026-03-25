ARG BUILD_FROM=python:3.12-slim
FROM ${BUILD_FROM}

# Allow pip to install into system site-packages (needed on Debian bookworm)
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install system dependencies (python3 needed when using HA base images)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    pydantic==2.* \
    playwright

# Install Playwright Chromium + its OS dependencies
RUN playwright install --with-deps chromium

# Copy application source
COPY src/ /app/src/
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# S6-overlay service (used by HA base images)
RUN mkdir -p /etc/services.d/sems-plus
COPY run.sh /etc/services.d/sems-plus/run
RUN chmod +x /etc/services.d/sems-plus/run

WORKDIR /app

# Fallback for non-S6 bases (local development)
CMD ["/app/run.sh"]
