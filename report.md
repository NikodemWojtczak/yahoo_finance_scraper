# Mini-Challenge Project Report: Yahoo Finance Scraper

# 1. Main Ideas of the Mini-Challenge

The core idea of this mini-challenge was to develop a robust web scraper capable of extracting historical stock data from Yahoo Finance. The project aimed to automate the process of fetching daily stock information (Open, High, Low, Close, Adjusted Close, Volume) for specified ticker symbols over a defined period (e.g., 1 year). A key component involved handling the complexities of web scraping, including website login, dynamic content loading, and data cleaning.

# 2. Relevance, Originality, and Usefulness

**Relevance to Real-World Applications:**
Access to historical stock data is fundamental in various financial applications. This includes:
*   **Quantitative Analysis:** Building and backtesting trading strategies.
*   **Financial Modeling:** Valuing companies and forecasting market movements.
*   **Risk Management:** Assessing volatility and potential drawdowns.
*   **Academic Research:** Studying market behavior and economic trends.
*   **Personal Investment:** Enabling individual investors to perform their own analysis.

Automating this data collection process, as done in this project, saves significant time and effort compared to manual data gathering.

**Originality:**
While web scraping itself is a known technique, the originality of this solution lies in its specific implementation for Yahoo Finance, which often updates its website structure, requiring adaptable scraping logic. The project demonstrates handling login procedures and navigating dynamic content, which are common hurdles in web scraping. The combination of Selenium for browser automation and Pandas for data manipulation and cleaning provides a practical approach.

**Usefulness:**
The solution is highly useful for anyone needing reliable historical stock data.
*   It provides data in a clean, structured CSV format, ready for analysis.
*   The scraper can be extended to fetch data for multiple tickers and different time periods.
*   By automating data acquisition, it allows users to focus on data analysis and decision-making rather than data collection.

# 3. Data Structure

The collected data for each stock ticker is saved as a CSV (Comma Separated Values) file. The filename typically follows the pattern: `[TICKER_SYMBOL]_historical_data_[PERIOD].csv` (e.g., `AAPL_historical_data_1y.csv`).

Each CSV file contains the following columns:

*   **Date:** The date of the trading day (formatted as YYYY-MM-DD after cleaning).
*   **Open:** The opening price of the stock for the day.
*   **High:** The highest price the stock reached during the day.
*   **Low:** The lowest price the stock reached during the day.
*   **Close:** The closing price of the stock for the day. (Original Yahoo Finance column might be "Close Close price adjusted for splits.")
*   **Adj_Close:** The adjusted closing price, accounting for dividends and stock splits. (Original Yahoo Finance column might be "Adj Close Adjusted close price adjusted for splits and dividend and/or capital gain distributions.")
*   **Volume:** The number of shares traded during the day.

The `scraper.py` script ensures that column names are cleaned (e.g., removing asterisks, standardizing "Adj Close" to "Adj_Close"). Numerical columns (Open, High, Low, Close, Adj_Close, Volume) are converted to numeric types, and the 'Date' column is converted to a datetime object. Any rows that are entirely NaN (Not a Number) are dropped.

# 4. Tests Conducted

The project includes a comprehensive test suite in `yahoo_finance_scraper/tests/test_scraper.py` using `pytest` and `unittest.mock`. The tests cover various aspects of the scraper's functionality:

*   **`test_scraper_successful_run`**:
    *   Mocks Selenium's WebDriver, WebDriverWait, and `pd.read_html`.
    *   Simulates a successful login sequence (email, password, cookie consent) and table finding.
    *   Verifies interactions with mocked web elements (e.g., `send_keys`, `click`).
    *   Asserts that `pd.read_html` is called with the driver's page source.
    *   Checks if the output CSV file is created in the temporary test directory.
    *   Asserts that column names are correctly cleaned (e.g., "Close Close price adjusted for splits." becomes "Close").
    *   Verifies that data types are correct after cleaning (e.g., 'Date' is datetime, 'Close' and 'Volume' are numeric).
    *   Checks the number of calls to `WebDriverWait().until` for the expected sequence of operations.

*   **`test_handling_malformed_data_and_cleaning`**:
    *   Simulates `pd.read_html` returning a DataFrame with "dirty" headers and malformed data (e.g., "N/A", "-", "Invalid Date", numbers with extra commas/periods, "No Volume").
    *   Asserts that the scraper still produces an output file.
    *   Verifies that column names are cleaned.
    *   Checks that the data cleaning logic correctly handles malformed entries, converting them to `NaN` or appropriate numeric/datetime values where possible (e.g., 'Invalid Date' becomes NaT, 'N/A' in 'Open' becomes NaN, '1.300.000' in 'Volume' becomes NaN).

