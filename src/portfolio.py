"""
Módulo de Portfolio
Define la clase Portfolio que contiene múltiples series de precios
con métodos de análisis y reportes
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats as scipy_stats

from .price_series import PriceSeries
from .data_cleaning import force_naive_datetime_index

# Asegurar que numpy se use para todas las conversiones de fechas
np.datetime64  # Referencia para asegurar que está disponible


def _normalize_datetime_to_naive(dt) -> pd.Timestamp:
    """
    Normaliza cualquier fecha/datetime a naive datetime (sin timezone)
    
    Args:
        dt: Cualquier objeto fecha/datetime (pd.Timestamp, datetime, etc.)
    
    Returns:
        pd.Timestamp sin timezone
    """
    # Convertir a pd.Timestamp si no lo es
    if not isinstance(dt, pd.Timestamp):
        dt = pd.to_datetime(dt)
    
    # Remover timezone si existe - múltiples formas para asegurar que funcione
    if hasattr(dt, 'tz') and dt.tz is not None:
        try:
            dt = dt.tz_localize(None)
        except:
            # Si tz_localize falla, intentar tz_convert(None) o crear nuevo Timestamp
            try:
                dt = dt.tz_convert(None)
            except:
                # Último recurso: crear nuevo Timestamp sin timezone
                dt = pd.Timestamp(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
    elif isinstance(dt, pd.Timestamp) and dt.tz is not None:
        try:
            dt = dt.tz_localize(None)
        except:
            dt = pd.Timestamp(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
    
    # Verificación final: asegurar que no tenga timezone
    if isinstance(dt, pd.Timestamp) and dt.tz is not None:
        # Forzar creación de nuevo Timestamp sin timezone
        dt = pd.Timestamp(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
    
    return dt


@dataclass
class Portfolio:
    """
    Portfolio: conjunto de series de precios con pesos asociados
    Una cartera es una colección de PriceSeries con pesos (porcentajes)
    """
    symbols: List[str]
    price_series: List[PriceSeries]
    weights: Optional[List[float]] = None
    
    def __post_init__(self):
        """Valida y normaliza los pesos al crear el portfolio"""
        if self.weights is None:
            # Si no se especifican pesos, distribuir equitativamente
            self.weights = [1.0 / len(self.price_series)] * len(self.price_series)
        
        if len(self.weights) != len(self.price_series):
            raise ValueError("El número de pesos debe coincidir con el número de series")
        
        # Normalizar pesos para que sumen 1.0
        total_weight = sum(self.weights)
        if abs(total_weight - 1.0) > 0.01:  # Tolerancia pequeña
            self.weights = [w / total_weight for w in self.weights]
    
    def get_portfolio_value_series(self) -> pd.Series:
        """
        Calcula la serie de valores de la cartera combinada
        
        Returns:
            Serie temporal del valor total de la cartera
        """
        if not self.price_series:
            return pd.Series(dtype=float)
        
        # SOLUCIÓN INTEGRAL: Crear series de precios ponderadas con índices completamente normalizados
        weighted_series = []
        for i, ps in enumerate(self.price_series):
            # FORZAR normalización de fechas usando la función de data_cleaning
            ps_dates = force_naive_datetime_index(ps.date)
            
            # Crear serie ponderada con valores y índice completamente nuevos para evitar problemas
            weighted_values = (ps.close * self.weights[i]).values
            weighted_series.append(pd.Series(weighted_values, index=ps_dates))
        
        # Asegurar que TODAS las series tengan índices completamente naive ANTES de concatenar
        for i, ws in enumerate(weighted_series):
            normalized_index = force_naive_datetime_index(ws.index)
            weighted_series[i] = pd.Series(ws.values, index=normalized_index)
        
        # Combinar todas las series usando pd.concat (alinea automáticamente por fecha)
        if len(weighted_series) == 1:
            portfolio_series = weighted_series[0].copy()
        else:
            # Concatenar y sumar los valores por fecha
            combined_df = pd.concat(weighted_series, axis=1, join='outer', sort=True)
            portfolio_series = combined_df.sum(axis=1)
        
        # FORZAR normalización del índice final de forma MÁS AGRESIVA
        # Extraer valores directamente y recrear todo desde cero usando numpy
        portfolio_values = portfolio_series.values.copy()
        
        # Convertir cada fecha del índice a numpy datetime64[ns] individualmente
        # Esto garantiza que ninguna fecha tenga timezone
        numpy_dates = []
        for dt in portfolio_series.index:
            # Convertir a numpy datetime64[ns] (garantiza naive)
            if isinstance(dt, pd.Timestamp):
                # Si tiene timezone, extraer solo los componentes de fecha/hora
                if hasattr(dt, 'tz') and dt.tz is not None:
                    dt = dt.tz_localize(None)
                numpy_dates.append(np.datetime64(dt))
            else:
                numpy_dates.append(np.datetime64(dt))
        
        # Crear array numpy y luego DatetimeIndex
        numpy_index_array = np.array(numpy_dates, dtype='datetime64[ns]')
        new_index = pd.DatetimeIndex(numpy_index_array)
        
        # Recrear la serie completamente con el nuevo índice
        portfolio_series = pd.Series(portfolio_values, index=new_index)
        
        # Rellenar valores faltantes con forward fill y luego backward fill
        portfolio_series = portfolio_series.ffill().bfill()
        
        return portfolio_series
    
    def get_portfolio_returns(self) -> pd.Series:
        """
        Calcula los retornos de la cartera
        
        Returns:
            Serie de retornos de la cartera
        """
        portfolio_value = self.get_portfolio_value_series()
        returns = portfolio_value.pct_change().dropna()
        
        # Validar que no haya valores NaN o infinitos
        if returns.isna().any() or np.isinf(returns).any():
            print(f"⚠️  Advertencia: Se encontraron valores NaN o infinitos en los retornos")
            returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        
        return returns
    
    def report(self,
               risk_free_rate: float = 0.02,
               include_warnings: bool = True,
               include_correlation: bool = True) -> str:
        """
        Genera un reporte formateado en Markdown con análisis relevante
        
        Args:
            risk_free_rate: Tasa libre de riesgo para cálculos
            include_warnings: Si True, incluye advertencias
            include_correlation: Si True, incluye matriz de correlación
        
        Returns:
            String con el reporte en formato Markdown
        """
        report_lines = []
        
        # Encabezado
        report_lines.append("# Reporte de Análisis de Portfolio\n")
        report_lines.append(f"**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"**Número de activos:** {len(self.symbols)}\n")
        report_lines.append("\n---\n")
        
        # Composición del portfolio
        report_lines.append("## Composición del Portfolio\n")
        report_lines.append("| Símbolo | Peso | Valor Actual |")
        report_lines.append("|---------|------|--------------|")
        
        portfolio_value = self.get_portfolio_value_series()
        current_value = portfolio_value.iloc[-1]
        
        for i, symbol in enumerate(self.symbols):
            ps = self.price_series[i]
            weight = self.weights[i]
            asset_value = ps.close.iloc[-1]
            report_lines.append(f"| {symbol} | {weight*100:.2f}% | ${asset_value:.2f} |")
        
        report_lines.append(f"\n**Valor total del portfolio:** ${current_value:.2f}\n")
        report_lines.append("\n---\n")
        
        # Análisis individual de activos
        report_lines.append("## Análisis Individual de Activos\n")
        
        for i, ps in enumerate(self.price_series):
            symbol = self.symbols[i]
            stats = ps.get_summary_stats()
            
            report_lines.append(f"### {symbol}\n")
            report_lines.append(f"- **Periodo:** {stats['period']}")
            report_lines.append(f"- **Precio actual:** ${stats['current_price']:.2f}")
            report_lines.append(f"- **Retorno total:** {stats['total_return']:.2f}%")
            report_lines.append(f"- **Volatilidad anualizada:** {stats['volatility_annualized']*100:.2f}%")
            report_lines.append(f"- **Ratio de Sharpe:** {stats['sharpe_ratio']:.3f}")
            report_lines.append(f"- **Máximo Drawdown:** {stats['max_drawdown']*100:.2f}%")
            report_lines.append(f"- **Skewness:** {stats['skewness']:.3f}")
            report_lines.append(f"- **Kurtosis:** {stats['kurtosis']:.3f}")
            report_lines.append("\n")
        
        report_lines.append("---\n")
        
        # Análisis del portfolio completo
        report_lines.append("## Análisis del Portfolio Completo\n")
        
        portfolio_returns = self.get_portfolio_returns()
        portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
        portfolio_mean_return = portfolio_returns.mean() * 252
        
        portfolio_sharpe = (portfolio_mean_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        report_lines.append(f"- **Retorno medio anualizado:** {portfolio_mean_return*100:.2f}%")
        report_lines.append(f"- **Volatilidad anualizada:** {portfolio_volatility*100:.2f}%")
        report_lines.append(f"- **Ratio de Sharpe:** {portfolio_sharpe:.3f}")
        report_lines.append("\n")
        
        # Matriz de correlación
        if include_correlation and len(self.price_series) > 1:
            report_lines.append("## Matriz de Correlación entre Activos\n")
            report_lines.append("| Activo | " + " | ".join(self.symbols) + " |")
            report_lines.append("|" + "---|" * (len(self.symbols) + 1))
            
            for i, symbol1 in enumerate(self.symbols):
                row = [f"**{symbol1}**"]
                for j, symbol2 in enumerate(self.symbols):
                    if i == j:
                        row.append("1.000")
                    else:
                        corr = self.price_series[i].correlation_with(self.price_series[j])
                        row.append(f"{corr:.3f}")
                report_lines.append("| " + " | ".join(row) + " |")
            report_lines.append("\n")
        
        # Métricas adicionales del portfolio
        report_lines.append("## Métricas Adicionales\n")
        
        # Calcular métricas adicionales
        portfolio_value_series = self.get_portfolio_value_series()
        max_dd = self._calculate_max_drawdown(portfolio_returns)
        var_95 = np.percentile(portfolio_returns, 5) * 100  # Value at Risk 95%
        cvar_95 = portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean() * 100  # CVaR
        
        # Calcular retorno total del portfolio
        total_return_portfolio = (current_value / portfolio_value_series.iloc[0] - 1) * 100
        
        # Calcular beta (necesitaríamos un índice de referencia, por ahora usar promedio)
        # Simular beta como correlación promedio con el mercado
        avg_correlation = 0
        if len(self.price_series) > 1:
            correlations = []
            for i in range(len(self.price_series)):
                for j in range(i+1, len(self.price_series)):
                    corr = self.price_series[i].correlation_with(self.price_series[j])
                    correlations.append(corr)
            if correlations:
                avg_correlation = np.mean(correlations)
        
        report_lines.append(f"- **Retorno total del período:** {total_return_portfolio:.2f}%")
        report_lines.append(f"- **Máximo Drawdown:** {max_dd*100:.2f}%")
        report_lines.append(f"- **Value at Risk (95%):** {var_95:.2f}%")
        report_lines.append(f"- **Conditional VaR (95%):** {cvar_95:.2f}%")
        report_lines.append(f"- **Correlación promedio entre activos:** {avg_correlation:.3f}")
        
        # Calcular diversificación
        diversification_ratio = self._calculate_diversification_ratio()
        report_lines.append(f"- **Ratio de diversificación:** {diversification_ratio:.3f}")
        report_lines.append("\n")
        
        # Advertencias
        if include_warnings:
            report_lines.append("## Advertencias y Recomendaciones\n")
            
            warnings = []
            recommendations = []
            
            # Verificar concentración
            max_weight = max(self.weights)
            if max_weight > 0.5:
                warnings.append(f"⚠️ **Alta concentración:** El activo más pesado representa {max_weight*100:.1f}% del portfolio")
                recommendations.append(f"- Considerar diversificar más el portfolio para reducir el riesgo de concentración")
            elif max_weight > 0.4:
                warnings.append(f"⚠️ **Concentración moderada:** El activo más pesado representa {max_weight*100:.1f}% del portfolio")
            
            # Verificar número de activos
            if len(self.symbols) < 3:
                warnings.append(f"⚠️ **Pocos activos:** El portfolio solo tiene {len(self.symbols)} activo(s), considerando agregar más para diversificación")
            
            # Verificar correlaciones altas
            if len(self.price_series) > 1:
                high_corr_pairs = []
                for i in range(len(self.price_series)):
                    for j in range(i+1, len(self.price_series)):
                        corr = self.price_series[i].correlation_with(self.price_series[j])
                        if corr > 0.8:
                            high_corr_pairs.append((self.symbols[i], self.symbols[j], corr))
                
                if high_corr_pairs:
                    warnings.append("⚠️ **Alta correlación:** Los siguientes pares tienen correlación > 0.8:")
                    for sym1, sym2, corr in high_corr_pairs:
                        warnings.append(f"  - {sym1} - {sym2}: {corr:.3f}")
                    recommendations.append("- Considerar agregar activos con menor correlación para mejorar la diversificación")
            
            # Verificar volatilidad
            if portfolio_volatility > 0.3:
                warnings.append(f"⚠️ **Alta volatilidad:** El portfolio tiene volatilidad anualizada de {portfolio_volatility*100:.1f}%")
                recommendations.append("- Considerar reducir la exposición a activos volátiles o agregar activos defensivos")
            elif portfolio_volatility < 0.10:
                warnings.append(f"ℹ️ **Baja volatilidad:** El portfolio tiene volatilidad anualizada de {portfolio_volatility*100:.1f}% (conservador)")
            
            # Verificar Sharpe ratio
            if portfolio_sharpe < 0.5:
                warnings.append(f"⚠️ **Bajo ratio de Sharpe:** {portfolio_sharpe:.3f} (considerar revisar la composición)")
                recommendations.append("- El ratio de Sharpe bajo indica que el retorno no compensa adecuadamente el riesgo asumido")
            elif portfolio_sharpe > 1.5:
                warnings.append(f"✅ **Excelente ratio de Sharpe:** {portfolio_sharpe:.3f} (buen balance riesgo/retorno)")
            
            # Verificar drawdown
            if max_dd < -0.20:
                warnings.append(f"⚠️ **Drawdown significativo:** Máximo drawdown de {max_dd*100:.1f}%")
                recommendations.append("- Considerar estrategias de gestión de riesgo o stop-loss")
            
            # Verificar diversificación
            if diversification_ratio < 0.8:
                warnings.append(f"⚠️ **Baja diversificación:** Ratio de diversificación de {diversification_ratio:.3f}")
                recommendations.append("- El portfolio podría beneficiarse de mayor diversificación")
            
            # Verificar skewness del portfolio
            portfolio_skewness = float(scipy_stats.skew(portfolio_returns.dropna()))
            if portfolio_skewness < -0.5:
                warnings.append(f"⚠️ **Skewness negativo:** {portfolio_skewness:.3f} (riesgo de pérdidas extremas)")
            elif portfolio_skewness > 0.5:
                warnings.append(f"ℹ️ **Skewness positivo:** {portfolio_skewness:.3f} (potencial de ganancias extremas)")
            
            # Verificar kurtosis (colas pesadas)
            portfolio_kurtosis = float(scipy_stats.kurtosis(portfolio_returns.dropna()))
            if portfolio_kurtosis > 3:
                warnings.append(f"⚠️ **Kurtosis alta:** {portfolio_kurtosis:.3f} (colas pesadas, riesgo de eventos extremos)")
            
            if warnings:
                for warning in warnings:
                    report_lines.append(f"- {warning}\n")
            else:
                report_lines.append("- ✅ No se detectaron advertencias significativas\n")
            
            if recommendations:
                report_lines.append("\n### Recomendaciones\n")
                for rec in recommendations:
                    report_lines.append(f"- {rec}\n")
            
            report_lines.append("\n")
        
        # Footer
        report_lines.append("---\n")
        report_lines.append(f"*Reporte generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        report_lines.append("\n**Nota:** Este reporte es informativo y no constituye asesoramiento financiero.")
        report_lines.append("Las simulaciones y análisis están basados en datos históricos y pueden no reflejar resultados futuros.\n")
        
        return "\n".join(report_lines)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcula el máximo drawdown de una serie de retornos"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def _calculate_diversification_ratio(self) -> float:
        """
        Calcula el ratio de diversificación del portfolio
        Ratio = (Suma de volatilidades ponderadas) / (Volatilidad del portfolio)
        Un ratio > 1 indica diversificación efectiva
        """
        if len(self.price_series) == 1:
            return 1.0
        
        # Calcular volatilidades individuales anualizadas
        individual_vols = []
        for ps in self.price_series:
            vol = ps.volatility(annualized=True)
            individual_vols.append(vol)
        
        # Suma ponderada de volatilidades
        weighted_vol_sum = sum(w * vol for w, vol in zip(self.weights, individual_vols))
        
        # Volatilidad del portfolio
        portfolio_returns = self.get_portfolio_returns()
        portfolio_vol = portfolio_returns.std() * np.sqrt(252)
        
        if portfolio_vol == 0:
            return 1.0
        
        diversification_ratio = weighted_vol_sum / portfolio_vol
        return float(diversification_ratio)
    
    def plots_report(self, save_dir: str = "plots") -> None:
        """
        Genera y muestra visualizaciones útiles del portfolio
        
        Args:
            save_dir: Directorio donde guardar los gráficos
        """
        Path(save_dir).mkdir(exist_ok=True)
        
        # Configuración de estilo
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 8)
        
        # 1. Evolución de precios de todos los activos
        fig, ax = plt.subplots(figsize=(14, 6))
        for i, ps in enumerate(self.price_series):
            normalized = ps.close / ps.close.iloc[0] * 100  # Normalizar a 100
            ax.plot(ps.date, normalized, label=f"{self.symbols[i]} ({self.weights[i]*100:.1f}%)", linewidth=2)
        
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Precio Normalizado (Base 100)', fontsize=12)
        ax.set_title('Evolución de Precios Normalizados', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/price_evolution.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        # 2. Retornos diarios del portfolio
        fig, ax = plt.subplots(figsize=(14, 6))
        portfolio_returns = self.get_portfolio_returns()
        ax.plot(portfolio_returns.index, portfolio_returns.values, linewidth=1, alpha=0.7)
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Retorno Diario', fontsize=12)
        ax.set_title('Retornos Diarios del Portfolio', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/daily_returns.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        # 3. Distribución de retornos
        fig, ax = plt.subplots(figsize=(10, 6))
        portfolio_returns = self.get_portfolio_returns()
        ax.hist(portfolio_returns.values, bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(x=portfolio_returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Media: {portfolio_returns.mean():.4f}')
        ax.set_xlabel('Retorno Diario', fontsize=12)
        ax.set_ylabel('Frecuencia', fontsize=12)
        ax.set_title('Distribución de Retornos del Portfolio', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/returns_distribution.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        # 4. Composición del portfolio (pie chart)
        if len(self.symbols) > 1:
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.Set3(np.linspace(0, 1, len(self.symbols)))
            ax.pie(self.weights, labels=self.symbols, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.set_title('Composición del Portfolio', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{save_dir}/portfolio_composition.png", dpi=300, bbox_inches='tight')
            plt.show()
        
        # 5. Matriz de correlación (heatmap)
        if len(self.price_series) > 1:
            fig, ax = plt.subplots(figsize=(10, 8))
            corr_matrix = []
            for i in range(len(self.price_series)):
                row = []
                for j in range(len(self.price_series)):
                    if i == j:
                        row.append(1.0)
                    else:
                        row.append(self.price_series[i].correlation_with(self.price_series[j]))
                corr_matrix.append(row)
            
            corr_df = pd.DataFrame(corr_matrix, index=self.symbols, columns=self.symbols)
            sns.heatmap(corr_df, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                       square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
            ax.set_title('Matriz de Correlación entre Activos', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{save_dir}/correlation_matrix.png", dpi=300, bbox_inches='tight')
            plt.show()
        
        # 6. Drawdown del portfolio
        fig, ax = plt.subplots(figsize=(14, 6))
        portfolio_value = self.get_portfolio_value_series()
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        ax.fill_between(drawdown.index, 0, drawdown.values, alpha=0.3, color='red')
        ax.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Drawdown', fontsize=12)
        ax.set_title('Drawdown del Portfolio', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/drawdown.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\n✅ Todos los gráficos han sido guardados en el directorio '{save_dir}/'")
    
    def monte_carlo_simulation(self,
                               days: int = 252,
                               simulations: int = 1000,
                               initial_value: Optional[float] = None,
                               random_seed: Optional[int] = None,
                               distribution: str = 'normal',
                               drift_override: Optional[float] = None,
                               volatility_override: Optional[float] = None,
                               use_historical_volatility: bool = True,
                               annualized: bool = True) -> pd.DataFrame:
        """
        Simula la evolución del portfolio completo usando método Monte Carlo
        
        Args:
            days: Número de días a simular (252 = 1 año de trading)
            simulations: Número de simulaciones a ejecutar
            initial_value: Valor inicial del portfolio (None = usar valor actual)
            random_seed: Semilla para reproducibilidad
            distribution: Tipo de distribución ('normal', 'student_t', 'lognormal')
            drift_override: Retorno esperado personalizado (anualizado si annualized=True)
            volatility_override: Volatilidad personalizada (anualizada si annualized=True)
            use_historical_volatility: Si True, usa volatilidad histórica cuando no hay override
            annualized: Si True, asume que drift y volatility están anualizados
        
        Returns:
            DataFrame con las simulaciones (columnas = simulaciones, filas = días)
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Obtener estadísticas históricas del portfolio
        portfolio_returns = self.get_portfolio_returns()
        
        if len(portfolio_returns) < 10:
            raise ValueError("No hay suficientes datos históricos para la simulación")
        
        # Calcular drift (retorno esperado)
        if drift_override is not None:
            drift = drift_override
        else:
            # Usar retorno medio histórico
            drift = portfolio_returns.mean() * 252  # Anualizar
        
        # Calcular volatilidad
        if volatility_override is not None:
            volatility = volatility_override
        else:
            if use_historical_volatility:
                volatility = portfolio_returns.std() * np.sqrt(252)  # Anualizar
            else:
                volatility = 0.15  # Default 15%
        
        # Convertir a diario si están anualizados
        if annualized:
            drift_daily = drift / 252
            volatility_daily = volatility / np.sqrt(252)
        else:
            drift_daily = drift
            volatility_daily = volatility
        
        # Obtener valor inicial - normalizar a 100 para que tenga sentido
        if initial_value is None:
            # Usar valor base normalizado (100) para que los resultados sean interpretables
            # Los resultados mostrarán el valor relativo desde el valor inicial
            initial_value = 100.0
        else:
            # Si se proporciona un valor inicial, normalizarlo a 100 para mantener consistencia
            # Guardar el factor de escala para poder convertir de vuelta si es necesario
            portfolio_value = self.get_portfolio_value_series()
            if portfolio_value.iloc[-1] != 0:
                scale_factor = initial_value / portfolio_value.iloc[-1]
                initial_value = 100.0
            else:
                scale_factor = 1.0
                initial_value = 100.0
        
        # Generar simulaciones
        results = []
        
        for sim in range(simulations):
            # Inicializar trayectoria con valor normalizado
            path = [initial_value]
            
            for day in range(1, days + 1):
                # Generar retorno aleatorio según distribución
                if distribution == 'normal':
                    random_return = np.random.normal(drift_daily, volatility_daily)
                elif distribution == 'student_t':
                    # Student-t con grados de libertad = 5 (colas pesadas)
                    df = 5
                    random_return = np.random.standard_t(df) * volatility_daily / np.sqrt(df / (df - 2)) + drift_daily
                elif distribution == 'lognormal':
                    # Log-normal: usar retornos logarítmicos
                    # Para lognormal, el drift debe ser ajustado: mu = drift - 0.5 * sigma^2
                    log_drift = drift_daily - 0.5 * volatility_daily**2
                    log_return = np.random.normal(log_drift, volatility_daily)
                    # Limitar el log_return para evitar overflow
                    log_return = np.clip(log_return, -10, 10)  # exp(10) ≈ 22,000, exp(-10) ≈ 0.00005
                    random_return = np.exp(log_return) - 1
                else:
                    raise ValueError(f"Distribución no soportada: {distribution}")
                
                # Asegurar que el retorno no cause overflow
                if np.isnan(random_return) or np.isinf(random_return):
                    random_return = 0.0
                
                # Calcular nuevo valor usando retorno compuesto
                new_value = path[-1] * (1 + random_return)
                
                # Validar que el nuevo valor sea válido
                if np.isnan(new_value) or np.isinf(new_value) or new_value < 0:
                    # Si hay problema, mantener el valor anterior
                    new_value = path[-1]
                
                path.append(new_value)
            
            results.append(path[1:])  # Excluir valor inicial
        
        # Convertir a DataFrame
        sim_df = pd.DataFrame(results).T
        sim_df.index = range(1, days + 1)  # Días desde 1 hasta days
        
        # Limpiar valores inválidos (NaN, Inf) reemplazándolos con valores anteriores
        sim_df = sim_df.fillna(method='ffill').fillna(method='bfill')
        sim_df = sim_df.replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')
        
        # Si aún hay valores inválidos, reemplazar con el valor inicial
        if sim_df.isna().any().any():
            sim_df = sim_df.fillna(initial_value)
        
        return sim_df
    
    def monte_carlo_individual_assets(self,
                                     days: int = 252,
                                     simulations: int = 1000,
                                     random_seed: Optional[int] = None,
                                     distribution: str = 'normal',
                                     drift_override: Optional[Dict[str, float]] = None,
                                     volatility_override: Optional[Dict[str, float]] = None,
                                     use_correlation: bool = False,
                                     annualized: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Simula la evolución de cada activo individualmente usando Monte Carlo
        
        Args:
            days: Número de días a simular
            simulations: Número de simulaciones
            random_seed: Semilla para reproducibilidad
            distribution: Tipo de distribución
            drift_override: Diccionario con drift por símbolo (ej: {'AAPL': 0.10})
            volatility_override: Diccionario con volatilidad por símbolo
            use_correlation: Si True, incluye correlaciones entre activos (no implementado aún)
            annualized: Si True, asume parámetros anualizados
        
        Returns:
            Diccionario con símbolo como clave y DataFrame de simulaciones como valor
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        results = {}
        
        for i, symbol in enumerate(self.symbols):
            ps = self.price_series[i]
            asset_returns = ps.returns()
            
            if len(asset_returns) < 10:
                print(f"⚠️  Advertencia: {symbol} no tiene suficientes datos, saltando...")
                continue
            
            # Calcular drift
            if drift_override and symbol in drift_override:
                drift = drift_override[symbol]
            else:
                drift = asset_returns.mean() * 252  # Anualizar
            
            # Calcular volatilidad
            if volatility_override and symbol in volatility_override:
                volatility = volatility_override[symbol]
            else:
                volatility = asset_returns.std() * np.sqrt(252)  # Anualizar
            
            # Convertir a diario
            if annualized:
                drift_daily = drift / 252
                volatility_daily = volatility / np.sqrt(252)
            else:
                drift_daily = drift
                volatility_daily = volatility
            
            # Valor inicial - normalizar a 100 para que sea comparable entre activos
            # Guardar el precio real para referencia si es necesario
            real_price = ps.close.iloc[-1]
            initial_value = 100.0
            
            # Generar simulaciones
            asset_results = []
            
            for sim in range(simulations):
                path = [initial_value]
                
                for day in range(1, days + 1):
                    # Generar retorno aleatorio
                    if distribution == 'normal':
                        random_return = np.random.normal(drift_daily, volatility_daily)
                    elif distribution == 'student_t':
                        df = 5
                        random_return = np.random.standard_t(df) * volatility_daily / np.sqrt(df / (df - 2)) + drift_daily
                    elif distribution == 'lognormal':
                        # Log-normal: ajustar drift para lognormal
                        log_drift = drift_daily - 0.5 * volatility_daily**2
                        log_return = np.random.normal(log_drift, volatility_daily)
                        # Limitar el log_return para evitar overflow
                        log_return = np.clip(log_return, -10, 10)
                        random_return = np.exp(log_return) - 1
                    else:
                        raise ValueError(f"Distribución no soportada: {distribution}")
                    
                    # Asegurar que el retorno sea válido
                    if np.isnan(random_return) or np.isinf(random_return):
                        random_return = 0.0
                    
                    new_value = path[-1] * (1 + random_return)
                    
                    # Validar que el nuevo valor sea válido
                    if np.isnan(new_value) or np.isinf(new_value) or new_value < 0:
                        new_value = path[-1]
                    
                    path.append(new_value)
                
                asset_results.append(path[1:])
            
            # Convertir a DataFrame
            sim_df = pd.DataFrame(asset_results).T
            sim_df.index = range(1, days + 1)
            
            # Limpiar valores inválidos
            sim_df = sim_df.fillna(method='ffill').fillna(method='bfill')
            sim_df = sim_df.replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')
            
            # Si aún hay valores inválidos, reemplazar con el valor inicial
            if sim_df.isna().any().any():
                sim_df = sim_df.fillna(initial_value)
            
            results[symbol] = sim_df
        
        return results
    
    def plot_monte_carlo_results(self,
                                 simulation_df: pd.DataFrame,
                                 title: str = "Simulación Monte Carlo",
                                 initial_value: Optional[float] = None,
                                 save_path: Optional[str] = None,
                                 show_confidence_intervals: bool = True,
                                 show_all_paths: bool = True,
                                 confidence_levels: List[float] = [0.05, 0.95],
                                 show_statistics: bool = True) -> None:
        """
        Visualiza los resultados de la simulación Monte Carlo del portfolio completo
        
        Args:
            simulation_df: DataFrame con simulaciones (de monte_carlo_simulation)
            title: Título del gráfico
            initial_value: Valor inicial para referencia
            save_path: Ruta para guardar el gráfico
            show_confidence_intervals: Si True, muestra intervalos de confianza
            show_all_paths: Si True, muestra todas las trayectorias (puede ser lento si hay muchas)
            confidence_levels: Lista de percentiles para intervalos (ej: [0.05, 0.95] = 90% confianza)
            show_statistics: Si True, muestra estadísticas en el gráfico
        """
        Path("plots").mkdir(exist_ok=True)
        
        # Limpiar valores inválidos antes de graficar
        simulation_df = simulation_df.replace([np.inf, -np.inf], np.nan)
        simulation_df = simulation_df.fillna(method='ffill').fillna(method='bfill')
        # Si aún hay NaN, reemplazar con el valor inicial
        if simulation_df.isna().any().any():
            default_init = initial_value if initial_value is not None else 100.0
            simulation_df = simulation_df.fillna(default_init)
        
        # Validar que hay datos válidos
        if simulation_df.empty:
            raise ValueError("No hay datos válidos para graficar")
        
        # Filtrar valores extremos que puedan causar problemas de visualización
        # Mantener solo valores en un rango razonable (0.01 a 10000)
        simulation_df = simulation_df.clip(lower=0.01, upper=10000)
        
        # Crear figura con subplots
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Trayectorias de simulación
        ax1 = fig.add_subplot(gs[0:2, :])
        
        # Mostrar trayectorias (limitado para rendimiento)
        if show_all_paths:
            max_paths = min(100, simulation_df.shape[1])
            for i in range(max_paths):
                ax1.plot(simulation_df.index, simulation_df.iloc[:, i], 
                        alpha=0.1, color='blue', linewidth=0.5)
        
        # Media
        mean_path = simulation_df.mean(axis=1)
        ax1.plot(simulation_df.index, mean_path, 'r-', linewidth=2, label='Media')
        
        # Mediana
        median_path = simulation_df.median(axis=1)
        ax1.plot(simulation_df.index, median_path, 'g-', linewidth=2, label='Mediana')
        
        # Intervalos de confianza
        if show_confidence_intervals:
            for level in confidence_levels:
                percentile = simulation_df.quantile(level, axis=1)
                ax1.plot(simulation_df.index, percentile, 
                        '--', alpha=0.7, linewidth=1.5, 
                        label=f'{int(level*100)}% percentil')
        
        # Valor inicial
        if initial_value is not None:
            ax1.axhline(y=initial_value, color='black', linestyle=':', linewidth=2, label='Valor inicial')
        
        ax1.set_xlabel('Días', fontsize=12)
        ax1.set_ylabel('Valor del Portfolio (Índice, Base 100)', fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 2. Distribución de valores finales
        ax2 = fig.add_subplot(gs[2, 0])
        final_values = simulation_df.iloc[-1].values
        ax2.hist(final_values, bins=50, alpha=0.7, edgecolor='black', color='skyblue')
        ax2.axvline(final_values.mean(), color='red', linestyle='--', linewidth=2, label='Media')
        ax2.axvline(np.median(final_values), color='green', linestyle='--', linewidth=2, label='Mediana')
        if initial_value is not None:
            ax2.axvline(initial_value, color='black', linestyle=':', linewidth=2, label='Inicial')
        ax2.set_xlabel('Valor Final', fontsize=11)
        ax2.set_ylabel('Frecuencia', fontsize=11)
        ax2.set_title('Distribución de Valores Finales', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Estadísticas
        ax3 = fig.add_subplot(gs[2, 1])
        ax3.axis('off')
        
        if show_statistics:
            stats_text = []
            stats_text.append("ESTADÍSTICAS DE SIMULACIÓN")
            stats_text.append("=" * 30)
            stats_text.append(f"Simulaciones: {simulation_df.shape[1]:,}")
            stats_text.append(f"Días simulados: {len(simulation_df)}")
            stats_text.append("")
            stats_text.append("Valores Finales:")
            stats_text.append(f"  Media: ${final_values.mean():,.2f}")
            stats_text.append(f"  Mediana: ${np.median(final_values):,.2f}")
            stats_text.append(f"  Mínimo: ${final_values.min():,.2f}")
            stats_text.append(f"  Máximo: ${final_values.max():,.2f}")
            stats_text.append(f"  Std: ${final_values.std():,.2f}")
            stats_text.append("")
            
            if initial_value is not None:
                returns = (final_values - initial_value) / initial_value
                stats_text.append("Retornos Esperados:")
                stats_text.append(f"  Media: {returns.mean()*100:.2f}%")
                stats_text.append(f"  Mediana: {np.median(returns)*100:.2f}%")
                stats_text.append(f"  Prob. ganancia: {(returns > 0).sum() / len(returns)*100:.1f}%")
            
            stats_str = "\n".join(stats_text)
            ax3.text(0.1, 0.5, stats_str, fontsize=10, family='monospace',
                    verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_monte_carlo_individual(self,
                                   simulation_dict: Dict[str, pd.DataFrame],
                                   save_path: Optional[str] = None,
                                   show_combined: bool = True) -> None:
        """
        Visualiza los resultados de simulaciones Monte Carlo de activos individuales
        
        Args:
            simulation_dict: Diccionario con símbolos como clave y DataFrames de simulaciones como valor
            save_path: Ruta para guardar el gráfico
            show_combined: Si True, muestra todos los activos en un gráfico combinado
        """
        Path("plots").mkdir(exist_ok=True)
        
        if show_combined:
            # Gráfico combinado
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            axes = axes.flatten()
            
            # Gráfico 1: Trayectorias medias
            ax = axes[0]
            colors = plt.cm.tab10(np.linspace(0, 1, len(simulation_dict)))
            for i, (symbol, sim_df) in enumerate(simulation_dict.items()):
                mean_path = sim_df.mean(axis=1)
                ax.plot(sim_df.index, mean_path, label=symbol, linewidth=2, color=colors[i])
            ax.set_xlabel('Días', fontsize=12)
            ax.set_ylabel('Valor (Índice, Base 100)', fontsize=12)
            ax.set_title('Trayectorias Medias por Activo', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Gráfico 2: Distribuciones de valores finales
            ax = axes[1]
            for i, (symbol, sim_df) in enumerate(simulation_dict.items()):
                final_values = sim_df.iloc[-1].values
                ax.hist(final_values, bins=30, alpha=0.5, label=symbol, color=colors[i])
            ax.set_xlabel('Valor Final', fontsize=12)
            ax.set_ylabel('Frecuencia', fontsize=12)
            ax.set_title('Distribuciones de Valores Finales', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Gráfico 3: Estadísticas comparativas
            ax = axes[2]
            symbols_list = list(simulation_dict.keys())
            means = [sim_df.iloc[-1].mean() for sim_df in simulation_dict.values()]
            medians = [sim_df.iloc[-1].median() for sim_df in simulation_dict.values()]
            x = np.arange(len(symbols_list))
            width = 0.35
            ax.bar(x - width/2, means, width, label='Media', alpha=0.8)
            ax.bar(x + width/2, medians, width, label='Mediana', alpha=0.8)
            ax.set_xlabel('Activo', fontsize=12)
            ax.set_ylabel('Valor Final Esperado', fontsize=12)
            ax.set_title('Comparación de Valores Finales', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(symbols_list)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            # Gráfico 4: Retornos esperados
            ax = axes[3]
            returns_list = []
            for symbol, sim_df in simulation_dict.items():
                initial = sim_df.iloc[0, 0]  # Valor inicial aproximado
                final_values = sim_df.iloc[-1].values
                returns = (final_values - initial) / initial
                returns_list.append(returns.mean() * 100)
            
            ax.barh(symbols_list, returns_list, alpha=0.7)
            ax.set_xlabel('Retorno Esperado (%)', fontsize=12)
            ax.set_title('Retornos Esperados por Activo', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.show()
        else:
            # Gráficos individuales
            n_assets = len(simulation_dict)
            fig, axes = plt.subplots(n_assets, 1, figsize=(14, 4 * n_assets))
            if n_assets == 1:
                axes = [axes]
            
            for i, (symbol, sim_df) in enumerate(simulation_dict.items()):
                ax = axes[i]
                
                # Mostrar algunas trayectorias
                max_paths = min(50, sim_df.shape[1])
                for j in range(max_paths):
                    ax.plot(sim_df.index, sim_df.iloc[:, j], alpha=0.1, color='blue', linewidth=0.5)
                
                # Media y mediana
                mean_path = sim_df.mean(axis=1)
                median_path = sim_df.median(axis=1)
                ax.plot(sim_df.index, mean_path, 'r-', linewidth=2, label='Media')
                ax.plot(sim_df.index, median_path, 'g-', linewidth=2, label='Mediana')
                
                # Intervalos de confianza
                p5 = sim_df.quantile(0.05, axis=1)
                p95 = sim_df.quantile(0.95, axis=1)
                ax.fill_between(sim_df.index, p5, p95, alpha=0.2, color='gray', label='90% CI')
                
                ax.set_xlabel('Días', fontsize=12)
                ax.set_ylabel('Valor (Índice, Base 100)', fontsize=12)
                ax.set_title(f'{symbol} - Simulación Monte Carlo', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.show()
    
    def run_and_plot_monte_carlo(self,
                                 days: int = 252,
                                 simulations: int = 1000,
                                 save_path: Optional[str] = None,
                                 **kwargs) -> pd.DataFrame:
        """
        Método auxiliar: ejecuta simulación y visualiza en un solo paso
        
        Args:
            days: Días a simular
            simulations: Número de simulaciones
            save_path: Ruta para guardar gráfico
            **kwargs: Argumentos adicionales para monte_carlo_simulation
        
        Returns:
            DataFrame con simulaciones
        """
        sim_df = self.monte_carlo_simulation(days=days, simulations=simulations, **kwargs)
        # Usar valor inicial normalizado (100) para consistencia
        initial_value = 100.0
        self.plot_monte_carlo_results(sim_df, initial_value=initial_value, save_path=save_path)
        return sim_df
    
    def run_and_plot_monte_carlo_individual(self,
                                           days: int = 252,
                                           simulations: int = 1000,
                                           save_path: Optional[str] = None,
                                           **kwargs) -> Dict[str, pd.DataFrame]:
        """
        Método auxiliar: ejecuta simulaciones individuales y visualiza en un solo paso
        
        Args:
            days: Días a simular
            simulations: Número de simulaciones
            save_path: Ruta para guardar gráfico
            **kwargs: Argumentos adicionales para monte_carlo_individual_assets
        
        Returns:
            Diccionario con simulaciones por activo
        """
        sim_dict = self.monte_carlo_individual_assets(days=days, simulations=simulations, **kwargs)
        self.plot_monte_carlo_individual(sim_dict, save_path=save_path, show_combined=True)
        return sim_dict

