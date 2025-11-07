"""
Script de prueba para verificar que las correcciones de Monte Carlo funcionan correctamente
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio

def test_monte_carlo_basico():
    """Prueba básica de Monte Carlo"""
    print("=" * 60)
    print("PRUEBA: Simulación Monte Carlo Básica")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbols = ["AAPL", "MSFT"]
    
    print(f"\n📥 Descargando datos de {', '.join(symbols)}...")
    data_dict = extractor.download_multiple_series(
        symbols=symbols,
        period="1y",
        source="yahoo"
    )
    
    price_series_list = []
    for symbol, data in data_dict.items():
        ps = PriceSeries.from_standardized_data(data)
        price_series_list.append(ps)
        print(f"   ✓ {symbol}: {len(ps)} días")
    
    portfolio = Portfolio(
        symbols=list(data_dict.keys()),
        price_series=price_series_list,
        weights=None
    )
    
    # Obtener estadísticas históricas
    portfolio_returns = portfolio.get_portfolio_returns()
    historical_mean = portfolio_returns.mean() * 252  # Anualizado
    historical_std = portfolio_returns.std() * np.sqrt(252)  # Anualizado
    
    print(f"\n📊 Estadísticas históricas del portfolio:")
    print(f"   - Retorno medio anualizado: {historical_mean*100:.2f}%")
    print(f"   - Volatilidad anualizada: {historical_std*100:.2f}%")
    
    # Prueba 1: Sin override (usar histórico)
    print(f"\n🎲 Prueba 1: Sin override (usar histórico)")
    sim1 = portfolio.monte_carlo_simulation(
        days=252,
        simulations=100,
        annualized=True,
        random_seed=42
    )
    
    final_values1 = sim1.iloc[:, -1]
    initial_value = portfolio.get_portfolio_value_series().iloc[-1]
    
    print(f"   - Valor inicial: ${initial_value:.2f}")
    print(f"   - Valor medio final: ${final_values1.mean():.2f}")
    print(f"   - Retorno simulado medio: {(final_values1.mean()/initial_value - 1)*100:.2f}%")
    print(f"   - Retorno histórico esperado: {historical_mean*100:.2f}%")
    
    # Prueba 2: Con override (10% anual)
    print(f"\n🎲 Prueba 2: Con drift override (10% anual)")
    sim2 = portfolio.monte_carlo_simulation(
        days=252,
        simulations=100,
        drift_override=0.10,  # 10% anual
        annualized=True,
        random_seed=42
    )
    
    final_values2 = sim2.iloc[:, -1]
    print(f"   - Valor inicial: ${initial_value:.2f}")
    print(f"   - Valor medio final: ${final_values2.mean():.2f}")
    print(f"   - Retorno simulado medio: {(final_values2.mean()/initial_value - 1)*100:.2f}%")
    print(f"   - Retorno esperado: 10.00%")
    
    # Verificar que el retorno simulado está cerca del esperado
    simulated_return2 = (final_values2.mean()/initial_value - 1) * 100
    expected_return2 = 10.0
    
    if abs(simulated_return2 - expected_return2) < 5:  # Tolerancia del 5%
        print(f"   ✅ Retorno simulado ({simulated_return2:.2f}%) está cerca del esperado ({expected_return2:.2f}%)")
    else:
        print(f"   ⚠️  Retorno simulado ({simulated_return2:.2f}%) difiere mucho del esperado ({expected_return2:.2f}%)")
    
    print("\n✅ Pruebas completadas")


if __name__ == "__main__":
    import numpy as np
    test_monte_carlo_basico()

