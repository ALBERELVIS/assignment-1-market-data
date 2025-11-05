"""
Script principal interactivo del sistema de análisis bursátil
Permite al usuario extraer datos de forma interactiva desde cualquier API
"""

import sys
from pathlib import Path
from datetime import datetime

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
except ImportError:
    # Fallback a importación absoluta (cuando se ejecuta directamente)
    from data_extractor import DataExtractor, StandardizedPriceData, Recommendation, NewsItem
    from price_series import PriceSeries
    from portfolio import Portfolio
    from data_cleaning import DataCleaner


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
    print("  8. Análisis completo (extraer datos + crear portfolio + reporte)")
    print("  9. Ver fuentes de datos disponibles")
    print("  10. Crear cartera personalizada (acciones e índices) + simulación Monte Carlo")
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
        
        # Convertir a PriceSeries (mostrando que estadísticas se calculan automáticamente)
        print("\n📊 Creando series de precios con estadísticas automáticas...")
        price_series_list = []
        for symbol, standardized_data in data_dict.items():
            ps = PriceSeries.from_standardized_data(standardized_data)
            price_series_list.append(ps)
            print(f"   ✓ {symbol}: Media=${ps.mean_price:.2f}, Std=${ps.std_price:.2f}")
        
        # Crear portfolio
        print("\n💼 Creando portfolio...")
        print("¿Quieres especificar pesos? (s/n, Enter para distribución equitativa): ", end="")
        use_weights = input().strip().lower() == 's'
        
        if use_weights:
            print(f"Ingresa pesos para {len(symbols)} activos (separados por comas, deben sumar 1.0):")
            weights_input = input("Pesos: ").strip()
            try:
                weights = [float(w.strip()) for w in weights_input.split(",")]
                if len(weights) != len(symbols):
                    raise ValueError("Número de pesos incorrecto")
            except:
                print("⚠️  Error en pesos. Usando distribución equitativa.")
                weights = None
        else:
            weights = None
        
        portfolio = Portfolio(
            symbols=list(data_dict.keys()),
            price_series=price_series_list,
            weights=weights
        )
        
        print(f"   ✓ Portfolio creado con {len(portfolio.symbols)} activos")
        for i, symbol in enumerate(portfolio.symbols):
            print(f"      - {symbol}: {portfolio.weights[i]*100:.1f}%")
        
        # Generar reporte
        print("\n📄 Generando reporte...")
        report = portfolio.report(include_warnings=True, include_correlation=True)
        
        filename = "portfolio_report.md"
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
        
        # Convertir a PriceSeries
        price_series_list = []
        for symbol, data in data_dict.items():
            ps = PriceSeries.from_standardized_data(data)
            price_series_list.append(ps)
            print(f"   ✓ {symbol}: {len(ps)} días de datos")
        
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
        
        # Crear portfolio
        portfolio = Portfolio(
            symbols=list(data_dict.keys()),
            price_series=price_series_list,
            weights=weights
        )
        
        print(f"\n✅ Portfolio creado con {len(portfolio.symbols)} activos:")
        for i, symbol in enumerate(portfolio.symbols):
            print(f"   - {symbol}: {portfolio.weights[i]*100:.1f}%")
        
        portfolio_value = portfolio.get_portfolio_value_series()
        current_value = portfolio_value.iloc[-1]
        print(f"\n   Valor actual del portfolio: ${current_value:.2f}")
        
        # Simulación Monte Carlo
        print("\n🎲 SIMULACIÓN MONTE CARLO")
        print("\n¿Quieres ejecutar una simulación Monte Carlo? (s/n, Enter para sí): ", end="")
        run_mc = input().strip().lower() != 'n'
        
        if run_mc:
            print("\nConfiguración de la simulación:")
            
            # Días a simular
            days_input = input("   Días a simular (Enter para 252 = 1 año): ").strip()
            days = int(days_input) if days_input.isdigit() else 252
            
            # Número de simulaciones
            sims_input = input("   Número de simulaciones (Enter para 1000): ").strip()
            simulations = int(sims_input) if sims_input.isdigit() else 1000
            
            # Tipo de simulación
            print("\n   Tipo de simulación:")
            print("   1. Portfolio completo (simulación conjunta)")
            print("   2. Activos individuales (simulación por componente)")
            print("   3. Ambos")
            
            sim_type = input("   Opción (1, 2 o 3, Enter para portfolio completo): ").strip()
            if not sim_type:
                sim_type = "1"
            
            # Distribución
            print("\n   Distribución para la simulación:")
            print("   1. Normal (por defecto)")
            print("   2. Student-t (colas pesadas)")
            print("   3. Log-normal")
            
            dist_choice = input("   Opción (1, 2 o 3, Enter para normal): ").strip()
            distribution_map = {"1": "normal", "2": "student_t", "3": "lognormal"}
            distribution = distribution_map.get(dist_choice, "normal")
            
            # Ejecutar simulaciones
            if sim_type in ["1", "3"]:
                print(f"\n📊 Ejecutando simulación Monte Carlo del portfolio completo...")
                print(f"   Días: {days}, Simulaciones: {simulations}, Distribución: {distribution}")
                
                sim_df = portfolio.monte_carlo_simulation(
                    days=days,
                    simulations=simulations,
                    distribution=distribution,
                    random_seed=42
                )
                
                print("   ✅ Simulación completada")
                
                # Visualizar resultados
                print("\n   Generando visualización...")
                portfolio.plot_monte_carlo_results(
                    sim_df,
                    title=f"Simulación Monte Carlo - Portfolio Completo ({days} días)",
                    initial_value=100.0,  # Valor normalizado
                    save_path="plots/monte_carlo_portfolio.png"
                )
                print("   ✅ Gráfico guardado en 'plots/monte_carlo_portfolio.png'")
            
            if sim_type in ["2", "3"]:
                print(f"\n📊 Ejecutando simulaciones Monte Carlo de activos individuales...")
                print(f"   Días: {days}, Simulaciones: {simulations}, Distribución: {distribution}")
                
                sim_dict = portfolio.monte_carlo_individual_assets(
                    days=days,
                    simulations=simulations,
                    distribution=distribution,
                    random_seed=42
                )
                
                print("   ✅ Simulaciones completadas")
                
                # Visualizar resultados
                print("\n   Generando visualización...")
                portfolio.plot_monte_carlo_individual(
                    sim_dict,
                    save_path="plots/monte_carlo_individual.png",
                    show_combined=True
                )
                print("   ✅ Gráfico guardado en 'plots/monte_carlo_individual.png'")
        
        # Generar reporte
        print("\n📄 Generando reporte del portfolio...")
        report = portfolio.report(include_warnings=True, include_correlation=True)
        
        filename = "portfolio_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"   ✅ Reporte guardado en '{filename}'")
        
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
            analisis_completo(extractor)
        elif choice == "9":
            ver_fuentes_disponibles(extractor)
        elif choice == "10":
            crear_cartera_personalizada(extractor)
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
