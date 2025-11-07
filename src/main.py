"""
Script principal interactivo del sistema de análisis bursátil
Permite al usuario extraer datos de forma interactiva desde cualquier API
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Agregar el directorio raíz al path para importar install_dependencies
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar funciones de instalación desde el módulo dedicado
try:
    from install_dependencies import check_and_install
except ImportError:
    print("⚠️  No se pudo importar install_dependencies.py")
    print("Ejecuta desde la raíz del proyecto: python run_main.py")
    sys.exit(1)

# Verificar e instalar dependencias antes de importar módulos
if not check_and_install():
    print("\n⚠️  No se pudieron instalar las dependencias.")
    print("Ejecuta: python install_dependencies.py")
    sys.exit(1)

try:
    # Intentar importación relativa (cuando se ejecuta como módulo)
    from .data_extractor import DataExtractor, StandardizedPriceData, Recommendation, NewsItem
    from .price_series import PriceSeries
    from .portfolio import Portfolio
    from .data_cleaning import DataCleaner
    from .price_plots import plot_price_series_from_standardized, plot_multiple_series_from_dict
except ImportError:
    # Fallback a importación absoluta (cuando se ejecuta directamente)
    from data_extractor import DataExtractor, StandardizedPriceData, Recommendation, NewsItem
    from price_series import PriceSeries
    from portfolio import Portfolio
    from data_cleaning import DataCleaner
    from price_plots import plot_price_series_from_standardized, plot_multiple_series_from_dict


def print_header(title: str):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def menu_principal():
    """Menú principal interactivo"""
    print_header("SISTEMA DE ANÁLISIS BURSÁTIL - MENÚ PRINCIPAL")
    print("\nSelecciona qué tipo de datos quieres extraer:")
    print("  1. Precios históricos de acciones")
    print("  2. Precios históricos de índices")
    print("  3. Múltiples series de datos (acciones/índices)")
    print("  4. Recomendaciones de analistas")
    print("  5. Noticias financieras")
    print("  6. Información de empresa")
    print("  7. Todos los datos disponibles (precios + noticias + recomendaciones + info)")
    print("  8. Crear cartera personalizada (acciones e índices) + simulación Monte Carlo")
    print("  9. Indicadores macroeconómicos (FRED: inflación, desempleo, PIB, etc.)")
    print("  10. Ver fuentes de datos disponibles")
    print("  0. Salir")
    
    choice = input("\nOpción: ").strip()
    return choice


def obtener_simbolos(tipo: str = "acciones") -> list:
    """Solicita símbolos al usuario"""
    print(f"\nIngresa los símbolos de {tipo} (separados por comas):")
    print("Ejemplos:")
    if tipo == "acciones":
        print("  - Para acciones: AAPL, MSFT, GOOGL, TSLA")
    else:
        print("  - Para índices: ^GSPC (S&P 500), ^DJI (Dow Jones), ^IXIC (NASDAQ), ^IBEX (IBEX 35)")
        print("  - Para índices españoles: ^IBEX (IBEX 35)")
        print("  - Si ^IBEX no funciona, prueba: IBEX.MC")
    
    symbols_input = input("\nSímbolos: ").strip()
    
    if not symbols_input:
        print("⚠️  No se ingresaron símbolos. Usando valores por defecto...")
        return ["AAPL", "MSFT", "GOOGL"] if tipo == "acciones" else ["^GSPC"]
    
    # Separar por comas y limpiar
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    return symbols


def obtener_fuente(extractor: DataExtractor) -> str:
    """Solicita la fuente de datos al usuario"""
    sources = extractor.get_supported_sources()
    
    print("\nFuentes de datos disponibles:")
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source}")
    
    if len(sources) == 1:
        print(f"\nUsando fuente por defecto: {sources[0]}")
        return sources[0]
    
    choice = input("\nSelecciona fuente (número o nombre, Enter para usar 'yahoo'): ").strip()
    
    if not choice:
        return "yahoo"
    
    # Si es un número
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(sources):
            return sources[idx]
    
    # Si es un nombre
    if choice in sources:
        return choice
    
    print(f"⚠️  Fuente '{choice}' no válida. Usando 'yahoo' por defecto.")
    return "yahoo"


def obtener_periodo() -> tuple:
    """Solicita período o fechas al usuario"""
    print("\n¿Cómo quieres especificar el período?")
    print("  1. Usar período predefinido (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)")
    print("  2. Especificar fechas de inicio y fin")
    
    choice = input("\nOpción (1 o 2, Enter para usar '1y'): ").strip()
    
    if choice == "2":
        start_date = input("Fecha inicio (YYYY-MM-DD): ").strip()
        end_date = input("Fecha fin (YYYY-MM-DD): ").strip()
        return (None, None, start_date, end_date)
    else:
        period = input("\nPeríodo (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max) [Enter para '1y']: ").strip()
        if not period:
            period = "1y"
        return (period, None, None, None)


def extraer_precios_acciones(extractor: DataExtractor):
    """Extrae precios históricos de acciones con input del usuario"""
    print_header("EXTRAER PRECIOS HISTÓRICOS DE ACCIONES")
    
    symbols = obtener_simbolos("acciones")
    source = obtener_fuente(extractor)
    periodo_data = obtener_periodo()
    period, _, start_date, end_date = periodo_data
    
    print(f"\n📥 Descargando datos de: {', '.join(symbols)}")
    print(f"   Fuente: {source}")
    print(f"   Período: {period if period else f'{start_date} a {end_date}'}")
    
    try:
        if start_date and end_date:
            data = extractor.download_historical_prices(
                symbol=symbols[0],
                start_date=start_date,
                end_date=end_date,
                source=source
            )
        else:
            data = extractor.download_historical_prices(
                symbol=symbols[0],
                period=period,
                source=source
            )
        
        print(f"\n✅ Datos descargados exitosamente")
        print(f"   - Símbolo: {data.symbol}")
        print(f"   - Fuente: {data.source}")
        print(f"   - Días de datos: {len(data)}")
        print(f"   - Período: {data.date.min().date()} a {data.date.max().date()}")
        print(f"   - Formato estandarizado: ✓")
        
        # Convertir a PriceSeries para mostrar estadísticas automáticas
        ps = PriceSeries.from_standardized_data(data)
        print(f"\n📊 Estadísticas automáticas calculadas:")
        print(f"   - Precio medio: ${ps.mean_price:.2f}")
        print(f"   - Desviación típica: ${ps.std_price:.2f}")
        print(f"   - Volatilidad anualizada: {ps.volatility(annualized=True)*100:.2f}%")
        
        # Mostrar que el formato es estandarizado
        print(f"\n✓ FORMATO ESTANDARIZADO: Los datos están en formato StandardizedPriceData")
        print(f"  independientemente de la fuente '{source}'")
        
        # Generar gráfico de evolución de precios
        print(f"\n📈 Generando gráfico de evolución de precios...")
        try:
            plot_path = plot_price_series_from_standardized(
                data,
                save_dir="plots",
                filename=f"{data.symbol}_price_evolution.png",
                show_plot=False
            )
        except Exception as e:
            print(f"   ⚠️  Error generando gráfico: {e}")
        
        return data
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def extraer_precios_indices(extractor: DataExtractor):
    """Extrae precios históricos de índices con input del usuario"""
    print_header("EXTRAER PRECIOS HISTÓRICOS DE ÍNDICES")
    
    symbols = obtener_simbolos("índices")
    source = obtener_fuente(extractor)
    periodo_data = obtener_periodo()
    period, _, start_date, end_date = periodo_data
    
    print(f"\n📥 Descargando datos de índices: {', '.join(symbols)}")
    print(f"   Fuente: {source}")
    
    try:
        if start_date and end_date:
            data = extractor.download_index_data(
                index_symbol=symbols[0],
                start_date=start_date,
                end_date=end_date,
                source=source
            )
        else:
            data = extractor.download_index_data(
                index_symbol=symbols[0],
                period=period,
                source=source
            )
        
        print(f"\n✅ Datos de índice descargados exitosamente")
        print(f"   - Índice: {data.symbol}")
        print(f"   - Fuente: {data.source}")
        print(f"   - Días de datos: {len(data)}")
        print(f"   - Formato estandarizado: ✓")
        
        # Convertir a PriceSeries
        ps = PriceSeries.from_standardized_data(data)
        print(f"\n📊 Estadísticas automáticas:")
        print(f"   - Precio medio: ${ps.mean_price:.2f}")
        print(f"   - Desviación típica: ${ps.std_price:.2f}")
        print(f"   - Volatilidad anualizada: {ps.volatility(annualized=True)*100:.2f}%")
        
        # Generar gráfico de evolución de precios
        print(f"\n📈 Generando gráfico de evolución de precios...")
        try:
            plot_path = plot_price_series_from_standardized(
                data,
                save_dir="plots",
                filename=f"{data.symbol}_index_evolution.png",
                show_plot=False
            )
        except Exception as e:
            print(f"   ⚠️  Error generando gráfico: {e}")
        
        return data
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def extraer_multiple_series(extractor: DataExtractor):
    """Extrae N series de datos al mismo tiempo con input del usuario"""
    print_header("EXTRAER MÚLTIPLES SERIES DE DATOS")
    
    print("\n¿Qué tipo de datos quieres descargar?")
    print("  1. Solo acciones")
    print("  2. Solo índices")
    print("  3. Mezcla de acciones e índices")
    
    tipo_choice = input("\nOpción (Enter para acciones): ").strip()
    
    if tipo_choice == "2":
        symbols = obtener_simbolos("índices")
        tipo = "índices"
    elif tipo_choice == "3":
        print("\nIngresa símbolos (acciones e índices mezclados):")
        symbols_input = input("Símbolos (separados por comas): ").strip()
        symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
        tipo = "mixto"
    else:
        symbols = obtener_simbolos("acciones")
        tipo = "acciones"
    
    source = obtener_fuente(extractor)
    periodo_data = obtener_periodo()
    period, _, start_date, end_date = periodo_data
    
    print(f"\n📥 Descargando {len(symbols)} series simultáneamente:")
    print(f"   Símbolos: {', '.join(symbols)}")
    print(f"   Fuente: {source}")
    
    try:
        if start_date and end_date:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                source=source
            )
        else:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                period=period,
                source=source
            )
        
        print(f"\n✅ {len(data_dict)} series descargadas exitosamente")
        
        # Mostrar cada serie y verificar formato estandarizado
        price_series_list = []
        for symbol, data in data_dict.items():
            print(f"\n   📊 {symbol}:")
            print(f"      - Días: {len(data)}")
            print(f"      - Fuente: {data.source}")
            print(f"      - Formato: StandardizedPriceData ✓")
            
            # Convertir a PriceSeries para mostrar estadísticas automáticas
            ps = PriceSeries.from_standardized_data(data)
            price_series_list.append(ps)
            print(f"      - Precio medio: ${ps.mean_price:.2f}")
            print(f"      - Desviación típica: ${ps.std_price:.2f}")
        
        print(f"\n✓ TODAS LAS SERIES ESTÁN EN FORMATO ESTANDARIZADO")
        print(f"  independientemente de la fuente '{source}'")
        
        # Generar gráfico comparativo de evolución de precios
        print(f"\n📈 Generando gráfico comparativo de evolución de precios...")
        try:
            plot_path = plot_multiple_series_from_dict(
                data_dict,
                save_dir="plots",
                filename="multiple_series_comparison.png",
                show_plot=False,
                normalize=False
            )
        except Exception as e:
            print(f"   ⚠️  Error generando gráfico: {e}")
        
        return data_dict, price_series_list
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None


def extraer_recomendaciones(extractor: DataExtractor):
    """Extrae recomendaciones de analistas con input del usuario"""
    print_header("EXTRAER RECOMENDACIONES DE ANALISTAS")
    
    symbol = input("\nIngresa el símbolo de la acción (ej: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
        print(f"Usando símbolo por defecto: {symbol}")
    
    source = obtener_fuente(extractor)
    
    print(f"\n📥 Obteniendo recomendaciones para {symbol} desde {source}...")
    
    try:
        recommendations = extractor.get_recommendations(symbol, source=source)
        
        print(f"\n✅ {len(recommendations)} recomendaciones encontradas")
        
        if recommendations:
            print("\n📋 Recomendaciones:")
            for i, rec in enumerate(recommendations[:10], 1):  # Mostrar primeras 10
                print(f"\n   {i}. {rec.firm}")
                print(f"      - Rating: {rec.rating}")
                try:
                    # Manejar diferentes tipos de fecha
                    if isinstance(rec.date, datetime):
                        print(f"      - Fecha: {rec.date.strftime('%Y-%m-%d')}")
                    elif hasattr(rec.date, 'date'):
                        print(f"      - Fecha: {rec.date.date()}")
                    elif hasattr(rec.date, 'strftime'):
                        print(f"      - Fecha: {rec.date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"      - Fecha: {rec.date}")
                except Exception as e:
                    print(f"      - Fecha: {rec.date}")
                if rec.target_price:
                    print(f"      - Precio objetivo: ${rec.target_price:.2f}")
        else:
            print("\n⚠️  No se encontraron recomendaciones para este símbolo")
        
        return recommendations
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []


def extraer_noticias(extractor: DataExtractor):
    """Extrae noticias financieras con input del usuario"""
    print_header("EXTRAER NOTICIAS FINANCIERAS")
    
    symbol = input("\nIngresa el símbolo (ej: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
        print(f"Usando símbolo por defecto: {symbol}")
    
    limit_input = input("\nNúmero de noticias (Enter para 10): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 10
    
    source = obtener_fuente(extractor)
    
    print(f"\n📥 Obteniendo {limit} noticias para {symbol} desde {source}...")
    
    try:
        news = extractor.get_news(symbol, limit=limit, source=source)
        
        print(f"\n✅ {len(news)} noticias encontradas")
        
        if news:
            print("\n📰 Noticias:")
            for i, item in enumerate(news, 1):
                # Asegurar que el título se muestre correctamente
                title_display = item.title if item.title and item.title.strip() else "Sin título disponible"
                print(f"\n   {i}. {title_display}")
                try:
                    # Manejar diferentes tipos de fecha
                    if isinstance(item.date, datetime):
                        print(f"      - Fecha: {item.date.strftime('%Y-%m-%d')}")
                    elif hasattr(item.date, 'date'):
                        print(f"      - Fecha: {item.date.date()}")
                    elif hasattr(item.date, 'strftime'):
                        print(f"      - Fecha: {item.date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"      - Fecha: {item.date}")
                except Exception as e:
                    print(f"      - Fecha: {item.date}")
                if item.summary:
                    summary_display = item.summary[:200] if len(item.summary) > 200 else item.summary
                    print(f"      - Resumen: {summary_display}")
                    if len(item.summary) > 200:
                        print(f"        ... (texto completo: {len(item.summary)} caracteres)")
                if item.url:
                    print(f"      - URL: {item.url}")
        else:
            print("\n⚠️  No se encontraron noticias para este símbolo")
            print("   Esto puede deberse a:")
            print("   - El símbolo no tiene noticias disponibles")
            print("   - Problemas de conexión con la API")
            print("   - Cambios en la API de Yahoo Finance")
        
        return news
    except Exception as e:
        print(f"\n❌ Error obteniendo noticias: {e}")
        import traceback
        traceback.print_exc()
        return []


def extraer_info_empresa(extractor: DataExtractor):
    """Extrae información de empresa con input del usuario"""
    print_header("EXTRAER INFORMACIÓN DE EMPRESA")
    
    symbol = input("\nIngresa el símbolo (ej: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
        print(f"Usando símbolo por defecto: {symbol}")
    
    source = obtener_fuente(extractor)
    
    print(f"\n📥 Obteniendo información de {symbol} desde {source}...")
    
    try:
        info = extractor.get_company_info(symbol, source=source)
        
        if info:
            print(f"\n✅ Información obtenida exitosamente")
            print("\n📋 Información de la empresa:")
            for key, value in info.items():
                if key != 'source':
                    print(f"   - {key.replace('_', ' ').title()}: {value}")
        else:
            print("\n⚠️  No se encontró información para este símbolo")
        
        return info
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {}


def extraer_todos_los_datos(extractor: DataExtractor):
    """Extrae todos los datos disponibles con input del usuario"""
    print_header("EXTRAER TODOS LOS DATOS DISPONIBLES")
    
    symbol = input("\nIngresa el símbolo (ej: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
        print(f"Usando símbolo por defecto: {symbol}")
    
    source = obtener_fuente(extractor)
    
    print("\n¿Qué datos quieres incluir?")
    include_news = input("¿Incluir noticias? (s/n, Enter para sí): ").strip().lower() != 'n'
    include_rec = input("¿Incluir recomendaciones? (s/n, Enter para sí): ").strip().lower() != 'n'
    include_info = input("¿Incluir información de empresa? (s/n, Enter para sí): ").strip().lower() != 'n'
    
    news_limit = 10
    if include_news:
        limit_input = input("\nNúmero de noticias a obtener (Enter para 10): ").strip()
        news_limit = int(limit_input) if limit_input.isdigit() else 10
    
    print(f"\n📥 Obteniendo todos los datos de {symbol} desde {source}...")
    
    try:
        all_data = extractor.get_all_data(
            symbol=symbol,
            source=source,
            include_news=include_news,
            include_recommendations=include_rec,
            include_info=include_info,
            news_limit=news_limit
        )
        
        print(f"\n✅ Datos obtenidos exitosamente")
        print(f"\n📊 Resumen:")
        print(f"   - Precios: {'✓' if all_data['prices'] else '✗'}")
        if all_data['prices']:
            print(f"     • Días: {len(all_data['prices'])}")
            print(f"     • Formato estandarizado: ✓")
        
        print(f"   - Noticias: {len(all_data['news'])}")
        if all_data['news']:
            print("\n📰 Noticias encontradas:")
            for i, item in enumerate(all_data['news'][:5], 1):  # Mostrar primeras 5
                print(f"   {i}. {item.title}")
                try:
                    if hasattr(item.date, 'date'):
                        print(f"      Fecha: {item.date.date()}")
                    else:
                        print(f"      Fecha: {item.date}")
                except Exception:
                    print(f"      Fecha: {item.date}")
                if item.summary:
                    summary_display = item.summary[:150] if len(item.summary) > 150 else item.summary
                    print(f"      Resumen: {summary_display}...")
        
        print(f"   - Recomendaciones: {len(all_data['recommendations'])}")
        if all_data['recommendations']:
            print("\n📋 Recomendaciones encontradas:")
            for i, rec in enumerate(all_data['recommendations'][:5], 1):  # Mostrar primeras 5
                print(f"   {i}. {rec.firm}")
                print(f"      Rating: {rec.rating}")
                try:
                    if hasattr(rec.date, 'date'):
                        print(f"      Fecha: {rec.date.date()}")
                    else:
                        print(f"      Fecha: {rec.date}")
                except Exception:
                    print(f"      Fecha: {rec.date}")
        
        print(f"   - Info empresa: {'✓' if all_data['company_info'] else '✗'}")
        if all_data['company_info']:
            print("\n📋 Información de la empresa:")
            for key, value in list(all_data['company_info'].items())[:5]:  # Mostrar primeras 5
                if key != 'source':
                    print(f"   - {key.replace('_', ' ').title()}: {value}")
        
        return all_data
    except Exception as e:
        print(f"\n❌ Error obteniendo datos: {e}")
        import traceback
        traceback.print_exc()
        return None


def analisis_completo(extractor: DataExtractor):
    """Análisis completo: extraer datos + crear portfolio + reporte"""
    print_header("ANÁLISIS COMPLETO")
    
    symbols = obtener_simbolos("acciones")
    source = obtener_fuente(extractor)
    periodo_data = obtener_periodo()
    period, _, start_date, end_date = periodo_data
    
    print(f"\n📥 Descargando datos para análisis completo...")
    print(f"   Símbolos: {', '.join(symbols)}")
    print(f"   Fuente: {source}")
    
    try:
        # Descargar múltiples series
        if start_date and end_date:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                source=source
            )
        else:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                period=period,
                source=source
            )
        
        print(f"\n✅ {len(data_dict)} series descargadas")
        
        # Validar que se descargaron datos
        if len(data_dict) == 0:
            print("\n❌ Error: No se pudieron descargar datos para ningún símbolo")
            return None
        
        # Verificar si algunos símbolos no se descargaron
        downloaded_symbols = list(data_dict.keys())
        if len(downloaded_symbols) < len(symbols):
            missing = set(symbols) - set(downloaded_symbols)
            print(f"\n⚠️  Advertencia: {len(missing)} de {len(symbols)} símbolos no se descargaron: {', '.join(missing)}")
            print(f"   Continuando con {len(downloaded_symbols)} símbolos descargados exitosamente")
        
        # Convertir a PriceSeries (mostrando que estadísticas se calculan automáticamente)
        print("\n📊 Creando series de precios con estadísticas automáticas...")
        price_series_list = []
        for symbol, standardized_data in data_dict.items():
            try:
                ps = PriceSeries.from_standardized_data(standardized_data)
                price_series_list.append(ps)
                print(f"   ✓ {symbol}: Media=${ps.mean_price:.2f}, Std=${ps.std_price:.2f}, Días={len(ps)}")
            except Exception as e:
                print(f"   ❌ Error creando PriceSeries para {symbol}: {e}")
                # Remover del diccionario si falla
                data_dict.pop(symbol, None)
        
        # Validar que tenemos al menos una serie
        if len(price_series_list) == 0:
            print("\n❌ Error: No se pudieron crear series de precios para ningún símbolo")
            return None
        
        # Asegurar que symbols y price_series estén alineados
        final_symbols = list(data_dict.keys())
        if len(final_symbols) != len(price_series_list):
            print(f"\n⚠️  Advertencia: Desalineación detectada. Símbolos: {len(final_symbols)}, Series: {len(price_series_list)}")
            # Usar solo los que coinciden
            n_assets = min(len(final_symbols), len(price_series_list))
            final_symbols = final_symbols[:n_assets]
            price_series_list = price_series_list[:n_assets]
            print(f"   Ajustado a {n_assets} activos")
        
        # Crear portfolio
        print("\n💼 Creando portfolio...")
        print("¿Quieres especificar pesos? (s/n, Enter para distribución equitativa): ", end="")
        use_weights = input().strip().lower() == 's'
        
        if use_weights:
            print(f"Ingresa pesos para {len(final_symbols)} activos (separados por comas, deben sumar 1.0):")
            print(f"   Activos: {', '.join(final_symbols)}")
            weights_input = input("Pesos: ").strip()
            try:
                weights = [float(w.strip()) for w in weights_input.split(",")]
                if len(weights) != len(final_symbols):
                    raise ValueError(f"Número de pesos ({len(weights)}) no coincide con número de activos ({len(final_symbols)})")
            except Exception as e:
                print(f"⚠️  Error en pesos: {e}. Usando distribución equitativa.")
                weights = None
        else:
            weights = None
        
        portfolio = Portfolio(
            symbols=final_symbols,
            price_series=price_series_list,
            weights=weights
        )
        
        print(f"\n   ✓ Portfolio creado con {len(portfolio.symbols)} activos")
        for i, symbol in enumerate(portfolio.symbols):
            print(f"      - {symbol}: {portfolio.weights[i]*100:.1f}%")
        
        # Generar reporte
        print("\n📄 Generando reporte...")
        report = portfolio.report(include_warnings=True, include_correlation=True)
        
        # Asegurar que la carpeta plots existe
        Path("plots").mkdir(exist_ok=True)
        filename = "plots/portfolio_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"   ✓ Reporte guardado en '{filename}'")
        
        # Generar gráficos
        print("\n📈 Generando visualizaciones...")
        portfolio.plots_report(save_dir="plots")
        print("   ✓ Gráficos guardados en 'plots/'")
        
        print("\n✅ Análisis completo finalizado")
        return portfolio
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def ver_fuentes_disponibles(extractor: DataExtractor):
    """Muestra las fuentes de datos disponibles"""
    print_header("FUENTES DE DATOS DISPONIBLES")
    
    sources = extractor.get_supported_sources()
    
    print(f"\n✅ {len(sources)} fuente(s) disponible(s):")
    for i, source in enumerate(sources, 1):
        print(f"   {i}. {source}")
    
    print("\n💡 Tip: Puedes agregar más fuentes usando register_adapter() o register_generic_api()")
    print("   Ver: GUIA_APIS_PERSONALIZADAS.md")


def ver_indicadores_macroeconomicos(extractor: DataExtractor):
    """Muestra indicadores macroeconómicos relevantes usando FRED"""
    print_header("INDICADORES MACROECONÓMICOS (FRED)")
    
    # Verificar si FRED está disponible
    sources = extractor.get_supported_sources()
    if "fred" not in sources:
        print("\n⚠️  FRED no está disponible.")
        print("   Para usar esta función, necesitas configurar FRED_API_KEY en config.json")
        print("   Obtén una API key gratuita en: https://fred.stlouisfed.org/docs/api/api_key.html")
        return
    
    # Definir indicadores macroeconómicos relevantes
    indicadores = {
        "Inflación (CPI)": {
            "id": "CPIAUCSL",
            "descripcion": "Consumer Price Index - Índice de Precios al Consumidor",
            "unidad": "Índice (1982-84=100)"
        },
        "Tasa de Desempleo": {
            "id": "UNRATE",
            "descripcion": "Unemployment Rate - Tasa de desempleo",
            "unidad": "Porcentaje"
        },
        "PIB (Producto Interno Bruto)": {
            "id": "GDP",
            "descripcion": "Gross Domestic Product - Producto Interno Bruto",
            "unidad": "Billones de USD"
        },
        "Tasa de Interés (Fed Funds)": {
            "id": "FEDFUNDS",
            "descripcion": "Effective Federal Funds Rate - Tasa de interés de la Fed",
            "unidad": "Porcentaje anual"
        },
        "Producción Industrial": {
            "id": "INDPRO",
            "descripcion": "Industrial Production Index - Índice de producción industrial",
            "unidad": "Índice (2017=100)"
        },
        "Ventas al Por Menor": {
            "id": "RETAILSMNSA",
            "descripcion": "Retail Sales: Total (Excluding Food Services) - Ventas al por menor",
            "unidad": "Millones de USD"
        },
        "Confianza del Consumidor": {
            "id": "UMCSENT",
            "descripcion": "University of Michigan Consumer Sentiment - Confianza del consumidor",
            "unidad": "Índice (1966:Q1=100)"
        },
        "Déficit/Superávit Presupuestario": {
            "id": "FYFSD",
            "descripcion": "Federal Surplus or Deficit - Déficit o superávit federal",
            "unidad": "Millones de USD"
        },
        "Balance Comercial": {
            "id": "BOPGSTB",
            "descripcion": "Trade Balance: Goods and Services - Balance comercial",
            "unidad": "Millones de USD"
        },
        "Viviendas Iniciadas": {
            "id": "HOUST",
            "descripcion": "Housing Starts - Viviendas iniciadas",
            "unidad": "Miles de unidades"
        }
    }
    
    print("\n📊 Indicadores macroeconómicos disponibles:")
    print("   Estos datos provienen de FRED (Federal Reserve Economic Data)")
    print("   y representan los indicadores económicos más relevantes de EE.UU.\n")
    
    # Preguntar período
    print("¿Qué período quieres consultar?")
    print("  1. Último año (por defecto)")
    print("  2. Últimos 5 años")
    print("  3. Últimos 10 años")
    print("  4. Especificar fechas personalizadas")
    
    periodo_choice = input("\nOpción (Enter para último año): ").strip()
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    if periodo_choice == "2":
        start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
        periodo_desc = "últimos 5 años"
    elif periodo_choice == "3":
        start_date = (datetime.now() - timedelta(days=10*365)).strftime("%Y-%m-%d")
        periodo_desc = "últimos 10 años"
    elif periodo_choice == "4":
        start_date = input("Fecha inicio (YYYY-MM-DD): ").strip()
        end_date = input("Fecha fin (YYYY-MM-DD, Enter para hoy): ").strip()
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        periodo_desc = f"{start_date} a {end_date}"
    else:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        periodo_desc = "último año"
    
    print(f"\n📥 Obteniendo indicadores macroeconómicos ({periodo_desc})...")
    print("   Esto puede tomar unos momentos...\n")
    
    resultados = {}
    errores = []
    
    # Obtener datos para cada indicador
    for nombre, info in indicadores.items():
        try:
            print(f"   📊 Obteniendo {nombre}...", end=" ")
            data = extractor.download_historical_prices(
                symbol=info["id"],
                start_date=start_date,
                end_date=end_date,
                source="fred"
            )
            
            if data and len(data) > 0:
                # Obtener último valor y estadísticas
                # data.close es una Series, data.date es un DatetimeIndex
                ultimo_valor = data.close.iloc[-1] if hasattr(data.close, 'iloc') else data.close.values[-1]
                valor_anterior = data.close.iloc[-2] if len(data) > 1 and hasattr(data.close, 'iloc') else (data.close.values[-2] if len(data) > 1 else ultimo_valor)
                cambio = ultimo_valor - valor_anterior
                cambio_pct = (cambio / valor_anterior * 100) if valor_anterior != 0 else 0
                
                # Obtener información de la serie
                serie_info = extractor.get_company_info(info["id"], source="fred")
                
                # data.date es un DatetimeIndex, usar indexación directa
                fecha_ultima = data.date[-1] if len(data.date) > 0 else None
                
                resultados[nombre] = {
                    "data": data,
                    "ultimo_valor": ultimo_valor,
                    "valor_anterior": valor_anterior,
                    "cambio": cambio,
                    "cambio_pct": cambio_pct,
                    "fecha_ultimo": fecha_ultima,
                    "info": info,
                    "serie_info": serie_info
                }
                print("✓")
            else:
                errores.append(f"{nombre}: No se encontraron datos")
                print("✗")
        except Exception as e:
            errores.append(f"{nombre}: {str(e)}")
            print("✗")
    
    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESUMEN DE INDICADORES MACROECONÓMICOS")
    print("=" * 80)
    
    if resultados:
        print(f"\n📅 Período: {periodo_desc}")
        print(f"📊 {len(resultados)} indicadores obtenidos exitosamente\n")
        
        # Agrupar por categoría
        categorias = {
            "Inflación y Precios": ["Inflación (CPI)"],
            "Mercado Laboral": ["Tasa de Desempleo"],
            "Producción y Crecimiento": ["PIB (Producto Interno Bruto)", "Producción Industrial"],
            "Política Monetaria": ["Tasa de Interés (Fed Funds)"],
            "Consumo": ["Ventas al Por Menor", "Confianza del Consumidor"],
            "Sector Inmobiliario": ["Viviendas Iniciadas"],
            "Finanzas Públicas": ["Déficit/Superávit Presupuestario", "Balance Comercial"]
        }
        
        for categoria, indicadores_cat in categorias.items():
            print(f"\n{'─' * 80}")
            print(f"📌 {categoria}")
            print(f"{'─' * 80}")
            
            for nombre in indicadores_cat:
                if nombre in resultados:
                    res = resultados[nombre]
                    fecha_str = res["fecha_ultimo"]
                    if hasattr(fecha_str, 'strftime'):
                        fecha_display = fecha_str.strftime("%Y-%m-%d")
                    else:
                        fecha_display = str(fecha_str)
                    
                    print(f"\n   {nombre}")
                    print(f"   └─ Descripción: {res['info']['descripcion']}")
                    print(f"   └─ Unidad: {res['info']['unidad']}")
                    print(f"   └─ Último valor ({fecha_display}): {res['ultimo_valor']:,.2f}")
                    
                    if res['cambio'] != 0:
                        cambio_signo = "+" if res['cambio'] > 0 else ""
                        print(f"   └─ Cambio: {cambio_signo}{res['cambio']:,.2f} ({cambio_signo}{res['cambio_pct']:.2f}%)")
                    
                    # Mostrar estadísticas básicas
                    if len(res['data']) > 0:
                        ps = PriceSeries.from_standardized_data(res['data'])
                        print(f"   └─ Media del período: {ps.mean_price:,.2f}")
                        print(f"   └─ Desviación estándar: {ps.std_price:,.2f}")
                        print(f"   └─ Días de datos: {len(res['data'])}")
        
        # Mostrar tabla resumen
        print(f"\n{'─' * 80}")
        print("📊 TABLA RESUMEN")
        print(f"{'─' * 80}")
        print(f"{'Indicador':<40} {'Último Valor':<20} {'Cambio %':<15}")
        print(f"{'─' * 80}")
        
        for nombre, res in resultados.items():
            fecha_str = res["fecha_ultimo"]
            if hasattr(fecha_str, 'strftime'):
                fecha_display = fecha_str.strftime("%Y-%m-%d")
            else:
                fecha_display = str(fecha_str)
            
            cambio_pct_str = f"{res['cambio_pct']:+.2f}%" if res['cambio_pct'] != 0 else "N/A"
            print(f"{nombre:<40} {res['ultimo_valor']:>15,.2f} ({fecha_display}) {cambio_pct_str:>15}")
        
    else:
        print("\n⚠️  No se pudieron obtener indicadores.")
    
    if errores:
        print(f"\n⚠️  Errores encontrados ({len(errores)}):")
        for error in errores[:5]:  # Mostrar solo primeros 5
            print(f"   - {error}")
        if len(errores) > 5:
            print(f"   ... y {len(errores) - 5} más")
    
    print(f"\n{'─' * 80}")
    print("💡 Nota: Los datos provienen de FRED (Federal Reserve Economic Data)")
    print("   Para más información, visita: https://fred.stlouisfed.org/")
    print(f"{'─' * 80}\n")
    
    return resultados


def crear_cartera_personalizada(extractor: DataExtractor):
    """Crea una cartera personalizada con acciones e índices y permite simulación Monte Carlo"""
    print_header("CREAR CARTERA PERSONALIZADA")
    
    print("\nIngresa los símbolos de acciones e índices que quieres incluir en tu cartera.")
    print("Puedes mezclar acciones e índices (ej: AAPL, MSFT, ^GSPC, ^IBEX)")
    print("Ejemplos:")
    print("  - Acciones: AAPL, MSFT, GOOGL, TSLA")
    print("  - Índices: ^GSPC (S&P 500), ^DJI (Dow Jones), ^IXIC (NASDAQ), ^IBEX (IBEX 35)")
    
    symbols_input = input("\nSímbolos (separados por comas): ").strip()
    
    if not symbols_input:
        print("⚠️  No se ingresaron símbolos. Usando valores por defecto...")
        symbols = ["AAPL", "MSFT", "GOOGL"]
    else:
        symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    
    if not symbols:
        print("❌ No se ingresaron símbolos válidos.")
        return None
    
    source = obtener_fuente(extractor)
    periodo_data = obtener_periodo()
    period, _, start_date, end_date = periodo_data
    
    print(f"\n📥 Descargando datos para {len(symbols)} activos...")
    print(f"   Símbolos: {', '.join(symbols)}")
    print(f"   Fuente: {source}")
    
    try:
        # Descargar múltiples series
        if start_date and end_date:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                source=source
            )
        else:
            data_dict = extractor.download_multiple_series(
                symbols=symbols,
                period=period,
                source=source
            )
        
        if not data_dict:
            print("❌ No se pudieron descargar datos para ningún símbolo.")
            return None
        
        print(f"\n✅ {len(data_dict)} series descargadas exitosamente")
        
        # Verificar si algunos símbolos no se descargaron
        downloaded_symbols = list(data_dict.keys())
        if len(downloaded_symbols) < len(symbols):
            missing = set(symbols) - set(downloaded_symbols)
            print(f"\n⚠️  Advertencia: {len(missing)} de {len(symbols)} símbolos no se descargaron: {', '.join(missing)}")
            print(f"   Continuando con {len(downloaded_symbols)} símbolos descargados exitosamente")
        
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
                print(f"   ❌ Error creando PriceSeries para {symbol}: {e}")
        
        # Validar que tenemos al menos una serie
        if len(price_series_list) == 0:
            print("\n❌ Error: No se pudieron crear series de precios para ningún símbolo")
            return None
        
        # Asegurar que symbols y price_series estén alineados
        if len(final_symbols) != len(price_series_list):
            print(f"\n⚠️  Advertencia: Desalineación detectada. Símbolos: {len(final_symbols)}, Series: {len(price_series_list)}")
            n_assets = min(len(final_symbols), len(price_series_list))
            final_symbols = final_symbols[:n_assets]
            price_series_list = price_series_list[:n_assets]
            print(f"   Ajustado a {n_assets} activos")
        
        # Configurar pesos de la cartera
        print("\n💼 Configuración de pesos de la cartera:")
        print("   Opciones:")
        print("   1. Distribución equitativa (pesos iguales)")
        print("   2. Especificar pesos manualmente")
        
        weight_choice = input("\n   Opción (1 o 2, Enter para equitativa): ").strip()
        weights = None
        
        if weight_choice == "2":
            print(f"\n   Ingresa los pesos para {len(data_dict)} activos (deben sumar 1.0 o 100%):")
            print(f"   Símbolos: {', '.join(data_dict.keys())}")
            weights_input = input("   Pesos (separados por comas, ej: 0.4, 0.3, 0.3): ").strip()
            
            try:
                weights = [float(w.strip()) for w in weights_input.split(",")]
                if len(weights) != len(data_dict):
                    raise ValueError("Número de pesos incorrecto")
                # Si suman más de 1, asumir que son porcentajes
                if sum(weights) > 1.5:
                    weights = [w / 100 for w in weights]
                # Normalizar
                total = sum(weights)
                if abs(total - 1.0) > 0.01:
                    print(f"   ⚠️  Los pesos suman {total:.2f}, normalizando a 1.0...")
                    weights = [w / total for w in weights]
            except Exception as e:
                print(f"   ⚠️  Error en pesos: {e}. Usando distribución equitativa.")
                weights = None
        
        # Configurar valor inicial de la cartera
        print("\n💰 Valor inicial de la cartera:")
        print("   Ingresa el valor inicial que quieres usar para la simulación.")
        print("   (Dejar vacío para usar el valor actual calculado)")
        initial_value_input = input("   Valor inicial ($, Enter para usar valor actual): ").strip()
        
        # Crear portfolio
        portfolio = Portfolio(
            symbols=final_symbols,
            price_series=price_series_list,
            weights=weights
        )
        
        print(f"\n✅ Portfolio creado con {len(portfolio.symbols)} activos:")
        for i, symbol in enumerate(portfolio.symbols):
            print(f"   - {symbol}: {portfolio.weights[i]*100:.1f}%")
        
        portfolio_value = portfolio.get_portfolio_value_series()
        current_value = portfolio_value.iloc[-1]
        
        # Determinar valor inicial a usar
        if initial_value_input:
            try:
                initial_value = float(initial_value_input)
                print(f"\n   Valor inicial especificado: ${initial_value:,.2f}")
            except ValueError:
                print(f"   ⚠️  Valor inválido, usando valor actual: ${current_value:.2f}")
                initial_value = current_value
        else:
            initial_value = current_value
            print(f"\n   Valor actual del portfolio: ${current_value:.2f}")
        
        # Simulación Monte Carlo estilo Portfolio Visualizer
        print("\n🎲 SIMULACIÓN MONTE CARLO")
        print("\n¿Quieres ejecutar una simulación Monte Carlo? (s/n, Enter para sí): ", end="")
        run_mc = input().strip().lower() != 'n'
        
        if run_mc:
            print("\n📋 Configuración de la simulación:")
            
            # Tipo de simulación: cartera completa o activos individuales
            print("\n   Tipo de simulación:")
            print("   1. Cartera completa (simula el portfolio como un todo)")
            print("   2. Activos individuales (simula cada activo por separado)")
            
            sim_type_choice = input("   Opción (1 o 2, Enter para cartera completa): ").strip()
            sim_type = "individual" if sim_type_choice == "2" else "portfolio"
            
            # Años a simular
            years_input = input("\n   Años a simular (Enter para 10 años): ").strip()
            years = int(years_input) if years_input.isdigit() else 10
            
            # Número de simulaciones
            sims_input = input("   Número de simulaciones (Enter para 10,000): ").strip()
            simulations = int(sims_input) if sims_input.isdigit() else 10000
            
            # Ajuste por inflación
            print("\n   ¿Ajustar por inflación?")
            print("   (Ajusta los retornos futuros considerando inflación anual)")
            inflation_choice = input("   Ajustar por inflación? (s/n, Enter para no): ").strip().lower()
            use_inflation = inflation_choice == 's'
            inflation_rate = 0.0
            if use_inflation:
                inflation_input = input("   Tasa de inflación anual (% por defecto 2.5%): ").strip()
                try:
                    inflation_rate = float(inflation_input) / 100 if inflation_input else 0.025
                except ValueError:
                    inflation_rate = 0.025  # 2.5% por defecto
                print(f"   Tasa de inflación: {inflation_rate*100:.2f}% anual")
            
            # Reequilibrio (solo para cartera completa)
            rebalance = False
            rebalance_frequency = 'monthly'
            if sim_type == "portfolio":
                print("\n   ¿Reequilibrar el portfolio periódicamente?")
                print("   (Reequilibrar mantiene los pesos iniciales, reduce dispersión)")
                rebalance_choice = input("   Reequilibrar? (s/n, Enter para sí): ").strip().lower()
                rebalance = rebalance_choice != 'n'
                
                if rebalance:
                    print("\n   Frecuencia de reequilibrio:")
                    print("   1. Mensual (por defecto)")
                    print("   2. Trimestral")
                    print("   3. Anual")
                    freq_choice = input("   Opción (1, 2 o 3, Enter para mensual): ").strip()
                    freq_map = {"1": "monthly", "2": "quarterly", "3": "yearly"}
                    rebalance_frequency = freq_map.get(freq_choice, "monthly")
            
            # Ejecutar simulación según el tipo elegido
            if sim_type == "portfolio":
                # Simulación de cartera completa
                print(f"\n📊 Ejecutando simulación Monte Carlo - CARTERA COMPLETA...")
                print(f"   Período: {years} años")
                print(f"   Simulaciones: {simulations:,}")
                print(f"   Reequilibrio: {'Sí' if rebalance else 'No'}")
                if rebalance:
                    print(f"   Frecuencia: {rebalance_frequency}")
                
                # Ejecutar simulación con la nueva función simplificada
                sim_df = portfolio.run_and_plot_monte_carlo(
                    years=years,
                    simulations=simulations,
                    initial_value=initial_value,
                    inflation_rate=inflation_rate if use_inflation else None,
                    rebalance=rebalance,
                    rebalance_frequency=rebalance_frequency,
                    random_seed=42,
                    save_path="plots/monte_carlo_portfolio.png"
                )
                
                print("\n   ✅ Simulación completada y visualización generada")
                
                # Calcular y mostrar estadísticas adicionales
                print("\n📈 Estadísticas de la simulación:")
                final_values = sim_df.iloc[-1].values
                returns = (final_values - initial_value) / initial_value
                
                print(f"   - Valor esperado: ${np.mean(final_values):,.2f}")
                print(f"   - Mediana: ${np.median(final_values):,.2f}")
                print(f"   - Retorno esperado: {returns.mean()*100:.2f}%")
                print(f"   - Probabilidad de ganancia: {(returns > 0).sum() / len(returns)*100:.1f}%")
                print(f"   - Probabilidad de pérdida: {(returns < 0).sum() / len(returns)*100:.1f}%")
                print(f"\n   📊 Percentiles:")
                print(f"   - P5: ${np.percentile(final_values, 5):,.2f}")
                print(f"   - P50: ${np.percentile(final_values, 50):,.2f}")
                print(f"   - P95: ${np.percentile(final_values, 95):,.2f}")
                
                # Generar gráficos adicionales de análisis
                print("\n📊 Generando gráficos adicionales de análisis...")
                portfolio.plot_portfolio_analysis(
                    sim_df,
                    initial_value=initial_value,
                    save_dir="plots"
                )
            else:
                # Simulación de activos individuales
                print(f"\n📊 Ejecutando simulación Monte Carlo - ACTIVOS INDIVIDUALES...")
                print(f"   Período: {years} años")
                print(f"   Simulaciones: {simulations:,}")
                print(f"   Activos: {', '.join(portfolio.symbols)}")
                
                # Ejecutar simulación de activos individuales
                sim_dict = portfolio.run_and_plot_monte_carlo_individual_assets(
                    years=years,
                    simulations=simulations,
                    inflation_rate=inflation_rate if use_inflation else None,
                    random_seed=42,
                    save_path="plots/monte_carlo_individual_assets.png"
                )
                
                print("\n   ✅ Simulación completada y visualización generada")
                
                # Mostrar estadísticas por activo
                print("\n📈 Estadísticas por activo:")
                for symbol, sim_df in sim_dict.items():
                    final_values = sim_df.iloc[-1].values
                    initial_asset_value = sim_df.iloc[0, 0]  # Valor inicial normalizado (100)
                    returns = (final_values - initial_asset_value) / initial_asset_value
                    
                    print(f"\n   {symbol}:")
                    print(f"   - Valor esperado: ${np.mean(final_values):,.2f}")
                    print(f"   - Mediana: ${np.median(final_values):,.2f}")
                    print(f"   - Retorno esperado: {returns.mean()*100:.2f}%")
                    print(f"   - Probabilidad de ganancia: {(returns > 0).sum() / len(returns)*100:.1f}%")
                    print(f"   - P5: ${np.percentile(final_values, 5):,.2f}")
                    print(f"   - P50: ${np.percentile(final_values, 50):,.2f}")
                    print(f"   - P95: ${np.percentile(final_values, 95):,.2f}")
        
        # Generar reporte
        print("\n📄 Generando reporte del portfolio...")
        report = portfolio.report(include_warnings=True, include_correlation=True)
        
        # Asegurar que la carpeta plots existe
        Path("plots").mkdir(exist_ok=True)
        filename = "plots/portfolio_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"   ✅ Reporte guardado en '{filename}'")
        
        # Generar todos los gráficos del reporte
        print("\n📈 Generando gráficos del reporte...")
        try:
            portfolio.plots_report(save_dir="plots")
            print("   ✅ Gráficos guardados en 'plots/'")
        except Exception as e:
            print(f"   ⚠️  Error generando algunos gráficos: {e}")
            import traceback
            traceback.print_exc()
        
        # Preguntar si quiere ver el reporte
        ver_reporte = input("\n¿Quieres ver el reporte por pantalla? (s/n, Enter para no): ").strip().lower()
        if ver_reporte == 's':
            print("\n" + "="*60)
            print("REPORTE DEL PORTFOLIO")
            print("="*60)
            print(report)
        
        print("\n✅ Proceso completado")
        return portfolio
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Función principal interactiva que permite al usuario extraer datos
    """
    print_header("SISTEMA DE ANÁLISIS BURSÁTIL")
    print("\nEste sistema permite extraer datos desde múltiples fuentes (APIs)")
    print("con formato estandarizado independientemente de la fuente original.")
    
    extractor = DataExtractor()
    
    while True:
        choice = menu_principal()
        
        if choice == "0":
            print("\n¡Hasta luego! 👋")
            break
        elif choice == "1":
            extraer_precios_acciones(extractor)
        elif choice == "2":
            extraer_precios_indices(extractor)
        elif choice == "3":
            extraer_multiple_series(extractor)
        elif choice == "4":
            extraer_recomendaciones(extractor)
        elif choice == "5":
            extraer_noticias(extractor)
        elif choice == "6":
            extraer_info_empresa(extractor)
        elif choice == "7":
            extraer_todos_los_datos(extractor)
        elif choice == "8":
            crear_cartera_personalizada(extractor)
        elif choice == "9":
            ver_indicadores_macroeconomicos(extractor)
        elif choice == "10":
            ver_fuentes_disponibles(extractor)
        else:
            print("\n⚠️  Opción no válida. Intenta de nuevo.")
        
        # Preguntar si quiere continuar
        if choice != "0":
            continue_choice = input("\n¿Quieres hacer otra operación? (s/n, Enter para sí): ").strip().lower()
            if continue_choice == 'n':
                print("\n¡Hasta luego! 👋")
                break


if __name__ == "__main__":
    main()
