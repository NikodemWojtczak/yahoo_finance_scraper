import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scraper import scrape_yahoo_finance_history, main as scraper_main
from dotenv import load_dotenv

load_dotenv()
yahoo_email = os.getenv("YAHOO_EMAIL")
yahoo_password = os.getenv("YAHOO_PASSWORD")

TEST_OUTPUT_DIR_NAME = "test_temp_scraper_output"


@pytest.fixture(scope="function")
def temp_test_dir(tmp_path):
    original_cwd = os.getcwd()
    test_output_dir = tmp_path / TEST_OUTPUT_DIR_NAME
    test_output_dir.mkdir()
    os.chdir(test_output_dir)
    yield test_output_dir
    os.chdir(original_cwd)


@pytest.fixture
def mock_driver_page_source_and_table_attribute():
    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.page_source = "<html><body><table id='correct_table_for_page_source'><tr><th>Date</th><th>Close</th></tr><tr><td>2023-01-01</td><td>100</td></tr></table></body></html>"
    mock_table_element_found = MagicMock()
    mock_table_element_found.get_attribute.return_value = "<table><tr><th>Date</th><th>Close</th><th>Volume</th></tr><tr><td>Jan 01, 2023</td><td>151.50</td><td>100,000</td></tr></table>"
    return mock_driver, mock_table_element_found


@patch("scraper.webdriver.Chrome")
@patch("scraper.WebDriverWait")
@patch("scraper.pd.read_html")
def test_scraper_successful_run(
    mock_read_html,
    mock_webdriverwait_class,
    mock_webdriver_chrome_class,
    temp_test_dir,
    mock_driver_page_source_and_table_attribute,
):
    mock_driver_instance, mock_table_element = (
        mock_driver_page_source_and_table_attribute
    )
    mock_webdriver_chrome_class.return_value = mock_driver_instance

    # Mock elements for login sequence + cookie + table
    mock_email_input = MagicMock()
    mock_next_button = MagicMock()
    mock_password_input = MagicMock()
    mock_signin_button = MagicMock()
    mock_cookie_button = MagicMock()

    mock_webdriverwait_class.return_value.until.side_effect = [
        mock_email_input,  # For username input
        mock_next_button,  # For "next" after username
        mock_password_input,  # For password input
        mock_signin_button,  # For "sign in" button
        mock_cookie_button,  # For cookie consent
        mock_table_element,  # For data table
    ]

    # Simulate dirty headers from Yahoo
    sample_data_dict_dirty_headers = {
        "Date": ["Jan 01, 2023"],
        "Open": ["150.00"],
        "High": ["152.00"],
        "Low": ["149.00"],
        "Close Close price adjusted for splits.": ["151.50"],
        "Adj Close Adjusted close price adjusted for splits and dividend and/or capital gain distributions.": [
            "151.00"
        ],
        "Volume": ["100,000"],
    }
    mock_df_from_read_html = pd.DataFrame(sample_data_dict_dirty_headers)
    mock_read_html.return_value = [mock_df_from_read_html]

    ticker = "TESTAAPL"
    result_df = scrape_yahoo_finance_history(ticker_symbol=ticker, period="1y")

    assert (
        result_df is not None
    ), "Scraper returned None, check stdout for errors from SUT."
    assert not result_df.empty

    # Check call count for WebDriverWait().until()
    # username, next, password, signin, cookie, table = 6 calls
    assert mock_webdriverwait_class.return_value.until.call_count == 6

    mock_email_input.send_keys.assert_called_with(yahoo_email)
    mock_next_button.click.assert_called_once()
    mock_password_input.send_keys.assert_called_with(yahoo_password)
    mock_signin_button.click.assert_called_once()

    mock_read_html.assert_called_once_with(mock_driver_instance.page_source)

    expected_file_path = os.path.join(temp_test_dir, f"{ticker}_historical_data_1y.csv")
    assert os.path.exists(expected_file_path)

    # Assert cleaned column names
    expected_columns = ["Date", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]
    assert all(col in result_df.columns for col in expected_columns)
    assert len(result_df.columns) == len(expected_columns)

    assert pd.api.types.is_datetime64_any_dtype(result_df["Date"])
    assert pd.api.types.is_numeric_dtype(result_df["Close"])
    assert result_df["Volume"].iloc[0] == 100000


