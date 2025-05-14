#!/bin/bash

# Script to build and run the Docker container for the Yahoo Finance Scraper

IMAGE_NAME="yahoo-scraper"
CONTAINER_NAME="yahoo-scraper-container"
HOST_DATA_DIR="./host_stock_data"

mkdir -p "$HOST_DATA_DIR"

echo "Building Docker image: $IMAGE_NAME (forcing no-cache)..."
# Added --no-cache to ensure a fresh build
docker build  -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
fi

echo "Docker image built successfully."
echo ""
echo "Attempting to remove old container named $CONTAINER_NAME (if it exists)..."
docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "Running Docker container: $CONTAINER_NAME..."
echo "Scraped data will be saved to: $(pwd)/$HOST_DATA_DIR"

docker run \
    --name "$CONTAINER_NAME" \
    -v "$(pwd)/$HOST_DATA_DIR:/app/stock_data" \
    "$IMAGE_NAME" --tickers AAPL MSFT GOOGL AMZN META TSLA NVDA JPM V WMT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Scraper container ($CONTAINER_NAME) exited successfully (Code: $EXIT_CODE)."
else
    echo ""
    echo "Scraper container ($CONTAINER_NAME) exited with error (Code: $EXIT_CODE)."
fi

echo "To see logs, run: docker logs $CONTAINER_NAME"
echo "To remove the container, run: docker rm $CONTAINER_NAME"
echo "Data should be in: $(pwd)/$HOST_DATA_DIR"

exit $EXIT_CODE