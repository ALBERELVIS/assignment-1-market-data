"""
datamodels.py
-------------
Define las clases base para series de precios y carteras.
Incluye métodos estadísticos automáticos y validación de datos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from .utils import clean_price_data, validate_price_series


@dataclass
class PriceSeries:
    """
    Representa una serie temporal de precios de un activo.
    
    Atributos:
        symbol: Símbolo del activo (ej. 'AAPL', '^GSPC')
        data: DataFrame con columnas estándar ['open', 'high', 'low', 'close', 'adj_close', 'volume']
        source: Fuente de los datos (ej. 'yfinance')
        _mean: Media calculada automáticamente (cached)
        _std: Desviación típica calculada automáticamente (cached)
        _stats: Diccionario con estadísticas calculadas (cached)
    """
    symbol: str
    data: pd.DataFrame
    source: str = "unknown"
    _mean: Optional[float] = field(default=None, init=False, repr=False)
    _std: Optional[float] = field(default=None, init=False, repr=False)
    _stats: Optional[Dict] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Valida y limpia los datos al inicializar."""
        if self.data is None or self.data.empty:
            raise ValueError(f"Data for {self.symbol} is empty or None")
        
        # Validar que tiene las columnas necesarias
        required_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
        missing = [c for c in required_cols if c not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns for {self.symbol}: {missing}")
        
        # Limpiar datos
        self.data = clean_price_data(self.data)
        
        # Validar integridad
        validate_price_series(self.data, self.symbol)
        
        # Calcular estadísticas básicas automáticamente
        self._calculate_basic_stats()
    
    def _calculate_basic_stats(self):
        """Calcula media y desviación típica automáticamente."""
        if self.data.empty:
            return
        
        # Usar precio de cierre ajustado para cálculos
        prices = self.data['adj_close'].dropna()
        
        if len(prices) == 0:
            self._mean = np.nan
            self._std = np.nan
        else:
            self._mean = float(prices.mean())
            self._std = float(prices.std())
        
        # Calcular estadísticas adicionales
        returns = prices.pct_change().dropna()
        
        self._stats = {
            'mean_price': self._mean,
            'std_price': self._std,
            'min_price': float(prices.min()),
            'max_price': float(prices.max()),
            'mean_return': float(returns.mean()) if len(returns) > 0 else np.nan,
            'std_return': float(returns.std()) if len(returns) > 0 else np.nan,
            'total_return': float((prices.iloc[-1] / prices.iloc[0] - 1)) if len(prices) > 0 else np.nan,
            'sharpe_ratio': float(returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 0 and returns.std() > 0 else np.nan,
            'data_points': len(prices),
            'date_range': (prices.index[0], prices.index[-1]) if len(prices) > 0 else (None, None)
        }
    
    @property
    def mean(self) -> float:
        """Retorna la media del precio de cierre ajustado."""
        if self._mean is None:
            self._calculate_basic_stats()
        return self._mean
    
    @property
    def std(self) -> float:
        """Retorna la desviación típica del precio de cierre ajustado."""
        if self._std is None:
            self._calculate_basic_stats()
        return self._std
    
    @property
    def stats(self) -> Dict:
        """Retorna diccionario con todas las estadísticas."""
        if self._stats is None:
            self._calculate_basic_stats()
        return self._stats.copy()
    
    def get_returns(self, method: str = 'simple') -> pd.Series:
        """
        Calcula retornos de la serie de precios.
        
        Args:
            method: 'simple' o 'log'
        
        Returns:
            Series con retornos
        """
        prices = self.data['adj_close'].dropna()
        if method == 'log':
            return np.log(prices / prices.shift(1)).dropna()
        else:
            return prices.pct_change().dropna()
    
    def get_volatility(self, annualized: bool = True) -> float:
        """
        Calcula la volatilidad (desviación estándar de retornos).
        
        Args:
            annualized: Si True, anualiza asumiendo 252 días de trading
        
        Returns:
            Volatilidad (anualizada o diaria)
        """
        returns = self.get_returns()
        if len(returns) == 0:
            return np.nan
        
        vol = returns.std()
        if annualized:
            vol = vol * np.sqrt(252)
        return float(vol)
    
    def align_with(self, other: 'PriceSeries') -> Tuple['PriceSeries', 'PriceSeries']:
        """
        Alinea dos series de precios en el mismo rango de fechas.
        
        Args:
            other: Otra PriceSeries para alinear
        
        Returns:
            Tuple con ambas series alineadas
        """
        # Encontrar intersección de fechas
        common_dates = self.data.index.intersection(other.data.index)
        
        if len(common_dates) == 0:
            raise ValueError(f"No common dates between {self.symbol} and {other.symbol}")
        
        # Filtrar ambas series
        aligned_self = PriceSeries(
            symbol=self.symbol,
            data=self.data.loc[common_dates].copy(),
            source=self.source
        )
        aligned_other = PriceSeries(
            symbol=other.symbol,
            data=other.data.loc[common_dates].copy(),
            source=other.source
        )
        
        return aligned_self, aligned_other


@dataclass
class Portfolio:
    """
    Representa una cartera de activos con sus pesos.
    
    Una cartera es una colección de PriceSeries con pesos asignados.
    
    Atributos:
        assets: Dict {symbol: PriceSeries}
        weights: Dict {symbol: weight} - pesos normalizados (suman 1.0)
        name: Nombre de la cartera
        _portfolio_value: Serie temporal del valor de la cartera (cached)
    """
    assets: Dict[str, PriceSeries]
    weights: Dict[str, float]
    name: str = "Portfolio"
    _portfolio_value: Optional[pd.Series] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Valida y normaliza pesos."""
        if not self.assets:
            raise ValueError("Portfolio must contain at least one asset")
        
        # Validar que todos los símbolos en weights existen en assets
        for symbol in self.weights:
            if symbol not in self.assets:
                raise ValueError(f"Weight specified for {symbol} but asset not in portfolio")
        
        # Normalizar pesos (deben sumar 1.0)
        total_weight = sum(self.weights.values())
        if total_weight == 0:
            raise ValueError("Sum of weights must be greater than 0")
        
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        # Alinear todas las series a fechas comunes
        self._align_assets()
    
    def _align_assets(self):
        """Alinea todas las series de precios a fechas comunes."""
        if len(self.assets) == 1:
            return
        
        # Encontrar intersección de todas las fechas
        asset_list = list(self.assets.values())
        common_dates = asset_list[0].data.index
        
        for asset in asset_list[1:]:
            common_dates = common_dates.intersection(asset.data.index)
        
        if len(common_dates) == 0:
            raise ValueError("No common dates across all assets in portfolio")
        
        # Filtrar todas las series
        for symbol in self.assets:
            self.assets[symbol].data = self.assets[symbol].data.loc[common_dates].copy()
            # Recalcular estadísticas
            self.assets[symbol]._calculate_basic_stats()
    
    @property
    def portfolio_value(self) -> pd.Series:
        """
        Calcula el valor de la cartera a lo largo del tiempo.
        Retorna una serie temporal con el valor total de la cartera.
        """
        if self._portfolio_value is not None:
            return self._portfolio_value
        
        # Obtener fechas comunes
        common_dates = None
        for asset in self.assets.values():
            if common_dates is None:
                common_dates = asset.data.index
            else:
                common_dates = common_dates.intersection(asset.data.index)
        
        if len(common_dates) == 0:
            return pd.Series(dtype=float)
        
        # Calcular valor de cartera día a día
        portfolio_values = []
        for date in common_dates:
            total_value = 0.0
            for symbol, asset in self.assets.items():
                weight = self.weights.get(symbol, 0.0)
                price = asset.data.loc[date, 'adj_close']
                total_value += weight * price
            portfolio_values.append(total_value)
        
        self._portfolio_value = pd.Series(portfolio_values, index=common_dates)
        return self._portfolio_value
    
    @property
    def mean(self) -> float:
        """Media del valor de la cartera."""
        pv = self.portfolio_value
        return float(pv.mean()) if len(pv) > 0 else np.nan
    
    @property
    def std(self) -> float:
        """Desviación típica del valor de la cartera."""
        pv = self.portfolio_value
        return float(pv.std()) if len(pv) > 0 else np.nan
    
    @property
    def stats(self) -> Dict:
        """Estadísticas agregadas de la cartera."""
        pv = self.portfolio_value
        if len(pv) == 0:
            return {}
        
        returns = pv.pct_change().dropna()
        
        return {
            'mean_value': float(pv.mean()),
            'std_value': float(pv.std()),
            'min_value': float(pv.min()),
            'max_value': float(pv.max()),
            'mean_return': float(returns.mean()) if len(returns) > 0 else np.nan,
            'std_return': float(returns.std()) if len(returns) > 0 else np.nan,
            'total_return': float((pv.iloc[-1] / pv.iloc[0] - 1)) if len(pv) > 0 else np.nan,
            'sharpe_ratio': float(returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 0 and returns.std() > 0 else np.nan,
            'data_points': len(pv),
            'date_range': (pv.index[0], pv.index[-1]) if len(pv) > 0 else (None, None),
            'num_assets': len(self.assets),
            'weights': self.weights.copy()
        }
    
    def get_returns(self) -> pd.Series:
        """Retorna los retornos de la cartera."""
        pv = self.portfolio_value
        return pv.pct_change().dropna()
    
    def get_volatility(self, annualized: bool = True) -> float:
        """Calcula la volatilidad de la cartera."""
        returns = self.get_returns()
        if len(returns) == 0:
            return np.nan
        
        vol = returns.std()
        if annualized:
            vol = vol * np.sqrt(252)
        return float(vol)
