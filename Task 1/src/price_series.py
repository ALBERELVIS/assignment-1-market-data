"""
Módulo de series de precios
Define DataClasses para series de precios con métodos estadísticos
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from scipy import stats
import warnings


@dataclass
class PriceSeries:
    """
    DataClass para representar una serie temporal de precios
    Incluye métodos estadísticos que se calculan automáticamente
    """
    symbol: str
    date: pd.DatetimeIndex
    open: pd.Series
    high: pd.Series
    low: pd.Series
    close: pd.Series
    volume: pd.Series
    source: str
    
    # Métricas estadísticas básicas (se calculan automáticamente)
    mean_price: Optional[float] = field(init=False, default=None)
    std_price: Optional[float] = field(init=False, default=None)
    mean_volume: Optional[float] = field(init=False, default=None)
    std_volume: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calcula automáticamente media y desviación típica al crear el objeto"""
        self._calculate_basic_stats()
    
    def _calculate_basic_stats(self):
        """Calcula estadísticas básicas automáticamente"""
        self.mean_price = float(self.close.mean())
        self.std_price = float(self.close.std())
        self.mean_volume = float(self.volume.mean())
        self.std_volume = float(self.volume.std())
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte la serie a DataFrame"""
        return pd.DataFrame({
            'Open': self.open.values,
            'High': self.high.values,
            'Low': self.low.values,
            'Close': self.close.values,
            'Volume': self.volume.values
        }, index=self.date)
    
    def returns(self, method: str = 'simple') -> pd.Series:
        """
        Calcula los retornos de la serie
        
        Args:
            method: 'simple' o 'log' para retornos logarítmicos
        
        Returns:
            Serie de retornos
        """
        if method == 'simple':
            return self.close.pct_change().dropna()
        elif method == 'log':
            return np.log(self.close / self.close.shift(1)).dropna()
        else:
            raise ValueError("method debe ser 'simple' o 'log'")
    
    def volatility(self, window: int = 30, annualized: bool = True) -> float:
        """
        Calcula la volatilidad (desviación estándar de retornos)
        
        Args:
            window: Ventana de días para el cálculo
            annualized: Si True, anualiza la volatilidad (asumiendo 252 días de trading)
        
        Returns:
            Volatilidad
        """
        returns = self.returns()
        if len(returns) < window:
            window = len(returns)
        
        vol = returns.tail(window).std()
        
        if annualized:
            vol = vol * np.sqrt(252)  # Anualización
        
        return float(vol)
    
    def sharpe_ratio(self, risk_free_rate: float = 0.02, window: int = 30) -> float:
        """
        Calcula el ratio de Sharpe
        
        Args:
            risk_free_rate: Tasa libre de riesgo (por defecto 2% anual)
            window: Ventana de días para el cálculo
        
        Returns:
            Ratio de Sharpe
        """
        returns = self.returns()
        if len(returns) < window:
            window = len(returns)
        
        recent_returns = returns.tail(window)
        excess_returns = recent_returns.mean() - (risk_free_rate / 252)  # Diario
        volatility = recent_returns.std()
        
        if volatility == 0:
            return 0.0
        
        sharpe = excess_returns / volatility * np.sqrt(252)  # Anualizado
        return float(sharpe)
    
    def max_drawdown(self) -> float:
        """
        Calcula el máximo drawdown (caída máxima desde un pico)
        
        Returns:
            Máximo drawdown como porcentaje
        """
        cumulative = (1 + self.returns()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def correlation_with(self, other: 'PriceSeries') -> float:
        """
        Calcula la correlación con otra serie de precios
        
        Args:
            other: Otra PriceSeries
        
        Returns:
            Coeficiente de correlación
        """
        # Alinear las fechas
        self_returns = self.returns()
        other_returns = other.returns()
        
        common_dates = self_returns.index.intersection(other_returns.index)
        if len(common_dates) < 2:
            return 0.0
        
        aligned_self = self_returns.loc[common_dates]
        aligned_other = other_returns.loc[common_dates]
        
        correlation = aligned_self.corr(aligned_other)
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def get_summary_stats(self) -> dict:
        """
        Obtiene un resumen completo de estadísticas
        
        Returns:
            Diccionario con todas las estadísticas
        """
        returns = self.returns()
        
        return {
            'symbol': self.symbol,
            'period': f"{self.date.min().date()} a {self.date.max().date()}",
            'days': len(self.date),
            'mean_price': self.mean_price,
            'std_price': self.std_price,
            'min_price': float(self.close.min()),
            'max_price': float(self.close.max()),
            'current_price': float(self.close.iloc[-1]),
            'mean_volume': self.mean_volume,
            'volatility_30d': self.volatility(window=30),
            'volatility_annualized': self.volatility(annualized=True),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'total_return': float((self.close.iloc[-1] / self.close.iloc[0] - 1) * 100),
            'mean_daily_return': float(returns.mean()),
            'std_daily_return': float(returns.std()),
            'skewness': float(stats.skew(returns.dropna())),
            'kurtosis': float(stats.kurtosis(returns.dropna()))
        }
    
    def __len__(self):
        """Devuelve el número de registros"""
        return len(self.date)
    
    @classmethod
    def from_standardized_data(cls, data) -> 'PriceSeries':
        """
        Crea una PriceSeries desde un objeto StandardizedPriceData
        
        Args:
            data: Objeto StandardizedPriceData
        
        Returns:
            PriceSeries
        """
        return cls(
            symbol=data.symbol,
            date=data.date,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            source=data.source
        )

