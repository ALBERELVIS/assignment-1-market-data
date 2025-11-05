# Guía de Simulación Monte Carlo

Esta guía explica cómo usar las funcionalidades mejoradas de simulación Monte Carlo para portfolios y activos individuales.

## Características Principales

Las simulaciones Monte Carlo ahora incluyen:

- ✅ **Múltiples distribuciones**: Normal, Student-t (colas pesadas), Log-normal
- ✅ **Parámetros personalizables**: Drift (retorno esperado) y volatilidad personalizados
- ✅ **Simulación para portfolio completo**: Análisis conjunto de toda la cartera
- ✅ **Simulación para activos individuales**: Análisis por componente de la cartera
- ✅ **Visualizaciones avanzadas**: Gráficos con estadísticas, intervalos de confianza y distribuciones
- ✅ **Métodos auxiliares**: Funciones simplificadas para uso rápido

## Uso Básico

### 1. Simulación Monte Carlo para Portfolio Completo

#### Método Simple (Recomendado para principiantes)

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

# Crear portfolio
extractor = DataExtractor()
data_dict = extractor.download_multiple_series(
    symbols=["AAPL", "MSFT", "GOOGL"],
    period="1y"
)

price_series_list = [
    PriceSeries.from_standardized_data(data)
    for data in data_dict.values()
]

portfolio = Portfolio(
    symbols=list(data_dict.keys()),
    price_series=price_series_list
)

# Método más simple: ejecutar y visualizar en un solo paso
sim_df = portfolio.run_and_plot_monte_carlo(
    days=252,
    simulations=1000,
    save_path="mi_simulacion.png"
)
```

#### Método Avanzado (Control total)

```python
# Paso 1: Ejecutar simulación
sim_df = portfolio.monte_carlo_simulation(
    days=252,                    # Número de días a simular
    simulations=1000,            # Número de simulaciones
    distribution='normal',       # 'normal', 'student_t', o 'lognormal'
    drift_override=0.10,        # Retorno esperado 10% anual (opcional)
    volatility_override=0.20,    # Volatilidad 20% anual (opcional)
    annualized=True,             # Parámetros en formato anualizado
    random_seed=42                # Semilla para reproducibilidad
)

# Paso 2: Visualizar resultados
initial_value = portfolio.get_portfolio_value_series().iloc[-1]
portfolio.plot_monte_carlo_results(
    sim_df,
    title="Mi Simulación Monte Carlo",
    initial_value=initial_value,
    save_path="mi_simulacion.png",
    confidence_levels=[0.05, 0.95]  # Intervalo 90% confianza
)
```

### 2. Simulación Monte Carlo para Activos Individuales

#### Método Simple

```python
# Ejecutar y visualizar en un solo paso
sim_dict = portfolio.run_and_plot_monte_carlo_individual(
    days=252,
    simulations=1000,
    save_path="simulaciones_individuales.png"
)
```

#### Método Avanzado con Parámetros Personalizados

```python
# Definir drift personalizado por activo
drift_personalizado = {
    "AAPL": 0.15,   # 15% anual para Apple
    "MSFT": 0.12,   # 12% anual para Microsoft
    "GOOGL": 0.10   # 10% anual para Google
}

# Ejecutar simulaciones
sim_dict = portfolio.monte_carlo_individual_assets(
    days=252,
    simulations=1000,
    distribution='student_t',        # Distribución con colas pesadas
    drift_override=drift_personalizado,
    use_correlation=False,            # Por ahora sin correlación entre activos
    annualized=True,
    random_seed=42
)

# Visualizar
portfolio.plot_monte_carlo_individual(
    sim_dict,
    save_path="simulaciones_individuales.png",
    show_combined=True  # Mostrar gráfico combinado
)
```

## Parámetros Disponibles

### `monte_carlo_simulation()` - Portfolio Completo

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `days` | int | 252 | Días a simular (252 = 1 año) |
| `simulations` | int | 1000 | Número de simulaciones |
| `initial_value` | float | None | Valor inicial (None = valor actual) |
| `random_seed` | int | None | Semilla para reproducibilidad |
| `distribution` | str | 'normal' | 'normal', 'student_t', 'lognormal' |
| `drift_override` | float | None | Retorno esperado personalizado (anualizado) |
| `volatility_override` | float | None | Volatilidad personalizada (anualizada) |
| `use_historical_volatility` | bool | True | Usar volatilidad histórica |
| `annualized` | bool | True | Parámetros en formato anualizado |

### `monte_carlo_individual_assets()` - Activos Individuales

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `days` | int | 252 | Días a simular |
| `simulations` | int | 1000 | Número de simulaciones |
| `random_seed` | int | None | Semilla para reproducibilidad |
| `distribution` | str | 'normal' | Tipo de distribución |
| `drift_override` | Dict[str, float] | None | Drift por símbolo (ej: {'AAPL': 0.10}) |
| `volatility_override` | Dict[str, float] | None | Volatilidad por símbolo |
| `use_correlation` | bool | True | Incluir correlaciones (próximamente) |
| `annualized` | bool | True | Parámetros anualizados |

### `plot_monte_carlo_results()` - Visualización

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `simulation_df` | DataFrame | - | DataFrame con simulaciones |
| `save_path` | str | None | Ruta para guardar gráfico |
| `title` | str | "..." | Título del gráfico |
| `show_confidence_intervals` | bool | True | Mostrar intervalos de confianza |
| `show_all_paths` | bool | True | Mostrar todas las trayectorias |
| `confidence_levels` | List[float] | [0.05, 0.95] | Niveles de confianza |
| `show_statistics` | bool | True | Mostrar estadísticas en gráfico |
| `initial_value` | float | None | Valor inicial para referencia |

## Distribuciones Disponibles

### 1. Normal (`'normal'`)
- Distribución estándar
- Adecuada para la mayoría de casos
- Retornos simétricos

### 2. Student-t (`'student_t'`)
- Colas más pesadas que la normal
- Captura mejor eventos extremos
- Útil para activos volátiles

### 3. Log-normal (`'lognormal'`)
- Basada en retornos logarítmicos
- Precios siempre positivos
- Útil para modelar precios de acciones

## Ejemplos de Uso

### Ejemplo 1: Simulación Básica

```python
# Crear portfolio
portfolio = Portfolio(...)

