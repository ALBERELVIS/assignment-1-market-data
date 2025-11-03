"""
extractor.py
-------------
Module for downloading and standardizing market data from online APIs.

Currently uses the yfinance library (Yahoo Finance).
"""

import yfinance as yf
import pandas as pd

def download_price_series(tickers, start="2020-01-01", end=None):
    """
    Download historical price data for multiple tickers from Yahoo Finance.

    Parameters
    ----------
    tickers : list of str
        List of ticker symbols (e.g., ["AAPL", "MSFT", "^GSPC"])
    start : str
        Start date in 'YYYY-MM-DD' format
    end : str, optional
        End date (default: today)

    Returns
    -------
    dict
        Dictionary where each key is a ticker symbol and each value is a DataFrame
        with standardized columns: ["open", "high", "low", "close", "volume"]
    """
    all_data = {}
    for ticker in tickers:
        print(f"⬇️ Downloading data for {ticker}...")
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            print(f"⚠️ No data found for {ticker}")
            continue
        data = data.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume"
        })
        all_data[ticker] = data[["open", "high", "low", "close", "volume"]]
        print(f"✅ {ticker} data downloaded — {len(data)} rows.")
    return all_data
