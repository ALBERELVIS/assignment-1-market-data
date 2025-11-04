"""
Módulo extractor de datos bursátiles
Obtiene información histórica de precios desde múltiples fuentes (APIs)
y estandariza el formato de salida independientemente de la fuente.
Ahora soporta cualquier API mediante adaptadores y extrae datos cualitativos
(recomendaciones, noticias, etc.)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Optional, Union, Callable, Any
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json


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


@dataclass
class Recommendation:
    """Estructura para recomendaciones de analistas"""
    symbol: str
    date: datetime
    firm: str  # Casa de análisis
    rating: str  # "Buy", "Hold", "Sell", etc.
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    source: str = ""


@dataclass
class NewsItem:
    """Estructura para noticias financieras"""
    symbol: str
    title: str
    summary: str
    date: datetime
    url: Optional[str] = None
    source: str = ""
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"


class APISourceAdapter(ABC):
    """
    Clase abstracta base para adaptadores de diferentes APIs
    Permite agregar nuevas fuentes de datos fácilmente
    """
    
    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
        """Obtiene datos históricos de precios desde la API"""
        pass
    
    @abstractmethod
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza los datos al formato común"""
        pass
    
    def get_recommendations(self, symbol: str) -> List[Recommendation]:
        """Obtiene recomendaciones de analistas (opcional)"""
        return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Obtiene noticias relacionadas (opcional)"""
        return []
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información adicional de la empresa (opcional)"""
        return {}
    
    def get_earnings_calendar(self, symbol: str) -> List[Dict]:
        """Obtiene calendario de resultados (opcional)"""
        return []
    
    def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Obtiene estados financieros (opcional)"""
        return {}


class YahooFinanceAdapter(APISourceAdapter):
    """Adaptador para Yahoo Finance"""
    
    def __init__(self):
        self.source_name = "yahoo"
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = "1y") -> pd.DataFrame:
        """Obtiene datos históricos desde Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        if start_date and end_date:
            return ticker.history(start=start_date, end=end_date)
        else:
            return ticker.history(period=period or "1y")
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza datos de Yahoo Finance"""
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
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
            source=self.source_name
        )
    
    def get_recommendations(self, symbol: str) -> List[Recommendation]:
        """Obtiene recomendaciones desde Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations
            
            if recommendations is None or recommendations.empty:
                return []
            
            result = []
            for date, row in recommendations.iterrows():
                # Yahoo Finance puede tener diferentes formatos
                if isinstance(row, pd.Series):
                    rating = str(row.iloc[0]) if len(row) > 0 else "N/A"
                else:
                    rating = str(row)
                
                result.append(Recommendation(
                    symbol=symbol.upper(),
                    date=pd.to_datetime(date),
                    firm="Yahoo Finance",
                    rating=rating,
                    source=self.source_name
                ))
            
            return result
        except Exception as e:
            print(f"Error obteniendo recomendaciones de {symbol}: {e}")
            return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Obtiene noticias desde Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            # Intentar obtener noticias - yfinance puede tener diferentes atributos
            news = []
            if hasattr(ticker, 'news') and ticker.news:
                news = ticker.news[:limit]
            elif hasattr(ticker, 'get_news'):
                news = ticker.get_news()[:limit] if callable(ticker.get_news) else []
            
            result = []
            for item in news:
                # yfinance puede devolver diferentes formatos
                if isinstance(item, dict):
                    result.append(NewsItem(
                        symbol=symbol.upper(),
                        title=item.get('title', item.get('headline', 'Sin título')),
                        summary=item.get('summary', item.get('description', '')),
                        date=datetime.fromtimestamp(item.get('providerPublishTime', item.get('pubDate', 0))),
                        url=item.get('link', item.get('url', '')),
                        source=self.source_name
                    ))
            
            return result
        except Exception as e:
            print(f"Error obteniendo noticias de {symbol}: {e}")
            return []
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información de la empresa desde Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'website': info.get('website', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A')[:500],
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                'source': self.source_name
            }
        except Exception as e:
            print(f"Error obteniendo información de {symbol}: {e}")
            return {}
    
    def get_earnings_calendar(self, symbol: str) -> List[Dict]:
        """Obtiene calendario de resultados desde Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            
            if calendar is None or calendar.empty:
                return []
            
            result = []
            for date, row in calendar.iterrows():
                result.append({
                    'date': date,
                    'earnings_date': row.get('Earnings Date', 'N/A'),
                    'source': self.source_name
                })
            
            return result
        except Exception as e:
            print(f"Error obteniendo calendario de resultados de {symbol}: {e}")
            return []


class GenericAPIAdapter(APISourceAdapter):
    """
    Adaptador genérico que permite conectarse a cualquier API mediante funciones personalizadas
    """
    
    def __init__(self, source_name: str,
                 price_function: Callable,
                 standardize_function: Callable,
                 recommendations_function: Optional[Callable] = None,
                 news_function: Optional[Callable] = None,
                 info_function: Optional[Callable] = None):
        """
        Args:
            source_name: Nombre de la fuente
            price_function: Función que obtiene precios (symbol, start_date, end_date, period) -> DataFrame
            standardize_function: Función que estandariza datos (symbol, DataFrame) -> StandardizedPriceData
            recommendations_function: Función opcional para recomendaciones (symbol) -> List[Recommendation]
            news_function: Función opcional para noticias (symbol, limit) -> List[NewsItem]
            info_function: Función opcional para info de empresa (symbol) -> Dict
        """
        self.source_name = source_name
        self._price_function = price_function
        self._standardize_function = standardize_function
        self._recommendations_function = recommendations_function
        self._news_function = news_function
        self._info_function = info_function
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
        return self._price_function(symbol, start_date, end_date, period)
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        return self._standardize_function(symbol, data)
    
    def get_recommendations(self, symbol: str) -> List[Recommendation]:
        if self._recommendations_function:
            return self._recommendations_function(symbol)
        return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        if self._news_function:
            return self._news_function(symbol, limit)
        return []
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        if self._info_function:
            return self._info_function(symbol)
        return {}


class DataExtractor:
    """
    Extractor de datos bursátiles desde múltiples fuentes
    Estandariza el formato de salida para que todas las fuentes
    produzcan objetos compatibles.
    Ahora soporta cualquier API mediante adaptadores.
    """
    
    def __init__(self):
        # Adaptadores predefinidos
        self._adapters: Dict[str, APISourceAdapter] = {
            'yahoo': YahooFinanceAdapter()
        }
        self.cache = {}  # Cache para datos descargados
        self._cache_recommendations = {}  # Cache para recomendaciones
        self._cache_news = {}  # Cache para noticias
    
    def register_adapter(self, source_name: str, adapter: APISourceAdapter):
        """
        Registra un nuevo adaptador de API
        
        Args:
            source_name: Nombre de la fuente (ej: "alpha_vantage", "polygon", etc.)
            adapter: Instancia de APISourceAdapter
        """
        self._adapters[source_name] = adapter
        print(f"✅ Adaptador '{source_name}' registrado exitosamente")
    
    def register_generic_api(self, source_name: str,
                            price_function: Callable,
                            standardize_function: Callable,
                            recommendations_function: Optional[Callable] = None,
                            news_function: Optional[Callable] = None,
                            info_function: Optional[Callable] = None):
        """
        Registra una API genérica mediante funciones personalizadas
        
        Args:
            source_name: Nombre de la fuente
            price_function: Función (symbol, start_date, end_date, period) -> DataFrame
            standardize_function: Función (symbol, DataFrame) -> StandardizedPriceData
            recommendations_function: Función opcional (symbol) -> List[Recommendation]
            news_function: Función opcional (symbol, limit) -> List[NewsItem]
            info_function: Función opcional (symbol) -> Dict
        """
        adapter = GenericAPIAdapter(
            source_name=source_name,
            price_function=price_function,
            standardize_function=standardize_function,
            recommendations_function=recommendations_function,
            news_function=news_function,
            info_function=info_function
        )
        self.register_adapter(source_name, adapter)
    
    def get_supported_sources(self) -> List[str]:
        """Devuelve lista de fuentes soportadas"""
        return list(self._adapters.keys())
    
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
            period: Período si no se especifican fechas
            source: Fuente de datos (por defecto "yahoo")
        
        Returns:
            StandardizedPriceData: Datos estandarizados independientemente de la fuente
        """
        if source not in self._adapters:
            raise ValueError(f"Fuente no soportada: {source}. "
                           f"Fuentes disponibles: {list(self._adapters.keys())}")
        
        # Crear clave de cache
        cache_key = f"{source}_{symbol}_{start_date}_{end_date}_{period}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Usar el adaptador correspondiente
        adapter = self._adapters[source]
        data = adapter.get_historical_prices(symbol, start_date, end_date, period)
        standardized = adapter.standardize_data(symbol, data)
        
        self.cache[cache_key] = standardized
        return standardized
    
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
            index_symbol: Símbolo del índice (ej: "^GSPC" para S&P 500)
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
    
    def get_recommendations(self, symbol: str, source: str = "yahoo") -> List[Recommendation]:
        """
        Obtiene recomendaciones de analistas para un símbolo
        
        Args:
            symbol: Símbolo de la acción
            source: Fuente de datos
        
        Returns:
            Lista de objetos Recommendation
        """
        if source not in self._adapters:
            raise ValueError(f"Fuente no soportada: {source}")
        
        cache_key = f"rec_{source}_{symbol}"
        if cache_key in self._cache_recommendations:
            return self._cache_recommendations[cache_key]
        
        adapter = self._adapters[source]
        recommendations = adapter.get_recommendations(symbol)
        
        self._cache_recommendations[cache_key] = recommendations
        return recommendations
    
    def get_news(self, symbol: str, limit: int = 10, source: str = "yahoo") -> List[NewsItem]:
        """
        Obtiene noticias relacionadas con un símbolo
        
        Args:
            symbol: Símbolo de la acción
            limit: Número máximo de noticias a obtener
            source: Fuente de datos
        
        Returns:
            Lista de objetos NewsItem
        """
        if source not in self._adapters:
            raise ValueError(f"Fuente no soportada: {source}")
        
        cache_key = f"news_{source}_{symbol}_{limit}"
        if cache_key in self._cache_news:
            return self._cache_news[cache_key]
        
        adapter = self._adapters[source]
        news = adapter.get_news(symbol, limit)
        
        self._cache_news[cache_key] = news
        return news
    
    def get_company_info(self, symbol: str, source: str = "yahoo") -> Dict[str, Any]:
        """
        Obtiene información adicional de la empresa
        
        Args:
            symbol: Símbolo de la acción
            source: Fuente de datos
        
        Returns:
            Diccionario con información de la empresa
        """
        if source not in self._adapters:
            raise ValueError(f"Fuente no soportada: {source}")
        
        adapter = self._adapters[source]
        return adapter.get_company_info(symbol)
    
    def get_earnings_calendar(self, symbol: str, source: str = "yahoo") -> List[Dict]:
        """
        Obtiene calendario de resultados (earnings)
        
        Args:
            symbol: Símbolo de la acción
            source: Fuente de datos
        
        Returns:
            Lista de diccionarios con información de earnings
        """
        if source not in self._adapters:
            raise ValueError(f"Fuente no soportada: {source}")
        
        adapter = self._adapters[source]
        if hasattr(adapter, 'get_earnings_calendar'):
            return adapter.get_earnings_calendar(symbol)
        return []
    
    def get_all_data(self, symbol: str, source: str = "yahoo",
                    include_news: bool = True,
                    include_recommendations: bool = True,
                    include_info: bool = True) -> Dict[str, Any]:
        """
        Obtiene todos los datos disponibles para un símbolo
        
        Args:
            symbol: Símbolo de la acción
            source: Fuente de datos
            include_news: Si True, incluye noticias
            include_recommendations: Si True, incluye recomendaciones
            include_info: Si True, incluye información de empresa
        
        Returns:
            Diccionario con todos los datos disponibles
        """
        result = {
            'symbol': symbol.upper(),
            'source': source,
            'prices': None,
            'news': [],
            'recommendations': [],
            'company_info': {}
        }
        
        try:
            # Precios históricos (siempre)
            result['prices'] = self.download_historical_prices(symbol, source=source)
        except Exception as e:
            print(f"Error obteniendo precios de {symbol}: {e}")
        
        if include_news:
            try:
                result['news'] = self.get_news(symbol, source=source)
            except Exception as e:
                print(f"Error obteniendo noticias de {symbol}: {e}")
        
        if include_recommendations:
            try:
                result['recommendations'] = self.get_recommendations(symbol, source=source)
            except Exception as e:
                print(f"Error obteniendo recomendaciones de {symbol}: {e}")
        
        if include_info:
            try:
                result['company_info'] = self.get_company_info(symbol, source=source)
            except Exception as e:
                print(f"Error obteniendo información de {symbol}: {e}")
        
        return result
    
    def clear_cache(self):
        """Limpia toda la caché de datos descargados"""
        self.cache.clear()
        self._cache_recommendations.clear()
        self._cache_news.clear()
