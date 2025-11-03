"""
utils.py
--------
Funciones auxiliares para limpieza, validación y preprocesado de datos.
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def clean_price_data(df: pd.DataFrame, 
                     fill_method: str = 'forward',
                     remove_outliers: bool = True,
                     outlier_threshold: float = 5.0) -> pd.DataFrame:
    """
    Limpia y preprocesa datos de precios.
    
    Args:
        df: DataFrame con datos de precios
        fill_method: Método para llenar valores faltantes ('forward', 'backward', 'interpolate')
        remove_outliers: Si True, elimina outliers usando método Z-score
        outlier_threshold: Número de desviaciones estándar para considerar outlier
    
    Returns:
        DataFrame limpio
    """
    df = df.copy()
    
    # Asegurar que el índice es datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Ordenar por fecha
    df = df.sort_index()
    
    # Llenar valores faltantes
    if fill_method == 'forward':
        df = df.ffill()
    elif fill_method == 'backward':
        df = df.bfill()
    elif fill_method == 'interpolate':
        df = df.interpolate(method='time')
    
    # Llenar cualquier valor restante con el último valor conocido
    df = df.ffill().bfill()
    
    # Eliminar outliers si se solicita
    if remove_outliers:
        for col in ['open', 'high', 'low', 'close', 'adj_close']:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df = df[z_scores < outlier_threshold]
    
    # Validar que los precios sean positivos
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].clip(lower=0.01)  # Precios mínimos de 0.01
    
    # Validar que high >= low, high >= open, high >= close, etc.
    if 'high' in df.columns and 'low' in df.columns:
        df['high'] = df[['high', 'low']].max(axis=1)
    
    if 'high' in df.columns and 'open' in df.columns:
        df['high'] = df[['high', 'open']].max(axis=1)
    
    if 'high' in df.columns and 'close' in df.columns:
        df['high'] = df[['high', 'close']].max(axis=1)
    
    if 'low' in df.columns and 'open' in df.columns:
        df['low'] = df[['low', 'open']].min(axis=1)
    
    if 'low' in df.columns and 'close' in df.columns:
        df['low'] = df[['low', 'close']].min(axis=1)
    
    return df


def validate_price_series(df: pd.DataFrame, symbol: str = "unknown") -> bool:
    """
    Valida que un DataFrame contiene una serie de precios válida.
    
    Args:
        df: DataFrame a validar
        symbol: Símbolo del activo (para mensajes de error)
    
    Returns:
        True si es válido, lanza excepción si no
    
    Raises:
        ValueError: Si la serie no es válida
    """
    if df is None or df.empty:
        raise ValueError(f"Price series for {symbol} is empty or None")
    
    # Validar índice
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Index for {symbol} must be DatetimeIndex")
    
    # Validar columnas requeridas
    required_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {symbol}: {missing}")
    
    # Validar que no hay fechas duplicadas
    if df.index.duplicated().any():
        raise ValueError(f"Duplicate dates found in {symbol}")
    
    # Validar que los precios son positivos
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if (df[col] <= 0).any():
            raise ValueError(f"Non-positive prices found in {col} for {symbol}")
    
    # Validar relaciones lógicas entre precios
    if (df['high'] < df['low']).any():
        raise ValueError(f"High < Low found in {symbol}")
    
    if (df['high'] < df['open']).any():
        raise ValueError(f"High < Open found in {symbol}")
    
    if (df['high'] < df['close']).any():
        raise ValueError(f"High < Close found in {symbol}")
    
    if (df['low'] > df['open']).any():
        raise ValueError(f"Low > Open found in {symbol}")
    
    if (df['low'] > df['close']).any():
        raise ValueError(f"Low > Close found in {symbol}")
    
    return True


def standardize_price_format(df: pd.DataFrame, 
                             symbol: str,
                             source: str = "unknown") -> pd.DataFrame:
    """
    Estandariza un DataFrame de precios al formato interno.
    
    Esta función acepta cualquier DataFrame con datos de precios y lo convierte
    al formato estándar esperado por el sistema.
    
    Args:
        df: DataFrame con datos de precios (puede tener cualquier formato)
        symbol: Símbolo del activo
        source: Fuente de los datos
    
    Returns:
        DataFrame estandarizado
    """
    df = df.copy()
    
    # Si no tiene índice datetime, buscar columna de fecha
    if not isinstance(df.index, pd.DatetimeIndex):
        date_cols = ['date', 'Date', 'DATE', 'timestamp', 'Timestamp', 'time', 'Time']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                df = df.set_index(col)
                break
        
        # Si aún no es datetime, intentar convertir el índice
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except:
                raise ValueError("Cannot convert index or date column to datetime")
    
    # Mapear columnas a nombres estándar
    col_mapping = {}
    col_lower = {c.lower(): c for c in df.columns}
    
    # Mapeos comunes
    mappings = {
        'open': ['open', 'open_price', 'o', 'opening'],
        'high': ['high', 'h', 'high_price', 'maximum'],
        'low': ['low', 'l', 'low_price', 'minimum'],
        'close': ['close', 'close_price', 'c', 'closing', 'price'],
        'adj_close': ['adj close', 'adj_close', 'adjusted_close', 'adjclose', 'adjusted'],
        'volume': ['volume', 'vol', 'v', 'trading_volume']
    }
    
    for standard_name, variants in mappings.items():
        for variant in variants:
            if variant in col_lower:
                col_mapping[col_lower[variant]] = standard_name
                break
    
    if col_mapping:
        df = df.rename(columns=col_mapping)
    
    # Crear columnas faltantes
    required_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            if col == 'adj_close' and 'close' in df.columns:
                df['adj_close'] = df['close']  # Usar close como adj_close si no existe
            else:
                df[col] = np.nan
    
    # Limpiar datos
    df = clean_price_data(df)
    
    # Añadir metadatos
    df.attrs['symbol'] = symbol
    df.attrs['source'] = source
    
    return df


def detect_data_quality_issues(df: pd.DataFrame) -> dict:
    """
    Detecta problemas de calidad en los datos.
    
    Args:
        df: DataFrame con datos de precios
    
    Returns:
        Diccionario con problemas detectados
    """
    issues = {
        'missing_values': {},
        'outliers': {},
        'duplicate_dates': False,
        'negative_prices': False,
        'logical_errors': []
    }
    
    # Valores faltantes
    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            issues['missing_values'][col] = missing
    
    # Outliers (usando IQR)
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            if outliers > 0:
                issues['outliers'][col] = outliers
    
    # Fechas duplicadas
    if df.index.duplicated().any():
        issues['duplicate_dates'] = True
    
    # Precios negativos
    for col in price_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                issues['negative_prices'] = True
                break
    
    # Errores lógicos
    if 'high' in df.columns and 'low' in df.columns:
        if (df['high'] < df['low']).any():
            issues['logical_errors'].append("High < Low")
    
    if 'high' in df.columns and 'close' in df.columns:
        if (df['high'] < df['close']).any():
            issues['logical_errors'].append("High < Close")
    
    return issues


def prepare_for_analysis(df: pd.DataFrame, 
                        min_data_points: int = 30,
                        require_continuous: bool = False) -> pd.DataFrame:
    """
    Prepara datos para análisis, asegurando calidad mínima.
    
    Args:
        df: DataFrame con datos de precios
        min_data_points: Número mínimo de puntos de datos requeridos
        require_continuous: Si True, requiere datos continuos sin gaps grandes
    
    Returns:
        DataFrame preparado
    
    Raises:
        ValueError: Si los datos no cumplen los requisitos
    """
    df = df.copy()
    
    # Limpiar datos
    df = clean_price_data(df)
    
    # Validar número mínimo de puntos
    if len(df) < min_data_points:
        raise ValueError(f"Insufficient data points: {len(df)} < {min_data_points}")
    
    # Validar continuidad si se requiere
    if require_continuous:
        date_diffs = df.index.to_series().diff()
        max_gap_days = date_diffs.max().days
        if max_gap_days > 30:  # Gap mayor a 30 días
            raise ValueError(f"Large gap in data: {max_gap_days} days")
    
    return df
