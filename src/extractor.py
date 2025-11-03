"""
extractor.py
-------------
Framework extensible de extractores + implementación para Yahoo Finance (yfinance).

Características:
- Registry/adapters: añade nuevos extractores con @register_extractor("nombre").
- GenericCallableExtractor para envolver cualquier función HTTP/SDK.
- download_price_series admite data_type: 'prices' (por defecto), 'dividends',
  'splits', 'info', 'financials', 'balance_sheet', 'cashflow', 'earnings',
  'sustainability', 'recommendations', 'holders', etc.
- Estandariza DataFrames de precios a columnas: ['open','high','low','close','adj_close','volume'] y guarda metadatos en df.attrs.
- Soporta descarga paralela.
"""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Dict, List, Optional
import pandas as pd
import numpy as np
import yfinance as yf

# Registro de extractores
_EXTRACTOR_REGISTRY: Dict[str, type] = {}

def register_extractor(name: str):
    def _decorator(cls):
        _EXTRACTOR_REGISTRY[name] = cls
        return cls
    return _decorator

def get_extractor(name: str):
    cls = _EXTRACTOR_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"No extractor registered under name '{name}'")
    return cls

def _standardize_prices_df(df: pd.DataFrame, symbol: str, source: str) -> pd.DataFrame:
    """Estandariza DataFrame de precios: index datetime, columnas mínimas, metadatos en attrs."""
    df = df.copy()
    # if date column present -> set index
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            raise ValueError("DataFrame index is not datetime-like and no 'date' column present.")
    # rename known variants
    col_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ("open", "open_price", "o"):
            col_map[c] = "open"
        elif lc in ("high", "h"):
            col_map[c] = "high"
        elif lc in ("low", "l"):
            col_map[c] = "low"
        elif lc in ("close", "close_price", "c"):
            col_map[c] = "close"
        elif lc in ("adj close", "adj_close", "adjusted_close"):
            col_map[c] = "adj_close"
        elif lc in ("volume", "vol"):
            col_map[c] = "volume"
        elif lc in ("dividends", "dividend"):
            col_map[c] = "dividends"
        elif lc in ("splits",):
            col_map[c] = "splits"
    if col_map:
        df = df.rename(columns=col_map)
    # ensure minimal price columns exist
    for req in ["open", "high", "low", "close", "adj_close", "volume"]:
        if req not in df.columns:
            df[req] = np.nan
    df = df.sort_index()
    # metadata
    df.attrs["symbol"] = symbol
    df.attrs["source"] = source
    df.attrs["retrieved_at"] = datetime.utcnow().isoformat()
    return df

class ExtractorBase(ABC):
    """Interfaz: implementar fetch(symbol, start, end, data_type, **kwargs) -> pd.DataFrame"""
    def __init__(self, **kwargs):
        self.config = kwargs

    @abstractmethod
    def fetch(self, symbol: str, start: Optional[str] = None, end: Optional[str] = None,
              data_type: str = "prices", **kwargs) -> pd.DataFrame:
        pass

