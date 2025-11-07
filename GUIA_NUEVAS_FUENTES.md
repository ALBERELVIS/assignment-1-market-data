# 📊 Guía: Nuevas Fuentes de Datos

El extractor de datos ahora soporta múltiples fuentes además de Yahoo Finance:
- **FRED** (Federal Reserve Economic Data)
- **Stooq**
- **Alpha Vantage**

---

## 🔑 Configuración de API Keys

### Opción 1: Archivo de Configuración (Recomendado)

Crea un archivo `config.json` en la raíz del proyecto:

```json
{
  "FRED_API_KEY": "tu_fred_api_key_aqui",
  "ALPHA_VANTAGE_API_KEY": "tu_alpha_vantage_api_key_aqui"
}
```

O crea un archivo `.env`:

```
FRED_API_KEY=tu_fred_api_key_aqui
ALPHA_VANTAGE_API_KEY=tu_alpha_vantage_api_key_aqui
```

**Nota:** Estos archivos están en `.gitignore` para proteger tus API keys.

### Opción 2: Input del Usuario

Si no configuras las API keys en un archivo, el sistema te pedirá que las ingreses cuando las necesites.

### Obtener API Keys

- **FRED**: Gratis en https://fred.stlouisfed.org/docs/api/api_key.html
- **Alpha Vantage**: Gratis en https://www.alphavantage.co/support/#api-key
- **Stooq**: No requiere API key

---

## 📚 Uso de las Nuevas Fuentes

### FRED (Federal Reserve Economic Data)

FRED proporciona datos económicos y financieros de la Reserva Federal de St. Louis.

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar datos de una serie de FRED
# Ejemplos de series: "SP500", "DEXUSEU", "UNRATE", "GDP"
data = extractor.download_historical_prices(
    symbol="SP500",  # S&P 500 Index
    start_date="2020-01-01",
    end_date="2023-12-31",
    source="fred"
)

print(f"Datos descargados: {len(data)} días")
print(data.to_dataframe().head())

# Obtener información de la serie
info = extractor.get_company_info("SP500", source="fred")
print(f"Título: {info.get('title')}")
print(f"Unidades: {info.get('units')}")
```

**Series populares de FRED:**
- `SP500`: S&P 500 Index
- `DEXUSEU`: Euro/USD Exchange Rate
- `UNRATE`: Unemployment Rate
- `GDP`: Gross Domestic Product
- `DGS10`: 10-Year Treasury Rate

**Nota:** FRED generalmente solo proporciona valores de cierre (Close). Los valores de Open, High y Low se duplican del Close.

### Stooq

Stooq proporciona datos históricos de acciones e índices de múltiples mercados.

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar datos desde Stooq
# Formato de símbolos: "AAPL.US", "MSFT.US", "IBEX.ES", "SAN.ES"
data = extractor.download_historical_prices(
    symbol="AAPL.US",  # Apple en mercado US
    start_date="2020-01-01",
    end_date="2023-12-31",
    source="stooq"
)

print(f"Datos descargados: {len(data)} días")
print(data.to_dataframe().head())
```

**Formatos de símbolos Stooq:**
- Acciones US: `AAPL.US`, `MSFT.US`, `GOOGL.US`
- Acciones españolas: `SAN.ES`, `BBVA.ES`, `REP.ES`
- Índices: `IBEX.ES`, `SPX.US`, `DJI.US`

**Nota:** 
- Stooq no requiere API key
- **Importante:** El símbolo debe tener formato `SYMBOL.MARKET` (ej: `AAPL.US`)
- Si ingresas solo `AAPL`, el sistema automáticamente lo convertirá a `AAPL.US`
- Para otros mercados, especifica el sufijo correcto (`.ES` para España, `.UK` para Reino Unido, etc.)

### Alpha Vantage

Alpha Vantage proporciona datos de acciones, forex, criptomonedas y más.

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar datos desde Alpha Vantage
data = extractor.download_historical_prices(
    symbol="AAPL",
    period="1y",
    source="alpha_vantage"
)

print(f"Datos descargados: {len(data)} días")
print(data.to_dataframe().head())

