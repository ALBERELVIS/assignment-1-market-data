# Assignment 1 – Market Data Toolkit

Herramientas profesionales para la obtención, estandarización y análisis de información bursátil.

## 📋 Descripción

Este proyecto proporciona un conjunto completo de herramientas para trabajar con datos financieros. El sistema está diseñado con arquitectura modular, siguiendo buenas prácticas de programación para permitir escalabilidad y mantenibilidad.

### Características Principales

- ✅ **Extractores de datos extensibles**: Framework para conectar múltiples APIs (Yahoo Finance, Alpha Vantage, etc.)
- ✅ **Estandarización automática**: Todos los datos se convierten a un formato común independientemente de la fuente
- ✅ **Análisis estadístico integrado**: Cálculo automático de media, desviación típica y métricas avanzadas
- ✅ **Simulación de Monte Carlo**: Previsión de evolución de activos y carteras
- ✅ **Reportes automáticos**: Generación de informes en Markdown con análisis y advertencias
- ✅ **Visualizaciones profesionales**: Gráficos interactivos para análisis de carteras
- ✅ **Limpieza y validación**: Herramientas para asegurar calidad de datos

## 🚀 Instalación

### Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/assignment-1-market-data.git
cd assignment-1-market-data
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. (Opcional) Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 📁 Estructura del Proyecto

```
assignment-1-market-data/
├── src/
│   ├── __init__.py          # Inicialización del paquete
│   ├── extractor.py         # Framework de extractores de datos
│   ├── datamodels.py        # Clases PriceSeries y Portfolio
│   ├── portfolio.py         # Análisis de carteras y Monte Carlo
│   ├── plots.py             # Funciones de visualización
│   ├── utils.py             # Utilidades de limpieza y validación
│   └── main.ipynb           # Notebook de ejemplo
├── docs/
│   ├── README.md            # Documentación adicional
│   └── structure_diagram.png # Diagrama de estructura del proyecto
├── examples/
│   └── sample_colab_notebook.ipynb
├── requirements.txt         # Dependencias del proyecto
├── LICENSE
└── README.md               # Este archivo
```

## 🔧 Uso Básico

### 1. Descargar Datos de Mercado

```python
from src import download_price_series

# Descargar datos históricos de múltiples acciones
tickers = ['AAPL', 'GOOGL', 'MSFT', '^GSPC']  # ^GSPC es el S&P 500
data = download_price_series(
    tickers=tickers,
    start='2020-01-01',
    end='2024-01-01',
    source='yfinance',
    parallel=True
)

# data es un diccionario: {symbol: DataFrame}
```

### 2. Crear Series de Precios

```python
from src import PriceSeries, standardize_price_format

# Crear una PriceSeries desde un DataFrame
aapl_data = data['AAPL']
aapl_series = PriceSeries(
    symbol='AAPL',
    data=aapl_data,
    source='yfinance'
)

# Acceder a estadísticas automáticas
print(f"Media: ${aapl_series.mean:.2f}")
print(f"Desviación típica: ${aapl_series.std:.2f}")
print(f"Retorno total: {aapl_series.stats['total_return']:.2%}")
```

### 3. Crear una Cartera

```python
from src import Portfolio

# Crear múltiples series de precios
assets = {}
for symbol, df in data.items():
    assets[symbol] = PriceSeries(symbol=symbol, data=df, source='yfinance')

# Definir pesos (deben sumar 1.0, se normalizan automáticamente)
weights = {
    'AAPL': 0.3,
    'GOOGL': 0.3,
    'MSFT': 0.2,
    '^GSPC': 0.2
}

# Crear cartera
portfolio = Portfolio(
    assets=assets,
    weights=weights,
    name='Mi Cartera Diversificada'
)

# Acceder a estadísticas de la cartera
print(f"Volatilidad de la cartera: {portfolio.get_volatility():.2%}")
```

### 4. Simulación de Monte Carlo

```python
# Simulación para la cartera completa
mc_results = portfolio.monte_carlo(
    num_simulations=10000,
    num_days=252,  # Un año de trading
    random_seed=42,
    for_individual_assets=True  # También simula cada activo
)

# Acceder a resultados
portfolio_sims = mc_results['portfolio']['simulations']
portfolio_stats = mc_results['portfolio']['statistics']

print(f"Valor esperado final: ${portfolio_stats['mean_final_value']:,.2f}")
print(f"Percentil 5%: ${portfolio_stats['percentile_5']:,.2f}")
print(f"Probabilidad de ganancia: {portfolio_stats['probability_positive']:.2%}")
```

### 5. Generar Reportes

```python
# Generar reporte en Markdown
report = portfolio.report(
    include_warnings=True,
    include_statistics=True,
    include_quality_check=True
)

print(report)

# Guardar en archivo
with open('reporte_cartera.md', 'w', encoding='utf-8') as f:
    f.write(report)
```

### 6. Visualizaciones

```python
# Generar todas las visualizaciones
plots = portfolio.plots_report(
    save_path='plots/',  # Guardar en carpeta
    show=True  # Mostrar en pantalla
)

# O crear visualizaciones individuales
from src import plot_portfolio_evolution, plot_monte_carlo_results

plot_portfolio_evolution(portfolio)
plot_monte_carlo_results(
    portfolio_sims,
    portfolio_stats,
    portfolio.portfolio_value.iloc[-1],
    title='Simulación Monte Carlo - Cartera'
)
```

## 📚 Documentación de Módulos

### Extractor (`extractor.py`)

