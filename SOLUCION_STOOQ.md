# 🔧 Solución: Problemas con Stooq

## ✅ Correcciones Implementadas

He mejorado el adaptador de Stooq para solucionar los problemas. Los cambios incluyen:

### 1. **Normalización Automática de Símbolos**
- Si ingresas `AAPL` sin el sufijo `.US`, el sistema automáticamente lo convierte a `AAPL.US`
- Esto hace más fácil usar Stooq sin recordar el formato exacto

### 2. **Mejor Manejo de Errores**
- Mensajes de error más claros y específicos
- Indica exactamente qué formato se espera
- Sugiere ejemplos de símbolos correctos

### 3. **Validación Mejorada**
- Verifica que la respuesta de Stooq sea válida
- Maneja mejor los casos de símbolos no encontrados
- Valida el formato del CSV antes de procesarlo

### 4. **Headers HTTP**
- Agrega User-Agent para evitar bloqueos
- Mejora la compatibilidad con el servidor de Stooq

---

## 📝 Cómo Usar Stooq Correctamente

### Formato de Símbolos

Stooq requiere el formato `SYMBOL.MARKET`:

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# ✅ CORRECTO: Con formato .MARKET
data = extractor.download_historical_prices("AAPL.US", period="6m", source="stooq")

# ✅ TAMBIÉN CORRECTO: Sin formato (se normaliza automáticamente)
data = extractor.download_historical_prices("AAPL", period="6m", source="stooq")
# El sistema mostrará: "ℹ️  Símbolo normalizado a formato Stooq: AAPL -> AAPL.US"

# ❌ INCORRECTO: Formato incorrecto (aunque ahora se corrige automáticamente)
# data = extractor.download_historical_prices("^AAPL", period="6m", source="stooq")
```

### Ejemplos de Símbolos por Mercado

**Estados Unidos:**
- `AAPL.US` - Apple
- `MSFT.US` - Microsoft
- `GOOGL.US` - Google
- `SPX.US` - S&P 500 Index

**España:**
- `SAN.ES` - Banco Santander
- `BBVA.ES` - BBVA
- `REP.ES` - Repsol
- `IBEX.ES` - IBEX 35 Index

**Reino Unido:**
- `BP.UK` - BP
- `VOD.UK` - Vodafone

---

## 🐛 Solución de Problemas

### Error: "Símbolo no encontrado en Stooq"

**Causa:** El símbolo no existe en Stooq o el formato es incorrecto.

**Solución:**
1. Verifica que el símbolo sea correcto
2. Asegúrate de usar el formato `SYMBOL.MARKET`
3. Prueba buscar el símbolo en https://stooq.com para verificar que existe

**Ejemplo:**
```python
# Si esto falla:
data = extractor.download_historical_prices("XYZ.US", source="stooq")

# Verifica en stooq.com si el símbolo existe
# O prueba con un símbolo conocido:
data = extractor.download_historical_prices("AAPL.US", source="stooq")
```

### Error: "No se encontraron datos válidos"

**Causa:** El rango de fechas no tiene datos o las fechas son incorrectas.

**Solución:**
1. Usa un rango de fechas más amplio
2. Verifica que las fechas sean correctas
3. Prueba con un período más reciente

**Ejemplo:**
```python
# Prueba con un período más corto y reciente
data = extractor.download_historical_prices(
    "AAPL.US", 
    period="3m",  # Últimos 3 meses
    source="stooq"
)
```

### Error: "Error conectando con Stooq"

**Causa:** Problema de conexión a internet o Stooq está temporalmente no disponible.

**Solución:**
1. Verifica tu conexión a internet
2. Espera unos minutos y vuelve a intentar
3. Prueba con otra fuente (Yahoo Finance, Alpha Vantage)

---

## 🧪 Prueba Rápida

Para verificar que Stooq funciona correctamente:

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor()

# Verificar que Stooq está disponible
if "stooq" in extractor.get_supported_sources():
    print("✅ Stooq está disponible")
    
    # Probar descarga
    try:
        data = extractor.download_historical_prices("AAPL.US", period="1m", source="stooq")
        print(f"✅ Datos descargados: {len(data)} días")
        print(data.to_dataframe().head())
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Stooq no está disponible")
```

---

## 📚 Más Información

- Ver `GUIA_NUEVAS_FUENTES.md` para información completa sobre todas las fuentes
- Ver `ejemplo_nuevas_fuentes.py` para ejemplos de código

---

**Si sigues teniendo problemas, verifica:**
1. ✅ Que el símbolo existe en Stooq (busca en https://stooq.com)
2. ✅ Que usas el formato correcto `SYMBOL.MARKET`
3. ✅ Que tienes conexión a internet
4. ✅ Que las fechas son válidas

