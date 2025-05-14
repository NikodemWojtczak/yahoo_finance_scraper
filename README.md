# Yahoo Finance Scraper

## Description
This project is a web scraper designed to fetch historical stock price data from Yahoo Finance. It utilizes Selenium for browser automation to navigate the website, log in, and extract data for specified stock tickers. The scraped data is then saved into CSV files. The project includes Docker support for easy setup and deployment.

## Project Structure
```
yahoo_finance_scraper/
├── .dockerignore         # Specifies intentionally untracked files that Docker should ignore
├── .env                  # Environment variables (YAHOO_EMAIL, YAHOO_PASSWORD) - Create this file
├── .github/              # GitHub specific files (e.g., workflows for CI/CD)
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── .pytest_cache/        # Pytest cache directory
├── Dockerfile            # Defines the Docker image for the scraper
├── README.md             # This file
├── entrypoint.sh         # Script executed when the Docker container starts
├── host_stock_data/      # Directory created by run.sh on the host to store scraped CSVs
├── requirements.txt      # Python dependencies
├── run.sh                # Script to build and run the Docker container
├── scraper.py            # The main Python script for scraping Yahoo Finance
├── eda.ipynb             # Jupyter notebook for exploratory data analysis
└── tests/                # Directory for test scripts (e.g., pytest)
```

## Prerequisites
- Python 3.10+
- Docker (recommended for running the scraper)
- The following Python libraries (automatically installed if using Docker or via `requirements.txt`):
    - `pandas`
    - `selenium`
    - `beautifulsoup4`
    - `openpyxl`
    - `lxml`
    - `pytest` (for development/testing)
    - `requests`
    - `python-dotenv`

## Setup

### 1. Clone the Repository (if applicable)
```bash
git clone <repository_url>
cd yahoo_finance_scraper
```

### 2. Environment Variables
The scraper requires Yahoo Finance login credentials. Create a `.env` file in the root of the `yahoo_finance_scraper` directory with the following content:

```env
YAHOO_EMAIL=\"your_yahoo_email@example.com\"
YAHOO_PASSWORD=\"your_yahoo_password\"
```
**Note:** This `.env` file is copied into the Docker image during the build process by the `Dockerfile`. Ensure it is present before building the Docker image if you intend to use the login feature. The `scraper.py` script also loads these variables using `python-dotenv` if run directly.

## Usage

### 1. Using Docker (Recommended)
The project includes a `run.sh` script that simplifies building the Docker image and running the container.

```bash
./run.sh
```
This script will:
1.  Build the Docker image named `yahoo-scraper`.
2.  Remove any old container named `yahoo-scraper-container`.
3.  Run a new container, mounting the local `./host_stock_data` directory to `/app/stock_data` inside the container.
4.  By default, it scrapes data for the following tickers: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, WMT.

**To scrape for different tickers using Docker:**
You can pass tickers as arguments to the `docker run` command. Modify the `run.sh` script or run `docker run` directly:
```bash
# First, build the image if you haven\'t already:
# docker build -t yahoo-scraper .

# Then run with custom tickers:
docker run \\
    --name yahoo-scraper-container \\
    -v \"$(pwd)/host_stock_data:/app/stock_data\" \\
    # Make sure your .env file is present in the build context or manage secrets appropriately
    yahoo-scraper --tickers YOUR_TICKER1 YOUR_TICKER2
```

The `entrypoint.sh` script inside the Docker container handles starting Xvfb (for headless browsing) and then executes `scraper.py` with the provided tickers.

### 2. Running the script directly (without Docker)
Ensure you have set up your Python environment and Chrome/ChromeDriver as mentioned in the "Setup" section.
Navigate to the `yahoo_finance_scraper` directory.
```bash
python scraper.py --tickers AAPL MSFT GOOGL
```
Or to scrape for the default list of tickers used in `run.sh`:
```bash
python scraper.py --tickers AAPL MSFT GOOGL AMZN META TSLA NVDA JPM V WMT
```
If no tickers are provided, the script might attempt to run with an empty list, which should be handled gracefully by `argparse` (nargs=\'*\').

## Output
The scraper creates a directory named `stock_data` (or `host_stock_data` on your host machine when using the `run.sh` script) and saves the historical data for each ticker in a separate CSV file.
The filename format is: `TICKER_historical_data_PERIOD.csv` (e.g., `AAPL_historical_data_1y.csv`).

The CSV files contain the following columns:
- Date
- Open
- High
- Low
- Close
- Adj_Close 
- Volume

---