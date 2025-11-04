"""
Script principal de demostración
Ejemplo completo de uso del sistema de análisis bursátil
"""

try:
    # Intentar importación relativa (cuando se ejecuta como módulo)
    from .data_extractor import DataExtractor
    from .price_series import PriceSeries
    from .portfolio import Portfolio
    from .data_cleaning import DataCleaner
except ImportError:
    # Fallback a importación absoluta (cuando se ejecuta directamente)
    from data_extractor import DataExtractor
    from price_series import PriceSeries
    from portfolio import Portfolio
    from data_cleaning import DataCleaner


def main():
    """
    Función principal que demuestra el uso completo del sistema
    """
    print("=" * 60)
    print("Sistema de Análisis Bursátil")
    print("=" * 60)
    print()
    
    # 1. Crear extractor de datos
    print("1. Creando extractor de datos...")
    extractor = DataExtractor()
    
    # 2. Descargar datos históricos de múltiples acciones
    print("\n2. Descargando datos históricos...")
    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"   Símbolos: {', '.join(symbols)}")
    
    # Descargar múltiples series al mismo tiempo
    data_dict = extractor.download_multiple_series(
        symbols=symbols,
        period="1y"  # Último año
    )
    
    print(f"   ✓ Datos descargados para {len(data_dict)} símbolos")
    
    # 3. Convertir a PriceSeries
    print("\n3. Creando series de precios...")
    price_series_list = []
    for symbol, standardized_data in data_dict.items():
        ps = PriceSeries.from_standardized_data(standardized_data)
        price_series_list.append(ps)
        print(f"   ✓ {symbol}: {len(ps)} días de datos")
        print(f"     - Precio medio: ${ps.mean_price:.2f}")
        print(f"     - Volatilidad: {ps.volatility(annualized=True)*100:.2f}%")
    
    # 4. Crear portfolio
    print("\n4. Creando portfolio...")
    weights = [0.4, 0.3, 0.3]  # 40% AAPL, 30% MSFT, 30% GOOGL
    portfolio = Portfolio(
        symbols=symbols,
        price_series=price_series_list,
        weights=weights
    )
    print(f"   ✓ Portfolio creado con {len(portfolio.symbols)} activos")
    
    # 5. Generar reporte
    print("\n5. Generando reporte de análisis...")
    report = portfolio.report(include_warnings=True, include_correlation=True)
    
    # Guardar reporte
    with open("portfolio_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("   ✓ Reporte guardado en 'portfolio_report.md'")
    
    # Mostrar reporte en consola
    print("\n" + "=" * 60)
    print("REPORTE DE ANÁLISIS")
    print("=" * 60)
    print(report[:500] + "...\n")  # Mostrar primeros 500 caracteres
    
    # 6. Generar gráficos
    print("\n6. Generando visualizaciones...")
    portfolio.plots_report(save_dir="plots")
    print("   ✓ Gráficos guardados en 'plots/'")
    
    # 7. Simulación Monte Carlo
    print("\n7. Ejecutando simulación Monte Carlo...")
    print("   Simulando 252 días (1 año) con 1000 simulaciones...")
    
    mc_results = portfolio.monte_carlo_simulation(
        days=252,
        simulations=1000,
        random_seed=42
    )
    
    print(f"   ✓ Simulación completada")
    print(f"   - Valor esperado final: ${mc_results.iloc[:, -1].mean():.2f}")
    print(f"   - Percentil 5%: ${mc_results.iloc[:, -1].quantile(0.05):.2f}")
    print(f"   - Percentil 95%: ${mc_results.iloc[:, -1].quantile(0.95):.2f}")
    
    # Visualizar Monte Carlo
    portfolio.plot_monte_carlo_results(
        mc_results,
        save_path="plots/monte_carlo_simulation.png",
        title="Simulación Monte Carlo - Portfolio Completo"
    )
    
    # 8. Simulación Monte Carlo para activos individuales
    print("\n8. Ejecutando simulación Monte Carlo para activos individuales...")
    individual_mc = portfolio.monte_carlo_individual_assets(
        days=252,
        simulations=1000,
        random_seed=42
    )
    
    for symbol, sim_df in individual_mc.items():
        print(f"   ✓ {symbol}: Valor esperado final = ${sim_df.iloc[:, -1].mean():.2f}")
    
    print("\n" + "=" * 60)
    print("✓ Proceso completado exitosamente")
    print("=" * 60)
    print("\nArchivos generados:")
    print("  - portfolio_report.md (reporte de análisis)")
    print("  - plots/ (gráficos y visualizaciones)")
    print("  - plots/monte_carlo_simulation.png (simulación Monte Carlo)")


if __name__ == "__main__":
    main()

