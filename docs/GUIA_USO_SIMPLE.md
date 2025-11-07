# 🚀 Guía Simple: Cómo Usar el Proyecto (Sin Saber Programar)

Esta guía te explica paso a paso cómo usar el proyecto **sin necesidad de saber programar**.

---

## 📋 ¿Qué Necesitas Tener?

1. **Python instalado** en tu computadora
2. **Conexión a Internet** (para descargar datos)
3. **Los archivos del proyecto** (que ya tienes)

---

## ✅ Paso 1: Verificar que Python Está Instalado

1. **Abre la terminal** (en Windows):
   - Presiona `Windows + R`
   - Escribe: `cmd`
   - Presiona Enter

2. **En la terminal, escribe:**
   ```
   python --version
   ```
   - Presiona Enter
   - Deberías ver algo como: `Python 3.10.x` o similar
   - Si ves un error, necesitas instalar Python primero

3. **Si NO tienes Python:**
   - Ve a: https://www.python.org/downloads/
   - Descarga la versión para Windows
   - **IMPORTANTE**: Durante la instalación, marca la casilla "Add Python to PATH"
   - Instala y reinicia la terminal

---

## 📦 Paso 2: Instalar las Dependencias (Librerías Necesarias)

Las "dependencias" son programas pequeños que el proyecto necesita para funcionar.

1. **Abre la terminal** en la carpeta del proyecto:
   - Navega hasta la carpeta del proyecto en el Explorador de Archivos
   - Haz clic en la barra de direcciones (donde dice la ruta)
   - Escribe: `cmd` y presiona Enter
   - Esto abrirá la terminal en esa carpeta

2. **Instala las dependencias:**
   ```
   pip install -r requirements.txt
   ```
   - Presiona Enter
   - Espera a que termine (puede tardar 1-2 minutos)
   - Verás muchos mensajes, es normal
   - Cuando termine, deberías ver algo como "Successfully installed..."

---

## ✅ Paso 3: Verificar que Todo Está Correcto

1. **Ejecuta el script de verificación:**
   ```
   python verificar_instalacion.py
   ```
   - Presiona Enter
   - Deberías ver muchas líneas con ✅ (checkmarks verdes)
   - Si todo está bien, verás: "✅ TODAS LAS VERIFICACIONES PASARON"

2. **Si ves errores:**
   - Revisa el mensaje de error
   - Asegúrate de haber ejecutado el Paso 2 (instalar dependencias)

---

## 🎯 Paso 4: Usar el Programa (Tres Formas)

### **Opción 1: Ejecutar el Programa Principal (MÁS FÁCIL)**

Este programa hace todo automáticamente:
- Descarga datos de acciones (Apple, Microsoft, Google)
- Crea un portfolio
- Genera un reporte
- Crea gráficos
- Hace simulaciones

**Cómo hacerlo:**
1. En la terminal, escribe:
   ```
   python run_main.py
   ```
2. Presiona Enter
3. **Espera** (puede tardar 1-2 minutos la primera vez)
4. El programa:
   - Descargará datos de Internet
   - Creará archivos con resultados
   - Mostrará gráficos en pantalla

**Resultados que verás:**
- Se creará un archivo: `portfolio_report.md` (reporte de análisis)
- Se creará una carpeta: `plots/` (con gráficos)
- Se mostrarán gráficos en pantalla

---

### **Opción 2: Ver Ejemplos de Uso**

Este archivo tiene 8 ejemplos diferentes que puedes probar.

**Cómo hacerlo:**
1. En la terminal, escribe:
   ```
   python example_usage.py
   ```
2. Presiona Enter
3. Verás un menú con opciones:
   ```
   1. Análisis de una acción
   2. Portfolio equilibrado
   3. Portfolio personalizado
   ...
   ```
4. Escribe el número de la opción que quieras
5. Presiona Enter

**Ejemplo:**
- Si escribes `1` y presionas Enter, verás el análisis de una sola acción (Apple)
- Si escribes `3` y presionas Enter, verás un portfolio con pesos personalizados

---

### **Opción 3: Crear tu Propio Script Simple**

Si quieres analizar acciones diferentes, puedes crear un archivo simple.

**Cómo hacerlo:**

1. **Crea un archivo nuevo** llamado `mi_analisis.py` en la carpeta del proyecto

