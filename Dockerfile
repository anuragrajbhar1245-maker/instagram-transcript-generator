# Base image: Python 3.12 slim
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=10000 \
    HOST=0.0.0.0 \
    WHISPER_MODEL=tiny

# Install system dependencies (FFmpeg is required for audio extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny and base models into container cache
# Pre-caching ensures instantaneous startup in cloud environments
RUN python -c "from faster_whisper import download_model; download_model('tiny'); download_model('base')"

# Copy application source code
COPY . /app

# Ensure temp directory exists with write permissions
RUN mkdir -p /app/temp && chmod 777 /app/temp

# Expose default ports (10000 for Render, 8000 for local Docker, 7860 for HF)
EXPOSE 10000
EXPOSE 8000
EXPOSE 7860

# Start FastAPI server
CMD ["python", "app.py"]
