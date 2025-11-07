"""
Ejemplos de uso del sistema de análisis bursátil
Este archivo contiene múltiples ejemplos para diferentes casos de uso
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar install_dependencies
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar funciones de instalación desde el módulo dedicado
from install_dependencies import check_and_install

# Verificar dependencias antes de importar
if not check_and_install():
    print("\n⚠️  No se pudieron instalar las dependencias.")
    print("Ejecuta: python install_dependencies.py")
    sys.exit(1)

from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio
from src.data_cleaning import DataCleaner


def ejemplo_1_analisis_una_accion():
    """
    Ejemplo 1: Análisis básico de una sola acción
    """
    print("=" * 60)
    print("EJEMPLO 1: Análisis de una Acción")
    print("=" * 60)
    
    # Crear extractor
    extractor = DataExtractor()
    
    # Descargar datos de Apple
    print("\nDescargando datos de AAPL...")
    data = extractor.download_historical_prices("AAPL", period="1y")
    
    # Crear serie de precios
    apple = PriceSeries.from_standardized_data(data)
    
    # Mostrar estadísticas
    print(f"\nEstadísticas de {apple.symbol}:")
    stats = apple.get_summary_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n✓ Análisis completado para {apple.symbol}")


def ejemplo_2_portfolio_equilibrado():
    """
    Ejemplo 2: Portfolio equilibrado (pesos iguales)
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Portfolio Equilibrado")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Descargar múltiples acciones
    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"\nDescargando datos de: {', '.join(symbols)}")
    data_dict = extractor.download_multiple_series(symbols, period="1y")
    
    # Crear series de precios
    price_series = [
        PriceSeries.from_standardized_data(data_dict[sym])
        for sym in symbols
    ]
    
    # Crear portfolio (sin especificar weights = distribución equitativa)
    portfolio = Portfolio(
        symbols=symbols,
        price_series=price_series
        # weights se calcula automáticamente: [0.33, 0.33, 0.33]
    )
    
    print(f"\nComposición del portfolio:")
    for i, symbol in enumerate(symbols):
        print(f"  {symbol}: {portfolio.weights[i]*100:.1f}%")
    
    # Generar reporte
    report = portfolio.report()
    with open("ejemplo_portfolio_equilibrado.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n✓ Reporte guardado en 'ejemplo_portfolio_equilibrado.md'")


def ejemplo_3_portfolio_personalizado():
    """
    Ejemplo 3: Portfolio con pesos personalizados
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Portfolio con Pesos Personalizados")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    print(f"\nDescargando datos de: {', '.join(symbols)}")
    data_dict = extractor.download_multiple_series(symbols, period="2y")
    
    price_series = [
        PriceSeries.from_standardized_data(data_dict[sym])
        for sym in symbols
    ]
    
    # Pesos personalizados: 40% Apple, 30% Microsoft, 20% Google, 10% Amazon
    weights = [0.4, 0.3, 0.2, 0.1]
    
    portfolio = Portfolio(
        symbols=symbols,
        price_series=price_series,
        weights=weights
    )
    
    print(f"\nComposición del portfolio:")
    for i, symbol in enumerate(symbols):
        print(f"  {symbol}: {portfolio.weights[i]*100:.1f}%")
    
    # Análisis completo
    report = portfolio.report(include_warnings=True, include_correlation=True)
    with open("ejemplo_portfolio_personalizado.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    # Generar gráficos
    portfolio.plots_report(save_dir="ejemplo_graficos")
    
    print("\n✓ Análisis completo guardado")


def ejemplo_4_analisis_indices():
    """
    Ejemplo 4: Análisis de índices bursátiles
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Análisis de Índices Bursátiles")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Índices: S&P 500, Dow Jones, NASDAQ
    indices = ["^GSPC", "^DJI", "^IXIC"]
    print(f"\nDescargando datos de índices: S&P 500, Dow Jones, NASDAQ")
    
    data_dict = {}
    for idx in indices:
        try:
            data_dict[idx] = extractor.download_index_data(idx, period="1y")
            print(f"  ✓ {idx} descargado")
        except Exception as e:
            print(f"  ✗ Error con {idx}: {e}")
    
    # Crear series
    price_series = [
        PriceSeries.from_standardized_data(data_dict[idx])
        for idx in indices
        if idx in data_dict
    ]
    
    indices_names = [idx for idx in indices if idx in data_dict]
    
    # Crear portfolio de índices
    portfolio = Portfolio(
        symbols=indices_names,
        price_series=price_series
    )
    
    # Análisis
    report = portfolio.report()
    with open("ejemplo_indices.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n✓ Análisis de índices completado")


def ejemplo_5_correlacion_activos():
    """
    Ejemplo 5: Análisis de correlación entre activos
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Análisis de Correlación")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    print(f"\nDescargando datos de: {', '.join(symbols)}")
    data_dict = extractor.download_multiple_series(symbols, period="1y")
    
    price_series = [
        PriceSeries.from_standardized_data(data_dict[sym])
        for sym in symbols
    ]
    
    print("\nMatriz de correlación:")
    print("  " + " | ".join(symbols))
    print("  " + "-" * (len(symbols) * 10))
    
    for i, symbol1 in enumerate(symbols):
        row = [f"{symbol1:>6}"]
        for j, symbol2 in enumerate(symbols):
            if i == j:
                row.append("  1.000")
            else:
                corr = price_series[i].correlation_with(price_series[j])
                row.append(f" {corr:6.3f}")
        print("  " + " | ".join(row))
    
    print("\n✓ Análisis de correlación completado")


def main():
    """
    Ejecuta todos los ejemplos
    """
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO DEL SISTEMA DE ANÁLISIS BURSÁTIL")
    print("=" * 60)
    print("\nSelecciona un ejemplo a ejecutar:")
    print("  1. Análisis de una acción")
    print("  2. Portfolio equilibrado")
    print("  3. Portfolio personalizado")
    print("  4. Análisis de índices")
    print("  5. Análisis de correlación")
    print("  6. Ejecutar todos")
    print("  0. Salir")
    
    choice = input("\nOpción: ").strip()
    
    examples = {
        "1": ejemplo_1_analisis_una_accion,
        "2": ejemplo_2_portfolio_equilibrado,
        "3": ejemplo_3_portfolio_personalizado,
        "4": ejemplo_4_analisis_indices,
        "5": ejemplo_5_correlacion_activos
    }
    
    if choice == "6":
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n✗ Error en ejemplo: {e}")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n✗ Error: {e}")
    elif choice == "0":
        print("\n¡Hasta luego!")
    else:
        print("\nOpción no válida")


if __name__ == "__main__":
    main()