@patch("scraper.webdriver.Chrome")
@patch("scraper.WebDriverWait")
@patch("scraper.pd.read_html")
def test_handling_malformed_data_and_cleaning(
    mock_read_html,
    mock_webdriverwait_class,
    mock_webdriver_chrome_class,
    temp_test_dir,
    mock_driver_page_source_and_table_attribute,
):
    mock_driver_instance, mock_table_element = (
        mock_driver_page_source_and_table_attribute
    )
    mock_webdriver_chrome_class.return_value = mock_driver_instance

    # Mock elements for login sequence + cookie + table
    mock_email_input = MagicMock()
    mock_next_button = MagicMock()
    mock_password_input = MagicMock()
    mock_signin_button = MagicMock()
    mock_cookie_button = MagicMock()

    mock_webdriverwait_class.return_value.until.side_effect = [
        mock_email_input,  # For username input
        mock_next_button,  # For "next" after username
        mock_password_input,  # For password input
        mock_signin_button,  # For "sign in" button
        mock_cookie_button,  # For cookie consent
        mock_table_element,  # For data table
    ]

    # Simulate dirty headers with malformed data
    malformed_data_source_dirty_headers = {
        "Date": ["Mar 10, 2023", "Invalid Date", "Mar 12, 2023", "Mar 13, 2023"],
        "Open": ["100.00", "101,00", "N/A", "103.50"],
        "High": ["102.50", "103.00", "-", "105.00"],
        "Low": ["99.50", "100.50", "98.00", "102.00"],
        "Close Close price adjusted for splits.": [
            "101.20",
            "102.30",
            "99.00",
            "104.00",
        ],
        "Adj Close Adjusted close price adjusted for splits and dividend and/or capital gain distributions.": [
            "101.20",
            "102.30",
            "99.00",
            "104.00",
        ],
        "Volume": ["1,200,000", "1.300.000", "1,000", "No Volume"],
    }
    mock_df_malformed = pd.DataFrame(malformed_data_source_dirty_headers)
    mock_read_html.return_value = [mock_df_malformed]
    mock_driver_instance.page_source = "dummy html for malformed test"

    ticker = "MALFORMED"
    result_df = scrape_yahoo_finance_history(ticker_symbol=ticker, period="1y")
    assert result_df is not None

    # Assert cleaned column names
    expected_columns = ["Date", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]
    assert all(col in result_df.columns for col in expected_columns)
    assert len(result_df.columns) == len(expected_columns)

    # Existing assertions for data cleaning (should still hold with cleaned column names)
    assert pd.isna(result_df.loc[result_df["Open"] == 10100.0, "Date"].iloc[0])
    assert result_df.loc[1, "Open"] == 10100.0
    assert pd.isna(result_df.loc[2, "Open"])
    assert pd.isna(result_df.loc[2, "High"])
    # Corrected assertion for Volume '1.300.000' which becomes NaN
    assert pd.isna(
        result_df.loc[1, "Volume"]
    ), "Volume '1.300.000' should become NaN after cleaning"
    assert pd.isna(result_df.loc[3, "Volume"])

    expected_file_path = os.path.join(temp_test_dir, f"{ticker}_historical_data_1y.csv")
    assert os.path.exists(expected_file_path)