# Simulación básica con valores por defecto
sim_df = portfolio.monte_carlo_simulation()
portfolio.plot_monte_carlo_results(sim_df)
```

### Ejemplo 2: Simulación con Parámetros Optimistas

```python
# Simulación con retorno esperado alto (15% anual)
sim_df = portfolio.monte_carlo_simulation(
    days=252,
    simulations=1000,
    drift_override=0.15,  # 15% anual
    volatility_override=0.25,  # 25% volatilidad
    distribution='normal'
)

portfolio.plot_monte_carlo_results(
    sim_df,
    title="Escenario Optimista (15% retorno esperado)"
)
```

### Ejemplo 3: Simulación Conservadora con Student-t

```python
# Simulación conservadora con distribución Student-t
sim_df = portfolio.monte_carlo_simulation(
    days=252,
    simulations=1000,
    drift_override=0.05,  # 5% anual (conservador)
    volatility_override=0.15,  # 15% volatilidad
    distribution='student_t'  # Colas pesadas
)

portfolio.plot_monte_carlo_results(
    sim_df,
    title="Escenario Conservador",
    confidence_levels=[0.01, 0.99, 0.05, 0.95]  # Múltiples intervalos
)
```

### Ejemplo 4: Comparar Activos Individuales

```python
# Simulación individual con drift personalizado
drift_personalizado = {
    "AAPL": 0.15,
    "MSFT": 0.12,
    "GOOGL": 0.10
}

sim_dict = portfolio.monte_carlo_individual_assets(
    days=252,
    simulations=1000,
    drift_override=drift_personalizado,
    distribution='normal'
)

# Visualizar todas las simulaciones
portfolio.plot_monte_carlo_individual(
    sim_dict,
    show_combined=True
)
```

## Interpretación de Resultados

### Gráfico de Trayectorias
- **Líneas azules transparentes**: Trayectorias individuales de cada simulación
- **Línea roja**: Media de todas las simulaciones
- **Línea verde**: Mediana de todas las simulaciones
- **Área gris**: Intervalo de confianza (por defecto 90%)

### Gráfico de Distribución
- Muestra la distribución de valores finales
- Líneas verticales indican:
  - Roja: Media
  - Verde: Mediana
  - Negra: Valor inicial

### Estadísticas Mostradas
- **Media**: Valor promedio esperado
- **Mediana**: Valor central (menos afectado por outliers)
- **Min/Max**: Rango de valores posibles
- **Std**: Desviación estándar (volatilidad)
- **Prob. ganancia**: Porcentaje de simulaciones con ganancia

## Consejos de Uso

1. **Número de simulaciones**: 
   - 500-1000: Rápido, suficiente para la mayoría de casos
   - 5000-10000: Más preciso, pero más lento

2. **Distribución**:
   - `normal`: Para activos estables
   - `student_t`: Para activos volátiles o análisis de riesgo
   - `lognormal`: Para modelado teórico de precios

3. **Parámetros personalizados**:
   - Use `drift_override` cuando tenga expectativas específicas de retorno
   - Use `volatility_override` cuando conozca la volatilidad implícita

4. **Reproducibilidad**:
   - Use `random_seed` para obtener resultados reproducibles
   - Útil para comparar diferentes escenarios

## Ejecutar Ejemplo Completo

```bash
python example_monte_carlo.py
```

Este script ejecuta varios ejemplos que demuestran todas las funcionalidades.

## Notas Técnicas

- Las simulaciones usan retornos diarios (252 días = 1 año de trading)
- Los parámetros anualizados se convierten automáticamente a diarios
- La correlación entre activos está planificada para futuras versiones
- Las visualizaciones se guardan en alta resolución (300 DPI)