2. **Copia y pega este código:**

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

# 1. Crear extractor
extractor = DataExtractor()

# 2. Descargar datos (cambia los símbolos si quieres)
# Símbolos comunes: AAPL (Apple), MSFT (Microsoft), GOOGL (Google), TSLA (Tesla)
symbols = ["AAPL", "MSFT", "GOOGL"]
print(f"Descargando datos de: {', '.join(symbols)}")

data_dict = extractor.download_multiple_series(symbols, period="1y")

# 3. Crear series de precios
price_series = [
    PriceSeries.from_standardized_data(data_dict[sym])
    for sym in symbols
]

# 4. Crear portfolio (pesos iguales)
portfolio = Portfolio(
    symbols=symbols,
    price_series=price_series
)

# 5. Generar reporte
print("\nGenerando reporte...")
report = portfolio.report()
with open("mi_reporte.md", "w", encoding="utf-8") as f:
    f.write(report)

print("✅ Reporte guardado en 'mi_reporte.md'")

# 6. Generar gráficos
print("Generando gráficos...")
portfolio.plots_report(save_dir="mis_graficos")
print("✅ Gráficos guardados en 'mis_graficos/'")
```

3. **Guarda el archivo**

4. **Ejecuta en la terminal:**
   ```
   python mi_analisis.py
   ```

5. **Cambia los símbolos** si quieres analizar otras acciones:
   - En la línea que dice `symbols = ["AAPL", "MSFT", "GOOGL"]`
   - Cambia por los símbolos que quieras (ej: `["TSLA", "NVDA"]`)

---

## 📊 ¿Qué Significan los Resultados?

### **Archivo `portfolio_report.md`**

Este archivo contiene:
- **Composición del portfolio**: Qué acciones tienes y en qué proporción
- **Análisis individual**: Estadísticas de cada acción
- **Análisis del portfolio**: Estadísticas del conjunto
- **Matriz de correlación**: Qué tan relacionadas están las acciones
- **Advertencias**: Si hay riesgos (alta concentración, alta volatilidad, etc.)

**Cómo verlo:**
- Ábrelo con cualquier editor de texto
- O súbelo a GitHub y se verá formateado

### **Carpeta `plots/`**

Contiene gráficos:
- **Evolución de precios**: Cómo han cambiado los precios en el tiempo
- **Retornos diarios**: Ganancias/pérdidas día a día
- **Distribución de retornos**: Histograma de los retornos
- **Composición del portfolio**: Gráfico de pastel
- **Matriz de correlación**: Gráfico de calor
- **Drawdown**: Caídas máximas del portfolio

**Cómo verlos:**
- Abre la carpeta `plots/`
- Abre cualquier imagen `.png` (se abrirá con tu visor de imágenes)

---

## 🔧 Solución de Problemas Comunes

### **Error: "No se encuentra el módulo 'yfinance'"**

**Solución:**
```
pip install yfinance
```

O reinstala todas las dependencias:
```
pip install -r requirements.txt
```

---

### **Error: "No se encontraron datos para [SYMBOL]"**

**Causas posibles:**
- El símbolo no existe (verifica que esté bien escrito)
- Problemas de conexión a Internet
- La API está temporalmente no disponible

**Solución:**
- Verifica que el símbolo sea correcto (ej: "AAPL", no "APPLE")
- Intenta de nuevo más tarde
- Prueba con otro símbolo conocido (AAPL, MSFT, GOOGL)

---

### **Los gráficos no se muestran**

**Solución:**
```
pip install --upgrade matplotlib
```

---

### **El programa es muy lento**

**Es normal** si:
- Es la primera vez que descarga datos
- Estás descargando muchos datos (períodos largos)
- Estás haciendo muchas simulaciones de Monte Carlo

**Solución:**
- Espera, es normal que tarde
- Para pruebas rápidas, usa períodos más cortos (ej: "1mo" en lugar de "1y")

---

## 📝 Ejemplos de Uso Rápido

### **Ejemplo 1: Analizar una sola acción**

Crea un archivo `ejemplo1.py`:

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries

extractor = DataExtractor()
data = extractor.download_historical_prices("AAPL", period="1y")
apple = PriceSeries.from_standardized_data(data)

stats = apple.get_summary_stats()
print(f"Precio actual: ${stats['current_price']:.2f}")
print(f"Retorno total: {stats['total_return']:.2f}%")
print(f"Volatilidad: {stats['volatility_annualized']*100:.2f}%")
```

