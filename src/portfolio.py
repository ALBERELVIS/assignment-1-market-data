"""
Módulo de Portfolio
Define la clase Portfolio que contiene múltiples series de precios
con métodos de análisis, Monte Carlo y reportes
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from .price_series import PriceSeries


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
        # Alinear todas las series por fecha
        all_dates = set()
        for ps in self.price_series:
            all_dates.update(ps.date)
        
        common_dates = sorted(list(all_dates))
        if not common_dates:
            return pd.Series(dtype=float)
        
        portfolio_values = []
        for date in common_dates:
            portfolio_value = 0.0
            for i, ps in enumerate(self.price_series):
                if date in ps.date:
                    idx = list(ps.date).index(date)
                    portfolio_value += self.weights[i] * ps.close.iloc[idx]
                else:
                    # Si no hay dato para esa fecha, usar el último disponible
                    portfolio_value += self.weights[i] * ps.close.iloc[-1]
            portfolio_values.append(portfolio_value)
        
        return pd.Series(portfolio_values, index=pd.DatetimeIndex(common_dates))
    
    def get_portfolio_returns(self) -> pd.Series:
        """
        Calcula los retornos de la cartera
        
        Returns:
            Serie de retornos de la cartera
        """
        portfolio_value = self.get_portfolio_value_series()
        returns = portfolio_value.pct_change().dropna()
        return returns
    
    def monte_carlo_simulation(self,
                              days: int = 252,
                              simulations: int = 1000,
                              initial_value: Optional[float] = None,
                              random_seed: Optional[int] = None) -> pd.DataFrame:
        """
        Simulación de Monte Carlo para la evolución de la cartera
        
        Args:
            days: Número de días a simular (por defecto 252 = 1 año)
            simulations: Número de simulaciones a realizar
            initial_value: Valor inicial de la cartera. Si None, usa el valor actual
            random_seed: Semilla para reproducibilidad
        
        Returns:
            DataFrame con todas las simulaciones (columnas = simulaciones, filas = días)
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Calcular parámetros de la cartera
        portfolio_returns = self.get_portfolio_returns()
        
        if len(portfolio_returns) < 30:
            raise ValueError("Se necesitan al menos 30 días de datos para la simulación")
        
        # Estadísticas de retornos históricos
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        # Valor inicial
        if initial_value is None:
            initial_value = self.get_portfolio_value_series().iloc[-1]
        
        # Generar simulaciones
        simulation_results = []
        
        for sim in range(simulations):
            # Generar retornos aleatorios (distribución normal)
            random_returns = np.random.normal(mean_return, std_return, days)
            
            # Calcular la trayectoria de precios
            prices = [initial_value]
            for ret in random_returns:
                prices.append(prices[-1] * (1 + ret))
            
            simulation_results.append(prices[1:])  # Excluir el valor inicial
        
        # Convertir a DataFrame
        simulation_df = pd.DataFrame(
            simulation_results,
            columns=range(1, days + 1),
            index=range(simulations)
        )
        
        return simulation_df
    
    def monte_carlo_individual_assets(self,
                                     days: int = 252,
                                     simulations: int = 1000,
                                     random_seed: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Simulación de Monte Carlo para cada activo individual de la cartera
        
        Args:
            days: Número de días a simular
            simulations: Número de simulaciones
            random_seed: Semilla para reproducibilidad
        
        Returns:
            Diccionario con símbolo como clave y DataFrame de simulaciones como valor
        """
        results = {}
        
        for i, ps in enumerate(self.price_series):
            symbol = self.symbols[i]
            
            # Calcular parámetros del activo
            returns = ps.returns()
            if len(returns) < 30:
                continue
            
            mean_return = returns.mean()
            std_return = returns.std()
            initial_value = ps.close.iloc[-1]
            
            if random_seed is not None:
                np.random.seed(random_seed + i)  # Diferente semilla por activo
            
            # Generar simulaciones
            simulation_results = []
            for sim in range(simulations):
                random_returns = np.random.normal(mean_return, std_return, days)
                prices = [initial_value]
                for ret in random_returns:
                    prices.append(prices[-1] * (1 + ret))
                simulation_results.append(prices[1:])
            
            results[symbol] = pd.DataFrame(
                simulation_results,
                columns=range(1, days + 1),
                index=range(simulations)
            )
        
        return results
    
    def plot_monte_carlo_results(self,
                                 simulation_df: pd.DataFrame,
                                 save_path: Optional[str] = None,
                                 title: str = "Simulación Monte Carlo - Portfolio",
                                 show_confidence_intervals: bool = True) -> None:
        """
        Muestra visualmente los resultados de la simulación Monte Carlo
        
        Args:
            simulation_df: DataFrame con resultados de simulaciones
            save_path: Ruta para guardar el gráfico (opcional)
            title: Título del gráfico
            show_confidence_intervals: Si True, muestra intervalos de confianza
        """
        plt.figure(figsize=(14, 8))
        
        # Plotear todas las simulaciones (transparentes)
        for col in simulation_df.columns:
            plt.plot(simulation_df[col].values, alpha=0.1, color='blue', linewidth=0.5)
        
        # Calcular y plotear estadísticas
        mean_simulation = simulation_df.mean(axis=0)
        median_simulation = simulation_df.median(axis=0)
        
        plt.plot(mean_simulation.values, color='red', linewidth=2, label='Media')
        plt.plot(median_simulation.values, color='green', linewidth=2, label='Mediana')
        
        # Intervalos de confianza
        if show_confidence_intervals:
            percentile_5 = simulation_df.quantile(0.05, axis=0)
            percentile_95 = simulation_df.quantile(0.95, axis=0)
            
            plt.fill_between(
                range(len(percentile_5)),
                percentile_5.values,
                percentile_95.values,
                alpha=0.3,
                color='gray',
                label='Intervalo 90% confianza'
            )
        
        plt.xlabel('Días', fontsize=12)
        plt.ylabel('Valor del Portfolio', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
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
        
        # Advertencias
        if include_warnings:
            report_lines.append("## Advertencias y Recomendaciones\n")
            
            warnings = []
            
            # Verificar concentración
            max_weight = max(self.weights)
            if max_weight > 0.5:
                warnings.append(f"⚠️ **Alta concentración:** El activo más pesado representa {max_weight*100:.1f}% del portfolio")
            
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
            
            # Verificar volatilidad
            if portfolio_volatility > 0.3:
                warnings.append(f"⚠️ **Alta volatilidad:** El portfolio tiene volatilidad anualizada de {portfolio_volatility*100:.1f}%")
            
            # Verificar Sharpe ratio bajo
            if portfolio_sharpe < 0.5:
                warnings.append(f"⚠️ **Bajo ratio de Sharpe:** {portfolio_sharpe:.3f} (considerar revisar la composición)")
            
            if warnings:
                for warning in warnings:
                    report_lines.append(f"- {warning}\n")
            else:
                report_lines.append("- ✅ No se detectaron advertencias significativas\n")
            
            report_lines.append("\n")
        
        # Footer
        report_lines.append("---\n")
        report_lines.append(f"*Reporte generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return "\n".join(report_lines)
    
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

