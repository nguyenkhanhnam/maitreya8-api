# Use the official Debian 13 (Trixie) slim image
FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    python3 \
    python3-pip \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Maitreya package
ARG MAITREYA_URL=https://github.com/martin-pe/maitreya8/releases/download/v8.2/maitreya8_8.2_debian13_amd64.deb
RUN wget -O /tmp/maitreya.deb ${MAITREYA_URL} && \
    apt-get update && \
    apt-get install -y /tmp/maitreya.deb && \
    rm /tmp/maitreya.deb && \
    rm -rf /var/lib/apt/lists/*

# --- Python Application Setup (The Improved Part) ---

# Set the working directory
WORKDIR /app

# 1. Copy only the requirements file first
COPY requirements.txt .

# 2. Install the Python dependencies (this step will be cached)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your application code
COPY app.py .

# Expose the port
EXPOSE 5000

# Set the command to run your API
CMD ["python3", "-u", "app.py"]
