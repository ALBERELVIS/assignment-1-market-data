"""
Módulo extractor de datos bursátiles
Obtiene información histórica de precios desde múltiples fuentes (APIs)
y estandariza el formato de salida independientemente de la fuente
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass


@dataclass
class StandardizedPriceData:
    """
    Formato estandarizado para datos de precios históricos
    Independiente de la fuente de datos original
    """
    symbol: str
    date: pd.DatetimeIndex
    open: pd.Series
    high: pd.Series
    low: pd.Series
    close: pd.Series
    volume: pd.Series
    source: str  # Fuente de donde provienen los datos
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte los datos a un DataFrame de pandas"""
        return pd.DataFrame({
            'Date': self.date,
            'Open': self.open.values,
            'High': self.high.values,
            'Low': self.low.values,
            'Close': self.close.values,
            'Volume': self.volume.values
        }).set_index('Date')
    
    def __len__(self):
        """Devuelve el número de registros"""
        return len(self.date)


class DataExtractor:
    """
    Extractor de datos bursátiles desde múltiples fuentes
    Estandariza el formato de salida para que todas las fuentes
    produzcan objetos compatibles
    """
    
    def __init__(self):
        self.supported_sources = ['yahoo', 'alpha_vantage']
        self.cache = {}  # Cache simple para evitar llamadas repetidas
    
    def _standardize_yahoo_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """
        Estandariza datos de Yahoo Finance al formato común
        """
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        # Asegurar que tenemos las columnas necesarias
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"Faltan columnas requeridas: {missing}")
        
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            volume=data['Volume'],
            source='yahoo'
        )
    
    def download_historical_prices(self, 
                                   symbol: str, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None,
                                   period: Optional[str] = "1y",
                                   source: str = "yahoo") -> StandardizedPriceData:
        """
        Descarga información histórica de precios de acciones o índices
        
        Args:
            symbol: Símbolo de la acción/índice (ej: "AAPL", "MSFT", "^GSPC")
            start_date: Fecha inicio (YYYY-MM-DD). Si no se especifica, usa period
            end_date: Fecha fin (YYYY-MM-DD). Si no se especifica, usa hoy
            period: Período si no se especifican fechas ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            source: Fuente de datos ("yahoo" por defecto)
        
        Returns:
            StandardizedPriceData: Datos estandarizados independientemente de la fuente
        """
        if source not in self.supported_sources:
            raise ValueError(f"Fuente no soportada: {source}. Fuentes disponibles: {self.supported_sources}")
        
        # Crear clave de cache
        cache_key = f"{source}_{symbol}_{start_date}_{end_date}_{period}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if source == "yahoo":
            ticker = yf.Ticker(symbol)
            
            if start_date and end_date:
                data = ticker.history(start=start_date, end=end_date)
            else:
                data = ticker.history(period=period)
            
            standardized = self._standardize_yahoo_data(symbol, data)
            self.cache[cache_key] = standardized
            return standardized
        
        else:
            raise NotImplementedError(f"Fuente {source} aún no implementada")
    
    def download_multiple_series(self, 
                                 symbols: List[str],
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None,
                                 period: Optional[str] = "1y",
                                 source: str = "yahoo") -> Dict[str, StandardizedPriceData]:
        """
        Descarga N series de datos al mismo tiempo
        
        Args:
            symbols: Lista de símbolos a descargar
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            period: Período si no se especifican fechas
            source: Fuente de datos
        
        Returns:
            Dict con símbolo como clave y StandardizedPriceData como valor
        """
        results = {}
        for symbol in symbols:
            try:
                data = self.download_historical_prices(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    source=source
                )
                results[symbol.upper()] = data
            except Exception as e:
                print(f"Error descargando {symbol}: {str(e)}")
                continue
        
        return results
    
    def download_index_data(self, 
                           index_symbol: str,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           period: Optional[str] = "1y",
                           source: str = "yahoo") -> StandardizedPriceData:
        """
        Descarga datos de índices bursátiles
        
        Args:
            index_symbol: Símbolo del índice (ej: "^GSPC" para S&P 500, "^DJI" para Dow Jones)
            start_date: Fecha inicio
            end_date: Fecha fin
            period: Período
            source: Fuente de datos
        
        Returns:
            StandardizedPriceData: Datos estandarizados del índice
        """
        return self.download_historical_prices(
            symbol=index_symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            source=source
        )
    
    def download_company_info(self, symbol: str) -> Dict:
        """
        Obtiene información adicional de la empresa (opción extra)
        
        Args:
            symbol: Símbolo de la acción
        
        Returns:
            Dict con información de la empresa
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extraer información relevante
            relevant_info = {
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'website': info.get('website', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A')[:500]  # Primeros 500 caracteres
            }
            
            return relevant_info
        except Exception as e:
            print(f"Error obteniendo información de {symbol}: {str(e)}")
            return {}
    
    def clear_cache(self):
        """Limpia la caché de datos descargados"""
        self.cache.clear()

