"""
Ejemplo de cómo usar el nuevo sistema extensible de extractor de datos
y cómo agregar APIs personalizadas
"""

from src.data_extractor import DataExtractor, Recommendation, NewsItem, StandardizedPriceData
import pandas as pd
from typing import Optional, List
from datetime import datetime


def ejemplo_uso_basico():
    """Ejemplo básico de uso (igual que antes)"""
    print("=" * 60)
    print("EJEMPLO 1: Uso Básico (compatible con código anterior)")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Descargar precios (funciona igual que antes)
    data = extractor.download_historical_prices("AAPL", period="1y")
    print(f"✓ Datos descargados: {len(data)} días")
    
    # Obtener recomendaciones
    recommendations = extractor.get_recommendations("AAPL")
    print(f"\n✓ Recomendaciones encontradas: {len(recommendations)}")
    for rec in recommendations[:3]:  # Mostrar primeras 3
        print(f"  - {rec.firm}: {rec.rating} (Fecha: {rec.date.date()})")
    
    # Obtener noticias
    news = extractor.get_news("AAPL", limit=5)
    print(f"\n✓ Noticias encontradas: {len(news)}")
    for item in news[:3]:  # Mostrar primeras 3
        print(f"  - {item.title[:60]}...")
        print(f"    Fecha: {item.date.date()}")
    
    # Obtener información de empresa
    info = extractor.get_company_info("AAPL")
    print(f"\n✓ Información de empresa:")
    print(f"  - Nombre: {info.get('name', 'N/A')}")
    print(f"  - Sector: {info.get('sector', 'N/A')}")
    print(f"  - P/E Ratio: {info.get('pe_ratio', 'N/A')}")


def ejemplo_obtener_todo():
    """Obtener todos los datos disponibles de una vez"""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Obtener Todos los Datos")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Obtener todo de una vez
    all_data = extractor.get_all_data(
        symbol="AAPL",
        source="yahoo",
        include_news=True,
        include_recommendations=True,
        include_info=True
    )
    
    print(f"\n✓ Datos obtenidos para {all_data['symbol']}")
    print(f"  - Precios: {'✓' if all_data['prices'] else '✗'}")
    print(f"  - Noticias: {len(all_data['news'])}")
    print(f"  - Recomendaciones: {len(all_data['recommendations'])}")
    print(f"  - Info empresa: {'✓' if all_data['company_info'] else '✗'}")


def ejemplo_agregar_api_personalizada():
    """
    Ejemplo de cómo agregar una API personalizada
    (ejemplo con Alpha Vantage - requiere API key)
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Agregar API Personalizada")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Ejemplo: Agregar Alpha Vantage (requiere API key)
    def alpha_vantage_get_prices(symbol: str, start_date: Optional[str] = None,
                                 end_date: Optional[str] = None, period: Optional[str] = None):
        """Función para obtener precios desde Alpha Vantage"""
        # NOTA: Esto es un ejemplo. Necesitarías una API key real
        # import requests
        # api_key = "TU_API_KEY"
        # url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        # response = requests.get(url)
        # data = response.json()
        # ... procesar y convertir a DataFrame ...
        
        # Por ahora, retornamos un DataFrame vacío como ejemplo
        print("⚠️  Este es solo un ejemplo. Necesitas implementar la conexión real a Alpha Vantage")
        return pd.DataFrame()
    
    def alpha_vantage_standardize(symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Función para estandarizar datos de Alpha Vantage"""
        # Convertir formato de Alpha Vantage a StandardizedPriceData
        # ... lógica de conversión ...
        pass
    
    def alpha_vantage_get_recommendations(symbol: str) -> List[Recommendation]:
        """Función para obtener recomendaciones desde Alpha Vantage"""
        # ... implementar lógica ...
        return []
    
    # Registrar la API personalizada
    extractor.register_generic_api(
        source_name="alpha_vantage",
        price_function=alpha_vantage_get_prices,
        standardize_function=alpha_vantage_standardize,
        recommendations_function=alpha_vantage_get_recommendations
    )
    
    print("✓ API 'alpha_vantage' registrada")
    print(f"  Fuentes disponibles: {extractor.get_supported_sources()}")


