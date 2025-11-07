"""
Adaptadores para diferentes fuentes de datos financieros:
- FRED (Federal Reserve Economic Data)
- Stooq
- Alpha Vantage
"""

import pandas as pd
import numpy as np
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .data_extractor import APISourceAdapter, StandardizedPriceData, Recommendation, NewsItem
from .config_manager import get_config_manager
from .data_cleaning import force_naive_datetime_index


class FREDAdapter(APISourceAdapter):
    """
    Adaptador para FRED (Federal Reserve Economic Data)
    https://fred.stlouisfed.org/
    
    Nota: FRED requiere una API key gratuita que se puede obtener en:
    https://fred.stlouisfed.org/docs/api/api_key.html
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el adaptador de FRED
        
        Args:
            api_key: API key de FRED (opcional, se puede obtener desde config)
        """
        self.source_name = "fred"
        self.base_url = "https://api.stlouisfed.org/fred"
        
        # Obtener API key desde config o parámetro
        if api_key:
            self.api_key = api_key
        else:
            config = get_config_manager()
            self.api_key = config.get_api_key(
                "FRED_API_KEY",
                prompt="Ingresa tu FRED API key (obtén una gratis en https://fred.stlouisfed.org/docs/api/api_key.html): ",
                required=False
            )
        
        if not self.api_key:
            print("⚠️  Advertencia: FRED API key no configurada. Algunas funciones pueden no funcionar.")
            print("   Obtén una API key gratuita en: https://fred.stlouisfed.org/docs/api/api_key.html")
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene datos históricos desde FRED
        
        Args:
            symbol: ID de la serie de FRED (ej: "SP500", "DEXUSEU", "UNRATE")
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            period: Período (no usado en FRED, se usa start_date/end_date)
        
        Returns:
            DataFrame con datos históricos
        """
        if not self.api_key:
            raise ValueError("FRED API key no configurada. Configúrala en config.json o .env")
        
        # Construir parámetros
        params = {
            "series_id": symbol,
            "api_key": self.api_key,
            "file_type": "json"
        }
        
        # Agregar fechas si están disponibles
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        
        # Si no hay fechas, usar período por defecto (último año)
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            params["observation_start"] = start_date
            params["observation_end"] = end_date
        
        try:
            url = f"{self.base_url}/series/observations"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "observations" not in data:
                raise ValueError(f"No se encontraron datos para {symbol}")
            
            # Convertir a DataFrame
            observations = data["observations"]
            df_data = []
            
            for obs in observations:
                date = obs.get("date")
                value = obs.get("value")
                
                # FRED usa "." para valores faltantes
                if value == "." or value is None:
                    continue
                
                try:
                    value_float = float(value)
                    df_data.append({
                        "date": pd.to_datetime(date),
                        "Close": value_float
                    })
                except (ValueError, TypeError):
                    continue
            
            if not df_data:
                raise ValueError(f"No se encontraron datos válidos para {symbol}")
            
            df = pd.DataFrame(df_data)
            df = df.set_index("date")
            df = df.sort_index()
            
            # FRED generalmente solo proporciona valores de cierre
            # Duplicar para Open, High, Low (ya que no están disponibles)
            df["Open"] = df["Close"]
            df["High"] = df["Close"]
            df["Low"] = df["Close"]
            df["Volume"] = 0  # FRED no proporciona volumen
            
            # Normalizar índice de fechas
            df.index = force_naive_datetime_index(df.index)
            
            return df[["Open", "High", "Low", "Close", "Volume"]]
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error conectando con FRED API: {e}")
        except Exception as e:
            raise ValueError(f"Error procesando datos de FRED: {e}")
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza datos de FRED"""
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        # Normalizar índice
        date_index = force_naive_datetime_index(data.index)
        
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=date_index,
            open=pd.Series(data["Open"].values, index=date_index),
            high=pd.Series(data["High"].values, index=date_index),
            low=pd.Series(data["Low"].values, index=date_index),
            close=pd.Series(data["Close"].values, index=date_index),
            volume=pd.Series(data["Volume"].values, index=date_index),
            source=self.source_name
        )
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información de la serie de FRED"""
        if not self.api_key:
            return {}
        
        try:
            url = f"{self.base_url}/series"
            params = {
                "series_id": symbol,
                "api_key": self.api_key,
                "file_type": "json"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "seriess" in data and len(data["seriess"]) > 0:
                series_info = data["seriess"][0]
                return {
                    "title": series_info.get("title", "N/A"),
                    "units": series_info.get("units", "N/A"),
                    "frequency": series_info.get("frequency", "N/A"),
                    "seasonal_adjustment": series_info.get("seasonal_adjustment", "N/A"),
                    "source": self.source_name
                }
        except Exception as e:
            print(f"Error obteniendo información de FRED para {symbol}: {e}")
        
        return {}


class StooqAdapter(APISourceAdapter):
    """
    Adaptador para Stooq
    https://stooq.com/
    
    Nota: Stooq no requiere API key para datos básicos
    """
    
    def __init__(self):
        self.source_name = "stooq"
        self.base_url = "https://stooq.com/q/d/l"
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene datos históricos desde Stooq
        
        Args:
            symbol: Símbolo de la acción (ej: "AAPL.US", "MSFT.US", "IBEX.ES")
                   Si no tiene formato .MARKET, intentará agregar .US automáticamente
            start_date: Fecha inicio (YYYY-MM-DD o YYYYMMDD)
            end_date: Fecha fin (YYYY-MM-DD o YYYYMMDD)
            period: Período (ej: "1y", "6m", "3d")
        """
        # Normalizar símbolo: Stooq requiere formato SYMBOL.MARKET
        original_symbol = symbol
        symbol = symbol.strip().upper()
        
        # Si el símbolo no tiene formato .MARKET, intentar agregar .US
        if '.' not in symbol:
            symbol = f"{symbol}.US"
            print(f"ℹ️  Símbolo normalizado a formato Stooq: {original_symbol} -> {symbol}")
        
        # Stooq requiere formato de fecha YYYYMMDD
        if not start_date or not end_date:
            # Calcular fechas desde período
            end_date_obj = datetime.now()
            if period:
                if period.endswith('y'):
                    years = int(period[:-1])
                    start_date_obj = end_date_obj - timedelta(days=years * 365)
                elif period.endswith('m'):
                    months = int(period[:-1])
                    start_date_obj = end_date_obj - timedelta(days=months * 30)
                elif period.endswith('d'):
                    days = int(period[:-1])
                    start_date_obj = end_date_obj - timedelta(days=days)
                else:
                    start_date_obj = end_date_obj - timedelta(days=365)
            else:
                start_date_obj = end_date_obj - timedelta(days=365)
            
            start_date = start_date_obj.strftime("%Y%m%d")
            end_date = end_date_obj.strftime("%Y%m%d")
        else:
            # Convertir formato YYYY-MM-DD a YYYYMMDD
            try:
                if len(start_date) == 10 and '-' in start_date:
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                    start_date = start_date_obj.strftime("%Y%m%d")
                elif len(start_date) == 8:
                    # Ya está en formato YYYYMMDD
                    pass
                else:
                    raise ValueError(f"Formato de fecha no válido: {start_date}")
                
                if len(end_date) == 10 and '-' in end_date:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                    end_date = end_date_obj.strftime("%Y%m%d")
                elif len(end_date) == 8:
                    # Ya está en formato YYYYMMDD
                    pass
                else:
                    raise ValueError(f"Formato de fecha no válido: {end_date}")
            except ValueError as e:
                raise ValueError(f"Error en formato de fechas: {e}")
        
        try:
            # Construir URL de Stooq
            url = f"{self.base_url}/?s={symbol}&d1={start_date}&d2={end_date}&i=d"
            
            # Descargar CSV con headers para evitar bloqueos
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Verificar que la respuesta es CSV
            if not response.text or len(response.text.strip()) < 10:
                raise ValueError(f"Respuesta vacía de Stooq para {symbol}")
            
            # Leer CSV
            from io import StringIO
            csv_data = StringIO(response.text)
            
            # Verificar si hay datos válidos
            first_line = csv_data.readline().strip()
            if not first_line or ("Date" not in first_line and "Data" not in first_line):
                # Puede ser un error de Stooq
                if "error" in response.text.lower() or "not found" in response.text.lower():
                    raise ValueError(f"Símbolo {symbol} no encontrado en Stooq. "
                                   f"Verifica el formato (ej: 'AAPL.US' para acciones US, 'SAN.ES' para acciones españolas)")
                raise ValueError(f"No se encontraron datos para {symbol}. "
                               f"Verifica el símbolo. Formato requerido: SYMBOL.MARKET (ej: AAPL.US, MSFT.US)")
            
            # Leer DataFrame
            csv_data.seek(0)
            try:
                df = pd.read_csv(csv_data)
            except Exception as e:
                raise ValueError(f"Error leyendo CSV de Stooq: {e}. Respuesta: {response.text[:200]}")
            
            if df.empty:
                raise ValueError(f"DataFrame vacío para {symbol}. Verifica el símbolo y las fechas.")
            
            # Normalizar nombres de columnas
            df.columns = [col.strip() for col in df.columns]
            
            # Buscar columna de fecha
            date_col = None
            for col in df.columns:
                if col.lower() in ["date", "data"]:
                    date_col = col
                    break
            
            if not date_col:
                raise ValueError(f"No se encontró columna de fecha en los datos de Stooq. Columnas: {list(df.columns)}")
            
            # Convertir fecha
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            except Exception as e:
                raise ValueError(f"Error convirtiendo fechas: {e}")
            
            df = df.set_index(date_col)
            
            # Mapear columnas a formato estándar (Stooq usa nombres en inglés por defecto)
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            column_mapping = {
                "Open": ["Open", "Otwarcie"],
                "High": ["High", "Najwyzszy"],
                "Low": ["Low", "Najnizszy"],
                "Close": ["Close", "Zamkniecie"],
                "Volume": ["Volume", "Wolumen"]
            }
            
            # Renombrar columnas si es necesario
            for target_col, possible_names in column_mapping.items():
                if target_col not in df.columns:
                    for name in possible_names:
                        if name in df.columns:
                            df = df.rename(columns={name: target_col})
                            break
            
            # Verificar que tenemos las columnas necesarias
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                # Intentar usar Close como fallback para Open, High, Low
                if "Close" in df.columns:
                    for col in ["Open", "High", "Low"]:
                        if col not in df.columns:
                            df[col] = df["Close"]
                # Volume puede ser 0 si no está disponible
                if "Volume" not in df.columns:
                    df["Volume"] = 0
                
                # Verificar de nuevo
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    raise ValueError(f"Faltan columnas requeridas: {missing_cols}. Columnas disponibles: {list(df.columns)}")
            
            # Seleccionar solo las columnas necesarias
            df = df[required_cols]
            
            # Convertir a numérico
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Eliminar filas con NaN en fechas o precios críticos
            df = df.dropna(subset=["Close"])
            
            if df.empty:
                raise ValueError(f"No se encontraron datos válidos para {symbol} en el rango de fechas especificado")
            
            # Ordenar por fecha
            df = df.sort_index()
            
            # Normalizar índice
            df.index = force_naive_datetime_index(df.index)
            
            return df
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error conectando con Stooq para {symbol}: {e}. "
                           f"Verifica tu conexión a internet y que el símbolo sea correcto.")
        except ValueError as e:
            # Re-lanzar errores de ValueError con el mensaje original
            raise
        except Exception as e:
            raise ValueError(f"Error procesando datos de Stooq para {symbol}: {e}. "
                           f"Verifica el formato del símbolo (ej: 'AAPL.US', 'MSFT.US', 'SAN.ES')")
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza datos de Stooq"""
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        # Normalizar índice
        date_index = force_naive_datetime_index(data.index)
        
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=date_index,
            open=pd.Series(data["Open"].values, index=date_index),
            high=pd.Series(data["High"].values, index=date_index),
            low=pd.Series(data["Low"].values, index=date_index),
            close=pd.Series(data["Close"].values, index=date_index),
            volume=pd.Series(data["Volume"].values, index=date_index),
            source=self.source_name
        )


class AlphaVantageAdapter(APISourceAdapter):
    """
    Adaptador para Alpha Vantage
    https://www.alphavantage.co/
    
    Nota: Alpha Vantage requiere una API key gratuita que se puede obtener en:
    https://www.alphavantage.co/support/#api-key
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el adaptador de Alpha Vantage
        
        Args:
            api_key: API key de Alpha Vantage (opcional, se puede obtener desde config)
        """
        self.source_name = "alpha_vantage"
        self.base_url = "https://www.alphavantage.co/query"
        
        # Obtener API key desde config o parámetro
        if api_key:
            self.api_key = api_key
        else:
            config = get_config_manager()
            self.api_key = config.get_api_key(
                "ALPHA_VANTAGE_API_KEY",
                prompt="Ingresa tu Alpha Vantage API key (obtén una gratis en https://www.alphavantage.co/support/#api-key): ",
                required=False
            )
        
        if not self.api_key:
            print("⚠️  Advertencia: Alpha Vantage API key no configurada. Algunas funciones pueden no funcionar.")
            print("   Obtén una API key gratuita en: https://www.alphavantage.co/support/#api-key")
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene datos históricos desde Alpha Vantage
        
        Args:
            symbol: Símbolo de la acción (ej: "AAPL", "MSFT")
            start_date: Fecha inicio (YYYY-MM-DD) - Alpha Vantage no soporta filtrado por fecha directamente
            end_date: Fecha fin (YYYY-MM-DD) - Alpha Vantage no soporta filtrado por fecha directamente
            period: Período (no usado directamente)
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key no configurada. Configúrala en config.json o .env")
        
        try:
            # Alpha Vantage TIME_SERIES_DAILY
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "full"  # "compact" para últimos 100 días, "full" para todo
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar errores de API
            if "Error Message" in data:
                raise ValueError(f"Error de Alpha Vantage: {data['Error Message']}")
            if "Note" in data:
                raise ValueError(f"Alpha Vantage: {data['Note']} (puede ser límite de llamadas)")
            
            # Extraer serie temporal
            time_series_key = None
            for key in data.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                raise ValueError(f"No se encontraron datos de serie temporal para {symbol}")
            
            time_series = data[time_series_key]
            
            # Convertir a DataFrame
            df_data = []
            for date_str, values in time_series.items():
                try:
                    date = pd.to_datetime(date_str)
                    df_data.append({
                        "date": date,
                        "Open": float(values.get("1. open", 0)),
                        "High": float(values.get("2. high", 0)),
                        "Low": float(values.get("3. low", 0)),
                        "Close": float(values.get("4. close", 0)),
                        "Volume": int(float(values.get("5. volume", 0)))
                    })
                except (ValueError, TypeError, KeyError):
                    continue
            
            if not df_data:
                raise ValueError(f"No se encontraron datos válidos para {symbol}")
            
            df = pd.DataFrame(df_data)
            df = df.set_index("date")
            df = df.sort_index()
            
            # Filtrar por fechas si se especificaron
            if start_date:
                start_date_obj = pd.to_datetime(start_date)
                df = df[df.index >= start_date_obj]
            if end_date:
                end_date_obj = pd.to_datetime(end_date)
                df = df[df.index <= end_date_obj]
            
            # Normalizar índice
            df.index = force_naive_datetime_index(df.index)
            
            return df[["Open", "High", "Low", "Close", "Volume"]]
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error conectando con Alpha Vantage API: {e}")
        except Exception as e:
            raise ValueError(f"Error procesando datos de Alpha Vantage: {e}")
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza datos de Alpha Vantage"""
        if data.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        # Normalizar índice
        date_index = force_naive_datetime_index(data.index)
        
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=date_index,
            open=pd.Series(data["Open"].values, index=date_index),
            high=pd.Series(data["High"].values, index=date_index),
            low=pd.Series(data["Low"].values, index=date_index),
            close=pd.Series(data["Close"].values, index=date_index),
            volume=pd.Series(data["Volume"].values, index=date_index),
            source=self.source_name
        )
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información de la empresa desde Alpha Vantage"""
        if not self.api_key:
            return {}
        
        try:
            # Usar OVERVIEW para obtener información de la empresa
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "Error Message" in data or "Note" in data:
                return {}
            
            return {
                "name": data.get("Name", "N/A"),
                "sector": data.get("Sector", "N/A"),
                "industry": data.get("Industry", "N/A"),
                "market_cap": data.get("MarketCapitalization", "N/A"),
                "pe_ratio": data.get("PERatio", "N/A"),
                "dividend_yield": data.get("DividendYield", "N/A"),
                "52_week_high": data.get("52WeekHigh", "N/A"),
                "52_week_low": data.get("52WeekLow", "N/A"),
                "description": data.get("Description", "N/A")[:500] if data.get("Description") else "N/A",
                "source": self.source_name
            }
        except Exception as e:
            print(f"Error obteniendo información de Alpha Vantage para {symbol}: {e}")
            return {}

