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
        # Limpiar el símbolo: asegurar que ^ esté al inicio si es un índice
        symbol = symbol.strip().upper()
        
        # Intentar obtener datos con manejo de errores mejorado
        ticker = yf.Ticker(symbol)
        
        try:
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date)
            else:
                df = ticker.history(period=period or "1y")
            
            # Verificar que se obtuvieron datos
            if df.empty:
                raise ValueError(f"No se encontraron datos para {symbol}. "
                               f"Verifica que el símbolo sea correcto. "
                               f"Para índices españoles, prueba: '^IBEX' o 'IBEX.MC'")
            
            # NORMALIZAR INMEDIATAMENTE el índice de fechas después de obtener los datos
            # Esto es crítico: yfinance puede devolver fechas con timezone
            # Usar la función centralizada de normalización para garantizar consistencia
            from .data_cleaning import force_naive_datetime_index
            df.index = force_naive_datetime_index(df.index)
            
            return df
        except Exception as e:
            # Si falla, intentar con formato alternativo para índices españoles
            if symbol.startswith('^'):
                # Intentar sin el ^ o con formato .MC
                alt_symbols = [symbol.replace('^', ''), f"{symbol.replace('^', '')}.MC", symbol]
                for alt_symbol in alt_symbols:
                    try:
                        ticker = yf.Ticker(alt_symbol)
                        if start_date and end_date:
                            df = ticker.history(start=start_date, end=end_date)
                        else:
                            df = ticker.history(period=period or "1y")
                        
                        if not df.empty:
                            # Normalizar índice usando la función centralizada
                            from .data_cleaning import force_naive_datetime_index
                            df.index = force_naive_datetime_index(df.index)
                            return df
                    except:
                        continue
            
            # Si todo falla, lanzar el error original con más contexto
            raise ValueError(f"Error obteniendo datos para {symbol}: {e}. "
                           f"Verifica que el símbolo sea correcto. "
                           f"Para índices: usa formato ^SYMBOL (ej: ^IBEX, ^GSPC). "
                           f"Para acciones españolas: usa formato SYMBOL.MC (ej: BBVA.MC)")
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """
        Estandariza datos de Yahoo Finance
        SOLUCIÓN INTEGRAL: Normaliza TODOS los índices de fecha a naive (sin timezone)
        Esto es crítico para evitar errores al mezclar índices con activos
        """
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"Faltan columnas requeridas: {missing}")
        
        # NORMALIZACIÓN INTEGRAL: Asegurar que el índice esté sin timezone
        # Esta es la normalización más importante: garantizar que el índice de fechas
        # esté completamente naive antes de crear cualquier Serie
        from .data_cleaning import force_naive_datetime_index
        date_index = force_naive_datetime_index(data.index)
        
        # Verificación doble: asegurar que el índice normalizado realmente esté sin timezone
        if hasattr(date_index, 'tz') and date_index.tz is not None:
            # Si aún tiene timezone, forzar normalización de nuevo
            date_index = force_naive_datetime_index(date_index)
        
        # Asegurar que todas las Series también tengan índices normalizados
        # Esto es crítico porque las Series pueden heredar el índice con timezone
        # Recrear TODAS las Series desde cero con el índice normalizado
        open_series = pd.Series(data['Open'].values, index=date_index)
        high_series = pd.Series(data['High'].values, index=date_index)
        low_series = pd.Series(data['Low'].values, index=date_index)
        close_series = pd.Series(data['Close'].values, index=date_index)
        volume_series = pd.Series(data['Volume'].values, index=date_index)
        
        # Verificación final: asegurar que TODAS las series tengan índices naive
        # Si alguna serie tiene timezone, recrearla con índice normalizado
        if hasattr(open_series.index, 'tz') and open_series.index.tz is not None:
            normalized_idx = force_naive_datetime_index(open_series.index)
            open_series = pd.Series(open_series.values, index=normalized_idx)
        if hasattr(high_series.index, 'tz') and high_series.index.tz is not None:
            normalized_idx = force_naive_datetime_index(high_series.index)
            high_series = pd.Series(high_series.values, index=normalized_idx)
        if hasattr(low_series.index, 'tz') and low_series.index.tz is not None:
            normalized_idx = force_naive_datetime_index(low_series.index)
            low_series = pd.Series(low_series.values, index=normalized_idx)
        if hasattr(close_series.index, 'tz') and close_series.index.tz is not None:
            normalized_idx = force_naive_datetime_index(close_series.index)
            close_series = pd.Series(close_series.values, index=normalized_idx)
        if hasattr(volume_series.index, 'tz') and volume_series.index.tz is not None:
            normalized_idx = force_naive_datetime_index(volume_series.index)
            volume_series = pd.Series(volume_series.values, index=normalized_idx)
        
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=date_index,
            open=open_series,
            high=high_series,
            low=low_series,
            close=close_series,
            volume=volume_series,
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
            # ticker.recommendations devuelve un DataFrame agregado por período
            # con columnas: period, strongBuy, buy, hold, sell, strongSell
            for idx, row in recommendations.iterrows():
                try:
                    # Obtener el período (puede ser "0m", "-1m", etc.)
                    period = str(row.get('period', 'N/A'))
                    
                    # Crear un resumen de recomendaciones basado en los conteos
                    strong_buy = int(row.get('strongBuy', 0))
                    buy = int(row.get('buy', 0))
                    hold = int(row.get('hold', 0))
                    sell = int(row.get('sell', 0))
                    strong_sell = int(row.get('strongSell', 0))
                    
                    # Determinar el rating predominante
                    ratings_dict = {
                        'Strong Buy': strong_buy,
                        'Buy': buy,
                        'Hold': hold,
                        'Sell': sell,
                        'Strong Sell': strong_sell
                    }
                    dominant_rating = max(ratings_dict, key=ratings_dict.get) if any(ratings_dict.values()) else "N/A"
                    
                    # Usar fecha actual como aproximación (el DataFrame no tiene fechas específicas)
                    # Intentar obtener la fecha del índice si existe
                    if isinstance(idx, (pd.Timestamp, datetime)):
                        rec_date = pd.to_datetime(idx)
                        # Normalizar a datetime naive
                        if hasattr(rec_date, 'tz') and rec_date.tz is not None:
                            rec_date = rec_date.tz_localize(None)
                        if isinstance(rec_date, pd.Timestamp):
                            rec_date = rec_date.to_pydatetime()
                    else:
                        # Si no hay fecha, usar fecha actual
                        rec_date = datetime.now()
                    
                    result.append(Recommendation(
                        symbol=symbol.upper(),
                        date=rec_date,
                        firm="Yahoo Finance (Agregado)",
                        rating=f"{dominant_rating} (Strong Buy: {strong_buy}, Buy: {buy}, Hold: {hold}, Sell: {sell}, Strong Sell: {strong_sell})",
                        source=self.source_name
                    ))
                except Exception as e:
                    # Si hay error procesando una fila, continuar con la siguiente
                    continue
            
            return result
        except Exception as e:
            print(f"Error obteniendo recomendaciones de {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Obtiene noticias desde Yahoo Finance - REESCRITO COMPLETAMENTE"""
        import re
        import json
        
        result = []
        
        # MÉTODO PRINCIPAL: Usar la API directa de Yahoo Finance (más confiable)
        try:
            # URL de la API de Yahoo Finance para búsqueda y noticias
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&quotesCount=1&newsCount={limit * 2}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': f'https://finance.yahoo.com/quote/{symbol}'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraer noticias del JSON
                news_list = []
                if 'news' in data and isinstance(data['news'], list):
                    news_list = data['news']
                elif isinstance(data, list):
                    # A veces devuelve directamente una lista
                    news_list = data
                
                # Procesar cada noticia
                for idx, item in enumerate(news_list[:limit]):
                    try:
                        if not isinstance(item, dict):
                            continue
                        
                        # Extraer título - formato Yahoo Finance API (múltiples ubicaciones posibles)
                        title = None
                        # Intentar diferentes campos y formatos
                        if 'title' in item:
                            title_val = item['title']
                            if isinstance(title_val, dict):
                                # Si es dict, puede tener 'text', 'title', 'headline', etc.
                                title = title_val.get('text') or title_val.get('title') or title_val.get('headline') or str(title_val)
                            elif isinstance(title_val, str):
                                title = title_val
                            else:
                                title = str(title_val) if title_val else None
                        
                        if not title and 'headline' in item:
                            headline_val = item['headline']
                            if isinstance(headline_val, dict):
                                title = headline_val.get('text') or headline_val.get('title') or headline_val.get('headline') or str(headline_val)
                            elif isinstance(headline_val, str):
                                title = headline_val
                            else:
                                title = str(headline_val) if headline_val else None
                        
                        # Verificar que tenemos un título válido
                        if not title or title.strip() == '' or title == 'None':
                            continue
                        
                        # Extraer resumen
                        summary = ''
                        if 'summary' in item:
                            summary = item['summary']
                        elif 'description' in item:
                            summary = item['description']
                        elif 'snippet' in item:
                            summary = item['snippet']
                        
                        # Limpiar HTML
                        if summary:
                            summary = re.sub('<[^<]+?>', '', summary)
                            summary = re.sub(r'\s+', ' ', summary).strip()
                        
                        # Extraer fecha
                        news_date = datetime.now()
                        if 'providerPublishTime' in item:
                            try:
                                ts = item['providerPublishTime']
                                if isinstance(ts, (int, float)):
                                    if ts > 1e10:  # Milisegundos
                                        news_date = datetime.fromtimestamp(ts / 1000)
                                    else:
                                        news_date = datetime.fromtimestamp(ts)
                            except:
                                pass
                        elif 'pubDate' in item:
                            try:
                                date_str = item['pubDate']
                                news_date = pd.to_datetime(date_str)
                                if isinstance(news_date, pd.Timestamp):
                                    if news_date.tz is not None:
                                        news_date = news_date.tz_localize(None).to_pydatetime()
                                    else:
                                        news_date = news_date.to_pydatetime()
                            except:
                                pass
                        
                        # Extraer URL
                        url = None
                        if 'link' in item:
                            url = item['link']
                        elif 'url' in item:
                            url = item['url']
                        elif 'uuid' in item:
                            # Construir URL desde UUID
                            uuid_val = item['uuid']
                            if isinstance(uuid_val, str):
                                url = f"https://finance.yahoo.com/news/{uuid_val}"
                        
                        # Validación final: asegurar que el título es válido antes de crear NewsItem
                        title_str = str(title).strip() if title else ''
                        if not title_str or title_str == '' or title_str == 'None':
                            continue
                        
                        # Crear NewsItem solo si tenemos un título válido
                        result.append(NewsItem(
                            symbol=symbol.upper(),
                            title=title_str,
                            summary=str(summary) if summary else '',
                            date=news_date,
                            url=str(url) if url else None,
                            source=self.source_name
                        ))
                    except Exception:
                        continue
                
                if result:
                    return result
        except Exception:
            pass
        
        # MÉTODO ALTERNATIVO 1: Intentar con yfinance directamente
        try:
            ticker = yf.Ticker(symbol)
            news_list = ticker.news
            
            if news_list and isinstance(news_list, list):
                for item in news_list[:limit]:
                    try:
                        if not isinstance(item, dict):
                            continue
                        
                        # Formato yfinance: puede tener diferentes estructuras
                        # Ejemplo: {'uuid': ..., 'title': {...}, 'provider': {...}, 'pubDate': ...}
                        # o: {'title': 'texto', 'link': '...', 'publisher': '...'}
                        title = None
                        
                        # Intentar múltiples campos y formatos
                        if 'title' in item:
                            title_obj = item['title']
                            if isinstance(title_obj, dict):
                                # Buscar en diferentes claves del dict
                                title = (title_obj.get('text') or 
                                        title_obj.get('title') or 
                                        title_obj.get('headline') or
                                        title_obj.get('plainText') or
                                        str(title_obj))
                            elif isinstance(title_obj, str) and title_obj.strip():
                                title = title_obj.strip()
                            else:
                                title = str(title_obj).strip() if title_obj else None
                        
                        # Si no encontramos título, intentar 'headline'
                        if (not title or title.strip() == '' or title == 'None') and 'headline' in item:
                            headline_obj = item['headline']
                            if isinstance(headline_obj, dict):
                                title = (headline_obj.get('text') or 
                                        headline_obj.get('title') or 
                                        headline_obj.get('headline') or
                                        headline_obj.get('plainText') or
                                        str(headline_obj))
                            elif isinstance(headline_obj, str) and headline_obj.strip():
                                title = headline_obj.strip()
                            else:
                                title = str(headline_obj).strip() if headline_obj else None
                        
                        # Si aún no hay título, intentar otros campos comunes
                        if (not title or title.strip() == '' or title == 'None'):
                            for field in ['name', 'text', 'plainText', 'content']:
                                if field in item:
                                    field_val = item[field]
                                    if isinstance(field_val, str) and field_val.strip():
                                        title = field_val.strip()
                                        break
                                    elif isinstance(field_val, dict):
                                        title = (field_val.get('text') or 
                                                field_val.get('title') or 
                                                field_val.get('headline') or
                                                str(field_val))
                                        if title and title.strip() and title != 'None':
                                            break
                        
                        # Verificar que tenemos un título válido
                        if not title or title.strip() == '' or title == 'None':
                            # Si no hay título, saltar esta noticia
                            continue
                        
                        # Resumen
                        summary = ''
                        if 'summary' in item:
                            summary_obj = item['summary']
                            if isinstance(summary_obj, dict):
                                summary = summary_obj.get('text', summary_obj.get('summary', ''))
                            elif isinstance(summary_obj, str):
                                summary = summary_obj
                        
                        # Limpiar HTML
                        if summary:
                            summary = re.sub('<[^<]+?>', '', summary)
                            summary = re.sub(r'\s+', ' ', summary).strip()
                        
                        # Fecha
                        news_date = datetime.now()
                        if 'pubDate' in item:
                            try:
                                date_val = item['pubDate']
                                if isinstance(date_val, (int, float)):
                                    if date_val > 1e10:
                                        news_date = datetime.fromtimestamp(date_val / 1000)
                                    else:
                                        news_date = datetime.fromtimestamp(date_val)
                                else:
                                    news_date = pd.to_datetime(date_val)
                                    if isinstance(news_date, pd.Timestamp):
                                        if news_date.tz is not None:
                                            news_date = news_date.tz_localize(None).to_pydatetime()
                                        else:
                                            news_date = news_date.to_pydatetime()
                            except:
                                pass
                        
                        # URL
                        url = None
                        if 'uuid' in item:
                            uuid_val = item['uuid']
                            if isinstance(uuid_val, str):
                                if '/' in uuid_val:
                                    url = f"https://finance.yahoo.com/news/{uuid_val.split('/')[-1]}"
                                else:
                                    url = f"https://finance.yahoo.com/news/{uuid_val}"
                        
                        # Validación final del título
                        title_str = str(title).strip() if title else ''
                        if not title_str or title_str == '' or title_str == 'None':
                            continue
                        
                        result.append(NewsItem(
                            symbol=symbol.upper(),
                            title=title_str,
                            summary=str(summary) if summary else '',
                            date=news_date,
                            url=str(url) if url else None,
                            source=self.source_name
                        ))
                    except Exception as e:
                        # Debug: mostrar error si es necesario
                        continue
                
                if result:
                    return result
        except Exception:
            pass
        
        # MÉTODO ALTERNATIVO 2: Endpoint alternativo de Yahoo
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol}&quotesCount=1&newsCount={limit * 2}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'news' in data and isinstance(data['news'], list):
                    for item in data['news'][:limit]:
                        try:
                            if not isinstance(item, dict):
                                continue
                            
                            title = item.get('title') or item.get('headline')
                            if not title:
                                continue
                            
                            summary = item.get('summary') or item.get('description') or item.get('snippet', '')
                            if summary:
                                summary = re.sub('<[^<]+?>', '', summary)
                                summary = re.sub(r'\s+', ' ', summary).strip()
                            
                            news_date = datetime.now()
                            if 'providerPublishTime' in item:
                                try:
                                    ts = item['providerPublishTime']
                                    if isinstance(ts, (int, float)):
                                        news_date = datetime.fromtimestamp(ts / 1000 if ts > 1e10 else ts)
                                except:
                                    pass
                            
                            url = item.get('link') or item.get('url')
                            if not url and 'uuid' in item:
                                url = f"https://finance.yahoo.com/news/{item['uuid']}"
                            
                            # Validación final del título
                            title_str = str(title).strip() if title else ''
                            if not title_str or title_str == '' or title_str == 'None':
                                continue
                            
                            result.append(NewsItem(
                                symbol=symbol.upper(),
                                title=title_str,
                                summary=str(summary),
                                date=news_date,
                                url=str(url) if url else None,
                                source=self.source_name
                            ))
                        except Exception:
                            continue
        except Exception:
            pass
        
        return result
    
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
        SOLUCIÓN INTEGRAL: Normaliza TODOS los índices de fecha a naive (sin timezone)
        para evitar errores al mezclar índices con activos
        
        Args:
            symbols: Lista de símbolos a descargar (puede incluir índices y activos mezclados)
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            period: Período si no se especifican fechas
            source: Fuente de datos
        
        Returns:
            Dict con símbolo como clave y StandardizedPriceData como valor
            TODOS con índices de fecha completamente normalizados (naive)
        """
        from .data_cleaning import force_naive_datetime_index
        
        results = {}
        for symbol in symbols:
            try:
                # Descargar datos históricos
                data = self.download_historical_prices(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    source=source
                )
                
                # NORMALIZACIÓN INTEGRAL: Asegurar que TODOS los índices estén sin timezone
                # Esto es crítico cuando se mezclan índices (^IBEX) con activos (AAPL)
                # porque pueden tener diferentes timezones y pandas falla al alinearlos
                
                # Normalizar el índice de fecha principal
                normalized_date = force_naive_datetime_index(data.date)
                
                # Recrear TODAS las Series con índices completamente nuevos y normalizados
                # Esto garantiza que ninguna serie herede timezone del índice original
                open_series = pd.Series(data.open.values, index=normalized_date)
                high_series = pd.Series(data.high.values, index=normalized_date)
                low_series = pd.Series(data.low.values, index=normalized_date)
                close_series = pd.Series(data.close.values, index=normalized_date)
                volume_series = pd.Series(data.volume.values, index=normalized_date)
                
                # Verificar que TODAS las series tengan índices naive
                for series in [open_series, high_series, low_series, close_series, volume_series]:
                    if hasattr(series.index, 'tz') and series.index.tz is not None:
                        # Si por alguna razón aún tiene timezone, forzar normalización
                        series.index = force_naive_datetime_index(series.index)
                
                # Crear nuevo StandardizedPriceData con datos completamente normalizados
                normalized_data = StandardizedPriceData(
                    symbol=data.symbol,
                    date=normalized_date,
                    open=open_series,
                    high=high_series,
                    low=low_series,
                    close=close_series,
                    volume=volume_series,
                    source=data.source
                )
                
                # Verificación final: asegurar que el índice de fecha esté completamente naive
                if hasattr(normalized_data.date, 'tz') and normalized_data.date.tz is not None:
                    normalized_data.date = force_naive_datetime_index(normalized_data.date)
                
                results[symbol.upper()] = normalized_data
                
            except Exception as e:
                print(f"Error descargando {symbol}: {str(e)}")
                continue
        
        # Verificación final: asegurar que TODAS las series en el diccionario tengan índices naive
        # Esto es una capa adicional de seguridad para evitar problemas al usar estas series juntas
        for symbol, data in results.items():
            try:
                # Verificar y normalizar el índice de fecha principal
                if hasattr(data.date, 'tz') and data.date.tz is not None:
                    data.date = force_naive_datetime_index(data.date)
                
                # Verificar y normalizar todas las Series
                for attr_name in ['open', 'high', 'low', 'close', 'volume']:
                    series = getattr(data, attr_name)
                    if hasattr(series, 'index') and hasattr(series.index, 'tz') and series.index.tz is not None:
                        normalized_idx = force_naive_datetime_index(series.index)
                        setattr(data, attr_name, pd.Series(series.values, index=normalized_idx))
            except Exception as e:
                print(f"Advertencia: Error normalizando {symbol}: {e}")
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
                    include_info: bool = True,
                    news_limit: int = 10) -> Dict[str, Any]:
        """
        Obtiene todos los datos disponibles para un símbolo
        
        Args:
            symbol: Símbolo de la acción
            source: Fuente de datos
            include_news: Si True, incluye noticias
            include_recommendations: Si True, incluye recomendaciones
            include_info: Si True, incluye información de empresa
            news_limit: Número máximo de noticias a obtener (por defecto 10)
        
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
                result['news'] = self.get_news(symbol, limit=news_limit, source=source)
            except Exception as e:
                print(f"Error obteniendo noticias de {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
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
