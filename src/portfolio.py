"""
portfolio.py
------------
Métodos para análisis de carteras, incluyendo simulación de Monte Carlo,
generación de reportes y visualizaciones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from .datamodels import Portfolio, PriceSeries


class MonteCarloSimulation:
    """
    Clase para realizar simulaciones de Monte Carlo.
    """
    
    def __init__(self, 
                 initial_value: float,
                 mean_return: float,
                 volatility: float,
                 num_simulations: int = 10000,
                 num_days: int = 252,
                 random_seed: Optional[int] = None):
        """
        Args:
            initial_value: Valor inicial
            mean_return: Retorno medio esperado (anualizado)
            volatility: Volatilidad (anualizada)
            num_simulations: Número de simulaciones
            num_days: Días a simular
            random_seed: Semilla para reproducibilidad
        """
        self.initial_value = initial_value
        self.mean_return = mean_return
        self.volatility = volatility
        self.num_simulations = num_simulations
        self.num_days = num_days
        self.random_seed = random_seed
        
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def simulate(self) -> pd.DataFrame:
        """
        Ejecuta la simulación de Monte Carlo.
        
        Returns:
            DataFrame con columnas: cada columna es una simulación, cada fila es un día
        """
        dt = 1.0 / 252.0  # Un día de trading
        
        # Drift y volatilidad diarios
        drift = (self.mean_return - 0.5 * self.volatility ** 2) * dt
        volatility_daily = self.volatility * np.sqrt(dt)
        
        # Generar retornos aleatorios
        random_shocks = np.random.normal(0, 1, (self.num_days, self.num_simulations))
        
        # Calcular retornos diarios usando modelo de difusión geométrica
        daily_returns = drift + volatility_daily * random_shocks
        
        # Calcular precios
        prices = np.zeros((self.num_days + 1, self.num_simulations))
        prices[0, :] = self.initial_value
        
        for day in range(1, self.num_days + 1):
            prices[day, :] = prices[day - 1, :] * np.exp(daily_returns[day - 1, :])
        
        # Crear DataFrame
        dates = pd.date_range(end=datetime.now(), periods=self.num_days + 1, freq='D')
        df = pd.DataFrame(prices, index=dates)
        
        return df
    
    def get_statistics(self, simulations: pd.DataFrame) -> Dict:
        """
        Calcula estadísticas de las simulaciones.
        
        Args:
            simulations: DataFrame con simulaciones
        
        Returns:
            Diccionario con estadísticas
        """
        final_values = simulations.iloc[-1, :]
        
        return {
            'mean_final_value': float(final_values.mean()),
            'std_final_value': float(final_values.std()),
            'min_final_value': float(final_values.min()),
            'max_final_value': float(final_values.max()),
            'percentile_5': float(np.percentile(final_values, 5)),
            'percentile_25': float(np.percentile(final_values, 25)),
            'percentile_50': float(np.percentile(final_values, 50)),
            'percentile_75': float(np.percentile(final_values, 75)),
            'percentile_95': float(np.percentile(final_values, 95)),
            'probability_positive': float((final_values > self.initial_value).sum() / len(final_values)),
            'expected_return': float((final_values.mean() / self.initial_value - 1)),
            'var_95': float(self.initial_value - np.percentile(final_values, 5)),  # Value at Risk 95%
        }


def monte_carlo_for_asset(asset: PriceSeries,
                          num_simulations: int = 10000,
                          num_days: int = 252,
                          random_seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Ejecuta simulación de Monte Carlo para un activo individual.
    
    Args:
        asset: PriceSeries del activo
        num_simulations: Número de simulaciones
        num_days: Días a simular
        random_seed: Semilla para reproducibilidad
    
    Returns:
        Tuple (simulaciones DataFrame, estadísticas dict)
    """
    # Calcular retornos históricos
    returns = asset.get_returns()
    
    if len(returns) == 0:
        raise ValueError(f"Insufficient data for {asset.symbol} to calculate returns")
    
    # Estadísticas de retornos (anualizadas)
    mean_return = returns.mean() * 252
    volatility = returns.std() * np.sqrt(252)
    
    # Valor inicial (último precio)
    initial_value = asset.data['adj_close'].iloc[-1]
    
    # Crear simulación
    mc = MonteCarloSimulation(
        initial_value=initial_value,
        mean_return=mean_return,
        volatility=volatility,
        num_simulations=num_simulations,
        num_days=num_days,
        random_seed=random_seed
    )
    
    simulations = mc.simulate()
    stats = mc.get_statistics(simulations)
    
    return simulations, stats


