"""
Script de verificación de instalación
Ejecuta este script para verificar que todas las dependencias están instaladas
y que el proyecto funciona correctamente
"""

import sys

def verificar_python():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    dependencias = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
        'requests': 'requests'
    }
    
    faltantes = []
    for nombre, modulo in dependencias.items():
        try:
            __import__(modulo)
            print(f"✅ {nombre} - OK")
        except ImportError:
            print(f"❌ {nombre} - NO INSTALADO")
            faltantes.append(nombre)
    
    if faltantes:
        print(f"\n⚠️  Faltan las siguientes dependencias: {', '.join(faltantes)}")
        print("   Ejecuta: pip install -r requirements.txt")
        return False
    
    return True

def verificar_modulos_proyecto():
    """Verifica que los módulos del proyecto se puedan importar"""
    modulos = [
        'src.data_extractor',
        'src.price_series',
        'src.portfolio',
        'src.data_cleaning'
    ]
    
    errores = []
    for modulo in modulos:
        try:
            __import__(modulo)
            print(f"✅ {modulo} - OK")
        except ImportError as e:
            print(f"❌ {modulo} - ERROR: {e}")
            errores.append(modulo)
    
    if errores:
        print(f"\n⚠️  No se pudieron importar: {', '.join(errores)}")
        return False
    
    return True

def prueba_rapida():
    """Ejecuta una prueba rápida del sistema"""
    print("\n" + "="*60)
    print("Ejecutando prueba rápida...")
    print("="*60)
    
    try:
        from src.data_extractor import DataExtractor
        from src.price_series import PriceSeries
        
        print("\n1. Creando extractor...")
        extractor = DataExtractor()
        print("   ✅ Extractor creado")
        
        print("\n2. Descargando datos de prueba (AAPL, último mes)...")
        data = extractor.download_historical_prices("AAPL", period="1mo")
        print(f"   ✅ Datos descargados: {len(data)} días")
        
        print("\n3. Creando serie de precios...")
        ps = PriceSeries.from_standardized_data(data)
        print(f"   ✅ Serie creada: {ps.symbol}")
        print(f"      - Precio medio: ${ps.mean_price:.2f}")
        print(f"      - Desviación típica: ${ps.std_price:.2f}")
        
        print("\n4. Calculando estadísticas...")
        stats = ps.get_summary_stats()
        print(f"   ✅ Estadísticas calculadas")
        print(f"      - Volatilidad: {stats['volatility_annualized']*100:.2f}%")
        print(f"      - Sharpe Ratio: {stats['sharpe_ratio']:.3f}")
        
        print("\n" + "="*60)
        print("✅ PRUEBA RÁPIDA COMPLETADA EXITOSAMENTE")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR en prueba rápida: {e}")
        print("   Esto puede deberse a problemas de conexión a Internet")
        print("   o a que la API de Yahoo Finance esté temporalmente no disponible")
        return False

def main():
    """Función principal de verificación"""
    print("="*60)
    print("VERIFICACIÓN DE INSTALACIÓN")
    print("Sistema de Análisis Bursátil")
    print("="*60)
    
    resultados = []
    
    print("\n[1/4] Verificando Python...")
    resultados.append(verificar_python())
    
    print("\n[2/4] Verificando dependencias...")
    resultados.append(verificar_dependencias())
    
    print("\n[3/4] Verificando módulos del proyecto...")
    resultados.append(verificar_modulos_proyecto())
    
    if all(resultados):
        print("\n[4/4] Ejecutando prueba rápida...")
        resultados.append(prueba_rapida())
    
    print("\n" + "="*60)
    if all(resultados):
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("   El proyecto está listo para usar")
        print("\n   Próximos pasos:")
        print("   1. Ejecuta: python src/main.py")
        print("   2. O revisa: example_usage.py")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("   Revisa los mensajes de error arriba")
        print("   Asegúrate de:")
        print("   1. Tener Python 3.8+ instalado")
        print("   2. Ejecutar: pip install -r requirements.txt")
        print("   3. Estar en la carpeta correcta del proyecto")
    print("="*60)

if __name__ == "__main__":
    main()