*   **`test_extraction_failure_paths`**:
    *   **Scenario 0 (No Table Found):** Mocks `WebDriverWait().until` to raise a `TimeoutException` when trying to find the data table, simulating that no table selectors (specific or generic fallback) succeed. Asserts that `scrape_yahoo_finance_history` returns `None`.
    *   **Scenario 1 (Pandas and BeautifulSoup Fail):** Mocks the table element to be "found", but then `pd.read_html` returns an empty list (no tables extracted), and subsequently, BeautifulSoup (`bs4.BeautifulSoup().find()`) also fails to find necessary elements (e.g., header row). Asserts that the scraper returns `None`.
    *   **Scenario 2 (Pandas Returns DataFrame with "Wrong" but Cleanable Columns, BS Fails):** Mocks `pd.read_html` to return a DataFrame with unexpected column names (but with "dirty" formatting that the scraper can clean, e.g., "ColA * "). BeautifulSoup is mocked to fail. Asserts that the scraper successfully processes and returns the DataFrame from `pd.read_html` after cleaning its headers (e.g., "ColA * " becomes "ColA").

*   **`test_main_function_calls_scraper_for_tickers`**:
    *   Mocks `scraper.scrape_yahoo_finance_history`, `os.makedirs`, and `os.chdir`.
    *   Patches `sys.argv` to simulate command-line arguments with a list of test tickers.
    *   Asserts that `scraper_main()` calls `scrape_yahoo_finance_history` once for each ticker provided.
    *   Verifies that the calls were made with the correct ticker symbols.
    *   Checks that `os.makedirs` and `os.chdir` are called to set up the output directory (`stock_data`).
    *   Simulates different outcomes from `scrape_yahoo_finance_history` (success and failure) to ensure the main loop handles them.

**Overall Coverage:**

The tests effectively cover:
*   The path of successful data scraping and cleaning.
*   Robustness in handling malformed or unexpected data formats from Yahoo Finance.
*   Graceful failure when critical data elements (like the main table) cannot be found or extracted by any method.
*   The correct functioning of the main script's argument parsing and iteration over multiple tickers.
*   File system interactions (directory creation, changing directory, file saving).
*   Crucial data cleaning steps like header normalization and data type conversion.

# 5. Exploratory Data Analysis Insights

## 1. Data Preparation and Integrity

### Dataset Overview
- **Initial Size:** 252 daily records of Apple's stock performance
- **Features:** Open, High, Low, Close, Adj_Close, Volume
- **Final Size:** 251 observations after cleaning

### Data Cleaning Process
- Removed one row with entirely missing values
- Addressed minor missing data points in numerical columns
- Handled 228 missing entries in Date column
- Applied linear interpolation for numerical missing values
- Resulted in a complete, clean dataset ready for analysis

## 2. Statistical Overview (2024-05-14 to 2025-05-14)

### Price Analysis
| Metric | Value |
|--------|-------|
| Price Range | $172.19 - $258.40 |
| Mean Price | $222.20 |
| Standard Deviation | $16.51 |

### Volume Analysis
- **Average Daily Volume:** ~56 million shares
- **Maximum Daily Volume:** ~319 million shares
- Indicates significant trading activity variation

## 3. Visualization Insights

### Chart Types
- **Candlestick Charts**
  - Full history view
  - 30-day recent view
  - OHLC data visualization
  - Volume overlay

### Technical Indicators
1. **Moving Averages (MAs)**
   - Price smoothing
   - Trend direction identification

2. **Bollinger Bands**
   - Volatility assessment
   - Overbought/oversold conditions

3. **Daily Returns & Volume Analysis**
   - Price movement patterns
   - Trading activity correlation

### Interactive Features
- **Plotly Integration**
  - Dynamic candlestick charts
  - Zoom and pan capabilities
  - Data point inspection
  - Moving average overlays

## 4. Trading Strategy and Backtesting

### Technical Indicators
1. **MACD (Moving Average Convergence Divergence)**
   - Momentum identification
   - Trend change detection
   - Bullish: MACD > Signal Line
   - Bearish: MACD < Signal Line

2. **RSI (Relative Strength Index)**
   - Overbought threshold: > 70
   - Oversold threshold: < 30

### Strategy Rules
| Signal | Conditions |
|--------|------------|
| BUY | MACD crosses above Signal Line AND RSI < 70 |
| SELL | MACD crosses below Signal Line AND RSI > 30 |

### Backtesting Results
- **Comparison:** MACD-RSI strategy vs. Buy-and-hold
- **Outcome:** Buy-and-hold strategy outperformed
- **Conclusion:** No advantage over passive investment approach for this dataset and timeframe