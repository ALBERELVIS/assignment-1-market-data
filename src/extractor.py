"""
extractor.py
-------------
This module fetches and standardizes market data (stocks and indices)
using the Yahoo Finance API through yfinance.

Author: ALBERELVIS
"""

import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Union


@dataclass
class MarketData:
    """Standard structure for historical price series."""
    ticker: str
    data: pd.DataFrame

    def __post_init__(self):
        # Standardize column names
        self.data.columns = [c.lower().replace(" ", "_") for c in self.data.columns]
        # Keep only the key columns
        self.data = self.data[["open", "high", "low", "close", "volume"]]
        # Sort by date just in case
        self.data = self.data.sort_index()


def download_price_series(
    tickers: Union[str, List[str]],
    start: str = "2020-01-01",
    end: str = None,
    interval: str = "1d"
) -> Dict[str, MarketData]:
    """
    Download historical data for one or multiple tickers.

    Returns a dictionary: {ticker: MarketData}
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    result = {}
    for t in tickers:
        print(f"⬇️ Downloading data for {t}...")
        df = yf.download(t, start=start, end=end, interval=interval, progress=False)
        if not df.empty:
            result[t] = MarketData(ticker=t, data=df)
            print(f"✅ {t} data downloaded — {len(df)} rows.")
        else:
            print(f"⚠️ Warning: No data found for {t}")
    return result

