ARG BUILD_FROM=python:3.12-slim
FROM ${BUILD_FROM}

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
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

WORKDIR /app

CMD ["/app/run.sh"]
