# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Chromium and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    # Chromium dependencies
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libcups2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    chromium \
    chromium-driver \
    xvfb \
    xauth \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env .
# Copy project code
COPY . .

# Copy entrypoint script separately to ensure it's present before RUN chmod
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set up Xvfb
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# CMD provides default arguments to the ENTRYPOINT (which in turn passes them to scraper.py)
# If 'docker run' provides arguments (like --tickers), they override this CMD.
# Since scraper.py handles the case of no tickers (via nargs='*'), an empty CMD is fine.
CMD []