def ejemplo_api_rest_simple():
    """
    Ejemplo de cómo agregar una API REST simple
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 4: API REST Simple")
    print("=" * 60)
    
    import requests
    
    extractor = DataExtractor()
    
    def custom_api_get_prices(symbol: str, start_date: Optional[str] = None,
                              end_date: Optional[str] = None, period: Optional[str] = None):
        """
        Ejemplo de función para obtener precios desde una API REST genérica
        """
        # Ejemplo: API REST que devuelve JSON
        # url = f"https://api.ejemplo.com/v1/prices/{symbol}"
        # params = {
        #     "start_date": start_date,
        #     "end_date": end_date,
        #     "api_key": "TU_API_KEY"
        # }
        # response = requests.get(url, params=params)
        # data = response.json()
        
        # Convertir respuesta JSON a DataFrame
        # df = pd.DataFrame(data['prices'])
        # df['date'] = pd.to_datetime(df['date'])
        # df = df.set_index('date')
        # return df
        
        print("⚠️  Implementa la conexión real a tu API")
        return pd.DataFrame()
    
    def custom_api_standardize(symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza datos de la API personalizada"""
        # Mapear columnas de tu API al formato estándar
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=data.index,
            open=data['open'],  # o el nombre que use tu API
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume'],
            source="custom_api"
        )
    
    def custom_api_get_news(symbol: str, limit: int = 10) -> List[NewsItem]:
        """Obtiene noticias desde la API personalizada"""
        # url = f"https://api.ejemplo.com/v1/news/{symbol}?limit={limit}"
        # response = requests.get(url)
        # news_data = response.json()
        
        # result = []
        # for item in news_data:
        #     result.append(NewsItem(
        #         symbol=symbol.upper(),
        #         title=item['title'],
        #         summary=item['summary'],
        #         date=datetime.fromisoformat(item['date']),
        #         url=item.get('url'),
        #         source="custom_api"
        #     ))
        # return result
        
        return []
    
    # Registrar la API
    extractor.register_generic_api(
        source_name="custom_api",
        price_function=custom_api_get_prices,
        standardize_function=custom_api_standardize,
        news_function=custom_api_get_news
    )
    
    print("✓ API 'custom_api' registrada")
    print("  Puedes usarla así: extractor.download_historical_prices('AAPL', source='custom_api')")


def ejemplo_crear_adaptador_completo():
    """
    Ejemplo de cómo crear un adaptador completo (clase)
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Crear Adaptador Completo (Clase)")
    print("=" * 60)
    
    from src.data_extractor import APISourceAdapter, Recommendation, NewsItem
    
    class PolygonAdapter(APISourceAdapter):
        """Adaptador para Polygon.io (ejemplo)"""
        
        def __init__(self, api_key: str):
            self.source_name = "polygon"
            self.api_key = api_key
            self.base_url = "https://api.polygon.io"
        
        def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                                 end_date: Optional[str] = None, period: Optional[str] = None):
            """Obtiene precios desde Polygon.io"""
            # url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
            # response = requests.get(url, params={"apiKey": self.api_key})
            # data = response.json()
            # ... procesar y convertir a DataFrame ...
            return pd.DataFrame()
        
        def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
            """Estandariza datos de Polygon.io"""
            # Lógica de estandarización específica para Polygon
            pass
        
        def get_recommendations(self, symbol: str) -> List[Recommendation]:
            """Obtiene recomendaciones (si la API las tiene)"""
            return []
        
        def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
            """Obtiene noticias desde Polygon.io"""
            # url = f"{self.base_url}/v2/reference/news"
            # response = requests.get(url, params={"ticker": symbol, "limit": limit, "apiKey": self.api_key})
            # ... procesar noticias ...
            return []
    
    # Usar el adaptador
    extractor = DataExtractor()
    polygon_adapter = PolygonAdapter(api_key="TU_API_KEY")
    extractor.register_adapter("polygon", polygon_adapter)
    
    print("✓ Adaptador 'polygon' registrado como clase completa")


def main():
    """Ejecuta todos los ejemplos"""
    ejemplo_uso_basico()
    ejemplo_obtener_todo()
    ejemplo_agregar_api_personalizada()
    ejemplo_api_rest_simple()
    ejemplo_crear_adaptador_completo()
    
    print("\n" + "=" * 60)
    print("✅ Todos los ejemplos completados")
    print("=" * 60)
    print("\nResumen:")
    print("1. El sistema es 100% compatible con código anterior")
    print("2. Puedes agregar cualquier API mediante funciones o clases")
    print("3. Soporta extracción de precios, noticias, recomendaciones, etc.")
    print("4. Cada API mantiene su formato interno pero se estandariza al salir")


if __name__ == "__main__":
    main()