@patch("scraper.webdriver.Chrome")
@patch("scraper.WebDriverWait")
@patch("scraper.pd.read_html")
@patch("bs4.BeautifulSoup")
def test_extraction_failure_paths(
    mock_bs_constructor,
    mock_read_html,
    mock_webdriverwait_class,
    mock_webdriver_chrome_class,
    temp_test_dir,
    mock_driver_page_source_and_table_attribute,
):
    mock_driver_instance, mock_table_element = (
        mock_driver_page_source_and_table_attribute
    )
    mock_webdriver_chrome_class.return_value = mock_driver_instance

    # Mock elements for login sequence (common for all scenarios below)
    mock_email_input = MagicMock()
    mock_next_button = MagicMock()
    mock_password_input = MagicMock()
    mock_signin_button = MagicMock()
    mock_cookie_button = MagicMock()  # Also common, for cookie consent part

    login_sequence_mocks = [
        mock_email_input,
        mock_next_button,
        mock_password_input,
        mock_signin_button,
        mock_cookie_button,  # Cookie consent mock
    ]

    # Scenario 0: All table selectors fail, including generic fallback
    # Login part succeeds, then cookie consent, then table finding fails.
    mock_webdriverwait_class.return_value.until.side_effect = login_sequence_mocks + [
        TimeoutException("Mocked: Table not found by any selector")
    ]
    ticker_s0 = "NO_TABLE_AT_ALL"
    assert scrape_yahoo_finance_history(ticker_symbol=ticker_s0, period="1y") is None
    # Expected WebDriverWait calls: login (4) + cookie (1) + table find attempts (at least 1, up to N selectors + generic)
    # Minimum 4+1+1 = 6 calls if first table selector check leads to TimeoutException.
    assert (
        mock_webdriverwait_class.return_value.until.call_count
        >= len(login_sequence_mocks) + 1
    )

    # Reset call count for the next scenario
    mock_webdriverwait_class.return_value.until.reset_mock()

    # Scenario 1: Table element is "found", but pd.read_html returns [], then BS fails
    # Login succeeds, cookie consent, table element found, then extraction fails.
    mock_webdriverwait_class.return_value.until.side_effect = login_sequence_mocks + [
        mock_table_element
    ]
    mock_read_html.return_value = []  # Pandas returns no tables
    mock_soup_instance = MagicMock()
    mock_soup_instance.find.return_value = None  # BS find header row fails
    mock_bs_constructor.return_value = mock_soup_instance
    ticker_s1 = "EMPTYTABLE_S1"
    assert (
        scrape_yahoo_finance_history(ticker_symbol=ticker_s1, period="1y") is None
    ), "Should return None when pd.read_html and BS both effectively fail after table element is found"
    assert (
        mock_webdriverwait_class.return_value.until.call_count
        == len(login_sequence_mocks) + 1
    )

    # Reset mocks for the next scenario
    mock_webdriverwait_class.return_value.until.reset_mock()
    mock_read_html.reset_mock()
    mock_bs_constructor.reset_mock()

    # Scenario 2: pd.read_html returns a DataFrame with "wrong" columns (but dirty headers that get cleaned), BS is mocked to fail
    # Login, cookie, table element found, pandas returns a df with unexpected but cleanable headers.
    mock_webdriverwait_class.return_value.until.side_effect = login_sequence_mocks + [
        mock_table_element
    ]

    wrong_cols_data_dirty_headers = {
        "ColA * ": [1, 2],
        "Another Col": [3, 4],
    }  # Dirty headers
    wrong_cols_df_dirty = pd.DataFrame(wrong_cols_data_dirty_headers)
    mock_read_html.return_value = [wrong_cols_df_dirty]

    # Mock BS to also fail so SUT doesn't successfully use it
    mock_bs_table_element_s2 = MagicMock()
    mock_bs_table_element_s2.find_all.return_value = []  # No rows for BS
    mock_soup_instance_s2 = MagicMock()
    mock_soup_instance_s2.find.return_value = (
        mock_bs_table_element_s2  # No header row for BS
    )
    mock_bs_constructor.return_value = mock_soup_instance_s2

    ticker_s2 = "WRONGTABLE_S2"
    result_df_s2 = scrape_yahoo_finance_history(ticker_symbol=ticker_s2, period="1y")

    # Assert that the returned DataFrame is the one from pd.read_html (after SUT's header cleaning)
    expected_cleaned_columns_s2 = ["ColA", "Another Col"]  # Expected cleaned headers
    assert all(col in result_df_s2.columns for col in expected_cleaned_columns_s2)
    assert len(result_df_s2.columns) == len(expected_cleaned_columns_s2)
    assert result_df_s2["ColA"].tolist() == [1, 2]
    assert result_df_s2["Another Col"].tolist() == [3, 4]
    assert (
        mock_webdriverwait_class.return_value.until.call_count
        == len(login_sequence_mocks) + 1
    )


@patch("scraper.scrape_yahoo_finance_history")
@patch("scraper.os.makedirs")
@patch("scraper.os.chdir")
def test_main_function_calls_scraper_for_tickers(
    mock_chdir, mock_makedirs, mock_scrape_func, temp_test_dir
):
    # Define test tickers that will be passed via command line arguments
    test_tickers_for_main = ["TESTMAIN1", "TESTMAIN2"]
    cli_args = ["scraper.py", "--tickers"] + test_tickers_for_main

    mock_df_success = pd.DataFrame({"Date": ["2023-01-01"], "Close": [100]})
    # Adjust side_effects to match the number of test_tickers_for_main
    # For example, one success and one failure
    side_effects_list = [mock_df_success, None]
    mock_scrape_func.side_effect = side_effects_list

    # Patch sys.argv for the duration of the scraper_main() call
    with patch.object(sys, "argv", cli_args):
        scraper_main()

    # Assert that scrape_yahoo_finance_history was called for each test ticker
    assert mock_scrape_func.call_count == len(test_tickers_for_main)

    # Check that the function was called with the correct ticker names
    # This is a more robust way to check calls than just assert_any_call with the first element
    called_tickers = [call_args[0][0] for call_args in mock_scrape_func.call_args_list]
    assert sorted(called_tickers) == sorted(test_tickers_for_main)

    mock_makedirs.assert_called_with("stock_data", exist_ok=True)
    mock_chdir.assert_called_with("stock_data")
