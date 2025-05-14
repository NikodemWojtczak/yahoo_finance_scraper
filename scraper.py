from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import os
from dotenv import load_dotenv
import argparse

load_dotenv()
yahoo_email = os.getenv("YAHOO_EMAIL")
yahoo_password = os.getenv("YAHOO_PASSWORD")

print(f"YAHOO_EMAIL: {yahoo_email}")
print(f"YAHOO_PASSWORD: {yahoo_password}")


def scrape_yahoo_finance_history(ticker_symbol, period="1y"):
    """
    Scrape historical stock price data from Yahoo Finance using Selenium

    Parameters:
    ticker_symbol (str): The stock ticker symbol
    period (str): Time period to fetch data for (default: "1y" for 1 year)

    Returns:
    pandas.DataFrame: The scraped historical data
    """
    # Generate output filename
    output_file = f"{ticker_symbol}_historical_data_{period}.csv"

    print(f"\n{'='*50}")
    print(f"Starting data collection for {ticker_symbol}")
    print(f"{'='*50}")

    # Set up Chrome options with more robust settings
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Set binary location for Chrome/Chromium
    chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")

    print(f"Initializing webdriver for {ticker_symbol}...")

    # Initialize the Chrome webdriver with service
    service = Service(
        executable_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    )
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Add a subtle delay to mimic human behavior
    def random_delay(min_seconds=1, max_seconds=3):
        time.sleep(random.uniform(min_seconds, max_seconds))

    try:
        # Navigate to Yahoo login page
        login_url = "https://login.yahoo.com/"
        print(f"Navigating to Yahoo login page for {ticker_symbol}...")
        driver.get(login_url)
        random_delay(2, 4)

        # Enter email
        try:
            print(f"Entering email for {ticker_symbol}...")
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='username']")
                )
            )
            email_input.send_keys(yahoo_email)
            random_delay(0.5, 1)

            # Click Next
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='signin']"))
            )
            next_button.click()
            print(f"Clicked 'Next' after email for {ticker_symbol}.")
            random_delay(2, 4)  # Wait for password field to appear
        except Exception as e:
            print(
                f"Error during email entry or 'Next' click for {ticker_symbol}: {str(e)}"
            )
            # driver.save_screenshot(f"{ticker_symbol}_email_error.png") # Optional: for debugging
            raise Exception(f"Could not enter email or click next for {ticker_symbol}")

        # Enter password
        try:
            print(f"Entering password for {ticker_symbol}...")
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='password']")
                )
            )
            password_input.send_keys(yahoo_password)
            random_delay(0.5, 1)

            # Click Sign In
            # Try a common selector first, then a more generic one.
            sign_in_button_selectors = [
                "button[name='verifyPassword']",  # Common name attribute
                "button#login-signin",  # Common ID
                "button[type='submit']",  # Generic submit button
            ]
            signed_in = False
            for selector in sign_in_button_selectors:
                try:
                    sign_in_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    sign_in_button.click()
                    print(
                        f"Clicked 'Sign In' for {ticker_symbol} using selector '{selector}'."
                    )
                    signed_in = True
                    random_delay(
                        3, 5
                    )  # Wait for login to process and potential redirects
                    break
                except Exception:
                    print(
                        f"Sign in button with selector '{selector}' not found or clickable for {ticker_symbol}."
                    )
                    continue

            if not signed_in:
                raise Exception(
                    f"Could not find or click Sign In button for {ticker_symbol}"
                )

        except Exception as e:
            print(
                f"Error during password entry or 'Sign In' click for {ticker_symbol}: {str(e)}"
            )
            # driver.save_screenshot(f"{ticker_symbol}_password_error.png") # Optional: for debugging
            raise Exception(
                f"Could not enter password or click sign in for {ticker_symbol}"
            )

        # Check for login success by looking for a known element on a logged-in page or URL change
        # For now, we'll just assume login was successful if no immediate error and proceed
        # A more robust check would be to navigate to a user-specific page or check for a welcome message.
        print(
            f"Login attempt completed for {ticker_symbol}. Proceeding to scrape data."
        )
        random_delay(2, 3)

        # Modify the user agent via JavaScript as well (extra layer of protection)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Calculate time parameters for the URL
        current_time = int(time.time())

        # Calculate period in seconds
        period_map = {
            "1y": 86400 * 365,  # 1 year in seconds
        }

        period_seconds = period_map.get(period, period_map["1y"])
        period1 = current_time - period_seconds
        period2 = current_time

        # Navigate directly to the URL with time parameters
        url = f"https://finance.yahoo.com/quote/{ticker_symbol}/history?period1={period1}&period2={period2}&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true"
        print(f"Navigating to Yahoo Finance for {ticker_symbol}...")
        driver.get(url)
        random_delay(2, 3)

        # Try to accept cookie consent dialog
        print(f"Checking for cookie dialogs for {ticker_symbol}...")
        cookie_selectors = [
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Agree')]",
            "//button[contains(@id, 'consent')]",
            "//button[contains(@class, 'accept')]",
            "//button[contains(@class, 'agree')]",
            "//button[contains(@class, 'consent')]",
        ]

        cookie_start_time = time.time()
        cookie_timeout = 5

        for selector in cookie_selectors:
            if time.time() - cookie_start_time > cookie_timeout:
                break

            try:
                cookie_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                cookie_button.click()
                random_delay(0.5, 1)
                break
            except Exception:
                continue

        # Wait for the data table
        print(f"Waiting for {ticker_symbol} data table to load...")
        table = None
        table_selectors = [
            "table[data-test='historical-prices']",
            "table.historical-prices",
            "//table[contains(@class, 'historical-prices')]",
            "//table[contains(@data-test, 'historical-prices')]",
            "//div[contains(@id, 'history')]//table",
            "//div[contains(@class, 'history')]//table",
        ]

        table_timeout = 15
        table_start_time = time.time()

        for selector in table_selectors:
            if time.time() - table_start_time > table_timeout:
                break

            try:
                if selector.startswith("//"):
                    table = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.XPATH, selector))
                    )
                else:
                    table = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                break
            except Exception:
                continue

        if table is None:
            try:
                table = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.TAG_NAME, "table"))
                )
            except Exception:
                raise Exception(
                    f"Could not find price history table for {ticker_symbol}"
                )

        # Try multiple approaches to extract data
        print(f"Extracting data for {ticker_symbol}...")

        # First try pandas read_html as it's the most reliable
        try:
            print(f"Attempting pandas extraction for {ticker_symbol}...")
            dfs = pd.read_html(driver.page_source)
            if dfs and len(dfs) > 0:
                df = dfs[0]  # Get the first table

                # Clean column names
                column_rename_map = {}
                for col_name_obj in df.columns:  # Iterate over original column objects
                    col_name = str(col_name_obj)  # Convert to string for processing

                    # Specific cleaning for "Adj Close" - must be checked first
                    if col_name.startswith("Adj Close"):
                        column_rename_map[col_name_obj] = "Adj_Close"
                    # Specific cleaning for "Close"
                    elif col_name.startswith("Close"):
                        column_rename_map[col_name_obj] = "Close"
                    else:
                        # General cleanup for other columns: remove asterisks and strip whitespace
                        cleaned_simple_col = col_name.replace("*", "").strip()
                        if (
                            cleaned_simple_col != col_name
                        ):  # only add to map if it actually changed
                            column_rename_map[col_name_obj] = cleaned_simple_col

                if column_rename_map:
                    df = df.rename(columns=column_rename_map)

                # Basic cleaning
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

                # Clean numeric columns
                numeric_cols = ["Open", "High", "Low", "Close", "Adj_Close"]
                for col in numeric_cols:
                    if col in df.columns:
                        if df[col].dtype == object:  # If string type
                            df[col] = df[col].str.replace(",", "")
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                # Process Volume column
                if "Volume" in df.columns:
                    if df["Volume"].dtype == object:  # If string type
                        df["Volume"] = df["Volume"].str.replace(",", "")
                    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

                # Drop rows with all NaN values
                df = df.dropna(how="all")

                # Save to CSV
                df.to_csv(output_file, index=False)
                print(
                    f"Successfully saved {ticker_symbol} data to {output_file} ({len(df)} rows)"
                )
                return df
        except Exception as e:
            print(f"Pandas extraction failed for {ticker_symbol}: {str(e)}")

        # If pandas fails, try BeautifulSoup
        try:
            print(f"Attempting BeautifulSoup extraction for {ticker_symbol}...")
            from bs4 import BeautifulSoup

            # Get the table HTML
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")

            # Get headers
            headers = []
            header_row = soup.find("tr")
            if header_row:
                headers = [th.text.strip() for th in header_row.find_all(["th"])]

            if not headers:
                headers = [
                    "Date",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Adj_Close",
                    "Volume",
                ]
            else:
                # Standardize header names
                cleaned_headers = []
                for h_original in headers:
                    h = str(
                        h_original
                    ).strip()  # Ensure string and strip leading/trailing whitespace

                    # Specific cleaning for "Adj Close" - must be checked first
                    if h.startswith("Adj Close"):
                        cleaned_headers.append("Adj_Close")
                    # Specific cleaning for "Close"
                    elif h.startswith("Close"):
                        cleaned_headers.append("Close")
                    else:
                        # General cleanup: remove asterisks (already stripped leading/trailing)
                        cleaned_headers.append(h.replace("*", ""))
                headers = cleaned_headers

            # Get data rows
            data_rows = []
            for row in soup.find_all("tr")[1:]:  # Skip header
                cells = row.find_all(["td"])
                if cells:
                    row_data = [cell.text.strip() for cell in cells]
                    if len(row_data) >= len(headers):
                        data_rows.append(row_data[: len(headers)])

            if data_rows:
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=headers)

                # Basic cleaning
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

                # Clean numeric columns
                numeric_cols = ["Open", "High", "Low", "Close", "Adj_Close"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].replace({",": ""}, regex=True)
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                # Process Volume column
                if "Volume" in df.columns:
                    df["Volume"] = df["Volume"].str.replace(",", "")
                    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

                # Drop rows with all NaN values
                df = df.dropna(how="all")

                # Save to CSV
                df.to_csv(output_file, index=False)
                print(
                    f"Successfully saved {ticker_symbol} data to {output_file} ({len(df)} rows)"
                )
                return df
        except Exception as e:
            print(f"BeautifulSoup extraction failed for {ticker_symbol}: {str(e)}")

        # If all extraction methods fail
        raise Exception(f"All data extraction methods failed for {ticker_symbol}")

    except Exception as e:
        print(f"Error processing {ticker_symbol}: {str(e)}")
        return None

    finally:
        # Close the browser
        print(f"Closing webdriver for {ticker_symbol}...")
        driver.quit()