def monte_carlo_for_portfolio(portfolio: Portfolio,
                              num_simulations: int = 10000,
                              num_days: int = 252,
                              random_seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Ejecuta simulación de Monte Carlo para una cartera completa.
    
    Args:
        portfolio: Portfolio a simular
        num_simulations: Número de simulaciones
        num_days: Días a simular
        random_seed: Semilla para reproducibilidad
    
    Returns:
        Tuple (simulaciones DataFrame, estadísticas dict)
    """
    # Calcular retornos históricos de la cartera
    portfolio_returns = portfolio.get_returns()
    
    if len(portfolio_returns) == 0:
        raise ValueError("Insufficient portfolio data to calculate returns")
    
    # Estadísticas de retornos (anualizadas)
    mean_return = portfolio_returns.mean() * 252
    volatility = portfolio_returns.std() * np.sqrt(252)
    
    # Valor inicial de la cartera
    initial_value = portfolio.portfolio_value.iloc[-1]
    
    # Crear simulación
    mc = MonteCarloSimulation(
        initial_value=initial_value,
        mean_return=mean_return,
        volatility=volatility,
        num_simulations=num_simulations,
        num_days=num_days,
        random_seed=random_seed
    )
    
    simulations = mc.simulate()
    stats = mc.get_statistics(simulations)
    
    return simulations, stats


# Extender Portfolio con métodos de Monte Carlo
def _portfolio_monte_carlo(self,
                          num_simulations: int = 10000,
                          num_days: int = 252,
                          random_seed: Optional[int] = None,
                          for_individual_assets: bool = False) -> Dict:
    """
    Ejecuta simulación de Monte Carlo para la cartera.
    
    Args:
        num_simulations: Número de simulaciones
        num_days: Días a simular
        random_seed: Semilla para reproducibilidad
        for_individual_assets: Si True, también simula cada activo individual
    
    Returns:
        Diccionario con simulaciones y estadísticas
    """
    # Simulación de la cartera
    portfolio_sims, portfolio_stats = monte_carlo_for_portfolio(
        self, num_simulations, num_days, random_seed
    )
    
    result = {
        'portfolio': {
            'simulations': portfolio_sims,
            'statistics': portfolio_stats
        }
    }
    
    # Simulación de activos individuales si se solicita
    if for_individual_assets:
        asset_sims = {}
        for symbol, asset in self.assets.items():
            try:
                sims, stats = monte_carlo_for_asset(
                    asset, num_simulations, num_days, random_seed
                )
                asset_sims[symbol] = {
                    'simulations': sims,
                    'statistics': stats
                }
            except Exception as e:
                print(f"Warning: Could not simulate {symbol}: {e}")
                asset_sims[symbol] = None
        
        result['assets'] = asset_sims
    
    return result


def _portfolio_report(self,
                     include_warnings: bool = True,
                     include_statistics: bool = True,
                     include_quality_check: bool = True,
                     format: str = 'markdown') -> str:
    """
    Genera un reporte en markdown de la cartera.
    
    Args:
        include_warnings: Incluir advertencias sobre la cartera
        include_statistics: Incluir estadísticas detalladas
        include_quality_check: Incluir verificación de calidad de datos
        format: Formato del reporte ('markdown' o 'text')
    
    Returns:
        String con el reporte formateado
    """
    lines = []
    
    # Encabezado
    lines.append(f"# Reporte de Cartera: {self.name}")
    lines.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Información básica
    lines.append("## Información General")
    lines.append(f"- **Número de activos:** {len(self.assets)}")
    lines.append(f"- **Pesos de la cartera:**")
    for symbol, weight in self.weights.items():
        lines.append(f"  - {symbol}: {weight:.2%}")
    lines.append("")
    
    # Estadísticas de la cartera
    if include_statistics:
        lines.append("## Estadísticas de la Cartera")
        stats = self.stats
        lines.append(f"- **Valor medio:** ${stats.get('mean_value', 0):.2f}")
        lines.append(f"- **Desviación estándar:** ${stats.get('std_return', 0):.2f}")
        lines.append(f"- **Retorno total:** {stats.get('total_return', 0):.2%}")
        lines.append(f"- **Retorno medio anualizado:** {stats.get('mean_return', 0) * 252:.2%}")
        lines.append(f"- **Volatilidad anualizada:** {stats.get('std_return', 0) * np.sqrt(252):.2%}")
        lines.append(f"- **Ratio de Sharpe:** {stats.get('sharpe_ratio', 0):.2f}")
        lines.append(f"- **Rango de fechas:** {stats.get('date_range', (None, None))[0]} a {stats.get('date_range', (None, None))[1]}")
        lines.append("")
    
    # Estadísticas por activo
    lines.append("## Estadísticas por Activo")
    for symbol, asset in self.assets.items():
        lines.append(f"### {symbol}")
        asset_stats = asset.stats
        lines.append(f"- **Retorno total:** {asset_stats.get('total_return', 0):.2%}")
        lines.append(f"- **Volatilidad anualizada:** {asset_stats.get('std_return', 0) * np.sqrt(252):.2%}")
        lines.append(f"- **Ratio de Sharpe:** {asset_stats.get('sharpe_ratio', 0):.2f}")
        lines.append(f"- **Precio medio:** ${asset_stats.get('mean_price', 0):.2f}")
        lines.append(f"- **Puntos de datos:** {asset_stats.get('data_points', 0)}")
        lines.append("")
    
    # Advertencias
    if include_warnings:
        lines.append("## Advertencias y Recomendaciones")
        warnings = []
        
        # Verificar diversificación
        if len(self.assets) < 3:
            warnings.append("⚠️ La cartera tiene pocos activos. Considera diversificar más.")
        
        # Verificar concentración
        max_weight = max(self.weights.values())
        if max_weight > 0.5:
            warnings.append(f"⚠️ Alta concentración en un activo ({max_weight:.1%}). Considera rebalancear.")
        
        # Verificar volatilidad
        portfolio_vol = self.get_volatility()
        if portfolio_vol > 0.3:
            warnings.append(f"⚠️ Alta volatilidad ({portfolio_vol:.1%}). Considera activos más estables.")
        
        # Verificar Sharpe ratio
        sharpe = self.stats.get('sharpe_ratio', 0)
        if sharpe < 0:
            warnings.append("⚠️ Ratio de Sharpe negativo. La cartera tiene bajo rendimiento ajustado al riesgo.")
        elif sharpe < 1:
            warnings.append("⚠️ Ratio de Sharpe bajo (<1). Considera optimizar la cartera.")
        
        if warnings:
            for warning in warnings:
                lines.append(warning)
        else:
            lines.append("✅ No se detectaron problemas significativos.")
        lines.append("")
    
    # Verificación de calidad de datos
    if include_quality_check:
        lines.append("## Verificación de Calidad de Datos")
        from .utils import detect_data_quality_issues
        
        for symbol, asset in self.assets.items():
            issues = detect_data_quality_issues(asset.data)
            if any([issues['missing_values'], issues['outliers'], 
                   issues['duplicate_dates'], issues['negative_prices'], 
                   issues['logical_errors']]):
                lines.append(f"### {symbol}")
                if issues['missing_values']:
                    lines.append(f"- ⚠️ Valores faltantes: {issues['missing_values']}")
                if issues['outliers']:
                    lines.append(f"- ⚠️ Outliers detectados: {issues['outliers']}")
                if issues['duplicate_dates']:
                    lines.append("- ⚠️ Fechas duplicadas encontradas")
                if issues['negative_prices']:
                    lines.append("- ⚠️ Precios negativos encontrados")
                if issues['logical_errors']:
                    lines.append(f"- ⚠️ Errores lógicos: {', '.join(issues['logical_errors'])}")
            else:
                lines.append(f"✅ {symbol}: Datos de calidad")
        lines.append("")
    
    # Resumen final
    lines.append("## Resumen")
    lines.append(f"Esta cartera está compuesta por {len(self.assets)} activos con una volatilidad ")
    lines.append(f"anualizada de {self.get_volatility():.2%} y un retorno total histórico de ")
    lines.append(f"{self.stats.get('total_return', 0):.2%}.")
    lines.append("")
    
    return "\n".join(lines)


def _portfolio_plots_report(self, 
                           save_path: Optional[str] = None,
                           show: bool = True):
    """
    Genera y muestra visualizaciones de la cartera.
    
    Args:
        save_path: Ruta donde guardar las figuras (opcional)
        show: Si True, muestra las figuras
    """
    from .plots import (
        plot_portfolio_evolution,
        plot_asset_comparison,
        plot_correlation_matrix,
        plot_returns_distribution,
        plot_risk_return_scatter
    )
    
    # Crear todas las visualizaciones
    plots = {}
    
    try:
        plots['evolution'] = plot_portfolio_evolution(self, save_path=save_path, show=show)
    except Exception as e:
        print(f"Warning: Could not create evolution plot: {e}")
    
    try:
        plots['comparison'] = plot_asset_comparison(self, save_path=save_path, show=show)
    except Exception as e:
        print(f"Warning: Could not create comparison plot: {e}")
    
    try:
        plots['correlation'] = plot_correlation_matrix(self, save_path=save_path, show=show)
    except Exception as e:
        print(f"Warning: Could not create correlation plot: {e}")
    
    try:
        plots['returns_dist'] = plot_returns_distribution(self, save_path=save_path, show=show)
    except Exception as e:
        print(f"Warning: Could not create returns distribution plot: {e}")
    
    try:
        plots['risk_return'] = plot_risk_return_scatter(self, save_path=save_path, show=show)
    except Exception as e:
        print(f"Warning: Could not create risk-return plot: {e}")
    
    return plots


# Añadir métodos a Portfolio
Portfolio.monte_carlo = _portfolio_monte_carlo
Portfolio.report = _portfolio_report
Portfolio.plots_report = _portfolio_plots_report
