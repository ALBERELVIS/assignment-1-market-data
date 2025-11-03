"""
Market Data Toolkit
-------------------
Herramientas para la obtención y análisis de información bursátil.

Este paquete proporciona:
- Extractores de datos de múltiples fuentes (APIs)
- Clases de datos estandarizadas (PriceSeries, Portfolio)
- Análisis estadístico automático
- Simulaciones de Monte Carlo
- Generación de reportes y visualizaciones
"""

from .extractor import (
    ExtractorBase,
    YFinanceExtractor,
    GenericCallableExtractor,
    download_price_series,
    register_extractor,
    get_extractor
)

from .datamodels import (
    PriceSeries,
    Portfolio
)

from .portfolio import (
    MonteCarloSimulation,
    monte_carlo_for_asset,
    monte_carlo_for_portfolio
)

from .utils import (
    clean_price_data,
    validate_price_series,
    standardize_price_format,
    detect_data_quality_issues,
    prepare_for_analysis
)

from .plots import (
    plot_portfolio_evolution,
    plot_asset_comparison,
    plot_correlation_matrix,
    plot_returns_distribution,
    plot_risk_return_scatter,
    plot_monte_carlo_results,
    plot_portfolio_composition
)

__version__ = "1.0.0"
__author__ = "Dr. Albert Martin"

__all__ = [
    # Extractors
    'ExtractorBase',
    'YFinanceExtractor',
    'GenericCallableExtractor',
    'download_price_series',
    'register_extractor',
    'get_extractor',
    # Data Models
    'PriceSeries',
    'Portfolio',
    # Portfolio Analysis
    'MonteCarloSimulation',
    'monte_carlo_for_asset',
    'monte_carlo_for_portfolio',
    # Utilities
    'clean_price_data',
    'validate_price_series',
    'standardize_price_format',
    'detect_data_quality_issues',
    'prepare_for_analysis',
    # Visualizations
    'plot_portfolio_evolution',
    'plot_asset_comparison',
    'plot_correlation_matrix',
    'plot_returns_distribution',
    'plot_risk_return_scatter',
    'plot_monte_carlo_results',
    'plot_portfolio_composition',
]
