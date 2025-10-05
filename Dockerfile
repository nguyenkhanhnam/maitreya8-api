# Use the official Debian 13 (Trixie) slim image for a smaller footprint
FROM debian:13-slim

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies needed to download and install the package, plus Python for our API
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    python3 \
    python3-pip \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set the URL for the Maitreya Debian package
ARG MAITREYA_URL=https://github.com/martin-pe/maitreya8/releases/download/v8.2/maitreya8_8.2_debian13_amd64.deb

# Download and install the Maitreya .deb package
RUN wget -O /tmp/maitreya.deb ${MAITREYA_URL} && \
    apt-get update && \
    apt-get install -y /tmp/maitreya.deb && \
    rm /tmp/maitreya.deb && \
    rm -rf /var/lib/apt/lists/*

# Set up the working directory for our API
WORKDIR /app

# Copy your Flask API application code into the image
COPY app.py .

# Install Flask
RUN pip install --no-cache-dir Flask

# Expose the port the app runs on
EXPOSE 5000

# Set the command to run your API when the container starts
CMD ["python3", "-u", "app.py"]
