"""
plots.py
--------
Funciones de visualización para carteras y activos.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional
from .datamodels import Portfolio, PriceSeries

# Configurar estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


def plot_portfolio_evolution(portfolio: Portfolio,
                             save_path: Optional[str] = None,
                             show: bool = True) -> plt.Figure:
    """
    Gráfica la evolución del valor de la cartera a lo largo del tiempo.
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Valor de la cartera
    portfolio_value = portfolio.portfolio_value
    ax.plot(portfolio_value.index, portfolio_value.values, 
            linewidth=2, label='Valor de la Cartera', color='#2E86AB')
    
    # Línea de tendencia
    z = np.polyfit(range(len(portfolio_value)), portfolio_value.values, 1)
    p = np.poly1d(z)
    ax.plot(portfolio_value.index, p(range(len(portfolio_value))), 
            "--", alpha=0.5, label='Tendencia', color='#A23B72')
    
    ax.set_title(f'Evolución de la Cartera: {portfolio.name}', fontsize=16, fontweight='bold')
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Valor de la Cartera ($)', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_asset_comparison(portfolio: Portfolio,
                          save_path: Optional[str] = None,
                          show: bool = True) -> plt.Figure:
    """
    Compara la evolución normalizada de todos los activos en la cartera.
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Normalizar todos los activos al precio inicial
    colors = plt.cm.Set3(np.linspace(0, 1, len(portfolio.assets)))
    
    for i, (symbol, asset) in enumerate(portfolio.assets.items()):
        prices = asset.data['adj_close']
        normalized = (prices / prices.iloc[0]) * 100
        weight = portfolio.weights.get(symbol, 0)
        ax.plot(normalized.index, normalized.values, 
                linewidth=2, label=f'{symbol} ({weight:.1%})', 
                color=colors[i], alpha=0.8)
    
    # Valor de la cartera normalizado
    portfolio_value = portfolio.portfolio_value
    normalized_portfolio = (portfolio_value / portfolio_value.iloc[0]) * 100
    ax.plot(normalized_portfolio.index, normalized_portfolio.values,
            linewidth=3, label='Cartera Total', color='black', linestyle='--')
    
    ax.set_title('Comparación de Activos (Normalizado al 100%)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Retorno Normalizado (%)', fontsize=12)
    ax.legend(loc='best', ncol=2)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_correlation_matrix(portfolio: Portfolio,
                           save_path: Optional[str] = None,
                           show: bool = True) -> plt.Figure:
    """
    Muestra la matriz de correlación entre los activos de la cartera.
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calcular retornos de cada activo
    returns_dict = {}
    for symbol, asset in portfolio.assets.items():
        returns = asset.get_returns()
        returns_dict[symbol] = returns
    
    # Crear DataFrame de retornos
    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.dropna()
    
    # Matriz de correlación
    corr_matrix = returns_df.corr()
    
    # Heatmap
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                vmin=-1, vmax=1, ax=ax)
    
    ax.set_title('Matriz de Correlación entre Activos', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_returns_distribution(portfolio: Portfolio,
                             save_path: Optional[str] = None,
                             show: bool = True) -> plt.Figure:
    """
    Muestra la distribución de retornos de la cartera y activos individuales.
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Retornos de la cartera
    portfolio_returns = portfolio.get_returns()
    axes[0].hist(portfolio_returns.values, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
    axes[0].axvline(portfolio_returns.mean(), color='red', linestyle='--', 
                    linewidth=2, label=f'Media: {portfolio_returns.mean():.4f}')
    axes[0].set_title('Distribución de Retornos de la Cartera', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Retorno Diario', fontsize=12)
    axes[0].set_ylabel('Frecuencia', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Retornos de activos individuales
    colors = plt.cm.Set3(np.linspace(0, 1, len(portfolio.assets)))
    for i, (symbol, asset) in enumerate(portfolio.assets.items()):
        returns = asset.get_returns()
        axes[1].hist(returns.values, bins=30, alpha=0.5, 
                    label=symbol, color=colors[i], edgecolor='black')
    
    axes[1].set_title('Distribución de Retornos por Activo', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Retorno Diario', fontsize=12)
    axes[1].set_ylabel('Frecuencia', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_risk_return_scatter(portfolio: Portfolio,
                            save_path: Optional[str] = None,
                            show: bool = True) -> plt.Figure:
    """
    Gráfica de dispersión riesgo-retorno para activos y cartera.
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calcular riesgo y retorno para cada activo
    for symbol, asset in portfolio.assets.items():
        returns = asset.get_returns()
        annual_return = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        weight = portfolio.weights.get(symbol, 0)
        
        ax.scatter(annual_vol, annual_return, s=weight*1000, 
                  alpha=0.6, label=f'{symbol} ({weight:.1%})',
                  edgecolors='black', linewidth=1)
    
    # Riesgo y retorno de la cartera
    portfolio_returns = portfolio.get_returns()
    portfolio_annual_return = portfolio_returns.mean() * 252
    portfolio_annual_vol = portfolio_returns.std() * np.sqrt(252)
    
    ax.scatter(portfolio_annual_vol, portfolio_annual_return, 
              s=500, marker='*', color='red', 
              label='Cartera Total', edgecolors='black', linewidth=2, zorder=5)
    
    ax.set_xlabel('Volatilidad Anualizada (Riesgo)', fontsize=12)
    ax.set_ylabel('Retorno Anualizado', fontsize=12)
    ax.set_title('Análisis Riesgo-Retorno', fontsize=16, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_monte_carlo_results(simulations: pd.DataFrame,
                            statistics: dict,
                            initial_value: float,
                            title: str = "Simulación de Monte Carlo",
                            save_path: Optional[str] = None,
                            show: bool = True) -> plt.Figure:
    """
    Visualiza los resultados de una simulación de Monte Carlo.
    
    Args:
        simulations: DataFrame con simulaciones (cada columna es una simulación)
        statistics: Diccionario con estadísticas
        initial_value: Valor inicial
        title: Título del gráfico
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Gráfico 1: Evolución de simulaciones
    ax1 = axes[0]
    
    # Mostrar algunas simulaciones (máximo 100 para no saturar)
    num_to_show = min(100, simulations.shape[1])
    for i in range(num_to_show):
        ax1.plot(simulations.index, simulations.iloc[:, i].values, 
                alpha=0.1, color='blue', linewidth=0.5)
    
    # Media y percentiles
    mean_sim = simulations.mean(axis=1)
    p5 = simulations.quantile(0.05, axis=1)
    p95 = simulations.quantile(0.95, axis=1)
    
    ax1.plot(simulations.index, mean_sim.values, 
            color='red', linewidth=2, label='Media')
    ax1.plot(simulations.index, p5.values, 
            color='orange', linewidth=2, linestyle='--', label='Percentil 5%')
    ax1.plot(simulations.index, p95.values, 
            color='orange', linewidth=2, linestyle='--', label='Percentil 95%')
    ax1.axhline(y=initial_value, color='green', linestyle=':', 
               linewidth=2, label='Valor Inicial')
    
    ax1.set_title(f'{title} - Evolución', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Fecha', fontsize=12)
    ax1.set_ylabel('Valor', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Distribución de valores finales
    ax2 = axes[1]
    final_values = simulations.iloc[-1, :]
    
    ax2.hist(final_values.values, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
    ax2.axvline(statistics['mean_final_value'], color='red', linestyle='--', 
               linewidth=2, label=f'Media: ${statistics["mean_final_value"]:,.2f}')
    ax2.axvline(statistics['percentile_5'], color='orange', linestyle='--', 
               linewidth=2, label=f'P5: ${statistics["percentile_5"]:,.2f}')
    ax2.axvline(statistics['percentile_95'], color='orange', linestyle='--', 
               linewidth=2, label=f'P95: ${statistics["percentile_95"]:,.2f}')
    ax2.axvline(initial_value, color='green', linestyle=':', 
               linewidth=2, label=f'Inicial: ${initial_value:,.2f}')
    
    ax2.set_title(f'{title} - Distribución de Valores Finales', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Valor Final', fontsize=12)
    ax2.set_ylabel('Frecuencia', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig


def plot_portfolio_composition(portfolio: Portfolio,
                              save_path: Optional[str] = None,
                              show: bool = True) -> plt.Figure:
    """
    Muestra la composición de la cartera (gráfico de pastel).
    
    Args:
        portfolio: Portfolio a visualizar
        save_path: Ruta donde guardar la figura
        show: Si True, muestra la figura
    
    Returns:
        Figura de matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    labels = list(portfolio.weights.keys())
    sizes = list(portfolio.weights.values())
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                     autopct='%1.1f%%', startangle=90,
                                     textprops={'fontsize': 12})
    
    # Mejorar texto
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(f'Composición de la Cartera: {portfolio.name}', 
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return fig