def main():
    """
    Main function that scrapes data for 10 stock tickers
    """
    parser = argparse.ArgumentParser(
        description="Scrape historical stock data from Yahoo Finance."
    )
    parser.add_argument(
        "--tickers",
        nargs="*",
        help="List of stock tickers to scrape (e.g., AAPL MSFT GOOGL)",
    )
    args = parser.parse_args()
    tickers_to_scrape = args.tickers

    # Create a directory for output files
    output_dir = "stock_data"
    os.makedirs(output_dir, exist_ok=True)

    # Change to the output directory
    os.chdir(output_dir)

    # List of 10 stock tickers to scrape
    tickers = tickers_to_scrape  # Use the provided or default tickers

    # Print start message
    print("\nStarting Yahoo Finance Historical Data Scraper")
    print(
        f"Scraping 1-year historical data for {len(tickers)} stocks: {', '.join(tickers)}"
    )
    print(f"Output directory: {os.path.abspath(output_dir)}\n")

    # Track successful and failed tickers
    successful = []
    failed = []

    # Process each ticker
    for i, ticker in enumerate(tickers, 1):
        print(f"\nProcessing ticker {i} of {len(tickers)}: {ticker}")

        # Add a delay between tickers to avoid rate limiting
        if i > 1:
            delay = random.uniform(3, 7)
            print(f"Waiting {delay:.1f} seconds before processing next ticker...")
            time.sleep(delay)

        # Attempt to scrape data for this ticker
        df = scrape_yahoo_finance_history(ticker)

        if df is not None and not df.empty:
            successful.append(ticker)
        else:
            failed.append(ticker)

    # Print summary
    print("\n" + "=" * 50)
    print("SCRAPING COMPLETE")
    print("=" * 50)
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successful: {len(successful)} ({', '.join(successful)})")
    print(f"Failed: {len(failed)} ({', '.join(failed) if failed else 'None'})")
    print(f"Data saved to: {os.path.abspath(output_dir)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
