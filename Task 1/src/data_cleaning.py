"""
Módulo de limpieza y preprocesado de datos
Permite que el programa acepte cualquier tipo de input siempre que exista
una serie temporal de precios
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, Dict, List
from datetime import datetime
import warnings

from .price_series import PriceSeries


class DataCleaner:
    """
    Clase para limpiar y preprocesar datos de series temporales de precios
    Acepta múltiples formatos de entrada y los normaliza
    """
    
    @staticmethod
    def detect_data_format(data: Union[pd.DataFrame, dict, list]) -> str:
        """
        Detecta el formato de los datos de entrada
        
        Args:
            data: Datos en cualquier formato
        
        Returns:
            String con el formato detectado
        """
        if isinstance(data, pd.DataFrame):
            return 'dataframe'
        elif isinstance(data, dict):
            return 'dict'
        elif isinstance(data, list):
            return 'list'
        else:
            raise ValueError(f"Formato de datos no soportado: {type(data)}")
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame, 
                           symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Normaliza un DataFrame a formato estándar
        
        Args:
            df: DataFrame con datos de precios
            symbol: Símbolo del activo (opcional)
        
        Returns:
            DataFrame normalizado con columnas: Date, Open, High, Low, Close, Volume
        """
        df = df.copy()
        
        # Intentar identificar la columna de fecha
        date_cols = ['date', 'Date', 'DATE', 'fecha', 'Fecha', 'timestamp', 'Timestamp']
        date_col = None
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
        elif df.index.name in date_cols or isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        else:
            raise ValueError("No se encontró columna de fecha en el DataFrame")
        
        # Mapeo de columnas comunes
        column_mapping = {
            # Open
            'open': 'Open', 'Open': 'Open', 'OPEN': 'Open',
            'o': 'Open', 'O': 'Open',
            # High
            'high': 'High', 'High': 'High', 'HIGH': 'High',
            'h': 'High', 'H': 'High',
            # Low
            'low': 'Low', 'Low': 'Low', 'LOW': 'Low',
            'l': 'Low', 'L': 'Low',
            # Close
            'close': 'Close', 'Close': 'Close', 'CLOSE': 'Close',
            'c': 'Close', 'C': 'Close', 'price': 'Close', 'Price': 'Close',
            'adj close': 'Close', 'Adj Close': 'Close',
            # Volume
            'volume': 'Volume', 'Volume': 'Volume', 'VOLUME': 'Volume',
            'vol': 'Volume', 'Vol': 'Volume', 'v': 'Volume'
        }
        
        # Renombrar columnas
        df = df.rename(columns=column_mapping)
        
        # Verificar que tenemos las columnas necesarias
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            # Intentar crear columnas faltantes
            if 'Close' in df.columns:
                if 'Open' not in df.columns:
                    df['Open'] = df['Close']  # Usar close como open
                if 'High' not in df.columns:
                    df['High'] = df['Close']  # Usar close como high
                if 'Low' not in df.columns:
                    df['Low'] = df['Close']  # Usar close como low
            else:
                raise ValueError(f"Faltan columnas requeridas y no se pueden inferir: {missing_cols}")
            
            if 'Volume' not in df.columns:
                df['Volume'] = 0  # Volume por defecto en 0
        
        # Seleccionar solo las columnas necesarias
        df = df[required_cols].copy()
        
        # Ordenar por fecha
        df = df.sort_index()
        
        return df
    
    @staticmethod
    def clean_price_data(df: pd.DataFrame,
                        remove_duplicates: bool = True,
                        fill_missing: bool = True,
                        remove_outliers: bool = True,
                        outlier_threshold: float = 3.0) -> pd.DataFrame:
        """
        Limpia datos de precios: elimina duplicados, completa valores faltantes,
        elimina outliers
        
        Args:
            df: DataFrame con datos de precios
            remove_duplicates: Si True, elimina duplicados
            fill_missing: Si True, completa valores faltantes
            remove_outliers: Si True, elimina outliers estadísticos
            outlier_threshold: Número de desviaciones estándar para considerar outlier
        
        Returns:
            DataFrame limpio
        """
        df = df.copy()
        
        # Eliminar duplicados
        if remove_duplicates:
            df = df[~df.index.duplicated(keep='first')]
        
        # Completar valores faltantes
        if fill_missing:
            # Forward fill para precios (asumir que el precio no cambió)
            df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].fillna(method='ffill')
            # Backward fill para los que quedan
            df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].fillna(method='bfill')
            # Volume en 0 si falta
            df['Volume'] = df['Volume'].fillna(0)
        
        # Eliminar outliers usando método Z-score
        if remove_outliers:
            for col in ['Open', 'High', 'Low', 'Close']:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = z_scores > outlier_threshold
                if outliers.any():
                    # Reemplazar outliers con el valor anterior
                    df.loc[outliers, col] = df[col].shift(1).loc[outliers]
                    warnings.warn(f"Se encontraron y corrigieron {outliers.sum()} outliers en {col}")
        
        # Validar que High >= Low, High >= Open, High >= Close, etc.
        invalid = (df['High'] < df['Low']) | (df['High'] < df['Open']) | (df['High'] < df['Close'])
        if invalid.any():
            # Corregir: High debe ser el máximo
            df.loc[invalid, 'High'] = df.loc[invalid, ['Open', 'High', 'Low', 'Close']].max(axis=1)
            warnings.warn(f"Se corrigieron {invalid.sum()} registros donde High no era el máximo")
        
        invalid = df['Low'] > df[['Open', 'Close']].min(axis=1)
        if invalid.any():
            # Corregir: Low debe ser el mínimo
            df.loc[invalid, 'Low'] = df.loc[invalid, ['Open', 'Low', 'Close']].min(axis=1)
            warnings.warn(f"Se corrigieron {invalid.sum()} registros donde Low no era el mínimo")
        
        return df
    
    @staticmethod
    def create_price_series_from_data(data: Union[pd.DataFrame, dict, list],
                                     symbol: str,
                                     source: str = "custom",
                                     clean: bool = True) -> PriceSeries:
        """
        Crea una PriceSeries desde datos en cualquier formato
        
        Args:
            data: Datos en DataFrame, dict o list
            symbol: Símbolo del activo
            source: Fuente de los datos
            clean: Si True, aplica limpieza de datos
        
        Returns:
            PriceSeries
        """
        # Detectar y convertir formato
        format_type = DataCleaner.detect_data_format(data)
        
        if format_type == 'dataframe':
            df = data.copy()
        elif format_type == 'dict':
            # Convertir dict a DataFrame
            df = pd.DataFrame(data)
            if 'date' in df.columns or 'Date' in df.columns:
                date_col = 'date' if 'date' in df.columns else 'Date'
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.set_index(date_col)
        elif format_type == 'list':
            # Asumir que es lista de diccionarios
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
        
        # Normalizar
        df = DataCleaner.normalize_dataframe(df, symbol)
        
        # Limpiar
        if clean:
            df = DataCleaner.clean_price_data(df)
        
        # Crear PriceSeries
        return PriceSeries(
            symbol=symbol.upper(),
            date=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            volume=df['Volume'],
            source=source
        )
    
    @staticmethod
    def validate_price_series(ps: PriceSeries) -> Dict[str, bool]:
        """
        Valida que una PriceSeries tenga datos coherentes
        
        Args:
            ps: PriceSeries a validar
        
        Returns:
            Diccionario con resultados de validación
        """
        validation = {
            'has_data': len(ps) > 0,
            'has_dates': len(ps.date) > 0,
            'dates_ordered': True,
            'no_negative_prices': True,
            'high_low_consistent': True,
            'has_volume': True
        }
        
        if validation['has_data']:
            # Verificar orden de fechas
            validation['dates_ordered'] = ps.date.is_monotonic_increasing
            
            # Verificar precios negativos
            validation['no_negative_prices'] = (ps.close > 0).all()
            
            # Verificar High >= Low
            validation['high_low_consistent'] = (ps.high >= ps.low).all()
            
            # Verificar volumen
            validation['has_volume'] = (ps.volume >= 0).all()
        
        return validation

