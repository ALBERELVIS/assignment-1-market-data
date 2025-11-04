# 🔌 Guía: Agregar APIs Personalizadas al Extractor de Datos

El extractor de datos ahora es **completamente extensible** y puede conectarse a **cualquier API** financiera. Además, extrae no solo valores numéricos, sino también **recomendaciones, noticias, información de empresa**, etc.

---

## ✨ Nuevas Características

### 1. **Soporte para Cualquier API**
- Sistema de adaptadores que permite agregar nuevas fuentes fácilmente
- No necesitas modificar el código base, solo registrar tu API

### 2. **Datos Cualitativos**
- **Recomendaciones** de analistas
- **Noticias** relacionadas
- **Información de empresa** (sector, P/E ratio, etc.)
- **Calendario de resultados** (earnings)
- **Estados financieros** (opcional)

### 3. **Compatibilidad Total**
- El código existente sigue funcionando igual
- No necesitas cambiar nada de lo que ya tienes

---

## 📚 Uso Básico (Igual que Antes)

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar precios (funciona igual)
data = extractor.download_historical_prices("AAPL", period="1y")

# ✨ NUEVO: Obtener recomendaciones
recommendations = extractor.get_recommendations("AAPL")
for rec in recommendations:
    print(f"{rec.firm}: {rec.rating}")

# ✨ NUEVO: Obtener noticias
news = extractor.get_news("AAPL", limit=10)
for item in news:
    print(f"{item.title} - {item.date}")

# ✨ NUEVO: Obtener información de empresa
info = extractor.get_company_info("AAPL")
print(f"Sector: {info['sector']}")
print(f"P/E Ratio: {info['pe_ratio']}")
```

---

## 🎯 Obtener Todos los Datos de Una Vez

```python
all_data = extractor.get_all_data(
    symbol="AAPL",
    source="yahoo",
    include_news=True,
    include_recommendations=True,
    include_info=True
)

print(f"Precios: {all_data['prices']}")
print(f"Noticias: {len(all_data['news'])}")
print(f"Recomendaciones: {len(all_data['recommendations'])}")
print(f"Info empresa: {all_data['company_info']}")
```

---

## 🔧 Agregar una API Personalizada (Método 1: Funciones)

La forma más simple es usar `register_generic_api()`:

```python
from src.data_extractor import DataExtractor, StandardizedPriceData, Recommendation, NewsItem
import pandas as pd
import requests
from typing import Optional, List
from datetime import datetime

extractor = DataExtractor()

