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
        # Validar que symbols y price_series tengan la misma longitud
        if len(self.symbols) != len(self.price_series):
            print(f"⚠️  ADVERTENCIA CRÍTICA: Número de símbolos ({len(self.symbols)}) no coincide con número de series ({len(self.price_series)})")
            print(f"   Símbolos: {self.symbols}")
            print(f"   Series: {len(self.price_series)} series")
            # Ajustar para que coincidan - usar el mínimo
            n_assets = min(len(self.symbols), len(self.price_series))
            self.symbols = self.symbols[:n_assets]
            self.price_series = self.price_series[:n_assets]
            print(f"   Ajustado a {n_assets} activos")
        
        if self.weights is None:
            # Si no se especifican pesos, distribuir equitativamente
            self.weights = [1.0 / len(self.price_series)] * len(self.price_series)
        
        # Validar que weights tenga la misma longitud que price_series
        if len(self.weights) != len(self.price_series):
            print(f"⚠️  ADVERTENCIA: Número de pesos ({len(self.weights)}) no coincide con número de series ({len(self.price_series)})")
            if len(self.weights) < len(self.price_series):
                # Agregar pesos equitativos para las series faltantes
                missing = len(self.price_series) - len(self.weights)
                equal_weight = 1.0 / len(self.price_series)
                self.weights.extend([equal_weight] * missing)
                print(f"   Agregados {missing} pesos equitativos")
            else:
                # Usar solo los primeros N pesos
                self.weights = self.weights[:len(self.price_series)]
                print(f"   Usando solo los primeros {len(self.price_series)} pesos")
        
        # Normalizar pesos para que sumen 1.0
        total_weight = sum(self.weights)
        if abs(total_weight - 1.0) > 0.01:  # Tolerancia pequeña
            self.weights = [w / total_weight for w in self.weights]
        
        # Validación final
        if len(self.symbols) != len(self.price_series) or len(self.price_series) != len(self.weights):
            raise ValueError(f"Error de alineación: symbols={len(self.symbols)}, price_series={len(self.price_series)}, weights={len(self.weights)}")
    
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
        
        # Calcular valor actual del portfolio de manera correcta
        if len(portfolio_value) > 0:
            current_value = float(portfolio_value.iloc[-1])
        else:
            current_value = 0.0
        
        # Mostrar composición con valores normalizados (para índices con valores enormes)
        for i, symbol in enumerate(self.symbols):
            ps = self.price_series[i]
            weight = self.weights[i]
            asset_price = float(ps.close.iloc[-1])
            
            # Calcular valor aportado al portfolio (precio * peso)
            # Para índices con valores enormes, mostrar el precio pero el valor aportado es proporcional
            asset_contribution = current_value * weight if current_value > 0 else 0.0
            
            report_lines.append(f"| {symbol} | {weight*100:.2f}% | ${asset_price:.2f} |")
        
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
        
        # Obtener retornos del portfolio y limpiarlos
        portfolio_returns = self.get_portfolio_returns()
        
        # Limpiar retornos: eliminar NaN, infinitos y valores extremos
        portfolio_returns_clean = portfolio_returns.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Inicializar variables para uso en advertencias
        mean_daily_return = 0.0
        std_daily_return = 0.0
        portfolio_annual_return = 0.0
        portfolio_volatility = 0.0
        portfolio_sharpe = 0.0
        
        # Validar que tenemos suficientes datos
        if len(portfolio_returns_clean) < 10:
            report_lines.append("⚠️ **Advertencia:** Insuficientes datos para calcular estadísticas del portfolio\n")
        else:
            # Calcular estadísticas básicas sobre retornos limpios
            mean_daily_return = float(portfolio_returns_clean.mean())
            std_daily_return = float(portfolio_returns_clean.std())
            
            # RETORNO ANUALIZADO - CÁLCULO CORRECTO DESDE CERO
            # Usar log retornos para mayor precisión y evitar problemas con valores extremos
            # Log retorno anualizado = exp(mean(log(1 + r)) * 252) - 1
            # Pero si hay valores negativos grandes, usar método compuesto directo
            portfolio_value_series = self.get_portfolio_value_series()
            if len(portfolio_value_series) > 1:
                # Método más robusto: calcular retorno anualizado desde valores del portfolio
                initial_val = float(portfolio_value_series.iloc[0])
                final_val = float(portfolio_value_series.iloc[-1])
                if initial_val > 0 and final_val > 0:
                    # Calcular número de días de trading
                    n_days = len(portfolio_value_series)
                    # Retorno total del período
                    total_return = (final_val / initial_val) - 1
                    # Retorno anualizado usando capitalización compuesta
                    # (1 + r_anual)^(n_days/252) = 1 + r_total
                    if total_return > -1:  # Evitar log de negativo
                        portfolio_annual_return = (1 + total_return) ** (252.0 / n_days) - 1
                    else:
                        # Si hay pérdida total, usar aproximación
                        portfolio_annual_return = total_return * (252.0 / n_days)
                else:
                    # Fallback: usar retorno diario medio compuesto
                    if mean_daily_return > -1:  # Evitar problemas con valores extremos
                        portfolio_annual_return = (1 + mean_daily_return) ** 252 - 1
                    else:
                        portfolio_annual_return = mean_daily_return * 252
            else:
                # Fallback: usar retorno diario medio compuesto
                if mean_daily_return > -1:  # Evitar problemas con valores extremos
                    portfolio_annual_return = (1 + mean_daily_return) ** 252 - 1
                else:
                    portfolio_annual_return = mean_daily_return * 252
            
            # VOLATILIDAD ANUALIZADA - CÁLCULO CORRECTO DESDE CERO
            # Volatilidad anualizada = desviación estándar diaria * sqrt(252)
            portfolio_volatility = std_daily_return * np.sqrt(252)
            
            # SHARPE RATIO - CÁLCULO CORRECTO DESDE CERO
            # Sharpe = (Retorno anualizado - Tasa libre de riesgo) / Volatilidad anualizada
            excess_return = portfolio_annual_return - risk_free_rate
            if portfolio_volatility > 1e-10:  # Evitar división por cero
                portfolio_sharpe = excess_return / portfolio_volatility
            else:
                portfolio_sharpe = 0.0
            
            report_lines.append(f"- **Retorno medio anualizado:** {portfolio_annual_return*100:.2f}%")
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
        
        # Calcular métricas adicionales usando datos limpios
        portfolio_value_series = self.get_portfolio_value_series()
        
        # RETORNO TOTAL DEL PERÍODO - CORRECTO
        if len(portfolio_value_series) > 1:
            initial_value = float(portfolio_value_series.iloc[0])
            final_value = float(portfolio_value_series.iloc[-1])
            if initial_value > 0:
                total_return_portfolio = (final_value / initial_value - 1) * 100
            else:
                total_return_portfolio = 0.0
        else:
            total_return_portfolio = 0.0
        
        # MÁXIMO DRAWDOWN - CORRECTO (sobre serie de valores, no retornos)
        max_dd = self._calculate_max_drawdown_from_values(portfolio_value_series)
        
        # VALUE AT RISK Y CONDITIONAL VaR - CORRECTOS
        if len(portfolio_returns_clean) > 0:
            var_95 = float(np.percentile(portfolio_returns_clean, 5)) * 100  # Value at Risk 95%
            var_threshold = np.percentile(portfolio_returns_clean, 5)
            cvar_95_data = portfolio_returns_clean[portfolio_returns_clean <= var_threshold]
            if len(cvar_95_data) > 0:
                cvar_95 = float(cvar_95_data.mean()) * 100  # Conditional VaR
            else:
                cvar_95 = var_95
        else:
            var_95 = 0.0
            cvar_95 = 0.0
        
        # CORRELACIÓN PROMEDIO - CORRECTA
        avg_correlation = 0.0
        if len(self.price_series) > 1:
            correlations = []
            for i in range(len(self.price_series)):
                for j in range(i+1, len(self.price_series)):
                    try:
                        corr = self.price_series[i].correlation_with(self.price_series[j])
                        if not np.isnan(corr) and not np.isinf(corr):
                            correlations.append(corr)
                    except:
                        pass
            if correlations:
                avg_correlation = float(np.mean(correlations))
        
        # SKEWNESS Y KURTOSIS - CORRECTOS
        if len(portfolio_returns_clean) > 10:
            portfolio_skewness = float(scipy_stats.skew(portfolio_returns_clean))
            portfolio_kurtosis = float(scipy_stats.kurtosis(portfolio_returns_clean))
        else:
            portfolio_skewness = 0.0
            portfolio_kurtosis = 0.0
        
        # DIVERSIFICACIÓN - CORRECTA
        diversification_ratio = self._calculate_diversification_ratio()
        
        report_lines.append(f"- **Retorno total del período:** {total_return_portfolio:.2f}%")
        report_lines.append(f"- **Máximo Drawdown:** {max_dd*100:.2f}%")
        report_lines.append(f"- **Value at Risk (95%):** {var_95:.2f}%")
        report_lines.append(f"- **Conditional VaR (95%):** {cvar_95:.2f}%")
        report_lines.append(f"- **Skewness:** {portfolio_skewness:.3f}")
        report_lines.append(f"- **Kurtosis:** {portfolio_kurtosis:.3f}")
        report_lines.append(f"- **Correlación promedio entre activos:** {avg_correlation:.3f}")
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
            
            # Verificar volatilidad (usar valores calculados correctamente, sin límites artificiales)
            if len(portfolio_returns_clean) > 10:
                portfolio_volatility_check = std_daily_return * np.sqrt(252)
                
                if portfolio_volatility_check > 0.30:  # Más de 30% anual
                    warnings.append(f"⚠️ **Alta volatilidad:** El portfolio tiene volatilidad anualizada de {portfolio_volatility_check*100:.1f}%")
                    recommendations.append("- Considerar reducir la exposición a activos volátiles o agregar activos defensivos")
                elif portfolio_volatility_check < 0.10:  # Menos de 10% anual
                    warnings.append(f"ℹ️ **Baja volatilidad:** El portfolio tiene volatilidad anualizada de {portfolio_volatility_check*100:.1f}% (conservador)")
                
                # Verificar Sharpe ratio (usar valores calculados correctamente, sin límites artificiales)
                # Usar el mismo método que en el cálculo principal
                portfolio_value_series_check = self.get_portfolio_value_series()
                if len(portfolio_value_series_check) > 1:
                    initial_val_check = float(portfolio_value_series_check.iloc[0])
                    final_val_check = float(portfolio_value_series_check.iloc[-1])
                    if initial_val_check > 0 and final_val_check > 0:
                        n_days_check = len(portfolio_value_series_check)
                        total_return_check = (final_val_check / initial_val_check) - 1
                        if total_return_check > -1:
                            portfolio_annual_return_check = (1 + total_return_check) ** (252.0 / n_days_check) - 1
                        else:
                            portfolio_annual_return_check = total_return_check * (252.0 / n_days_check)
                    else:
                        if mean_daily_return > -1:
                            portfolio_annual_return_check = (1 + mean_daily_return) ** 252 - 1
                        else:
                            portfolio_annual_return_check = mean_daily_return * 252
                else:
                    if mean_daily_return > -1:
                        portfolio_annual_return_check = (1 + mean_daily_return) ** 252 - 1
                    else:
                        portfolio_annual_return_check = mean_daily_return * 252
                
                excess_return_check = portfolio_annual_return_check - risk_free_rate
                portfolio_sharpe_check = excess_return_check / portfolio_volatility_check if portfolio_volatility_check > 1e-10 else 0.0
                
                if portfolio_sharpe_check < 0.5:
                    warnings.append(f"⚠️ **Bajo ratio de Sharpe:** {portfolio_sharpe_check:.3f} (considerar revisar la composición)")
                    recommendations.append("- El ratio de Sharpe bajo indica que el retorno no compensa adecuadamente el riesgo asumido")
                elif portfolio_sharpe_check > 1.5:
                    warnings.append(f"✅ **Excelente ratio de Sharpe:** {portfolio_sharpe_check:.3f} (buen balance riesgo/retorno)")
                elif portfolio_sharpe_check > 1.0:
                    warnings.append(f"✅ **Buen ratio de Sharpe:** {portfolio_sharpe_check:.3f}")
            
            # Verificar drawdown
            if max_dd < -0.20:  # Más de 20% de drawdown
                warnings.append(f"⚠️ **Drawdown significativo:** Máximo drawdown de {max_dd*100:.1f}%")
                recommendations.append("- Considerar estrategias de gestión de riesgo o stop-loss")
            elif max_dd < -0.10:  # Entre 10% y 20%
                warnings.append(f"ℹ️ **Drawdown moderado:** Máximo drawdown de {max_dd*100:.1f}%")
            
            # Verificar diversificación
            if diversification_ratio < 0.5:
                warnings.append(f"⚠️ **Baja diversificación:** Ratio de diversificación de {diversification_ratio:.3f}")
                recommendations.append("- El portfolio podría beneficiarse de mayor diversificación")
            elif diversification_ratio > 1.2:
                warnings.append(f"✅ **Buena diversificación:** Ratio de diversificación de {diversification_ratio:.3f}")
            
            # Verificar skewness del portfolio (ya calculado arriba)
            if portfolio_skewness < -0.5:
                warnings.append(f"⚠️ **Skewness negativo:** {portfolio_skewness:.3f} (riesgo de pérdidas extremas)")
                recommendations.append("- El skewness negativo indica mayor probabilidad de pérdidas extremas que ganancias extremas")
            elif portfolio_skewness > 0.5:
                warnings.append(f"ℹ️ **Skewness positivo:** {portfolio_skewness:.3f} (potencial de ganancias extremas)")
            
            # Verificar kurtosis (colas pesadas) - ya calculado arriba
            # Kurtosis normal = 0 (exceso de kurtosis), > 3 indica colas pesadas
            if portfolio_kurtosis > 3:
                warnings.append(f"⚠️ **Kurtosis alta:** {portfolio_kurtosis:.3f} (colas pesadas, riesgo de eventos extremos)")
                recommendations.append("- La alta kurtosis indica mayor probabilidad de eventos extremos (black swans)")
            elif portfolio_kurtosis < -1:
                warnings.append(f"ℹ️ **Kurtosis baja:** {portfolio_kurtosis:.3f} (distribución más plana de lo normal)")
            
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
        if len(returns) == 0:
            return 0.0
        
        # Limpiar retornos
        returns_clean = returns.replace([np.inf, -np.inf], np.nan).dropna()
        if len(returns_clean) == 0:
            return 0.0
        
        cumulative = (1 + returns_clean).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def _calculate_max_drawdown_from_values(self, values: pd.Series) -> float:
        """Calcula el máximo drawdown directamente de una serie de valores"""
        if len(values) == 0:
            return 0.0
        
        # Limpiar valores
        values_clean = values.replace([np.inf, -np.inf], np.nan).dropna()
        if len(values_clean) == 0:
            return 0.0
        
        # Convertir a array numpy para mejor rendimiento
        values_array = values_clean.values
        
        # Calcular running maximum
        running_max = np.maximum.accumulate(values_array)
        
        # Calcular drawdown
        drawdown = (values_array - running_max) / running_max
        
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
        # Asegurar que siempre se muestren todos los activos
        if len(self.symbols) > 0:
            fig, ax = plt.subplots(figsize=(10, 8))
            # Asegurar que tenemos el mismo número de colores que de símbolos
            colors = plt.cm.Set3(np.linspace(0, 1, len(self.symbols)))
            # Validar que weights y symbols tengan la misma longitud
            if len(self.weights) != len(self.symbols):
                print(f"⚠️  Advertencia: Número de pesos ({len(self.weights)}) no coincide con número de símbolos ({len(self.symbols)})")
                # Ajustar pesos si es necesario
                if len(self.weights) < len(self.symbols):
                    # Agregar pesos equitativos para los símbolos faltantes
                    missing = len(self.symbols) - len(self.weights)
                    equal_weight = 1.0 / len(self.symbols)
                    self.weights.extend([equal_weight] * missing)
                else:
                    # Usar solo los primeros N pesos
                    self.weights = self.weights[:len(self.symbols)]
                # Normalizar pesos
                total = sum(self.weights)
                if total > 0:
                    self.weights = [w / total for w in self.weights]
            
            ax.pie(self.weights, labels=self.symbols, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.set_title(f'Composición del Portfolio ({len(self.symbols)} activos)', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{save_dir}/portfolio_composition.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 5. Matriz de correlación (heatmap)
        # Asegurar que siempre se muestren todos los activos
        if len(self.price_series) > 1 and len(self.symbols) > 1:
            fig, ax = plt.subplots(figsize=(max(10, len(self.symbols) * 1.2), max(8, len(self.symbols) * 1.2)))
            corr_matrix = []
            # Validar que price_series y symbols tengan la misma longitud
            n_assets = min(len(self.price_series), len(self.symbols))
            symbols_to_use = self.symbols[:n_assets]
            
            for i in range(n_assets):
                row = []
                for j in range(n_assets):
                    if i == j:
                        row.append(1.0)
                    else:
                        try:
                            corr = self.price_series[i].correlation_with(self.price_series[j])
                            row.append(corr)
                        except Exception as e:
                            print(f"⚠️  Advertencia: Error calculando correlación entre {symbols_to_use[i]} y {symbols_to_use[j]}: {e}")
                            row.append(0.0)
                corr_matrix.append(row)
            
            corr_df = pd.DataFrame(corr_matrix, index=symbols_to_use, columns=symbols_to_use)
            sns.heatmap(corr_df, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                       square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax,
                       xticklabels=symbols_to_use, yticklabels=symbols_to_use)
            ax.set_title(f'Matriz de Correlación entre Activos ({len(symbols_to_use)} activos)', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{save_dir}/correlation_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
        elif len(self.price_series) == 1:
            print("⚠️  Solo hay 1 activo en el portfolio, no se puede generar matriz de correlación")
        
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
                               years: int = 10,
                               simulations: int = 10000,
                               initial_value: Optional[float] = None,
                               random_seed: Optional[int] = None,
                               rebalance: bool = True,
                               rebalance_frequency: str = 'monthly',
                               inflation_rate: Optional[float] = None) -> pd.DataFrame:
        """
        Simulación Monte Carlo estilo Portfolio Visualizer
        Usa movimiento geométrico Browniano con correlación entre activos y reequilibrio opcional.
        
        Args:
            years: Número de años a simular (por defecto 10 años)
            simulations: Número de simulaciones (por defecto 10,000)
            initial_value: Valor inicial del portfolio (None = usar valor actual)
            random_seed: Semilla para reproducibilidad
            rebalance: Si True, reequilibra el portfolio periódicamente (por defecto True)
            rebalance_frequency: Frecuencia de reequilibrio ('monthly', 'quarterly', 'yearly')
            inflation_rate: Tasa de inflación anual (None = sin ajuste por inflación)
        
        Returns:
            DataFrame con las simulaciones (columnas = simulaciones, filas = meses)
            El índice representa meses desde 0 hasta years*12
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Validar datos históricos
        portfolio_returns = self.get_portfolio_returns()
        if len(portfolio_returns) < 30:
            raise ValueError("Se requieren al menos 30 días de datos históricos para la simulación")
        
        # Obtener valor inicial
        portfolio_value = self.get_portfolio_value_series()
        if initial_value is None:
            initial_value = float(portfolio_value.iloc[-1]) if len(portfolio_value) > 0 else 100000.0
        else:
            initial_value = float(initial_value)
        
        # Calcular estadísticas de cada activo
        n_assets = len(self.price_series)
        months = years * 12
        
        # Calcular retornos y volatilidades anualizadas por activo
        asset_returns_list = []
        asset_vols = []
        initial_prices = []
        
        for ps in self.price_series:
            asset_returns = ps.returns().dropna()
            if len(asset_returns) < 30:
                # Si no hay suficientes datos, usar valores por defecto
                asset_returns_list.append(pd.Series([0.0] * 30))
                asset_vols.append(0.15)  # 15% volatilidad por defecto
            else:
                # Limpiar retornos: eliminar valores extremos (outliers)
                # Usar percentiles 1% y 99% para filtrar outliers extremos
                q1 = asset_returns.quantile(0.01)
                q99 = asset_returns.quantile(0.99)
                cleaned_returns = asset_returns[(asset_returns >= q1) & (asset_returns <= q99)]
                
                # Si después de limpiar hay muy pocos datos, usar todos
                if len(cleaned_returns) < 30:
                    cleaned_returns = asset_returns
                
                asset_returns_list.append(asset_returns)  # Guardar retornos originales para correlación
                
                # Volatilidad anualizada usando retornos limpios - CÁLCULO CORRECTO SIN LÍMITES
                # Volatilidad anualizada = desviación estándar diaria * sqrt(252)
                vol_annual = cleaned_returns.std() * np.sqrt(252)
                
                # Asegurar que la volatilidad sea positiva (no puede ser negativa)
                if vol_annual < 0:
                    vol_annual = abs(vol_annual)
                # Si es cero o muy pequeña, usar un valor mínimo razonable basado en los datos
                if vol_annual < 1e-6:
                    # Si la volatilidad calculada es prácticamente cero, usar la volatilidad de los retornos originales
                    vol_annual = asset_returns.std() * np.sqrt(252)
                    if vol_annual < 1e-6:
                        vol_annual = 0.15  # 15% por defecto solo si realmente no hay datos
                
                asset_vols.append(vol_annual)
            initial_prices.append(float(ps.close.iloc[-1]) if len(ps.close) > 0 else 100.0)
        
        # Calcular matriz de correlación
        if n_assets > 1:
            # Alinear todas las series de retornos por fecha
            aligned_returns = {}
            min_date = None
            max_date = None
            
            for i, ret_series in enumerate(asset_returns_list):
                if len(ret_series) > 0:
                    aligned_returns[i] = ret_series
                    if min_date is None or ret_series.index.min() > min_date:
                        min_date = ret_series.index.min()
                    if max_date is None or ret_series.index.max() < max_date:
                        max_date = ret_series.index.max()
            
            # Crear DataFrame con retornos alineados
            returns_df = pd.DataFrame(aligned_returns)
            returns_df = returns_df.dropna()
            
            if len(returns_df) > 30:
                correlation_matrix = returns_df.corr().values
                # Asegurar que la matriz sea positiva definida
                try:
                    np.linalg.cholesky(correlation_matrix)
                except np.linalg.LinAlgError:
                    # Si no es positiva definida, usar identidad
                    correlation_matrix = np.eye(n_assets)
            else:
                correlation_matrix = np.eye(n_assets)
        else:
            correlation_matrix = np.eye(1)
        
        # Calcular retornos medios anualizados por activo
        asset_means = []
        for ret_series in asset_returns_list:
            if len(ret_series) > 0:
                mean_annual = ret_series.mean() * 252
                asset_means.append(mean_annual)
            else:
                asset_means.append(0.08)  # 8% por defecto
        
        # Convertir a retornos y volatilidades mensuales
        asset_means_monthly = [mu / 12 for mu in asset_means]
        asset_vols_monthly = [vol / np.sqrt(12) for vol in asset_vols]
        
        # Ajustar por inflación si se especifica
        if inflation_rate is not None:
            inflation_monthly = inflation_rate / 12
            # Restar inflación de los retornos esperados (retornos reales)
            asset_means_monthly = [mu - inflation_monthly for mu in asset_means_monthly]
        
        # Calcular matriz de covarianza mensual
        if n_assets > 1:
            cov_matrix_monthly = np.zeros((n_assets, n_assets))
            for i in range(n_assets):
                for j in range(n_assets):
                    if i == j:
                        cov_matrix_monthly[i, j] = asset_vols_monthly[i] ** 2
                    else:
                        cov_matrix_monthly[i, j] = (correlation_matrix[i, j] * 
                                                     asset_vols_monthly[i] * 
                                                     asset_vols_monthly[j])
        else:
            cov_matrix_monthly = np.array([[asset_vols_monthly[0] ** 2]])
        
        # Decomposición de Cholesky para generar retornos correlacionados
        try:
            L = np.linalg.cholesky(cov_matrix_monthly)
        except np.linalg.LinAlgError:
            # Si falla, usar diagonal
            L = np.diag(asset_vols_monthly)
        
        # Pesos iniciales
        initial_weights = np.array(self.weights)
        
        # Generar simulaciones
        results = []
        means_monthly = np.array(asset_means_monthly)
        
        for sim in range(simulations):
            # Inicializar valores de activos proporcionales a los pesos
            total_initial_value = sum([initial_prices[j] * initial_weights[j] for j in range(n_assets)])
            if total_initial_value > 0:
                asset_values = np.array([initial_prices[i] * initial_weights[i] * initial_value / total_initial_value
                                       for i in range(n_assets)])
            else:
                # Si no hay precios válidos, distribuir equitativamente
                asset_values = np.array([initial_value * initial_weights[i] for i in range(n_assets)])
            
            path = [initial_value]
            
            for month in range(1, months + 1):
                # Generar shocks aleatorios correlacionados
                z = np.random.normal(0, 1, n_assets)
                correlated_shocks = L @ z
                
                # Calcular retornos mensuales para cada activo - CÁLCULO CORRECTO SIN CLIPPING
                # Retorno mensual = media mensual + shock correlacionado
                monthly_returns = means_monthly + correlated_shocks
                
                # No limitar retornos artificialmente - permitir que la simulación refleje la realidad
                # Si los datos históricos tienen alta volatilidad, la simulación debe reflejarlo
                # Solo asegurar que no haya valores infinitos o NaN
                monthly_returns = np.where(np.isfinite(monthly_returns), monthly_returns, 0.0)
                
                # Actualizar valores de activos
                # Asegurar que los valores no se vuelvan negativos (no puede haber valores negativos)
                asset_values = asset_values * (1 + monthly_returns)
                asset_values = np.maximum(asset_values, 0.0)  # Solo asegurar no negativos, no limitar retornos
                
                # Valor del portfolio
                portfolio_value_month = asset_values.sum()
                
                # Reequilibrio si está habilitado
                if rebalance:
                    should_rebalance = False
                    if rebalance_frequency == 'monthly':
                        should_rebalance = True
                    elif rebalance_frequency == 'quarterly':
                        should_rebalance = (month % 3 == 0)
                    elif rebalance_frequency == 'yearly':
                        should_rebalance = (month % 12 == 0)
                    
                    if should_rebalance:
                        # Reequilibrar: ajustar valores para mantener pesos iniciales
                        target_values = portfolio_value_month * initial_weights
                        asset_values = target_values
                
                path.append(portfolio_value_month)
            
            results.append(path[1:])  # Excluir valor inicial
        
        # Convertir a DataFrame
        sim_df = pd.DataFrame(results).T
        sim_df.index = range(months)  # Meses desde 0 hasta months-1
        
        # Limpiar valores inválidos
        sim_df = sim_df.replace([np.inf, -np.inf], np.nan)
        sim_df = sim_df.ffill().bfill()
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
                        # No limitar artificialmente - solo verificar valores finitos
                        if not np.isfinite(log_return):
                            log_return = 0.0
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
            sim_df = sim_df.ffill().bfill()
            sim_df = sim_df.replace([np.inf, -np.inf], np.nan).ffill().bfill()
            
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
        simulation_df = simulation_df.ffill().bfill()
        # Si aún hay NaN, reemplazar con el valor inicial
        if simulation_df.isna().any().any():
            default_init = initial_value if initial_value is not None else 100.0
            simulation_df = simulation_df.fillna(default_init)
        
        # Validar que hay datos válidos
        if simulation_df.empty:
            raise ValueError("No hay datos válidos para graficar")
        
        # Limpiar valores infinitos o NaN para visualización, pero no limitar valores reales
        # Solo reemplazar infinitos y NaN, no limitar valores válidos
        simulation_df = simulation_df.replace([np.inf, -np.inf], np.nan)
        # Rellenar NaN con forward fill y backward fill, pero mantener valores reales
        simulation_df = simulation_df.ffill().bfill()
        # Solo asegurar que no haya valores negativos (no tiene sentido financiero)
        simulation_df = simulation_df.clip(lower=0.0)
        
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
    
    def calculate_monte_carlo_probabilities(self,
                                           simulation_df: pd.DataFrame,
                                           initial_value: float,
                                           target_value: Optional[float] = None,
                                           target_return: Optional[float] = None) -> Dict[str, float]:
        """
        Calcula probabilidades basadas en los resultados de Monte Carlo
        
        Args:
            simulation_df: DataFrame con simulaciones
            initial_value: Valor inicial del portfolio
            target_value: Valor objetivo absoluto (si se especifica, se usa en lugar de target_return)
            target_return: Retorno objetivo (ej: 0.5 = 50% de retorno)
        
        Returns:
            Diccionario con probabilidades calculadas
        """
        final_values = simulation_df.iloc[-1].values
        
        # Calcular retornos
        returns = (final_values - initial_value) / initial_value
        
        # Probabilidad de pérdida
        prob_loss = (returns < 0).sum() / len(returns)
        
        # Probabilidad de ganancia
        prob_gain = (returns > 0).sum() / len(returns)
        
        # Determinar objetivo
        if target_value is not None:
            target = target_value
        elif target_return is not None:
            target = initial_value * (1 + target_return)
        else:
            target = None
        
        # Probabilidad de alcanzar objetivo
        prob_reach_target = None
        if target is not None:
            prob_reach_target = (final_values >= target).sum() / len(final_values)
        
        # Percentiles
        percentiles = {
            'p5': np.percentile(final_values, 5),
            'p25': np.percentile(final_values, 25),
            'p50': np.percentile(final_values, 50),  # Mediana
            'p75': np.percentile(final_values, 75),
            'p95': np.percentile(final_values, 95)
        }
        
        # Percentiles de retorno
        return_percentiles = {
            'p5': np.percentile(returns, 5) * 100,
            'p50': np.percentile(returns, 50) * 100,
            'p95': np.percentile(returns, 95) * 100
        }
        
        results = {
            'prob_loss': prob_loss,
            'prob_gain': prob_gain,
            'prob_reach_target': prob_reach_target,
            'expected_value': final_values.mean(),
            'median_value': np.median(final_values),
            'expected_return': returns.mean() * 100,
            'median_return': np.median(returns) * 100,
            'percentiles': percentiles,
            'return_percentiles': return_percentiles
        }
        
        return results
    
    def plot_monte_carlo_enhanced(self,
                                 simulation_df: pd.DataFrame,
                                 initial_value: float,
                                 title: str = "Simulación Monte Carlo - Portfolio",
                                 save_path: Optional[str] = None,
                                 view_type: str = 'relative',
                                 show_fan_chart: bool = True,
                                 show_histogram: bool = True,
                                 show_percentiles: bool = True,
                                 target_value: Optional[float] = None) -> None:
        """
        Visualización mejorada de Monte Carlo con características de Wallible
        Incluye fan chart, histograma de resultados a 10 años, y percentiles
        
        Args:
            simulation_df: DataFrame con simulaciones
            initial_value: Valor inicial del portfolio
            title: Título del gráfico
            save_path: Ruta para guardar el gráfico
            view_type: 'relative' (porcentajes) o 'absolute' (valores absolutos)
            show_fan_chart: Si True, muestra gráfico tipo abanico (fan chart)
            show_histogram: Si True, muestra histograma de resultados finales
            show_percentiles: Si True, muestra percentiles en el gráfico
            target_value: Valor objetivo para mostrar en el gráfico
        """
        Path("plots").mkdir(exist_ok=True)
        
        # Crear copia para no modificar el original
        sim_df_clean = simulation_df.copy()
        
        # Limpiar valores inválidos
        sim_df_clean = sim_df_clean.replace([np.inf, -np.inf], np.nan)
        sim_df_clean = sim_df_clean.ffill().bfill()
        if sim_df_clean.isna().any().any():
            sim_df_clean = sim_df_clean.fillna(initial_value)
        
        # Guardar original para cálculos de probabilidades
        sim_df_original = sim_df_clean.copy()
        
        # Convertir a vista relativa si es necesario
        if view_type == 'relative':
            # Convertir valores absolutos a porcentajes relativos al valor inicial
            sim_df_clean = ((sim_df_clean - initial_value) / initial_value) * 100
            ylabel = 'Variación respecto al valor inicial (%)'
            initial_display = 0.0  # En vista relativa, el inicio es 0%
        else:
            ylabel = 'Valor del Portfolio'
            initial_display = initial_value
        
        # Calcular estadísticas
        final_values = sim_df_clean.iloc[-1].values
        mean_path = sim_df_clean.mean(axis=1)
        median_path = sim_df_clean.median(axis=1)
        
        # Percentiles
        p5_path = sim_df_clean.quantile(0.05, axis=1)
        p25_path = sim_df_clean.quantile(0.25, axis=1)
        p75_path = sim_df_clean.quantile(0.75, axis=1)
        p95_path = sim_df_clean.quantile(0.95, axis=1)
        
        # Crear figura con subplots
        n_plots = sum([show_fan_chart, show_histogram])
        if n_plots == 0:
            n_plots = 1
        
        fig = plt.figure(figsize=(16, 10))
        
        if show_fan_chart and show_histogram:
            gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
            ax1 = fig.add_subplot(gs[0, :])
            ax2 = fig.add_subplot(gs[1, 0])
            ax3 = fig.add_subplot(gs[1, 1])
        elif show_fan_chart:
            gs = fig.add_gridspec(1, 1)
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = None
            ax3 = None
        else:
            gs = fig.add_gridspec(1, 2)
            ax1 = None
            ax2 = fig.add_subplot(gs[0, 0])
            ax3 = fig.add_subplot(gs[0, 1])
        
        # 1. Fan Chart (Curvas de escenarios)
        if show_fan_chart and ax1 is not None:
            # Mostrar una muestra de trayectorias (máximo 100 para no saturar)
            max_paths = min(100, sim_df_clean.shape[1])
            sample_indices = np.random.choice(sim_df_clean.shape[1], max_paths, replace=False)
            
            for idx in sample_indices:
                ax1.plot(sim_df_clean.index, sim_df_clean.iloc[:, idx], 
                        alpha=0.1, color='blue', linewidth=0.5)
            
            # Media
            ax1.plot(sim_df_clean.index, mean_path, 'r-', linewidth=2, label='Media')
            
            # Mediana
            ax1.plot(sim_df_clean.index, median_path, 'g-', linewidth=2, label='Mediana (P50)')
            
            # Percentiles (fan chart)
            if show_percentiles:
                ax1.fill_between(sim_df_clean.index, p5_path, p95_path, 
                                alpha=0.2, color='gray', label='90% intervalo (P5-P95)')
                ax1.fill_between(sim_df_clean.index, p25_path, p75_path, 
                                alpha=0.3, color='blue', label='50% intervalo (P25-P75)')
                ax1.plot(sim_df_clean.index, p5_path, '--', alpha=0.7, color='red', linewidth=1.5, label='P5')
                ax1.plot(sim_df_clean.index, p95_path, '--', alpha=0.7, color='red', linewidth=1.5, label='P95')
            
            # Valor inicial
            ax1.axhline(y=initial_display, color='black', linestyle=':', linewidth=2, label='Valor inicial')
            
            # Valor objetivo si se especifica
            if target_value is not None:
                if view_type == 'relative':
                    target_display = ((target_value - initial_value) / initial_value) * 100
                else:
                    target_display = target_value
                ax1.axhline(y=target_display, color='orange', linestyle='--', linewidth=2, label='Objetivo')
            
            # Etiquetas
            period_label = 'Meses' if len(sim_df_clean) > 252 else 'Días'
            ax1.set_xlabel(period_label, fontsize=12)
            ax1.set_ylabel(ylabel, fontsize=12)
            ax1.set_title(title + ' - Curvas de Escenarios', fontsize=14, fontweight='bold')
            ax1.legend(loc='best', fontsize=9)
            ax1.grid(True, alpha=0.3)
        
        # 2. Histograma de resultados finales
        if show_histogram and ax2 is not None:
            ax2.hist(final_values, bins=50, alpha=0.7, edgecolor='black', color='skyblue')
            ax2.axvline(final_values.mean(), color='red', linestyle='--', linewidth=2, label='Media')
            ax2.axvline(np.median(final_values), color='green', linestyle='--', linewidth=2, label='Mediana')
            ax2.axvline(initial_display, color='black', linestyle=':', linewidth=2, label='Inicial')
            
            if target_value is not None:
                if view_type == 'relative':
                    target_display = ((target_value - initial_value) / initial_value) * 100
                else:
                    target_display = target_value
                ax2.axvline(target_display, color='orange', linestyle='--', linewidth=2, label='Objetivo')
            
            period_label = 'Meses' if len(sim_df_clean) > 252 else 'Días'
            final_period = sim_df_clean.index[-1]
            ax2.set_xlabel(f'Valor Final ({ylabel})', fontsize=11)
            ax2.set_ylabel('Frecuencia', fontsize=11)
            ax2.set_title(f'Distribución de Resultados a {final_period} {period_label.lower()}', fontsize=12, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # 3. Estadísticas y probabilidades
        if ax3 is not None:
            ax3.axis('off')
            
            # Calcular probabilidades usando el DataFrame original (absoluto)
            probs = self.calculate_monte_carlo_probabilities(
                sim_df_original,
                initial_value,
                target_value=target_value
            )
            
            stats_text = []
            stats_text.append("ESTADÍSTICAS DE SIMULACIÓN")
            stats_text.append("=" * 40)
            stats_text.append(f"Simulaciones: {sim_df_clean.shape[1]:,}")
            period_label = 'Meses' if len(sim_df_clean) > 252 else 'Días'
            stats_text.append(f"Período: {sim_df_clean.index[-1]} {period_label.lower()}")
            stats_text.append("")
            
            if view_type == 'relative':
                stats_text.append("Retornos Finales:")
                stats_text.append(f"  Media: {probs['expected_return']:.2f}%")
                stats_text.append(f"  Mediana: {probs['median_return']:.2f}%")
                stats_text.append("")
                stats_text.append("Percentiles de Retorno:")
                stats_text.append(f"  P5: {probs['return_percentiles']['p5']:.2f}%")
                stats_text.append(f"  P50: {probs['return_percentiles']['p50']:.2f}%")
                stats_text.append(f"  P95: {probs['return_percentiles']['p95']:.2f}%")
            else:
                stats_text.append("Valores Finales:")
                stats_text.append(f"  Media: ${probs['expected_value']:,.2f}")
                stats_text.append(f"  Mediana: ${probs['median_value']:,.2f}")
                stats_text.append("")
                stats_text.append("Percentiles:")
                stats_text.append(f"  P5: ${probs['percentiles']['p5']:,.2f}")
                stats_text.append(f"  P50: ${probs['percentiles']['p50']:,.2f}")
                stats_text.append(f"  P95: ${probs['percentiles']['p95']:,.2f}")
            
            stats_text.append("")
            stats_text.append("Probabilidades:")
            stats_text.append(f"  Ganancia: {probs['prob_gain']*100:.1f}%")
            stats_text.append(f"  Pérdida: {probs['prob_loss']*100:.1f}%")
            
            if probs['prob_reach_target'] is not None:
                stats_text.append(f"  Alcanzar objetivo: {probs['prob_reach_target']*100:.1f}%")
            
            stats_str = "\n".join(stats_text)
            ax3.text(0.1, 0.5, stats_str, fontsize=10, family='monospace',
                    verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_monte_carlo_portfolio_visualizer(self,
                                             simulation_df: pd.DataFrame,
                                             initial_value: float,
                                             title: str = "Monte Carlo Simulation - Portfolio Visualizer Style",
                                             save_path: Optional[str] = None) -> None:
        """
        Visualización estilo Portfolio Visualizer con fan chart y estadísticas detalladas
        
        Args:
            simulation_df: DataFrame con simulaciones (de monte_carlo_simulation)
            initial_value: Valor inicial del portfolio
            title: Título del gráfico
            save_path: Ruta para guardar el gráfico
        """
        Path("plots").mkdir(exist_ok=True)
        
        # Limpiar valores inválidos
        sim_df = simulation_df.copy()
        sim_df = sim_df.replace([np.inf, -np.inf], np.nan)
        sim_df = sim_df.ffill().bfill()
        if sim_df.isna().any().any():
            sim_df = sim_df.fillna(initial_value)
        
        # Convertir meses a años para el eje X
        months = len(sim_df)
        years = months / 12
        x_axis = np.arange(months) / 12  # Convertir a años
        
        # Calcular estadísticas
        mean_path = sim_df.mean(axis=1).values
        median_path = sim_df.median(axis=1).values
        
        # Percentiles para fan chart
        p10_path = sim_df.quantile(0.10, axis=1).values
        p25_path = sim_df.quantile(0.25, axis=1).values
        p75_path = sim_df.quantile(0.75, axis=1).values
        p90_path = sim_df.quantile(0.90, axis=1).values
        
        # Valores finales
        final_values = sim_df.iloc[-1].values
        
        # Crear figura con subplots
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3, height_ratios=[2, 1])
        
        # 1. Fan Chart Principal (estilo Portfolio Visualizer)
        ax1 = fig.add_subplot(gs[0, :])
        
        # Mostrar algunas trayectorias de ejemplo (máximo 50)
        max_paths = min(50, sim_df.shape[1])
        sample_indices = np.random.choice(sim_df.shape[1], max_paths, replace=False)
        for idx in sample_indices:
            ax1.plot(x_axis, sim_df.iloc[:, idx].values, 
                   alpha=0.05, color='steelblue', linewidth=0.5)
        
        # Fan chart con bandas de percentiles
        ax1.fill_between(x_axis, p10_path, p90_path, 
                        alpha=0.15, color='lightblue', label='80% intervalo (P10-P90)')
        ax1.fill_between(x_axis, p25_path, p75_path, 
                        alpha=0.25, color='steelblue', label='50% intervalo (P25-P75)')
        
        # Líneas de percentiles
        ax1.plot(x_axis, p10_path, '--', alpha=0.6, color='navy', linewidth=1.5, label='P10')
        ax1.plot(x_axis, p90_path, '--', alpha=0.6, color='navy', linewidth=1.5, label='P90')
        
        # Media y mediana
        ax1.plot(x_axis, mean_path, '-', linewidth=2.5, color='red', label='Media')
        ax1.plot(x_axis, median_path, '-', linewidth=2.5, color='green', label='Mediana (P50)')
        
        # Valor inicial
        ax1.axhline(y=initial_value, color='black', linestyle=':', linewidth=2, label='Valor inicial')
        
        # Configuración del gráfico
        ax1.set_xlabel('Años', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Valor del Portfolio ($)', fontsize=12, fontweight='bold')
        ax1.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlim(0, years)
        
        # Formatear eje Y con separadores de miles
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 2. Histograma de valores finales
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.hist(final_values, bins=50, alpha=0.7, edgecolor='black', color='skyblue', linewidth=0.5)
        ax2.axvline(final_values.mean(), color='red', linestyle='--', linewidth=2, label=f'Media: ${final_values.mean():,.0f}')
        ax2.axvline(np.median(final_values), color='green', linestyle='--', linewidth=2, label=f'Mediana: ${np.median(final_values):,.0f}')
        ax2.axvline(initial_value, color='black', linestyle=':', linewidth=2, label=f'Inicial: ${initial_value:,.0f}')
        ax2.set_xlabel('Valor Final ($)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Frecuencia', fontsize=11, fontweight='bold')
        ax2.set_title(f'Distribución de Valores Finales ({years:.0f} años)', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 3. Estadísticas y probabilidades
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.axis('off')
        
        # Calcular probabilidades
        returns = (final_values - initial_value) / initial_value
        prob_gain = (returns > 0).sum() / len(returns)
        prob_loss = (returns < 0).sum() / len(returns)
        
        # Percentiles
        percentiles = {
            'p5': np.percentile(final_values, 5),
            'p10': np.percentile(final_values, 10),
            'p25': np.percentile(final_values, 25),
            'p50': np.percentile(final_values, 50),
            'p75': np.percentile(final_values, 75),
            'p90': np.percentile(final_values, 90),
            'p95': np.percentile(final_values, 95)
        }
        
        return_percentiles = {
            'p5': np.percentile(returns, 5) * 100,
            'p50': np.percentile(returns, 50) * 100,
            'p95': np.percentile(returns, 95) * 100
        }
        
        stats_text = []
        stats_text.append("ESTADÍSTICAS DE SIMULACIÓN")
        stats_text.append("=" * 50)
        stats_text.append(f"Simulaciones: {sim_df.shape[1]:,}")
        stats_text.append(f"Período: {years:.0f} años ({months:.0f} meses)")
        stats_text.append("")
        stats_text.append("VALORES FINALES:")
        stats_text.append(f"  Media:      ${np.mean(final_values):>12,.2f}")
        stats_text.append(f"  Mediana:    ${np.median(final_values):>12,.2f}")
        stats_text.append(f"  Mínimo:     ${np.min(final_values):>12,.2f}")
        stats_text.append(f"  Máximo:     ${np.max(final_values):>12,.2f}")
        stats_text.append("")
        stats_text.append("PERCENTILES:")
        stats_text.append(f"  P5:         ${percentiles['p5']:>12,.2f}")
        stats_text.append(f"  P10:        ${percentiles['p10']:>12,.2f}")
        stats_text.append(f"  P25:        ${percentiles['p25']:>12,.2f}")
        stats_text.append(f"  P50:        ${percentiles['p50']:>12,.2f}")
        stats_text.append(f"  P75:        ${percentiles['p75']:>12,.2f}")
        stats_text.append(f"  P90:        ${percentiles['p90']:>12,.2f}")
        stats_text.append(f"  P95:        ${percentiles['p95']:>12,.2f}")
        stats_text.append("")
        stats_text.append("RETORNOS ESPERADOS:")
        stats_text.append(f"  Media:      {returns.mean()*100:>12.2f}%")
        stats_text.append(f"  Mediana:    {return_percentiles['p50']:>12.2f}%")
        stats_text.append("")
        stats_text.append("PROBABILIDADES:")
        stats_text.append(f"  Ganancia:   {prob_gain*100:>12.1f}%")
        stats_text.append(f"  Pérdida:    {prob_loss*100:>12.1f}%")
        
        stats_str = "\n".join(stats_text)
        ax3.text(0.05, 0.95, stats_str, fontsize=10, family='monospace',
                verticalalignment='top', transform=ax3.transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, pad=10))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Gráfico guardado en: {save_path}")
        plt.show()
    
    def plot_portfolio_analysis(self,
                               simulation_df: pd.DataFrame,
                               initial_value: float,
                               save_dir: str = "plots") -> None:
        """
        Genera gráficos adicionales de análisis del portfolio:
        - Composición de la cartera
        - Máximo drawdown
        - Matriz de correlación
        - Retornos esperados anuales
        - Annual Return Probabilities
        - Probabilidades de pérdida
        
        Args:
            simulation_df: DataFrame con simulaciones Monte Carlo
            initial_value: Valor inicial del portfolio
            save_dir: Directorio donde guardar los gráficos
        """
        Path(save_dir).mkdir(exist_ok=True)
        
        # Limpiar datos
        sim_df = simulation_df.copy()
        sim_df = sim_df.replace([np.inf, -np.inf], np.nan)
        sim_df = sim_df.ffill().bfill()
        if sim_df.isna().any().any():
            sim_df = sim_df.fillna(initial_value)
        
        years = len(sim_df) / 12
        months = len(sim_df)
        x_axis = np.arange(months) / 12  # Convertir a años
        
        # Definir colores para los gráficos
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.symbols)))
        
        # ========== 1. COMPOSICIÓN DE LA CARTERA ==========
        # Validar que todos los datos estén alineados
        n_assets = len(self.symbols)
        if len(self.weights) != n_assets:
            print(f"⚠️  Advertencia: Número de pesos ({len(self.weights)}) no coincide con número de símbolos ({n_assets})")
            if len(self.weights) < n_assets:
                # Agregar pesos equitativos para los símbolos faltantes
                missing = n_assets - len(self.weights)
                equal_weight = 1.0 / n_assets
                weights_to_use = list(self.weights) + [equal_weight] * missing
            else:
                # Usar solo los primeros N pesos
                weights_to_use = self.weights[:n_assets]
            # Normalizar pesos
            total = sum(weights_to_use)
            if total > 0:
                weights_to_use = [w / total for w in weights_to_use]
        else:
            weights_to_use = self.weights
        
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax1.pie(
            weights_to_use, 
            labels=self.symbols, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=colors[:n_assets],
            textprops={'fontsize': 12, 'fontweight': 'bold'}
        )
        ax1.set_title(f'Composición de la Cartera ({n_assets} activos)', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/portfolio_composition.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # ========== 2. MÁXIMO DRAWDOWN ==========
        fig2, ax2 = plt.subplots(figsize=(14, 6))
        
        # Calcular drawdown para cada simulación
        max_drawdowns = []
        drawdown_paths = []
        
        for col in sim_df.columns:
            path = sim_df[col].values
            cumulative = path.copy()
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            drawdown_paths.append(drawdown)
            max_drawdowns.append(drawdown.min())
        
        # Promedio de drawdowns
        drawdown_mean = np.array(drawdown_paths).mean(axis=0)
        drawdown_p5 = np.percentile(drawdown_paths, 5, axis=0)
        drawdown_p95 = np.percentile(drawdown_paths, 95, axis=0)
        
        ax2.fill_between(x_axis, drawdown_p5, drawdown_p95, alpha=0.2, color='red', label='90% intervalo')
        ax2.plot(x_axis, drawdown_mean, 'r-', linewidth=2, label='Drawdown promedio')
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.set_xlabel('Años', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Máximo Drawdown del Portfolio', fontsize=16, fontweight='bold', pad=20)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.set_xlim(0, years)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.1f}%'))
        plt.tight_layout()
        plt.savefig(f"{save_dir}/max_drawdown.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # ========== 3. MATRIZ DE CORRELACIÓN ==========
        # Asegurar que siempre se muestren todos los activos
        n_assets = min(len(self.price_series), len(self.symbols))
        if n_assets > 1:
            fig3, ax3 = plt.subplots(figsize=(max(10, n_assets * 1.2), max(8, n_assets * 1.2)))
            
            # Calcular matriz de correlación usando el mismo método que el reporte
            # (correlation_with alinea correctamente las fechas)
            symbols_to_use = self.symbols[:n_assets]
            corr_matrix = []
            for i in range(n_assets):
                row = []
                for j in range(n_assets):
                    if i == j:
                        row.append(1.0)
                    else:
                        try:
                            corr = self.price_series[i].correlation_with(self.price_series[j])
                            row.append(corr)
                        except Exception as e:
                            print(f"⚠️  Advertencia: Error calculando correlación entre {symbols_to_use[i]} y {symbols_to_use[j]}: {e}")
                            row.append(0.0)
                corr_matrix.append(row)
            
            corr_df = pd.DataFrame(corr_matrix, index=symbols_to_use, columns=symbols_to_use)
            
            sns.heatmap(corr_df, annot=True, fmt='.3f', cmap='coolwarm', 
                       center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                       xticklabels=symbols_to_use, yticklabels=symbols_to_use, ax=ax3)
            ax3.set_title(f'Matriz de Correlación entre Activos ({n_assets} activos)', fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig(f"{save_dir}/correlation_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
        else:
            print("⚠️  Solo hay 1 activo en el portfolio, no se puede generar matriz de correlación")
        
        # ========== 4. RETORNOS ESPERADOS ANUALES ==========
        # Asegurar que siempre se muestren todos los activos
        n_assets = min(len(self.price_series), len(self.symbols))
        symbols_to_use = self.symbols[:n_assets]
        
        fig4, ax4 = plt.subplots(figsize=(12, max(6, n_assets * 0.8)))
        
        # Calcular retornos anuales por activo
        asset_annual_returns = []
        for i, ps in enumerate(self.price_series[:n_assets]):
            try:
                asset_returns = ps.returns().dropna()
                if len(asset_returns) > 0:
                    annual_return = asset_returns.mean() * 252 * 100  # En porcentaje
                    asset_annual_returns.append(annual_return)
                else:
                    print(f"⚠️  Advertencia: {symbols_to_use[i]} no tiene retornos calculables, usando 0%")
                    asset_annual_returns.append(0.0)
            except Exception as e:
                print(f"⚠️  Advertencia: Error calculando retorno para {symbols_to_use[i]}: {e}")
                asset_annual_returns.append(0.0)
        
        # Asegurar que tenemos el mismo número de colores que de activos
        colors_to_use = colors[:n_assets]
        
        bars = ax4.barh(symbols_to_use, asset_annual_returns, color=colors_to_use, alpha=0.7, edgecolor='black')
        ax4.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax4.set_xlabel('Retorno Anual Esperado (%)', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Activo', fontsize=12, fontweight='bold')
        ax4.set_title(f'Retornos Esperados Anuales por Activo ({n_assets} activos)', fontsize=16, fontweight='bold', pad=20)
        ax4.grid(True, alpha=0.3, linestyle='--', axis='x')
        
        # Añadir valores en las barras
        for i, (bar, ret) in enumerate(zip(bars, asset_annual_returns)):
            ax4.text(ret + (0.5 if ret >= 0 else -0.5), i, f'{ret:.2f}%',
                    va='center', ha='left' if ret >= 0 else 'right', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/annual_expected_returns.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # ========== 5. ANNUAL RETURN PROBABILITIES ==========
        fig5, ax5 = plt.subplots(figsize=(14, 8))
        
        # Calcular retornos anuales de las simulaciones
        annual_returns_list = []
        for col in sim_df.columns:
            path = sim_df[col].values
            # Calcular retorno anual para cada año
            for year in range(int(years)):
                start_idx = year * 12
                end_idx = min((year + 1) * 12, len(path))
                if end_idx > start_idx:
                    annual_return = (path[end_idx-1] / path[start_idx] - 1) * 100
                    annual_returns_list.append(annual_return)
        
        # Histograma de retornos anuales
        ax5.hist(annual_returns_list, bins=50, alpha=0.7, edgecolor='black', color='skyblue')
        ax5.axvline(np.mean(annual_returns_list), color='red', linestyle='--', 
                   linewidth=2, label=f'Media: {np.mean(annual_returns_list):.2f}%')
        ax5.axvline(np.median(annual_returns_list), color='green', linestyle='--', 
                   linewidth=2, label=f'Mediana: {np.median(annual_returns_list):.2f}%')
        ax5.axvline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
        ax5.set_xlabel('Retorno Anual (%)', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax5.set_title('Distribución de Retornos Anuales (Annual Return Probabilities)', 
                     fontsize=16, fontweight='bold', pad=20)
        ax5.legend(fontsize=10)
        ax5.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        plt.savefig(f"{save_dir}/annual_return_probabilities.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # ========== 6. PROBABILIDADES DE PÉRDIDA ==========
        fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Calcular probabilidades de pérdida por año
        final_values = sim_df.iloc[-1].values
        total_returns = (final_values - initial_value) / initial_value * 100
        
        # Probabilidad de pérdida total
        prob_loss_total = (total_returns < 0).sum() / len(total_returns) * 100
        
        # Probabilidades de pérdida por año
        years_list = list(range(1, int(years) + 1))
        prob_loss_by_year = []
        prob_loss_10 = []
        prob_loss_20 = []
        prob_loss_30 = []
        
        for year in years_list:
            year_idx = year * 12
            if year_idx <= len(sim_df):
                year_values = sim_df.iloc[year_idx - 1].values
                year_returns = (year_values - initial_value) / initial_value * 100
                prob_loss_by_year.append((year_returns < 0).sum() / len(year_returns) * 100)
                prob_loss_10.append((year_returns < -10).sum() / len(year_returns) * 100)
                prob_loss_20.append((year_returns < -20).sum() / len(year_returns) * 100)
                prob_loss_30.append((year_returns < -30).sum() / len(year_returns) * 100)
            else:
                # Si no hay suficientes datos para ese año, usar valores del último mes disponible
                if len(sim_df) > 0:
                    year_values = sim_df.iloc[-1].values
                    year_returns = (year_values - initial_value) / initial_value * 100
                    prob_loss_by_year.append((year_returns < 0).sum() / len(year_returns) * 100)
                    prob_loss_10.append((year_returns < -10).sum() / len(year_returns) * 100)
                    prob_loss_20.append((year_returns < -20).sum() / len(year_returns) * 100)
                    prob_loss_30.append((year_returns < -30).sum() / len(year_returns) * 100)
                else:
                    prob_loss_by_year.append(0)
                    prob_loss_10.append(0)
                    prob_loss_20.append(0)
                    prob_loss_30.append(0)
        
        # Gráfico 1: Probabilidades de pérdida por año
        ax6a.plot(years_list, prob_loss_by_year, 'o-', linewidth=2, markersize=8, 
                label='Prob. Pérdida', color='red')
        ax6a.plot(years_list, prob_loss_10, 's-', linewidth=2, markersize=6, 
                label='Prob. Pérdida >10%', color='orange', alpha=0.7)
        ax6a.plot(years_list, prob_loss_20, '^-', linewidth=2, markersize=6, 
                label='Prob. Pérdida >20%', color='darkorange', alpha=0.7)
        ax6a.plot(years_list, prob_loss_30, 'v-', linewidth=2, markersize=6, 
                label='Prob. Pérdida >30%', color='darkred', alpha=0.7)
        ax6a.set_xlabel('Año', fontsize=12, fontweight='bold')
        ax6a.set_ylabel('Probabilidad (%)', fontsize=12, fontweight='bold')
        ax6a.set_title('Probabilidades de Pérdida por Año', fontsize=14, fontweight='bold', pad=15)
        ax6a.legend(fontsize=9)
        ax6a.grid(True, alpha=0.3, linestyle='--')
        max_prob = max(prob_loss_by_year + prob_loss_10 + prob_loss_20 + prob_loss_30) if (prob_loss_by_year + prob_loss_10 + prob_loss_20 + prob_loss_30) else 100
        ax6a.set_ylim(0, max_prob * 1.1 if max_prob > 0 else 100)
        
        # Gráfico 2: Distribución de pérdidas totales
        loss_values = total_returns[total_returns < 0]
        gain_values = total_returns[total_returns >= 0]
        
        if len(loss_values) > 0:
            ax6b.hist(loss_values, bins=30, alpha=0.7, color='red', 
                     edgecolor='black', label=f'Pérdidas ({len(loss_values)} sims)')
        if len(gain_values) > 0:
            ax6b.hist(gain_values, bins=30, alpha=0.7, color='green', 
                     edgecolor='black', label=f'Ganancias ({len(gain_values)} sims)')
        
        ax6b.axvline(0, color='black', linestyle='--', linewidth=2)
        ax6b.set_xlabel('Retorno Total (%)', fontsize=12, fontweight='bold')
        ax6b.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax6b.set_title(f'Distribución de Pérdidas y Ganancias\n(Prob. Pérdida Total: {prob_loss_total:.1f}%)', 
                      fontsize=14, fontweight='bold', pad=15)
        ax6b.legend(fontsize=10)
        ax6b.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/loss_probabilities.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✅ Todos los gráficos de análisis guardados en '{save_dir}/':")
        print(f"   - portfolio_composition.png")
        print(f"   - max_drawdown.png")
        if len(self.price_series) > 1:
            print(f"   - correlation_matrix.png")
        print(f"   - annual_expected_returns.png")
        print(f"   - annual_return_probabilities.png")
        print(f"   - loss_probabilities.png")
    
    def run_and_plot_monte_carlo(self,
                                 years: int = 10,
                                 simulations: int = 10000,
                                 initial_value: Optional[float] = None,
                                 inflation_rate: Optional[float] = None,
                                 save_path: Optional[str] = None,
                                 **kwargs) -> pd.DataFrame:
        """
        Método auxiliar: ejecuta simulación y visualiza en un solo paso (estilo Portfolio Visualizer)
        
        Args:
            years: Años a simular (por defecto 10)
            simulations: Número de simulaciones (por defecto 10,000)
            initial_value: Valor inicial del portfolio (None = usar valor actual)
            inflation_rate: Tasa de inflación anual (None = sin ajuste)
            save_path: Ruta para guardar gráfico
            **kwargs: Argumentos adicionales para monte_carlo_simulation
        
        Returns:
            DataFrame con simulaciones
        """
        # Obtener valor inicial si no se especifica
        if initial_value is None:
            portfolio_value = self.get_portfolio_value_series()
            initial_value = float(portfolio_value.iloc[-1]) if len(portfolio_value) > 0 else 100000.0
        
        sim_df = self.monte_carlo_simulation(
            years=years, 
            simulations=simulations, 
            initial_value=initial_value,
            inflation_rate=inflation_rate,
            **kwargs
        )
        
        # Usar la nueva visualización estilo Portfolio Visualizer
        if save_path is None:
            save_path = "plots/monte_carlo_portfolio.png"
        self.plot_monte_carlo_portfolio_visualizer(
            sim_df, 
            initial_value=initial_value, 
            save_path=save_path
        )
        return sim_df
    
    def monte_carlo_individual_assets_improved(self,
                                             years: int = 10,
                                             simulations: int = 10000,
                                             initial_value: Optional[float] = None,
                                             random_seed: Optional[int] = None,
                                             inflation_rate: Optional[float] = None) -> Dict[str, pd.DataFrame]:
        """
        Simula la evolución de cada activo individualmente usando Monte Carlo mejorado
        Usa la misma estructura que monte_carlo_simulation (años, meses) pero para cada activo por separado
        
        Args:
            years: Número de años a simular (por defecto 10 años)
            simulations: Número de simulaciones (por defecto 10,000)
            initial_value: Valor inicial por activo (None = usar precio actual)
            random_seed: Semilla para reproducibilidad
            inflation_rate: Tasa de inflación anual (None = sin ajuste por inflación)
        
        Returns:
            Diccionario con símbolo como clave y DataFrame de simulaciones como valor
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        months = years * 12
        results = {}
        
        for i, (symbol, ps) in enumerate(zip(self.symbols, self.price_series)):
            asset_returns = ps.returns().dropna()
            
            if len(asset_returns) < 30:
                print(f"⚠️  Advertencia: {symbol} no tiene suficientes datos, saltando...")
                continue
            
            # Calcular estadísticas del activo
            # Limpiar retornos: eliminar outliers
            q1 = asset_returns.quantile(0.01)
            q99 = asset_returns.quantile(0.99)
            cleaned_returns = asset_returns[(asset_returns >= q1) & (asset_returns <= q99)]
            
            if len(cleaned_returns) < 30:
                cleaned_returns = asset_returns
            
            # Retorno medio anualizado
            mean_annual = cleaned_returns.mean() * 252
            
            # Volatilidad anualizada - CÁLCULO CORRECTO SIN LÍMITES
            vol_annual = cleaned_returns.std() * np.sqrt(252)
            # Asegurar que la volatilidad sea positiva (no puede ser negativa)
            if vol_annual < 0:
                vol_annual = abs(vol_annual)
            # Si es cero o muy pequeña, usar un valor mínimo razonable basado en los datos
            if vol_annual < 1e-6:
                vol_annual = asset_returns.std() * np.sqrt(252)
                if vol_annual < 1e-6:
                    vol_annual = 0.15  # 15% por defecto solo si realmente no hay datos
            
            # Convertir a mensual
            mean_monthly = mean_annual / 12
            vol_monthly = vol_annual / np.sqrt(12)
            
            # Ajustar por inflación si se especifica
            if inflation_rate is not None:
                inflation_monthly = inflation_rate / 12
                mean_monthly = mean_monthly - inflation_monthly
            
            # Valor inicial
            if initial_value is None:
                asset_initial_value = float(ps.close.iloc[-1]) if len(ps.close) > 0 else 100.0
            else:
                # Distribuir el valor inicial según el peso del activo
                asset_initial_value = initial_value * self.weights[i]
            
            # Generar simulaciones
            asset_results = []
            
            for sim in range(simulations):
                path = [asset_initial_value]
                
                for month in range(1, months + 1):
                    # Generar retorno mensual aleatorio - CÁLCULO CORRECTO SIN CLIPPING
                    random_shock = np.random.normal(0, 1)
                    monthly_return = mean_monthly + vol_monthly * random_shock
                    
                    # No limitar retornos artificialmente - solo verificar valores finitos
                    if not np.isfinite(monthly_return):
                        monthly_return = 0.0
                    
                    # Actualizar valor
                    new_value = path[-1] * (1 + monthly_return)
                    # Solo asegurar que no sea negativo (no tiene sentido financiero)
                    if new_value < 0:
                        new_value = 0.0
                    
                    # Validar
                    if np.isnan(new_value) or np.isinf(new_value) or new_value < 0:
                        new_value = path[-1]
                    
                    path.append(new_value)
                
                asset_results.append(path[1:])  # Excluir valor inicial
            
            # Convertir a DataFrame
            sim_df = pd.DataFrame(asset_results).T
            sim_df.index = range(months)  # Meses desde 0 hasta months-1
            
            # Limpiar valores inválidos
            sim_df = sim_df.replace([np.inf, -np.inf], np.nan)
            sim_df = sim_df.ffill().bfill()
            if sim_df.isna().any().any():
                sim_df = sim_df.fillna(asset_initial_value)
            
            results[symbol] = sim_df
        
        return results
    
    def plot_monte_carlo_individual_assets_improved(self,
                                                   simulation_dict: Dict[str, pd.DataFrame],
                                                   initial_values: Optional[Dict[str, float]] = None,
                                                   save_path: Optional[str] = None) -> None:
        """
        Visualiza los resultados de simulaciones Monte Carlo de activos individuales mejorado
        Estilo Portfolio Visualizer
        
        Args:
            simulation_dict: Diccionario con símbolos como clave y DataFrames de simulaciones como valor
            initial_values: Diccionario con valores iniciales por activo (None = usar del DataFrame)
            save_path: Ruta para guardar el gráfico
        """
        Path("plots").mkdir(exist_ok=True)
        
        if not simulation_dict:
            print("⚠️  No hay simulaciones para visualizar")
            return
        
        n_assets = len(simulation_dict)
        colors = plt.cm.tab10(np.linspace(0, 1, n_assets))
        
        # Crear figura con subplots
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Trayectorias medias de todos los activos
        ax1 = fig.add_subplot(gs[0, :])
        
        for i, (symbol, sim_df) in enumerate(simulation_dict.items()):
            # Limpiar datos
            sim_df_clean = sim_df.copy()
            sim_df_clean = sim_df_clean.replace([np.inf, -np.inf], np.nan)
            sim_df_clean = sim_df_clean.ffill().bfill()
            
            months = len(sim_df_clean)
            years = months / 12
            x_axis = np.arange(months) / 12  # Convertir a años
            
            # Calcular estadísticas
            mean_path = sim_df_clean.mean(axis=1).values
            median_path = sim_df_clean.median(axis=1).values
            p10_path = sim_df_clean.quantile(0.10, axis=1).values
            p90_path = sim_df_clean.quantile(0.90, axis=1).values
            
            # Mostrar algunas trayectorias
            max_paths = min(20, sim_df_clean.shape[1])
            sample_indices = np.random.choice(sim_df_clean.shape[1], max_paths, replace=False)
            for idx in sample_indices:
                ax1.plot(x_axis, sim_df_clean.iloc[:, idx].values, 
                        alpha=0.05, color=colors[i], linewidth=0.5)
            
            # Bandas de confianza
            ax1.fill_between(x_axis, p10_path, p90_path, alpha=0.1, color=colors[i])
            
            # Media y mediana
            ax1.plot(x_axis, mean_path, '-', linewidth=2, label=f'{symbol} (Media)', color=colors[i])
            ax1.plot(x_axis, median_path, '--', linewidth=1.5, alpha=0.7, 
                    label=f'{symbol} (Mediana)', color=colors[i])
        
        ax1.set_xlabel('Años', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Valor del Activo ($)', fontsize=12, fontweight='bold')
        ax1.set_title('Simulación Monte Carlo - Activos Individuales', fontsize=16, fontweight='bold', pad=20)
        ax1.legend(loc='upper left', fontsize=9, ncol=2)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 2. Distribuciones de valores finales
        ax2 = fig.add_subplot(gs[1, 0])
        for i, (symbol, sim_df) in enumerate(simulation_dict.items()):
            final_values = sim_df.iloc[-1].values
            ax2.hist(final_values, bins=30, alpha=0.5, label=symbol, color=colors[i], edgecolor='black')
        ax2.set_xlabel('Valor Final ($)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Frecuencia', fontsize=11, fontweight='bold')
        ax2.set_title('Distribuciones de Valores Finales', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 3. Comparación de retornos esperados
        ax3 = fig.add_subplot(gs[1, 1])
        symbols_list = []
        returns_list = []
        for symbol, sim_df in simulation_dict.items():
            final_values = sim_df.iloc[-1].values
            initial_val = sim_df.iloc[0, 0]
            returns = (final_values - initial_val) / initial_val * 100
            symbols_list.append(symbol)
            returns_list.append(returns.mean())
        
        bars = ax3.barh(symbols_list, returns_list, color=colors[:len(symbols_list)], alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax3.set_xlabel('Retorno Esperado (%)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Activo', fontsize=11, fontweight='bold')
        ax3.set_title('Retornos Esperados por Activo', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, linestyle='--', axis='x')
        
        # Añadir valores en las barras
        for i, (bar, ret) in enumerate(zip(bars, returns_list)):
            ax3.text(ret + (1 if ret >= 0 else -1), i, f'{ret:.2f}%',
                    va='center', ha='left' if ret >= 0 else 'right', fontweight='bold')
        
        # 4. Estadísticas comparativas
        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')
        
        stats_text = []
        stats_text.append("ESTADÍSTICAS POR ACTIVO")
        stats_text.append("=" * 80)
        
        for symbol, sim_df in simulation_dict.items():
            final_values = sim_df.iloc[-1].values
            initial_val = sim_df.iloc[0, 0]
            returns = (final_values - initial_val) / initial_val * 100
            
            stats_text.append(f"\n{symbol}:")
            stats_text.append(f"  Valor esperado:      ${np.mean(final_values):>12,.2f}")
            stats_text.append(f"  Mediana:             ${np.median(final_values):>12,.2f}")
            stats_text.append(f"  Retorno esperado:   {returns.mean():>12.2f}%")
            stats_text.append(f"  Prob. ganancia:     {(returns > 0).sum() / len(returns)*100:>12.1f}%")
            stats_text.append(f"  P5:                 ${np.percentile(final_values, 5):>12,.2f}")
            stats_text.append(f"  P50:                ${np.percentile(final_values, 50):>12,.2f}")
            stats_text.append(f"  P95:                ${np.percentile(final_values, 95):>12,.2f}")
        
        stats_str = "\n".join(stats_text)
        ax4.text(0.05, 0.95, stats_str, fontsize=9, family='monospace',
                verticalalignment='top', transform=ax4.transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, pad=10))
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = "plots/monte_carlo_individual_assets.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico guardado en: {save_path}")
        plt.show()
    
    def run_and_plot_monte_carlo_individual_assets(self,
                                                   years: int = 10,
                                                   simulations: int = 10000,
                                                   initial_value: Optional[float] = None,
                                                   inflation_rate: Optional[float] = None,
                                                   random_seed: Optional[int] = None,
                                                   save_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Método auxiliar: ejecuta simulaciones individuales y visualiza en un solo paso (mejorado)
        
        Args:
            years: Años a simular (por defecto 10)
            simulations: Número de simulaciones (por defecto 10,000)
            initial_value: Valor inicial total (se distribuye según pesos)
            inflation_rate: Tasa de inflación anual (None = sin ajuste)
            random_seed: Semilla para reproducibilidad
            save_path: Ruta para guardar gráfico
        
        Returns:
            Diccionario con simulaciones por activo
        """
        sim_dict = self.monte_carlo_individual_assets_improved(
            years=years,
            simulations=simulations,
            initial_value=initial_value,
            inflation_rate=inflation_rate,
            random_seed=random_seed
        )
        
        self.plot_monte_carlo_individual_assets_improved(
            sim_dict,
            save_path=save_path
        )
        
        return sim_dict

