"""
Módulo para generar gráficos de evolución de precios
Proporciona funciones modulares para visualizar datos de precios históricos
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Union, Any
from datetime import datetime

# Deshabilitar LaTeX para evitar errores de parsing con caracteres especiales ($, ^, %, etc.)
plt.rcParams['text.usetex'] = False

# Configurar estilo de matplotlib
try:
    if 'seaborn-v0_8-darkgrid' in plt.style.available:
        plt.style.use('seaborn-v0_8-darkgrid')
    elif 'seaborn-darkgrid' in plt.style.available:
        plt.style.use('seaborn-darkgrid')
    elif 'seaborn' in plt.style.available:
        plt.style.use('seaborn')
    else:
        plt.style.use('default')
except Exception:
    # Si hay algún problema con los estilos, usar el estilo por defecto
    pass


def plot_single_price_series(
    data,
    save_path: Optional[str] = None,
    show_plot: bool = False,
    figsize: tuple = (12, 6)
) -> None:
    """
    Genera un gráfico de evolución de precios para una sola serie
    
    Args:
        data: Objeto StandardizedPriceData o PriceSeries
        save_path: Ruta donde guardar el gráfico (opcional)
        show_plot: Si True, muestra el gráfico en pantalla
        figsize: Tamaño de la figura (ancho, alto)
    """
    # Extraer datos según el tipo de objeto
    if hasattr(data, 'close') and hasattr(data, 'date'):
        # Es StandardizedPriceData o PriceSeries
        dates = data.date
        close_prices = data.close.values if hasattr(data.close, 'values') else data.close
        symbol = data.symbol
        source = getattr(data, 'source', 'Unknown')
    elif isinstance(data, pd.DataFrame):
        # Es un DataFrame
        dates = data.index
        close_prices = data['Close'].values if 'Close' in data.columns else data.iloc[:, -1].values
        symbol = getattr(data, 'symbol', 'Unknown')
        source = 'DataFrame'
    else:
        raise ValueError("Tipo de datos no soportado para graficar")
    
    # Crear figura y ejes
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True, 
                                    gridspec_kw={'height_ratios': [3, 1]})
    
    # Gráfico principal: Precio de cierre
    ax1.plot(dates, close_prices, linewidth=2, color='#2E86AB', label='Precio de Cierre')
    ax1.fill_between(dates, close_prices, alpha=0.3, color='#2E86AB')
    ax1.set_ylabel('Precio ($)', fontsize=11, fontweight='bold')
    ax1.set_title(f'Evolución de Precios - {symbol}', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best')
    
    # Añadir estadísticas en el gráfico
    mean_price = np.mean(close_prices)
    max_price = np.max(close_prices)
    min_price = np.min(close_prices)
    current_price = close_prices[-1]
    
    # Líneas de referencia
    ax1.axhline(y=mean_price, color='orange', linestyle='--', linewidth=1.5, 
                alpha=0.7, label=f'Media: ${mean_price:.2f}')
    ax1.axhline(y=max_price, color='green', linestyle=':', linewidth=1, alpha=0.5)
    ax1.axhline(y=min_price, color='red', linestyle=':', linewidth=1, alpha=0.5)
    
    # Añadir texto con estadísticas
    stats_text = f'Actual: ${current_price:.2f} | Media: ${mean_price:.2f} | Max: ${max_price:.2f} | Min: ${min_price:.2f}'
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Gráfico secundario: Volumen
    if hasattr(data, 'volume'):
        volume = data.volume.values if hasattr(data.volume, 'values') else data.volume
        ax2.bar(dates, volume, color='#A23B72', alpha=0.6, width=1)
        ax2.set_ylabel('Volumen', fontsize=10, fontweight='bold')
        ax2.set_xlabel('Fecha', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    else:
        ax2.set_ylabel('Volumen', fontsize=10, fontweight='bold')
        ax2.set_xlabel('Fecha', fontsize=11, fontweight='bold')
        ax2.text(0.5, 0.5, 'Datos de volumen no disponibles', 
                transform=ax2.transAxes, ha='center', va='center', fontsize=10)
    
    # Formatear fechas en el eje X
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Añadir información de fuente
    fig.text(0.99, 0.01, f'Fuente: {source}', ha='right', va='bottom', 
             fontsize=8, style='italic', alpha=0.7)
    
    plt.tight_layout()
    
    # Guardar gráfico si se especifica ruta
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   📊 Gráfico guardado en: {save_path}")
    
    # Mostrar gráfico si se solicita
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_multiple_price_series(
    data_dict: Dict[str, Any],
    save_path: Optional[str] = None,
    show_plot: bool = False,
    figsize: tuple = (14, 8),
    normalize: bool = False
) -> None:
    """
    Genera un gráfico comparativo de evolución de precios para múltiples series
    
    Args:
        data_dict: Diccionario con símbolos como keys y StandardizedPriceData/PriceSeries como values
        save_path: Ruta donde guardar el gráfico (opcional)
        show_plot: Si True, muestra el gráfico en pantalla
        figsize: Tamaño de la figura (ancho, alto)
        normalize: Si True, normaliza todas las series al 100% al inicio para comparar retornos
    """
    if not data_dict:
        print("⚠️  No hay datos para graficar")
        return
    
    # Colores para las series
    colors = plt.cm.tab10(np.linspace(0, 1, len(data_dict)))
    
    # Crear figura y ejes
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})
    
    # Procesar cada serie
    series_data = {}
    for symbol, data in data_dict.items():
        if hasattr(data, 'close') and hasattr(data, 'date'):
            dates = data.date
            close_prices = data.close.values if hasattr(data.close, 'values') else data.close
            
            # Normalizar si se solicita
            if normalize:
                close_prices = (close_prices / close_prices[0]) * 100
            
            series_data[symbol] = {
                'dates': dates,
                'prices': close_prices,
                'source': getattr(data, 'source', 'Unknown')
            }
        else:
            print(f"⚠️  Saltando {symbol}: formato no soportado")
            continue
    
    if not series_data:
        print("⚠️  No hay datos válidos para graficar")
        return
    
    # Graficar cada serie
    for idx, (symbol, data_info) in enumerate(series_data.items()):
        dates = data_info['dates']
        prices = data_info['prices']
        color = colors[idx]
        
        label = f"{symbol}"
        if normalize:
            label += " (normalizado)"
        
        ax1.plot(dates, prices, linewidth=2, color=color, label=label, alpha=0.8)
        ax1.fill_between(dates, prices, alpha=0.15, color=color)
    
    # Configurar gráfico principal
    title = 'Comparación de Evolución de Precios' + (' (Normalizado)' if normalize else '')
    ax1.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('Precio ($)' if not normalize else 'Precio Normalizado (%)', 
                   fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best', ncol=min(len(series_data), 4))
    
    # Añadir estadísticas resumidas
    stats_lines = []
    for symbol, data_info in series_data.items():
        prices = data_info['prices']
        current = prices[-1]
        if normalize:
            change = current - 100  # Cambio desde 100%
            stats_lines.append(f"{symbol}: {change:+.1f}%")
        else:
            initial = prices[0]
            change_pct = ((current - initial) / initial) * 100
            stats_lines.append(f"{symbol}: ${current:.2f} ({change_pct:+.1f}%)")
    
    stats_text = " | ".join(stats_lines)
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Gráfico de volumen (promedio o suma si hay múltiples)
    # Por simplicidad, mostramos el volumen de la primera serie
    first_symbol = list(series_data.keys())[0]
    first_data = data_dict[first_symbol]
    
    if hasattr(first_data, 'volume'):
        volume = first_data.volume.values if hasattr(first_data.volume, 'values') else first_data.volume
        dates_vol = series_data[first_symbol]['dates']
        ax2.bar(dates_vol, volume, color='#A23B72', alpha=0.6, width=1)
        ax2.set_ylabel(f'Volumen ({first_symbol})', fontsize=10, fontweight='bold')
    else:
        ax2.set_ylabel('Volumen', fontsize=10, fontweight='bold')
        ax2.text(0.5, 0.5, 'Datos de volumen no disponibles',
                transform=ax2.transAxes, ha='center', va='center', fontsize=10)
    
    ax2.set_xlabel('Fecha', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Formatear fechas
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Añadir información de fuente
    sources = set([data_info['source'] for data_info in series_data.values()])
    source_text = ', '.join(sources) if sources else 'Unknown'
    fig.text(0.99, 0.01, f'Fuente: {source_text}', ha='right', va='bottom',
             fontsize=8, style='italic', alpha=0.7)
    
    plt.tight_layout()
    
    # Guardar gráfico
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   📊 Gráfico guardado en: {save_path}")
    
    # Mostrar gráfico
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_price_series_from_standardized(
    data,
    save_dir: str = "plots",
    filename: Optional[str] = None,
    show_plot: bool = False
) -> str:
    """
    Función de conveniencia para graficar desde StandardizedPriceData
    
    Args:
        data: Objeto StandardizedPriceData o PriceSeries
        save_dir: Directorio donde guardar el gráfico
        filename: Nombre del archivo (si None, se genera automáticamente)
        show_plot: Si True, muestra el gráfico
    
    Returns:
        Ruta del archivo guardado
    """
    # Generar nombre de archivo si no se proporciona
    if filename is None:
        symbol = getattr(data, 'symbol', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_price_evolution_{timestamp}.png"
    
    save_path = Path(save_dir) / filename
    
    plot_single_price_series(data, save_path=str(save_path), show_plot=show_plot)
    
    return str(save_path)


def plot_multiple_series_from_dict(
    data_dict: Dict[str, Any],
    save_dir: str = "plots",
    filename: Optional[str] = None,
    show_plot: bool = False,
    normalize: bool = False
) -> str:
    """
    Función de conveniencia para graficar múltiples series desde un diccionario
    
    Args:
        data_dict: Diccionario con símbolos y StandardizedPriceData/PriceSeries
        save_dir: Directorio donde guardar el gráfico
        filename: Nombre del archivo (si None, se genera automáticamente)
        show_plot: Si True, muestra el gráfico
        normalize: Si True, normaliza las series al inicio
    
    Returns:
        Ruta del archivo guardado
    """
    # Generar nombre de archivo si no se proporciona
    if filename is None:
        symbols = "_".join(list(data_dict.keys())[:3])  # Primeros 3 símbolos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_normalized" if normalize else ""
        filename = f"comparison_{symbols}{suffix}_{timestamp}.png"
    
    save_path = Path(save_dir) / filename
    
    plot_multiple_price_series(
        data_dict, 
        save_path=str(save_path), 
        show_plot=show_plot,
        normalize=normalize
    )
    
    return str(save_path)

