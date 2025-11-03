"""
Ejemplo de uso completo del Market Data Toolkit
Este script demuestra todas las funcionalidades principales del sistema.
"""

from src import (
    download_price_series,
    PriceSeries,
    Portfolio,
    plot_portfolio_evolution,
    plot_monte_carlo_results
)

def main():
    print("=" * 60)
    print("Market Data Toolkit - Ejemplo de Uso")
    print("=" * 60)
    
    # 1. Descargar datos de múltiples activos
    print("\n1. Descargando datos de mercado...")
    tickers = ['AAPL', 'GOOGL', 'MSFT', '^GSPC']  # ^GSPC es el S&P 500
    data = download_price_series(
        tickers=tickers,
        start='2022-01-01',
        end='2024-01-01',
        source='yfinance',
        parallel=True
    )
    
    print(f"   ✓ Datos descargados para {len(data)} símbolos")
    
    # 2. Crear PriceSeries para cada activo
    print("\n2. Creando series de precios...")
    assets = {}
    for symbol, df in data.items():
        if not df.empty:
            assets[symbol] = PriceSeries(
                symbol=symbol,
                data=df,
                source='yfinance'
            )
            print(f"   ✓ {symbol}: Media=${assets[symbol].mean:.2f}, "
                  f"Volatilidad={assets[symbol].get_volatility():.2%}")
    
    # 3. Crear una cartera
    print("\n3. Creando cartera...")
    weights = {
        'AAPL': 0.3,
        'GOOGL': 0.3,
        'MSFT': 0.2,
        '^GSPC': 0.2
    }
    # Ajustar pesos a los activos disponibles
    available_weights = {k: v for k, v in weights.items() if k in assets}
    total_weight = sum(available_weights.values())
    available_weights = {k: v/total_weight for k, v in available_weights.items()}
    
    portfolio = Portfolio(
        assets=assets,
        weights=available_weights,
        name='Cartera de Ejemplo'
    )
    
    print(f"   ✓ Cartera creada con {len(portfolio.assets)} activos")
    print(f"   ✓ Volatilidad de la cartera: {portfolio.get_volatility():.2%}")
    print(f"   ✓ Retorno total histórico: {portfolio.stats['total_return']:.2%}")
    
    # 4. Simulación de Monte Carlo
    print("\n4. Ejecutando simulación de Monte Carlo...")
    mc_results = portfolio.monte_carlo(
        num_simulations=5000,  # Reducido para ejemplo rápido
        num_days=252,
        random_seed=42,
        for_individual_assets=False
    )
    
    portfolio_stats = mc_results['portfolio']['statistics']
    print(f"   ✓ Simulación completada")
    print(f"   ✓ Valor esperado final: ${portfolio_stats['mean_final_value']:,.2f}")
    print(f"   ✓ Percentil 5%: ${portfolio_stats['percentile_5']:,.2f}")
    print(f"   ✓ Percentil 95%: ${portfolio_stats['percentile_95']:,.2f}")
    print(f"   ✓ Probabilidad de ganancia: {portfolio_stats['probability_positive']:.2%}")
    
    # 5. Generar reporte
    print("\n5. Generando reporte...")
    report = portfolio.report(
        include_warnings=True,
        include_statistics=True,
        include_quality_check=True
    )
    
    # Guardar reporte
    with open('reporte_cartera_ejemplo.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("   ✓ Reporte guardado en 'reporte_cartera_ejemplo.md'")
    
    # 6. Visualizaciones
    print("\n6. Generando visualizaciones...")
    try:
        # Generar todas las visualizaciones (guardar sin mostrar)
        portfolio.plots_report(save_path=None, show=False)
        print("   ✓ Visualizaciones generadas")
    except Exception as e:
        print(f"   ⚠ Error generando visualizaciones: {e}")
    
    print("\n" + "=" * 60)
    print("Ejemplo completado exitosamente!")
    print("=" * 60)
    print("\nArchivos generados:")
    print("  - reporte_cartera_ejemplo.md")
    print("\nPara ver las visualizaciones, ejecuta:")
    print("  portfolio.plots_report(show=True)")

if __name__ == "__main__":
    main()

