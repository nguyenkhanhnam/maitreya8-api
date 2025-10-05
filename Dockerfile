# Use the official Debian 13 (Trixie) slim image
FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, INCLUDING xvfb and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    python3 \
    python3-pip \
    python3-venv \
    xvfb \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Maitreya package
ARG MAITREYA_URL=https://github.com/martin-pe/maitreya8/releases/download/v8.2/maitreya8_8.2_debian13_amd64.deb
RUN wget -O /tmp/maitreya.deb ${MAITREYA_URL} && \
    apt-get update && \
    apt-get install -y /tmp/maitreya.deb && \
    rm /tmp/maitreya.deb && \
    rm -rf /var/lib/apt/lists/*

# --- Python Application Setup (Best Practice) ---

# 1. Create a non-root user to run the application
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# 2. Create and own the virtual environment
RUN python3 -m venv /home/appuser/venv
RUN chown -R appuser:appuser /home/appuser

# 3. Activate the virtual environment by adding it to the PATH
ENV PATH="/home/appuser/venv/bin:$PATH"

# 4. Copy requirements file and install dependencies into the venv
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the application code
COPY --chown=appuser:appuser app.py .

# 6. Switch to the non-root user
USER appuser

# Expose the port
EXPOSE 5000

# Set the command to run your API inside a virtual screen environment
CMD ["xvfb-run", "python", "-u", "app.py"]