Framework extensible para descargar datos de múltiples fuentes.

**Clases principales:**
- `ExtractorBase`: Clase abstracta base para todos los extractores
- `YFinanceExtractor`: Implementación para Yahoo Finance
- `GenericCallableExtractor`: Envoltorio para cualquier función fetcher

**Funciones principales:**
- `download_price_series()`: Descarga múltiples series en paralelo
- `register_extractor()`: Registrar nuevos extractores
- `get_extractor()`: Obtener extractor registrado

**Ejemplo de uso:**
```python
from src import download_price_series

data = download_price_series(
    tickers=['AAPL', 'MSFT'],
    start='2023-01-01',
    source='yfinance',
    data_type='prices',  # También: 'dividends', 'splits', 'info', etc.
    parallel=True
)
```

### Data Models (`datamodels.py`)

Clases de datos estandarizadas para series de precios y carteras.

**PriceSeries:**
- Representa una serie temporal de precios de un activo
- Calcula automáticamente: media, desviación típica, retornos, volatilidad
- Métodos: `get_returns()`, `get_volatility()`, `align_with()`

**Portfolio:**
- Colección de PriceSeries con pesos asignados
- Calcula valor agregado de la cartera
- Normaliza automáticamente los pesos
- Alinea todas las series a fechas comunes

### Portfolio Analysis (`portfolio.py`)

Análisis avanzado de carteras y simulaciones de Monte Carlo.

**MonteCarloSimulation:**
- Simula evolución futura usando modelo de difusión geométrica
- Configurable: número de simulaciones, horizonte temporal, semilla aleatoria

**Métodos de Portfolio:**
- `monte_carlo()`: Ejecuta simulación de Monte Carlo
- `report()`: Genera reporte en Markdown
- `plots_report()`: Genera todas las visualizaciones

### Utilities (`utils.py`)

Funciones de limpieza, validación y preprocesado.

**Funciones principales:**
- `clean_price_data()`: Limpia y preprocesa datos
- `validate_price_series()`: Valida integridad de datos
- `standardize_price_format()`: Estandariza formato de cualquier fuente
- `detect_data_quality_issues()`: Detecta problemas de calidad
- `prepare_for_analysis()`: Prepara datos para análisis

### Visualizations (`plots.py`)

Funciones de visualización para análisis de carteras.

**Funciones disponibles:**
- `plot_portfolio_evolution()`: Evolución del valor de la cartera
- `plot_asset_comparison()`: Comparación normalizada de activos
- `plot_correlation_matrix()`: Matriz de correlación entre activos
- `plot_returns_distribution()`: Distribución de retornos
- `plot_risk_return_scatter()`: Análisis riesgo-retorno
- `plot_monte_carlo_results()`: Visualización de simulaciones
- `plot_portfolio_composition()`: Composición de la cartera (gráfico de pastel)

## 🏗️ Arquitectura y Diseño

### Principios de Diseño

1. **Extensibilidad**: Sistema de registro de extractores permite añadir nuevas fuentes fácilmente
2. **Estandarización**: Todos los datos se convierten a formato común independientemente de la fuente
3. **Separación de responsabilidades**: Cada módulo tiene una función clara y bien definida
4. **Reutilización**: Funciones y clases diseñadas para ser reutilizables
5. **Validación**: Validación automática de datos en múltiples niveles

### Diagrama de Estructura

Ver `docs/structure_diagram.png` para un diagrama visual completo de la arquitectura del proyecto.

### Flujo de Datos

1. **Extracción**: `download_price_series()` → APIs externas
2. **Estandarización**: Datos convertidos a formato común
3. **Limpieza**: `clean_price_data()` elimina outliers y valores faltantes
4. **Validación**: `validate_price_series()` verifica integridad
5. **Modelado**: Datos convertidos a `PriceSeries` y `Portfolio`
6. **Análisis**: Cálculo de estadísticas, simulaciones, etc.
7. **Visualización/Reporte**: Generación de gráficos y reportes

## 🔌 Extensibilidad

### Añadir un Nuevo Extractor

```python
from src import ExtractorBase, register_extractor

@register_extractor("mi_fuente")
class MiExtractor(ExtractorBase):
    def fetch(self, symbol, start=None, end=None, data_type="prices", **kwargs):
        # Implementar lógica de descarga
        raw_data = ...  # Obtener datos de tu API
        
        # Estandarizar formato
        from src import standardize_price_format
        df = standardize_price_format(raw_data, symbol, "mi_fuente")
        
        return df

# Usar el nuevo extractor
data = download_price_series(
    tickers=['SYMBOL'],
    source='mi_fuente'
)
```

## 📊 Ejemplos de Uso

Ver `examples/sample_colab_notebook.ipynb` para ejemplos completos de uso.

## 🧪 Testing

```bash
# (Ejemplo - crear tests si es necesario)
python -m pytest tests/
```

## 📝 Licencia

Ver archivo `LICENSE` para más información.

## 🤝 Contribuciones

Este es un proyecto académico. Para sugerencias o mejoras, por favor abre un issue en GitHub.

## 📧 Contacto

Para preguntas sobre este proyecto, contacta al autor.

## 🙏 Agradecimientos

- Yahoo Finance (yfinance) por proporcionar datos gratuitos
- Comunidad de Python por las excelentes bibliotecas utilizadas

---

**Nota**: Este proyecto fue desarrollado como parte de un trabajo final de máster. El objetivo principal es demostrar buenas prácticas de programación, arquitectura de software y manejo de datos financieros.