# 1. Función para obtener precios
def mi_api_get_prices(symbol: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None, period: Optional[str] = None):
    """Obtiene precios desde tu API"""
    url = f"https://tu-api.com/v1/prices/{symbol}"
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": "TU_API_KEY"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # Convertir a DataFrame
    df = pd.DataFrame(data['prices'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df

# 2. Función para estandarizar datos
def mi_api_standardize(symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
    """Estandariza datos de tu API al formato común"""
    return StandardizedPriceData(
        symbol=symbol.upper(),
        date=data.index,
        open=data['open'],      # Mapea las columnas de tu API
        high=data['high'],
        low=data['low'],
        close=data['close'],
        volume=data['volume'],
        source="mi_api"
    )

# 3. Función para recomendaciones (opcional)
def mi_api_get_recommendations(symbol: str) -> List[Recommendation]:
    """Obtiene recomendaciones desde tu API"""
    url = f"https://tu-api.com/v1/recommendations/{symbol}"
    response = requests.get(url, params={"api_key": "TU_API_KEY"})
    data = response.json()
    
    recommendations = []
    for item in data['recommendations']:
        recommendations.append(Recommendation(
            symbol=symbol.upper(),
            date=datetime.fromisoformat(item['date']),
            firm=item['firm'],
            rating=item['rating'],
            target_price=item.get('target_price'),
            source="mi_api"
        ))
    return recommendations

# 4. Función para noticias (opcional)
def mi_api_get_news(symbol: str, limit: int = 10) -> List[NewsItem]:
    """Obtiene noticias desde tu API"""
    url = f"https://tu-api.com/v1/news/{symbol}"
    response = requests.get(url, params={"limit": limit, "api_key": "TU_API_KEY"})
    data = response.json()
    
    news = []
    for item in data['news']:
        news.append(NewsItem(
            symbol=symbol.upper(),
            title=item['title'],
            summary=item['summary'],
            date=datetime.fromisoformat(item['date']),
            url=item.get('url'),
            source="mi_api"
        ))
    return news

# Registrar la API
extractor.register_generic_api(
    source_name="mi_api",
    price_function=mi_api_get_prices,
    standardize_function=mi_api_standardize,
    recommendations_function=mi_api_get_recommendations,
    news_function=mi_api_get_news
)

# ¡Ya puedes usarla!
data = extractor.download_historical_prices("AAPL", source="mi_api")
news = extractor.get_news("AAPL", source="mi_api")
```

---

## 🏗️ Agregar una API Personalizada (Método 2: Clase)

Para APIs más complejas, crea una clase que herede de `APISourceAdapter`:

```python
from src.data_extractor import APISourceAdapter, StandardizedPriceData, Recommendation, NewsItem
import pandas as pd
import requests
from typing import Optional, List

class MiAPIAdapter(APISourceAdapter):
    """Adaptador para tu API personalizada"""
    
    def __init__(self, api_key: str):
        self.source_name = "mi_api"
        self.api_key = api_key
        self.base_url = "https://tu-api.com"
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None):
        """Obtiene precios históricos"""
        url = f"{self.base_url}/v1/prices/{symbol}"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        # Procesar y convertir a DataFrame
        df = pd.DataFrame(data['prices'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df
    
    def standardize_data(self, symbol: str, data: pd.DataFrame) -> StandardizedPriceData:
        """Estandariza los datos"""
        return StandardizedPriceData(
            symbol=symbol.upper(),
            date=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume'],
            source=self.source_name
        )
    
    def get_recommendations(self, symbol: str) -> List[Recommendation]:
        """Obtiene recomendaciones"""
        # Implementar lógica aquí
        return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Obtiene noticias"""
        # Implementar lógica aquí
        return []
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información de empresa"""
        # Implementar lógica aquí
        return {}

# Usar el adaptador
extractor = DataExtractor()
adapter = MiAPIAdapter(api_key="TU_API_KEY")
extractor.register_adapter("mi_api", adapter)
```

---

## 📊 Ejemplos de APIs Comunes

### Alpha Vantage

```python
def alpha_vantage_get_prices(symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None):
    import requests
    api_key = "TU_ALPHA_VANTAGE_KEY"
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # Convertir formato de Alpha Vantage a DataFrame
    time_series = data.get("Time Series (Daily)", {})
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    return df
```

### Polygon.io

```python
class PolygonAdapter(APISourceAdapter):
    def __init__(self, api_key: str):
        self.source_name = "polygon"
        self.api_key = api_key
    
    def get_historical_prices(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None, period: Optional[str] = None):
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
        response = requests.get(url, params={"apiKey": self.api_key})
        data = response.json()
        
        # Procesar respuesta de Polygon
        results = data.get('results', [])
        df = pd.DataFrame(results)
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
        df = df.set_index('timestamp')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'vw', 'n']
        return df[['Open', 'High', 'Low', 'Close', 'Volume']]
```

---

## 🎨 Estructuras de Datos

### `Recommendation`
```python
@dataclass
class Recommendation:
    symbol: str
    date: datetime
    firm: str          # Casa de análisis
    rating: str        # "Buy", "Hold", "Sell", etc.
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    source: str = ""
```

### `NewsItem`
```python
@dataclass
class NewsItem:
    symbol: str
    title: str
    summary: str
    date: datetime
    url: Optional[str] = None
    source: str = ""
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
```

---

## 📝 Checklist para Agregar una Nueva API

- [ ] Función/clase para obtener precios históricos
- [ ] Función para estandarizar datos a `StandardizedPriceData`
- [ ] (Opcional) Función para recomendaciones
- [ ] (Opcional) Función para noticias
- [ ] (Opcional) Función para información de empresa
- [ ] Registrar la API con `register_adapter()` o `register_generic_api()`
- [ ] Probar que funciona con `download_historical_prices(symbol, source="tu_api")`

---

## 🔍 Ver Fuentes Disponibles

```python
extractor = DataExtractor()
print(f"Fuentes disponibles: {extractor.get_supported_sources()}")
# Output: ['yahoo', 'mi_api', 'alpha_vantage', ...]
```

---

## 💡 Consejos

1. **Mantén la compatibilidad**: Siempre devuelve `StandardizedPriceData` para precios
2. **Usa cache**: El sistema tiene cache automático, pero puedes agregar más lógica
3. **Maneja errores**: Incluye try/except en tus funciones
4. **Documenta**: Añade docstrings explicando qué hace tu API
5. **Testa**: Prueba con diferentes símbolos y períodos

---

## 🚀 Ejemplo Completo

Ver `ejemplo_apis_personalizadas.py` para ejemplos completos y detallados.

---

**¡Ahora puedes conectar tu extractor a cualquier API financiera! 🎉**

