# 📊 Sistema de Análisis Bursátil

Sistema completo de herramientas para la obtención y análisis de información financiera y bursátil. Este proyecto implementa un conjunto de módulos para descargar datos históricos, crear portfolios, realizar análisis estadísticos, simulaciones de Monte Carlo y generar reportes visuales.

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Requisitos Previos](#requisitos-previos)
4. [Instalación Paso a Paso](#instalación-paso-a-paso)
5. [Uso del Sistema](#uso-del-sistema)
6. [Características Principales](#características-principales)
7. [Documentación de Módulos](#documentación-de-módulos)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción del Proyecto

Este proyecto implementa un sistema modular para:

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
│   └── main.py                  # Script principal de demostración
├── requirements.txt             # Dependencias del proyecto
├── .gitignore                   # Archivos a ignorar en Git
├── README.md                    # Este archivo
├── example_usage.py             # Ejemplos de uso adicionales
└── portfolio_report.md          # Reporte generado (se crea al ejecutar)
```

---

## ✅ Requisitos Previos

Antes de comenzar, necesitas tener instalado:

1. **Python 3.8 o superior**
   - Verifica tu versión: Abre la terminal y escribe `python --version`
   - Si no tienes Python, descárgalo de [python.org](https://www.python.org/downloads/)

2. **Conexión a Internet**
   - Necesaria para descargar datos de APIs financieras

3. **Cuenta de GitHub** (ya la tienes según mencionaste)

---

## 🔑 Configuración de API Keys (Opcional)

El sistema soporta múltiples fuentes de datos. Algunas requieren API keys gratuitas:

- **FRED**: Requiere API key (gratis en https://fred.stlouisfed.org/docs/api/api_key.html)
- **Alpha Vantage**: Requiere API key (gratis en https://www.alphavantage.co/support/#api-key)
- **Stooq**: No requiere API key
- **Yahoo Finance**: No requiere API key (fuente por defecto)

### Configurar API Keys

**Opción 1: Archivo de configuración (Recomendado)**

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

**Opción 2: Input del usuario**

Si no configuras las API keys, el sistema te pedirá que las ingreses cuando las necesites.

**Nota:** Los archivos de configuración están en `.gitignore` para proteger tus API keys.

Para más información, consulta `GUIA_NUEVAS_FUENTES.md`.

---

## 🚀 Instalación Paso a Paso

### Paso 1: Clonar o Descargar el Repositorio

Si tienes el repositorio en GitHub:

1. Ve a tu repositorio en GitHub
2. Haz clic en el botón verde **"Code"**
3. Selecciona **"Download ZIP"**
4. Extrae el archivo ZIP en tu computadora

**O si prefieres usar GitHub Desktop o la interfaz web:**

- Puedes crear/editar archivos directamente desde GitHub web

### Paso 2: Instalar Python (si no lo tienes)

1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga la versión más reciente para Windows
3. Durante la instalación, **marca la casilla "Add Python to PATH"**
4. Haz clic en "Install Now"

### Paso 3: Abrir Terminal en la Carpeta del Proyecto

1. Abre el Explorador de Archivos de Windows
2. Navega hasta la carpeta del proyecto
3. Haz clic en la barra de direcciones y escribe: `cmd` y presiona Enter
   - Esto abrirá la terminal en esa ubicación

### Paso 4: Crear Entorno Virtual (Recomendado)

```bash
python -m venv venv
```

Luego activar el entorno virtual:

**En Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**En Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

Verás que aparece `(venv)` al inicio de la línea de comandos.

### Paso 5: Instalar Dependencias

Con el entorno virtual activado, ejecuta:

```bash
pip install -r requirements.txt
```

Esto instalará todas las librerías necesarias:
- `pandas`: Para manipulación de datos
- `numpy`: Para cálculos numéricos
- `yfinance`: Para descargar datos de Yahoo Finance
- `matplotlib` y `seaborn`: Para gráficos
- `scipy`: Para estadísticas avanzadas

**Si tienes problemas**, prueba con:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 💻 Uso del Sistema

### Ejecución Básica

El script principal demuestra todas las funcionalidades:

**Opción 1: Usando el script auxiliar (recomendado)**
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

Este script:
1. Descarga datos históricos de AAPL, MSFT y GOOGL
2. Crea series de precios con estadísticas
3. Construye un portfolio
4. Genera un reporte en Markdown
5. Crea visualizaciones
6. Ejecuta simulaciones de Monte Carlo

### Uso Personalizado

Puedes crear tus propios scripts. Mira `example_usage.py` para más ejemplos.

---

## 🔧 Características Principales

### 1. Extractor de Datos (`data_extractor.py`)

**Funcionalidades:**
- Descarga de datos históricos de acciones e índices
- Soporte para múltiples fuentes: **Yahoo Finance**, **FRED**, **Stooq**, **Alpha Vantage**
- Formato estandarizado independiente de la fuente
- Descarga de múltiples series simultáneamente
- Cache para evitar llamadas repetidas
- Gestión automática de API keys (archivo de config o input del usuario)

**Ejemplo:**
```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Descargar una acción
data = extractor.download_historical_prices("AAPL", period="1y")

# Descargar múltiples acciones
data_dict = extractor.download_multiple_series(
    symbols=["AAPL", "MSFT", "GOOGL"],
    period="1y"
)
```

### 2. Series de Precios (`price_series.py`)

**DataClass con métodos estadísticos automáticos:**
- Media y desviación típica (calculadas automáticamente)
- Volatilidad (anualizada)
- Ratio de Sharpe
- Máximo Drawdown
- Correlación con otras series
- Estadísticas completas (skewness, kurtosis, etc.)

**Ejemplo:**
```python
from src.price_series import PriceSeries
from src.data_extractor import DataExtractor, StandardizedPriceData

extractor = DataExtractor()
data = extractor.download_historical_prices("AAPL", period="1y")
ps = PriceSeries.from_standardized_data(data)

# Estadísticas automáticas
print(f"Media: ${ps.mean_price:.2f}")
print(f"Volatilidad: {ps.volatility(annualized=True)*100:.2f}%")
print(f"Sharpe Ratio: {ps.sharpe_ratio():.3f}")

# Resumen completo
stats = ps.get_summary_stats()
print(stats)
```

### 3. Portfolio (`portfolio.py`)

**Una cartera es una colección de PriceSeries con pesos asociados.**

**Métodos principales:**
- `get_portfolio_value_series()`: Valor combinado de la cartera
- `monte_carlo_simulation()`: Simulación para la cartera completa
- `monte_carlo_individual_assets()`: Simulación por activo
- `report()`: Genera reporte en Markdown
- `plots_report()`: Genera visualizaciones

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

# Generar reporte
report = portfolio.report()
print(report)

# Guardar reporte
with open("mi_reporte.md", "w", encoding="utf-8") as f:
    f.write(report)

# Generar gráficos
portfolio.plots_report(save_dir="mis_graficos")

# Simulación Monte Carlo
mc_results = portfolio.monte_carlo_simulation(
    days=252,      # 1 año
    simulations=1000,
    random_seed=42
)

# Visualizar resultados
portfolio.plot_monte_carlo_results(mc_results)
```

### 4. Limpieza de Datos (`data_cleaning.py`)

**Acepta cualquier formato de entrada con serie temporal de precios.**

**Funcionalidades:**
- Detección automática de formato
- Normalización de DataFrames
- Eliminación de duplicados
- Completado de valores faltantes
- Detección y corrección de outliers
- Validación de coherencia

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

## 📚 Documentación de Módulos

### DataExtractor

**Métodos principales:**
- `download_historical_prices()`: Descarga datos de una acción/índice
- `download_multiple_series()`: Descarga N series simultáneamente
- `download_index_data()`: Descarga datos de índices
- `download_company_info()`: Información adicional de empresas

### PriceSeries

**Métodos estadísticos:**
- `returns()`: Calcula retornos (simple o logarítmicos)
- `volatility()`: Volatilidad con ventana configurable
- `sharpe_ratio()`: Ratio de Sharpe
- `max_drawdown()`: Máximo drawdown
- `correlation_with()`: Correlación con otra serie
- `get_summary_stats()`: Diccionario completo de estadísticas

### Portfolio

**Métodos de análisis:**
- `get_portfolio_value_series()`: Valor temporal de la cartera
- `get_portfolio_returns()`: Retornos de la cartera
- `monte_carlo_simulation()`: Simulación Monte Carlo del portfolio
- `monte_carlo_individual_assets()`: Simulación por activo
- `plot_monte_carlo_results()`: Visualización de resultados
- `report()`: Reporte en Markdown con análisis completo
- `plots_report()`: Genera múltiples visualizaciones

### DataCleaner

**Métodos de limpieza:**
- `detect_data_format()`: Detecta formato de entrada
- `normalize_dataframe()`: Normaliza a formato estándar
- `clean_price_data()`: Limpia datos (duplicados, outliers, etc.)
- `create_price_series_from_data()`: Crea PriceSeries desde cualquier formato
- `validate_price_series()`: Valida coherencia de datos

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Análisis Simple de una Acción

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries

# Crear extractor
extractor = DataExtractor()

# Descargar datos de Apple
data = extractor.download_historical_prices("AAPL", period="1y")

# Crear serie de precios
apple = PriceSeries.from_standardized_data(data)

# Ver estadísticas
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

# Descargar datos
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
data_dict = extractor.download_multiple_series(symbols, period="2y")

# Crear series
price_series = [
    PriceSeries.from_standardized_data(data_dict[sym])
    for sym in symbols
]

# Crear portfolio (pesos personalizados)
portfolio = Portfolio(
    symbols=symbols,
    price_series=price_series,
    weights=[0.3, 0.25, 0.25, 0.2]  # 30%, 25%, 25%, 20%
)

# Análisis completo
report = portfolio.report()
portfolio.plots_report()
```

### Ejemplo 3: Simulación Monte Carlo Avanzada

```python
from src.portfolio import Portfolio

# Portfolio ya creado
portfolio = ...

# Simulación a 2 años
mc_2y = portfolio.monte_carlo_simulation(
    days=504,           # 2 años (252 días/año * 2)
    simulations=5000,  # Más simulaciones = más precisión
    random_seed=123
)

# Visualizar
portfolio.plot_monte_carlo_results(
    mc_2y,
    title="Proyección 2 Años - Portfolio",
    show_confidence_intervals=True
)

# Estadísticas
final_values = mc_2y.iloc[:, -1]
print(f"Valor esperado: ${final_values.mean():.2f}")
print(f"Percentil 5%: ${final_values.quantile(0.05):.2f}")
print(f"Percentil 95%: ${final_values.quantile(0.95):.2f}")
```

### Ejemplo 4: Datos desde CSV Personalizado

```python
import pandas as pd
from src.data_cleaning import DataCleaner

# Leer CSV personalizado
df = pd.read_csv("mis_precios.csv")

# Crear PriceSeries
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
pip install yfinance
```

O reinstala todas las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "No se encontraron datos para [SYMBOL]"

**Posibles causas:**
- El símbolo no existe o está mal escrito
- Problemas de conexión a Internet
- La API de Yahoo Finance está temporalmente no disponible

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

### Problemas con caracteres especiales en Windows

**Solución:**
- Asegúrate de usar `encoding="utf-8"` al guardar archivos
- El código ya incluye esto por defecto

---

## 📝 Notas Importantes

1. **Formato Estandarizado**: Todos los extractores devuelven objetos `StandardizedPriceData`, garantizando compatibilidad independientemente de la fuente.

2. **Cálculos Automáticos**: Las estadísticas básicas (media, desviación) se calculan automáticamente al crear un `PriceSeries`.

3. **Monte Carlo Configurable**: La simulación acepta parámetros para días, número de simulaciones y valor inicial.

4. **Reportes en Markdown**: Los reportes se generan en formato Markdown y pueden visualizarse en GitHub directamente.

5. **Visualizaciones**: Los gráficos se guardan automáticamente en alta resolución (300 DPI).

---

## 🎓 Conceptos Clave del Proyecto

### ¿Qué es una Portfolio?

Una cartera es una **colección de series de precios con pesos asociados**. Por ejemplo:
- 40% Apple (AAPL)
- 30% Microsoft (MSFT)
- 30% Google (GOOGL)

El portfolio permite analizar el comportamiento conjunto de múltiples activos.

### ¿Por qué Estandarizar el Formato?

Diferentes APIs devuelven datos en formatos diferentes. Al estandarizar, el resto del código funciona igual independientemente de la fuente, facilitando:
- Cambiar de fuente sin modificar código
- Combinar datos de múltiples fuentes
- Mantener coherencia en el análisis

### ¿Cómo Funciona Monte Carlo?

La simulación de Monte Carlo:
1. Analiza los retornos históricos
2. Genera miles de escenarios aleatorios posibles
3. Proyecta la evolución futura basada en estadísticas históricas
4. Proporciona intervalos de confianza (ej: "con 90% de probabilidad, el valor estará entre X e Y")

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

---

## 🧪 Verificación de Instalación

Antes de ejecutar el programa, puedes verificar que todo esté correctamente instalado:

```bash
python verificar_instalacion.py
```

Este script verificará:
- ✅ Versión de Python
- ✅ Dependencias instaladas
- ✅ Módulos del proyecto
- ✅ Prueba rápida de funcionamiento

---

**¡Éxito con tu proyecto! 🚀**