Ejecuta: `python ejemplo1.py`

---

### **Ejemplo 2: Portfolio con 2 acciones**

Crea un archivo `ejemplo2.py`:

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

extractor = DataExtractor()
symbols = ["AAPL", "MSFT"]
data_dict = extractor.download_multiple_series(symbols, period="6mo")

price_series = [
    PriceSeries.from_standardized_data(data_dict[sym])
    for sym in symbols
]

# Portfolio 60% Apple, 40% Microsoft
portfolio = Portfolio(
    symbols=symbols,
    price_series=price_series,
    weights=[0.6, 0.4]
)

report = portfolio.report()
with open("reporte_2_acciones.md", "w", encoding="utf-8") as f:
    f.write(report)

portfolio.plots_report(save_dir="graficos_2_acciones")
print("✅ Listo! Revisa 'reporte_2_acciones.md' y la carpeta 'graficos_2_acciones'")
```

Ejecuta: `python ejemplo2.py`

---

### **Ejemplo 3: Simulación Monte Carlo**

Crea un archivo `ejemplo3.py`:

```python
from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

extractor = DataExtractor()
symbols = ["AAPL", "MSFT", "GOOGL"]
data_dict = extractor.download_multiple_series(symbols, period="1y")

price_series = [
    PriceSeries.from_standardized_data(data_dict[sym])
    for sym in symbols
]

portfolio = Portfolio(symbols=symbols, price_series=price_series)

# Simulación a 1 año (252 días) con 1000 simulaciones
mc_results = portfolio.monte_carlo_simulation(
    days=252,
    simulations=1000,
    random_seed=42
)

# Ver estadísticas
final_values = mc_results.iloc[:, -1]
print(f"Valor esperado: ${final_values.mean():.2f}")
print(f"Peor escenario (5%): ${final_values.quantile(0.05):.2f}")
print(f"Mejor escenario (95%): ${final_values.quantile(0.95):.2f}")

# Visualizar
portfolio.plot_monte_carlo_results(
    mc_results,
    save_path="monte_carlo.png",
    title="Simulación Monte Carlo"
)
```

Ejecuta: `python ejemplo3.py`

---

## 🎓 Conceptos Básicos (Para Entender Mejor)

### **¿Qué es un símbolo?**
- Es el código de la acción en la bolsa
- Ejemplos: AAPL (Apple), MSFT (Microsoft), GOOGL (Google)

### **¿Qué es un portfolio?**
- Es una colección de acciones con pesos (porcentajes)
- Ejemplo: 40% Apple + 30% Microsoft + 30% Google

### **¿Qué es Monte Carlo?**
- Es una simulación que proyecta el futuro
- Usa estadísticas históricas para predecir posibles escenarios
- Cuantas más simulaciones, más preciso

### **¿Qué es volatilidad?**
- Mide qué tan variable es el precio
- Alta volatilidad = precios cambian mucho
- Baja volatilidad = precios más estables

### **¿Qué es el Sharpe Ratio?**
- Mide el retorno ajustado por riesgo
- Más alto = mejor (más retorno por cada unidad de riesgo)

---

## ✅ Checklist: ¿Todo Funciona?

- [ ] Python está instalado (`python --version` funciona)
- [ ] Las dependencias están instaladas (`pip install -r requirements.txt` completado)
- [ ] La verificación pasa (`python verificar_instalacion.py` muestra todo ✅)
- [ ] Puedo ejecutar el programa principal (`python run_main.py` funciona)
- [ ] Se generan archivos (reporte y gráficos)

---

## 🆘 ¿Necesitas Más Ayuda?

1. **Revisa el README.md**: Tiene documentación más detallada
2. **Revisa example_usage.py**: Tiene 8 ejemplos diferentes
3. **Revisa ESTRUCTURA_PROYECTO.txt**: Explica cómo funciona el proyecto

---

**¡Listo! Ahora puedes usar el proyecto sin saber programar. 🚀**

*Empieza con el Paso 4, Opción 1 (la más fácil) y luego explora las demás opciones.*