@register_extractor("yfinance")
class YFinanceExtractor(ExtractorBase):
    """Extractor para yfinance (Yahoo). Soporta muchos data_type."""
    def fetch(self, symbol: str, start: Optional[str] = None, end: Optional[str] = None,
              data_type: str = "prices", **kwargs) -> pd.DataFrame:
        t = yf.Ticker(symbol)
        # prices
        if data_type == "prices":
            df = t.history(start=start, end=end, auto_adjust=False)
            if (df is None) or df.empty:
                df = yf.download(symbol, start=start, end=end, progress=False)
            if df is None or df.empty:
                return pd.DataFrame()  # caller handles empty
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Adj Close": "adj_close", "Volume": "volume",
                "Dividends": "dividends", "Stock Splits": "splits"
            })
            return _standardize_prices_df(df, symbol, source="yfinance")
        # dividends / splits are often in the history but also accessible
        if data_type == "dividends":
            series = t.dividends
            if isinstance(series, pd.Series):
                df = series.rename("dividends").to_frame()
                return _standardize_prices_df(df, symbol, source="yfinance")
            return pd.DataFrame()
        if data_type == "splits":
            series = t.splits
            if isinstance(series, pd.Series):
                df = series.rename("splits").to_frame()
                return _standardize_prices_df(df, symbol, source="yfinance")
            return pd.DataFrame()
        # metadata / fundamentals: return DataFrame (single row) with attrs set
        mapping = {
            "info": getattr(t, "info", None),
            "financials": getattr(t, "financials", None),
            "quarterly_financials": getattr(t, "quarterly_financials", None),
            "balance_sheet": getattr(t, "balance_sheet", None),
            "quarterly_balance_sheet": getattr(t, "quarterly_balance_sheet", None),
            "cashflow": getattr(t, "cashflow", None),
            "quarterly_cashflow": getattr(t, "quarterly_cashflow", None),
            "earnings": getattr(t, "earnings", None),
            "quarterly_earnings": getattr(t, "quarterly_earnings", None),
            "sustainability": getattr(t, "sustainability", None),
            "recommendations": getattr(t, "recommendations", None),
            "major_holders": getattr(t, "major_holders", None),
            "institutional_holders": getattr(t, "institutional_holders", None),
        }
        if data_type in mapping:
            raw = mapping[data_type]
            # if dict -> single-row DataFrame
            if isinstance(raw, dict):
                df = pd.DataFrame([raw])
                df.attrs["symbol"] = symbol
                df.attrs["source"] = "yfinance"
                df.attrs["data_type"] = data_type
                return df
            # if DataFrame/Series -> return with attrs
            if isinstance(raw, (pd.DataFrame, pd.Series)):
                df = pd.DataFrame(raw) if isinstance(raw, pd.Series) else raw.copy()
                df.attrs["symbol"] = symbol
                df.attrs["source"] = "yfinance"
                df.attrs["data_type"] = data_type
                return df
            return pd.DataFrame()
        # fallback / unsupported
        raise ValueError(f"yfinance extractor does not support data_type '{data_type}'")

class GenericCallableExtractor(ExtractorBase):
    """Envuelve cualquier función fetcher(...) y normalizer(...)."""
    def __init__(self, fetcher: Callable, normalizer: Optional[Callable] = None, source_name: str = "generic", **kwargs):
        super().__init__(**kwargs)
        self.fetcher = fetcher
        self.normalizer = normalizer or (lambda raw, symbol, source: _standardize_prices_df(pd.DataFrame(raw), symbol, source))
        self.source_name = source_name

    def fetch(self, symbol: str, start: Optional[str] = None, end: Optional[str] = None,
              data_type: str = "prices", **kwargs) -> pd.DataFrame:
        raw = self.fetcher(symbol=symbol, start=start, end=end, data_type=data_type, **kwargs)
        df = self.normalizer(raw, symbol, self.source_name)
        return df

def download_price_series(tickers: List[str],
                          start: Optional[str] = "2020-01-01",
                          end: Optional[str] = None,
                          source: str = "yfinance",
                          data_type: str = "prices",
                          parallel: bool = True,
                          max_workers: int = 8,
                          extractor_kwargs: Optional[Dict] = None) -> Dict[str, pd.DataFrame]:
    """
    Descarga múltiples símbolos usando el extractor registrado.
    - source: nombre del extractor (ej. 'yfinance')
    - data_type: 'prices','dividends','splits','info', etc.
    Devuelve dict {symbol: DataFrame}
    """
    extractor_kwargs = extractor_kwargs or {}
    ExtractorCls = get_extractor(source)
    extractor = ExtractorCls(**extractor_kwargs) if callable(ExtractorCls) else ExtractorCls

    results: Dict[str, pd.DataFrame] = {}

    def _fetch_one(t):
        try:
            df = extractor.fetch(symbol=t, start=start, end=end, data_type=data_type)
            return (t, df, None)
        except Exception as e:
            return (t, None, e)

    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_fetch_one, t): t for t in tickers}
            for fut in as_completed(futures):
                t, df, err = fut.result()
                if err:
                    print(f"⚠️ Error fetching {t} from {source}: {err}")
                else:
                    results[t] = df
    else:
        for t in tickers:
            t, df, err = _fetch_one(t)
            if err:
                print(f"⚠️ Error fetching {t} from {source}: {err}")
            else:
                results[t] = df

    return results
