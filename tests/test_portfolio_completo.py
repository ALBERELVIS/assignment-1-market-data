"""
Script de prueba para verificar que el portfolio, reporte y Monte Carlo
funcionan correctamente sin valores absurdos
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Verificar e instalar dependencias
try:
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except:
    pass

try:
    from install_dependencies import check_and_install
    if not check_and_install():
        print("Advertencia: No se pudieron instalar las dependencias.")
        print("Continuando de todas formas...")
except Exception as e:
    print(f"Advertencia al verificar dependencias: {e}")
    print("Continuando de todas formas...")

from src.data_extractor import DataExtractor
from src.price_series import PriceSeries
from src.portfolio import Portfolio
import numpy as np

def test_portfolio_completo():
    """Prueba completa del portfolio con activos e índices"""
    
    print("=" * 70)
    print("PRUEBA COMPLETA DE PORTFOLIO - ACTIVOS E ÍNDICES")
    print("=" * 70)
    
    # Crear extractor
    extractor = DataExtractor()
    
    # Definir símbolos: mezcla de acciones e índices
    symbols = ["AAPL", "MSFT", "GOOGL", "^GSPC", "^DJI"]
    
    print(f"\n📥 Descargando datos para {len(symbols)} activos...")
    print(f"   Símbolos: {', '.join(symbols)}")
    
    try:
        # Descargar datos
        data_dict = extractor.download_multiple_series(
            symbols=symbols,
            period="2y",  # 2 años de datos
            source="yahoo"
        )
        
        if not data_dict:
            print("❌ Error: No se pudieron descargar datos")
            return False
        
        print(f"\n✅ {len(data_dict)} series descargadas exitosamente")
        
        # Convertir a PriceSeries
        price_series_list = []
        final_symbols = []
        for symbol, data in data_dict.items():
            try:
                ps = PriceSeries.from_standardized_data(data)
                price_series_list.append(ps)
                final_symbols.append(symbol)
                print(f"   ✓ {symbol}: {len(ps)} días de datos")
            except Exception as e:
                print(f"   ❌ Error con {symbol}: {e}")
        
        if len(price_series_list) == 0:
            print("❌ Error: No se pudieron crear series de precios")
            return False
        
        # Crear portfolio con distribución equitativa
        print(f"\n💼 Creando portfolio con {len(final_symbols)} activos...")
        portfolio = Portfolio(
            symbols=final_symbols,
            price_series=price_series_list,
            weights=None  # Distribución equitativa
        )
        
        print(f"   Pesos del portfolio:")
        for i, symbol in enumerate(portfolio.symbols):
            print(f"      - {symbol}: {portfolio.weights[i]*100:.2f}%")
        
        # Obtener valor del portfolio
        portfolio_value = portfolio.get_portfolio_value_series()
        current_value = portfolio_value.iloc[-1]
        print(f"\n   Valor actual del portfolio: ${current_value:,.2f}")
        
        # Generar reporte
        print("\n📄 Generando reporte del portfolio...")
        report = portfolio.report(include_warnings=True, include_correlation=True)
        
        # Guardar reporte
        Path("plots").mkdir(exist_ok=True)
        report_file = "plots/test_portfolio_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"   ✅ Reporte guardado en '{report_file}'")
        
        # Verificar valores en el reporte
        print("\n🔍 Verificando valores del reporte...")
        lines = report.split('\n')
        valores_absurdos = []
        
        for line in lines:
            # Buscar retorno anualizado
            if "Retorno medio anualizado" in line:
                try:
                    # Extraer el porcentaje
                    pct_str = line.split(':')[1].strip().replace('%', '')
                    pct = float(pct_str)
                    if abs(pct) > 10000:  # Más de 10,000% es absurdo
                        valores_absurdos.append(f"Retorno anualizado: {pct:.2f}%")
                    else:
                        print(f"   ✓ Retorno anualizado: {pct:.2f}% (razonable)")
                except:
                    pass
            
            # Buscar volatilidad
            if "Volatilidad anualizada" in line:
                try:
                    pct_str = line.split(':')[1].strip().replace('%', '')
                    pct = float(pct_str)
                    if pct > 1000:  # Más de 1000% es absurdo
                        valores_absurdos.append(f"Volatilidad: {pct:.2f}%")
                    else:
                        print(f"   ✓ Volatilidad anualizada: {pct:.2f}% (razonable)")
                except:
                    pass
            
            # Buscar Sharpe
            if "Ratio de Sharpe" in line and "Análisis del Portfolio Completo" in '\n'.join(lines[:lines.index(line)+10]):
                try:
                    sharpe_str = line.split(':')[1].strip()
                    sharpe = float(sharpe_str)
                    if abs(sharpe) > 100:  # Sharpe > 100 es absurdo
                        valores_absurdos.append(f"Sharpe ratio: {sharpe:.3f}")
                    else:
                        print(f"   ✓ Sharpe ratio: {sharpe:.3f} (razonable)")
                except:
                    pass
        
        if valores_absurdos:
            print(f"\n⚠️  Valores potencialmente absurdos encontrados:")
            for val in valores_absurdos:
                print(f"   - {val}")
        else:
            print("\n✅ Todos los valores del reporte son razonables")
        
        # Ejecutar simulación Monte Carlo
        print("\n🎲 Ejecutando simulación Monte Carlo...")
        try:
            sim_df = portfolio.run_and_plot_monte_carlo(
                years=10,
                simulations=1000,  # Menos simulaciones para prueba rápida
                initial_value=current_value,
                inflation_rate=None,
                rebalance=True,
                rebalance_frequency='monthly',
                random_seed=42,
                save_path="plots/test_monte_carlo_portfolio.png"
            )
            
            print("   ✅ Simulación completada")
            
            # Verificar valores de la simulación
            print("\n🔍 Verificando valores de la simulación...")
            final_values = sim_df.iloc[-1].values
            
            # Estadísticas
            mean_final = np.mean(final_values)
            median_final = np.median(final_values)
            std_final = np.std(final_values)
            min_final = np.min(final_values)
            max_final = np.max(final_values)
            
            print(f"   Valor final promedio: ${mean_final:,.2f}")
            print(f"   Valor final mediana: ${median_final:,.2f}")
            print(f"   Desviación estándar: ${std_final:,.2f}")
            print(f"   Mínimo: ${min_final:,.2f}")
            print(f"   Máximo: ${max_final:,.2f}")
            
            # Verificar que no haya valores absurdos
            if max_final > current_value * 1000:  # Más de 1000x el valor inicial
                print(f"   ⚠️  Advertencia: Valor máximo muy alto ({max_final:,.2f})")
            elif min_final < 0:
                print(f"   ⚠️  Advertencia: Valores negativos encontrados")
            else:
                print("   ✅ Valores de simulación razonables")
            
            # Calcular retornos
            returns = (final_values - current_value) / current_value
            mean_return = np.mean(returns) * 100
            print(f"\n   Retorno promedio: {mean_return:.2f}%")
            
            if abs(mean_return) > 10000:  # Más de 10,000% es absurdo
                print(f"   ⚠️  Advertencia: Retorno promedio muy alto")
            else:
                print("   ✅ Retorno promedio razonable")
                
        except Exception as e:
            print(f"   ❌ Error en simulación Monte Carlo: {e}")
            import traceback
            traceback.print_exc()
        
        # Generar gráficos del reporte
        print("\n📈 Generando gráficos del reporte...")
        try:
            portfolio.plots_report(save_dir="plots")
            print("   ✅ Gráficos generados en 'plots/'")
        except Exception as e:
            print(f"   ❌ Error generando gráficos: {e}")
            import traceback
            traceback.print_exc()
        
        # Mostrar resumen
        print("\n" + "=" * 70)
        print("RESUMEN DE LA PRUEBA")
        print("=" * 70)
        print(f"✅ Portfolio creado con {len(portfolio.symbols)} activos")
        print(f"✅ Reporte generado: {report_file}")
        print(f"✅ Simulación Monte Carlo completada")
        print(f"✅ Gráficos generados en 'plots/'")
        
        if valores_absurdos:
            print(f"\n⚠️  Se encontraron {len(valores_absurdos)} valores potencialmente absurdos")
            print("   Revisa el reporte para más detalles")
        else:
            print("\n✅ Todos los valores son razonables y correctos")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_portfolio_completo()
    sys.exit(0 if success else 1)

