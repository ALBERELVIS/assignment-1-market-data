# 📊 Sistema de Análisis Bursátil - Trabajo Final

Sistema completo de herramientas para la obtención y análisis de información financiera y bursátil. Este proyecto implementa un conjunto de módulos para descargar datos históricos desde múltiples fuentes, crear portfolios, realizar análisis estadísticos, simulaciones de Monte Carlo y generar reportes visuales.

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Requisitos Previos](#requisitos-previos)
4. [Instalación](#instalación)
5. [Funcionalidades Principales](#funcionalidades-principales)
6. [Arquitectura y Diseño](#arquitectura-y-diseño)
7. [Uso del Sistema](#uso-del-sistema)
8. [Respuestas a Preguntas del Trabajo](#respuestas-a-preguntas-del-trabajo)
9. [Ejemplos de Uso](#ejemplos-de-uso)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción del Proyecto

Este proyecto implementa un sistema modular y extensible para:

- **Extracción de datos**: Descarga de información histórica de precios desde múltiples fuentes (Yahoo Finance, FRED, Stooq, Alpha Vantage)
- **Estandarización**: Formato unificado independientemente de la fuente de datos
- **Análisis estadístico**: Cálculo automático de métricas (media, desviación, volatilidad, Sharpe, etc.)
- **Portfolio Management**: Creación y gestión de carteras con múltiples activos
- **Simulación Monte Carlo**: Proyecciones de evolución futura con parámetros configurables
- **Visualizaciones**: Gráficos profesionales y reportes en Markdown
- **Limpieza de datos**: Preprocesado automático para aceptar múltiples formatos de entrada

---

## 📁 Estructura del Proyecto

```
.
├── src/                          # Código fuente principal
│   ├── __init__.py              # Inicialización del módulo
│   ├── data_extractor.py        # Extractor de datos desde APIs
│   ├── api_adapters.py          # Adaptadores para FRED, Stooq, Alpha Vantage
│   ├── config_manager.py        # Gestión de API keys y configuración
│   ├── price_series.py           # DataClass para series de precios
│   ├── portfolio.py             # Clase Portfolio con métodos de análisis
│   ├── data_cleaning.py         # Limpieza y preprocesado de datos
│   ├── price_plots.py           # Funciones de visualización
│   └── main.py                  # Script principal interactivo
├── tests/                        # Tests unitarios
├── docs/                         # Documentación adicional
├── requirements.txt             # Dependencias del proyecto
├── config.example.json          # Ejemplo de configuración
├── run_main.py                  # Script auxiliar para ejecución
└── README.md                    # Este archivo
```

---

## ✅ Requisitos Previos

- **Python 3.8 o superior**
- **Conexión a Internet** (necesaria para descargar datos de APIs financieras)
- **API Keys opcionales** (algunas fuentes requieren API keys gratuitas)

---

## 🚀 Instalación

### Paso 1: Clonar o Descargar el Repositorio

```bash
git clone <url-del-repositorio>
cd assignment-1-market-data-Improvements-Montecarlo
```

### Paso 2: Crear Entorno Virtual (Recomendado)

```bash
python -m venv venv
```

**Activar entorno virtual:**

- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- Windows (CMD): `venv\Scripts\activate.bat`
- Linux/Mac: `source venv/bin/activate`

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

O usar el script de instalación automática:

```bash
python install_dependencies.py
```

### Paso 4: Configurar API Keys (Opcional)

Crea un archivo `config.json` en la raíz del proyecto:

```json
{
  "FRED_API_KEY": "tu_fred_api_key_aqui",
  "ALPHA_VANTAGE_API_KEY": "tu_alpha_vantage_api_key_aqui"
}
```

**Nota:** Los archivos de configuración están en `.gitignore` para proteger tus API keys.

---

## 🔧 Funcionalidades Principales

### 1. Extractor de Datos (`data_extractor.py`)

**Funcionalidades:**
- ✅ Descarga de datos históricos de acciones e índices
- ✅ Soporte para múltiples fuentes: **Yahoo Finance**, **FRED**, **Stooq**, **Alpha Vantage**
- ✅ **Formato estandarizado** independiente de la fuente (`StandardizedPriceData`)
- ✅ Descarga de **N series simultáneamente** mediante `download_multiple_series()`
- ✅ Cache para evitar llamadas repetidas
- ✅ Gestión automática de API keys (archivo de config o input del usuario)
- ✅ Extracción de datos adicionales: noticias, recomendaciones, información de empresas

**Ejemplo:**
```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar una acción
data = extractor.download_historical_prices("AAPL", period="1y")

# Descargar múltiples acciones simultáneamente
data_dict = extractor.download_multiple_series(
    symbols=["AAPL", "MSFT", "GOOGL", "^GSPC"],
    period="1y"
)
```

### 2. Series de Precios (`price_series.py`)

**DataClass con métodos estadísticos automáticos:**
- ✅ **Media y desviación típica** (calculadas automáticamente en `__post_init__`)
- ✅ Volatilidad (anualizada)
- ✅ Ratio de Sharpe
- ✅ Máximo Drawdown
- ✅ Correlación con otras series
- ✅ Estadísticas completas (skewness, kurtosis, etc.)

**Ejemplo:**
```python
from src.price_series import PriceSeries
from src.data_extractor import DataExtractor

extractor = DataExtractor()
data = extractor.download_historical_prices("AAPL", period="1y")
ps = PriceSeries.from_standardized_data(data)

# Estadísticas automáticas (calculadas al crear el objeto)
print(f"Media: ${ps.mean_price:.2f}")  # Calculada automáticamente
print(f"Desviación típica: ${ps.std_price:.2f}")  # Calculada automáticamente
print(f"Volatilidad: {ps.volatility(annualized=True)*100:.2f}%")
print(f"Sharpe Ratio: {ps.sharpe_ratio():.3f}")
```

### 3. Portfolio (`portfolio.py`)

**Una cartera es una colección de PriceSeries con pesos asociados.**

**Métodos principales:**
- ✅ `get_portfolio_value_series()`: Valor combinado de la cartera
- ✅ `monte_carlo_simulation()`: Simulación para la cartera completa (configurable)
- ✅ `monte_carlo_individual_assets()`: Simulación por activo individual
- ✅ `report()`: Genera reporte en Markdown con análisis completo
- ✅ `plots_report()`: Genera visualizaciones profesionales

**Ejemplo:**
```python
from src.portfolio import Portfolio
from src.price_series import PriceSeries

# Crear portfolio
portfolio = Portfolio(
    symbols=["AAPL", "MSFT", "GOOGL"],
    price_series=[ps1, ps2, ps3],
    weights=[0.4, 0.3, 0.3]  # 40%, 30%, 30%
)

# Generar reporte en Markdown
report = portfolio.report(include_warnings=True, include_correlation=True)
print(report)

# Guardar reporte
with open("portfolio_report.md", "w", encoding="utf-8") as f:
    f.write(report)

# Generar gráficos
portfolio.plots_report(save_dir="plots")

# Simulación Monte Carlo (configurable)
mc_results = portfolio.monte_carlo_simulation(
    years=10,           # Años a simular
    simulations=10000,  # Número de simulaciones
    initial_value=10000,  # Valor inicial
    random_seed=42,     # Para reproducibilidad
    rebalance=True,     # Reequilibrar periódicamente
    rebalance_frequency='monthly',  # Frecuencia de reequilibrio
    inflation_rate=0.025  # Ajuste por inflación (opcional)
)
```

### 4. Limpieza de Datos (`data_cleaning.py`)

**Acepta cualquier formato de entrada con serie temporal de precios.**

**Funcionalidades:**
- ✅ Detección automática de formato
- ✅ Normalización de DataFrames
- ✅ Eliminación de duplicados
- ✅ Completado de valores faltantes
- ✅ Detección y corrección de outliers
- ✅ Validación de coherencia

**Ejemplo:**
```python
from src.data_cleaning import DataCleaner
import pandas as pd

# Desde DataFrame personalizado
df = pd.read_csv("mis_datos.csv")
cleaner = DataCleaner()
ps = cleaner.create_price_series_from_data(
    data=df,
    symbol="CUSTOM",
    source="mis_datos",
    clean=True
)
```

---

## 🏗️ Arquitectura y Diseño

Para un diagrama detallado de clases e interacciones, consulta [DIAGRAMA_CLASES.md](docs/DIAGRAMA_CLASES.md).

### Diagrama de Clases e Interacciones (Resumen)

```
┌─────────────────────────────────────────────────────────────────┐
│                        DataExtractor                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ - download_historical_prices()                           │   │
│  │ - download_multiple_series()                            │   │
│  │ - download_index_data()                                 │   │
│  │ - get_recommendations()                                  │   │
│  │ - get_news()                                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           │ usa                                  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              APISourceAdapter (Abstract)                  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ YahooFinanceAdapter                                 │  │   │
│  │  │ FREDAdapter                                         │  │   │
│  │  │ StooqAdapter                                        │  │   │
│  │  │ AlphaVantageAdapter                                 │  │   │
│  │  │ GenericAPIAdapter                                   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           │ retorna                              │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           StandardizedPriceData (DataClass)              │   │
│  │  - symbol: str                                          │   │
│  │  - date: pd.DatetimeIndex                               │   │
│  │  - open, high, low, close, volume: pd.Series            │   │
│  │  - source: str                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ convierte a
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PriceSeries (DataClass)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Atributos (calculados automáticamente):                  │  │
│  │ - mean_price: float  ← calculado en __post_init__       │  │
│  │ - std_price: float   ← calculado en __post_init__       │  │
│  │                                                           │  │
│  │ Métodos estadísticos:                                     │  │
│  │ - returns() → pd.Series                                  │  │
│  │ - volatility() → float                                   │  │
│  │ - sharpe_ratio() → float                                 │  │
│  │ - max_drawdown() → float                                 │  │
│  │ - correlation_with() → float                            │  │
│  │ - get_summary_stats() → dict                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ contiene múltiples
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Portfolio (DataClass)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Atributos:                                                │  │
│  │ - symbols: List[str]                                     │  │
│  │ - price_series: List[PriceSeries]                        │  │
│  │ - weights: List[float]                                   │  │
│  │                                                           │  │
│  │ Métodos principales:                                      │  │
│  │ - get_portfolio_value_series() → pd.Series              │  │
│  │ - get_portfolio_returns() → pd.Series                   │  │
│  │ - monte_carlo_simulation() → pd.DataFrame               │  │
│  │ - monte_carlo_individual_assets() → Dict[str, DataFrame]│  │
│  │ - report() → str (Markdown)                             │  │
│  │ - plots_report() → None (guarda gráficos)               │  │
│  │ - plot_monte_carlo_results() → None                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ usa
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DataCleaner                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - detect_data_format() → str                             │  │
│  │ - normalize_dataframe() → pd.DataFrame                   │  │
│  │ - clean_price_data() → pd.DataFrame                      │  │
│  │ - create_price_series_from_data() → PriceSeries         │  │
│  │ - validate_price_series() → bool                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
1. Usuario solicita datos
   │
   ▼
2. DataExtractor selecciona adaptador según fuente
   │
   ▼
3. Adaptador descarga datos de API
   │
   ▼
4. Adaptador estandariza datos → StandardizedPriceData
   │
   ▼
5. StandardizedPriceData → PriceSeries (estadísticas automáticas)
   │
   ▼
6. Múltiples PriceSeries → Portfolio
   │
   ▼
7. Portfolio genera:
   - Reporte Markdown (.report())
   - Visualizaciones (.plots_report())
   - Simulaciones Monte Carlo (.monte_carlo_simulation())
```

---

## 💻 Uso del Sistema

### Ejecución Básica

**Opción 1: Script interactivo (recomendado)**
```bash
python run_main.py
```

**Opción 2: Como módulo**
```bash
python -m src.main
```

**Opción 3: Desde el directorio src**
```bash
cd src
python main.py
```

### Uso Programático

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

# 1. Extraer datos
extractor = DataExtractor()
data_dict = extractor.download_multiple_series(
    symbols=["AAPL", "MSFT", "GOOGL"],
    period="1y"
)

# 2. Crear series de precios (estadísticas automáticas)
price_series = [
    PriceSeries.from_standardized_data(data)
    for data in data_dict.values()
]

# 3. Crear portfolio
portfolio = Portfolio(
    symbols=list(data_dict.keys()),
    price_series=price_series,
    weights=[0.4, 0.3, 0.3]
)

# 4. Generar reporte
report = portfolio.report()
with open("report.md", "w", encoding="utf-8") as f:
    f.write(report)

# 5. Generar visualizaciones
portfolio.plots_report(save_dir="plots")

# 6. Simulación Monte Carlo
mc_results = portfolio.monte_carlo_simulation(
    years=10,
    simulations=10000
)
```

---

## 📝 Respuestas a Preguntas del Trabajo

### 1. ¿Qué es una cartera?

**Respuesta:** Una cartera (Portfolio) es una **colección de series de precios con pesos asociados**. Cada serie de precios representa un activo (acción o índice), y cada activo tiene un peso que indica qué porcentaje del portfolio representa.

**Ejemplo:**
- 40% Apple (AAPL)
- 30% Microsoft (MSFT)
- 30% Google (GOOGL)

El portfolio permite analizar el comportamiento conjunto de múltiples activos, calcular métricas agregadas, y realizar simulaciones considerando las correlaciones entre activos.

**Implementación:**
```python
@dataclass
class Portfolio:
    symbols: List[str]              # Símbolos de los activos
    price_series: List[PriceSeries] # Series de precios de cada activo
    weights: List[float]            # Pesos (porcentajes) de cada activo
```

### 2. ¿Por qué estandarizar el formato de salida?

**Respuesta:** Diferentes APIs devuelven datos en formatos diferentes:
- Yahoo Finance: DataFrame con columnas `Open`, `High`, `Low`, `Close`, `Volume`
- FRED: JSON con estructura diferente
- Stooq: CSV con formato propio
- Alpha Vantage: JSON con estructura diferente

Al estandarizar, el resto del código funciona igual independientemente de la fuente, facilitando:
- ✅ Cambiar de fuente sin modificar código
- ✅ Combinar datos de múltiples fuentes
- ✅ Mantener coherencia en el análisis
- ✅ Extensibilidad: agregar nuevas fuentes fácilmente

**Implementación:**
```python
@dataclass
class StandardizedPriceData:
    symbol: str
    date: pd.DatetimeIndex
    open: pd.Series
    high: pd.Series
    low: pd.Series
    close: pd.Series
    volume: pd.Series
    source: str  # Identifica la fuente original
```

### 3. ¿Cómo funcionan los métodos estadísticos automáticos?

**Respuesta:** Los métodos estadísticos básicos (media y desviación típica) se calculan **automáticamente** al crear un objeto `PriceSeries` mediante el método `__post_init__()`.

**Implementación:**
```python
@dataclass
class PriceSeries:
    # Atributos calculados automáticamente
    mean_price: Optional[float] = field(init=False, default=None)
    std_price: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calcula automáticamente media y desviación típica"""
        self._calculate_basic_stats()
    
    def _calculate_basic_stats(self):
        """Calcula estadísticas básicas automáticamente"""
        self.mean_price = float(self.close.mean())
        self.std_price = float(self.close.std())
```

**Uso:**
```python
ps = PriceSeries.from_standardized_data(data)
# mean_price y std_price ya están calculados automáticamente
print(ps.mean_price)  # Disponible inmediatamente
print(ps.std_price)   # Disponible inmediatamente
```

### 4. ¿Cómo funciona la simulación de Monte Carlo?

**Respuesta:** La simulación de Monte Carlo:

1. **Analiza los retornos históricos** de cada activo
2. **Calcula estadísticas** (media, desviación estándar, correlaciones)
3. **Genera miles de escenarios aleatorios** posibles usando distribuciones normales multivariadas
4. **Proyecta la evolución futura** día a día (o mes a mes) basada en estadísticas históricas
5. **Proporciona intervalos de confianza** (ej: "con 90% de probabilidad, el valor estará entre X e Y")

**Parámetros configurables:**
- `years`: Años a simular
- `simulations`: Número de simulaciones (más = más precisión)
- `initial_value`: Valor inicial del portfolio
- `random_seed`: Para reproducibilidad
- `rebalance`: Si reequilibrar periódicamente
- `rebalance_frequency`: Frecuencia de reequilibrio (monthly, quarterly, yearly)
- `inflation_rate`: Tasa de inflación para ajustar retornos

**Disponible para:**
- Portfolio completo: `portfolio.monte_carlo_simulation()`
- Activos individuales: `portfolio.monte_carlo_individual_assets()`

### 5. ¿Debería el programa aceptar cualquier tipo de input siempre que exista una serie temporal de precios?

**Respuesta:** Sí. El programa acepta múltiples formatos de entrada mediante la clase `DataCleaner`:

- ✅ DataFrames de pandas (cualquier formato de columnas)
- ✅ Archivos CSV
- ✅ Diccionarios
- ✅ Listas de tuplas
- ✅ Cualquier formato con serie temporal de precios

**Implementación:**
```python
class DataCleaner:
    def create_price_series_from_data(
        self,
        data: Union[pd.DataFrame, dict, list],
        symbol: str,
        source: str,
        clean: bool = True
    ) -> PriceSeries:
        """
        Acepta cualquier formato de entrada y lo convierte a PriceSeries
        """
        # Detecta formato automáticamente
        # Normaliza a formato estándar
        # Limpia datos (duplicados, outliers, valores faltantes)
        # Valida coherencia
        # Retorna PriceSeries
```

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Análisis Simple de una Acción

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries

extractor = DataExtractor()
data = extractor.download_historical_prices("AAPL", period="1y")
apple = PriceSeries.from_standardized_data(data)

# Estadísticas automáticas
stats = apple.get_summary_stats()
for key, value in stats.items():
    print(f"{key}: {value}")
```

### Ejemplo 2: Portfolio con Pesos Personalizados

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

extractor = DataExtractor()
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
data_dict = extractor.download_multiple_series(symbols, period="2y")

price_series = [
    PriceSeries.from_standardized_data(data_dict[sym])
    for sym in symbols
]

portfolio = Portfolio(
    symbols=symbols,
    price_series=price_series,
    weights=[0.3, 0.25, 0.25, 0.2]
)

# Análisis completo
report = portfolio.report()
portfolio.plots_report()
```

### Ejemplo 3: Simulación Monte Carlo Avanzada

```python
from src.portfolio import Portfolio

portfolio = ...  # Portfolio ya creado

# Simulación a 10 años con 10,000 simulaciones
mc_results = portfolio.monte_carlo_simulation(
    years=10,
    simulations=10000,
    initial_value=10000,
    random_seed=123,
    rebalance=True,
    rebalance_frequency='monthly',
    inflation_rate=0.025
)

# Visualizar
portfolio.plot_monte_carlo_results(mc_results)

# Estadísticas
final_values = mc_results.iloc[-1]
print(f"Valor esperado: ${final_values.mean():.2f}")
print(f"Percentil 5%: ${final_values.quantile(0.05):.2f}")
print(f"Percentil 95%: ${final_values.quantile(0.95):.2f}")
```

### Ejemplo 4: Datos desde CSV Personalizado

```python
import pandas as pd
from src.data_cleaning import DataCleaner

df = pd.read_csv("mis_precios.csv")
cleaner = DataCleaner()
ps = cleaner.create_price_series_from_data(
    data=df,
    symbol="MI_ACCION",
    source="archivo_local",
    clean=True
)

# Usar normalmente
stats = ps.get_summary_stats()
```

---

## 🔍 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'yfinance'"

**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "No se encontraron datos para [SYMBOL]"

**Posibles causas:**
- El símbolo no existe o está mal escrito
- Problemas de conexión a Internet
- La API está temporalmente no disponible

**Solución:**
- Verifica que el símbolo sea correcto (ej: "AAPL", no "APPLE")
- Para índices, usa el símbolo correcto (ej: "^GSPC" para S&P 500)
- Intenta de nuevo más tarde

### Error al generar gráficos

**Solución:**
```bash
pip install --upgrade matplotlib seaborn
```

### El código es muy lento

**Causas comunes:**
- Descargando muchos datos
- Muchas simulaciones de Monte Carlo

**Solución:**
- Usa períodos más cortos para pruebas
- Reduce el número de simulaciones (500 en lugar de 1000)
- El extractor tiene cache automático

---

## 📄 Notas Importantes

1. **Formato Estandarizado**: Todos los extractores devuelven objetos `StandardizedPriceData`, garantizando compatibilidad independientemente de la fuente.

2. **Cálculos Automáticos**: Las estadísticas básicas (media, desviación) se calculan automáticamente al crear un `PriceSeries`.

3. **Monte Carlo Configurable**: La simulación acepta parámetros para años, número de simulaciones, valor inicial, reequilibrio e inflación.

4. **Reportes en Markdown**: Los reportes se generan en formato Markdown y pueden visualizarse en GitHub directamente.

5. **Visualizaciones**: Los gráficos se guardan automáticamente en alta resolución (300 DPI).

---

## 📧 Soporte

Si encuentras problemas:
1. Revisa la sección [Troubleshooting](#troubleshooting)
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de tener Python 3.8+
4. Comprueba tu conexión a Internet

---

## 📄 Licencia

Este proyecto es para uso educativo/académico.

---

**¡Éxito con tu proyecto! 🚀**