# Obtener información de la empresa
info = extractor.get_company_info("AAPL", source="alpha_vantage")
print(f"Nombre: {info.get('name')}")
print(f"Sector: {info.get('sector')}")
print(f"P/E Ratio: {info.get('pe_ratio')}")
```

**Límites de Alpha Vantage:**
- Plan gratuito: 5 llamadas por minuto, 500 por día
- Para uso intensivo, considera actualizar a un plan de pago

---

## 🔄 Comparar Datos de Diferentes Fuentes

Puedes comparar datos del mismo activo desde diferentes fuentes:

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar desde múltiples fuentes
yahoo_data = extractor.download_historical_prices("AAPL", period="1y", source="yahoo")
stooq_data = extractor.download_historical_prices("AAPL.US", period="1y", source="stooq")
alpha_data = extractor.download_historical_prices("AAPL", period="1y", source="alpha_vantage")

# Comparar precios de cierre
print("Último precio de cierre:")
print(f"Yahoo Finance: ${yahoo_data.close.iloc[-1]:.2f}")
print(f"Stooq: ${stooq_data.close.iloc[-1]:.2f}")
print(f"Alpha Vantage: ${alpha_data.close.iloc[-1]:.2f}")
```

---

## 📋 Fuentes Disponibles

Para ver todas las fuentes disponibles:

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()
print(f"Fuentes disponibles: {extractor.get_supported_sources()}")
# Output: ['yahoo', 'stooq', 'fred', 'alpha_vantage']
```

---

## ⚠️ Notas Importantes

1. **FRED**: 
   - Requiere API key (gratis)
   - Generalmente solo proporciona valores de cierre
   - Ideal para datos económicos e índices

2. **Stooq**:
   - No requiere API key
   - Soporta múltiples mercados (US, ES, etc.)
   - Formato de símbolos específico (ej: `AAPL.US`)

3. **Alpha Vantage**:
   - Requiere API key (gratis)
   - Tiene límites de llamadas (5/min, 500/día en plan gratuito)
   - Proporciona datos completos (OHLCV) e información de empresas

4. **Yahoo Finance**:
   - No requiere API key
   - Sigue siendo la fuente por defecto
   - Amplia cobertura de activos

---

## 🚀 Ejemplo Completo

```python
from src.data_extractor import DataExtractor

# Inicializar extractor (carga automáticamente todos los adaptadores)
extractor = DataExtractor()

# Ver fuentes disponibles
print("Fuentes disponibles:", extractor.get_supported_sources())

# Ejemplo 1: Datos económicos desde FRED
try:
    gdp_data = extractor.download_historical_prices(
        symbol="GDP",
        start_date="2020-01-01",
        end_date="2023-12-31",
        source="fred"
    )
    print(f"\n✅ Datos de GDP descargados: {len(gdp_data)} puntos")
except Exception as e:
    print(f"❌ Error con FRED: {e}")

# Ejemplo 2: Acción desde Stooq
try:
    aapl_stooq = extractor.download_historical_prices(
        symbol="AAPL.US",
        period="6m",
        source="stooq"
    )
    print(f"\n✅ Datos de AAPL desde Stooq: {len(aapl_stooq)} días")
except Exception as e:
    print(f"❌ Error con Stooq: {e}")

# Ejemplo 3: Acción desde Alpha Vantage
try:
    aapl_av = extractor.download_historical_prices(
        symbol="AAPL",
        period="6m",
        source="alpha_vantage"
    )
    print(f"\n✅ Datos de AAPL desde Alpha Vantage: {len(aapl_av)} días")
    
    # Obtener información adicional
    info = extractor.get_company_info("AAPL", source="alpha_vantage")
    print(f"   Nombre: {info.get('name')}")
    print(f"   Sector: {info.get('sector')}")
except Exception as e:
    print(f"❌ Error con Alpha Vantage: {e}")
```

---

## 🔧 Solución de Problemas

### Error: "API key no configurada"

**Solución:**
1. Crea un archivo `config.json` o `.env` en la raíz del proyecto
2. Agrega tu API key correspondiente
3. O ingresa la API key cuando el sistema te la solicite

### Error: "No se encontraron datos para [símbolo]"

**Solución:**
- **FRED**: Verifica que el ID de la serie sea correcto (ej: "SP500", no "^SP500")
- **Stooq**: Usa el formato correcto (ej: "AAPL.US" para acciones US, "SAN.ES" para acciones españolas)
- **Alpha Vantage**: Verifica que el símbolo sea correcto y que no hayas excedido el límite de llamadas

### Error: "Límite de llamadas excedido" (Alpha Vantage)

**Solución:**
- El plan gratuito tiene límites: 5 llamadas/minuto, 500/día
- Espera unos minutos antes de hacer más llamadas
- Considera usar otras fuentes (Yahoo Finance, Stooq) que no tienen límites

---

**¡Disfruta de múltiples fuentes de datos financieros! 🎉**

