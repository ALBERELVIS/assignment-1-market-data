"""
Ejemplo de uso de las nuevas fuentes de datos:
- FRED (Federal Reserve Economic Data)
- Stooq
- Alpha Vantage
"""

from src.data_extractor import DataExtractor


def ejemplo_fred():
    """Ejemplo de uso de FRED"""
    print("=" * 60)
    print("EJEMPLO 1: FRED (Federal Reserve Economic Data)")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Verificar si FRED está disponible
    if "fred" not in extractor.get_supported_sources():
        print("⚠️  FRED no está disponible. Configura FRED_API_KEY en config.json o .env")
        print("   Obtén una API key gratis en: https://fred.stlouisfed.org/docs/api/api_key.html")
        return
    
    try:
        # Descargar datos del S&P 500 desde FRED
        print("\n📊 Descargando datos del S&P 500 (SP500) desde FRED...")
        data = extractor.download_historical_prices(
            symbol="SP500",
            start_date="2023-01-01",
            end_date="2023-12-31",
            source="fred"
        )
        
        print(f"✅ Datos descargados: {len(data)} puntos")
        print(f"\nPrimeros 5 registros:")
        print(data.to_dataframe().head())
        
        # Obtener información de la serie
        info = extractor.get_company_info("SP500", source="fred")
        if info:
            print(f"\n📋 Información de la serie:")
            print(f"   Título: {info.get('title', 'N/A')}")
            print(f"   Unidades: {info.get('units', 'N/A')}")
            print(f"   Frecuencia: {info.get('frequency', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Consejos:")
        print("   - Verifica que tengas FRED_API_KEY configurada")
        print("   - Verifica que el símbolo sea correcto (ej: 'SP500', 'DEXUSEU', 'UNRATE')")


def ejemplo_stooq():
    """Ejemplo de uso de Stooq"""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Stooq")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Verificar si Stooq está disponible
    if "stooq" not in extractor.get_supported_sources():
        print("⚠️  Stooq no está disponible")
        return
    
    try:
        # Descargar datos de Apple desde Stooq
        print("\n📊 Descargando datos de Apple (AAPL.US) desde Stooq...")
        data = extractor.download_historical_prices(
            symbol="AAPL.US",  # Formato: SYMBOL.MARKET
            period="6m",
            source="stooq"
        )
        
        print(f"✅ Datos descargados: {len(data)} días")
        print(f"\nPrimeros 5 registros:")
        print(data.to_dataframe().head())
        print(f"\nÚltimos 5 registros:")
        print(data.to_dataframe().tail())
        
        print(f"\n📈 Estadísticas:")
        print(f"   Precio de cierre más alto: ${data.close.max():.2f}")
        print(f"   Precio de cierre más bajo: ${data.close.min():.2f}")
        print(f"   Último precio: ${data.close.iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Consejos:")
        print("   - Usa el formato correcto: SYMBOL.MARKET (ej: 'AAPL.US', 'SAN.ES')")
        print("   - Para acciones US: .US")
        print("   - Para acciones españolas: .ES")


def ejemplo_alpha_vantage():
    """Ejemplo de uso de Alpha Vantage"""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Alpha Vantage")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    # Verificar si Alpha Vantage está disponible
    if "alpha_vantage" not in extractor.get_supported_sources():
        print("⚠️  Alpha Vantage no está disponible. Configura ALPHA_VANTAGE_API_KEY en config.json o .env")
        print("   Obtén una API key gratis en: https://www.alphavantage.co/support/#api-key")
        return
    
    try:
        # Descargar datos de Microsoft desde Alpha Vantage
        print("\n📊 Descargando datos de Microsoft (MSFT) desde Alpha Vantage...")
        data = extractor.download_historical_prices(
            symbol="MSFT",
            period="6m",
            source="alpha_vantage"
        )
        
        print(f"✅ Datos descargados: {len(data)} días")
        print(f"\nPrimeros 5 registros:")
        print(data.to_dataframe().head())
        
        # Obtener información de la empresa
        print("\n📋 Obteniendo información de la empresa...")
        info = extractor.get_company_info("MSFT", source="alpha_vantage")
        if info:
            print(f"   Nombre: {info.get('name', 'N/A')}")
            print(f"   Sector: {info.get('sector', 'N/A')}")
            print(f"   Industria: {info.get('industry', 'N/A')}")
            print(f"   P/E Ratio: {info.get('pe_ratio', 'N/A')}")
            print(f"   Dividend Yield: {info.get('dividend_yield', 'N/A')}")
            print(f"   52 Week High: ${info.get('52_week_high', 'N/A')}")
            print(f"   52 Week Low: ${info.get('52_week_low', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Consejos:")
        print("   - Verifica que tengas ALPHA_VANTAGE_API_KEY configurada")
        print("   - El plan gratuito tiene límites: 5 llamadas/minuto, 500/día")
        print("   - Si excedes el límite, espera unos minutos")


def ejemplo_comparar_fuentes():
    """Compara datos del mismo activo desde diferentes fuentes"""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Comparar Fuentes")
    print("=" * 60)
    
    extractor = DataExtractor()
    
    symbol = "AAPL"
    period = "3m"
    
    print(f"\n📊 Comparando datos de {symbol} desde diferentes fuentes...")
    
    results = {}
    
    # Yahoo Finance (siempre disponible)
    try:
        yahoo_data = extractor.download_historical_prices(symbol, period=period, source="yahoo")
        results["Yahoo Finance"] = yahoo_data.close.iloc[-1]
        print(f"✅ Yahoo Finance: ${results['Yahoo Finance']:.2f}")
    except Exception as e:
        print(f"❌ Yahoo Finance: {e}")
    
    # Stooq
    if "stooq" in extractor.get_supported_sources():
        try:
            stooq_data = extractor.download_historical_prices(f"{symbol}.US", period=period, source="stooq")
            results["Stooq"] = stooq_data.close.iloc[-1]
            print(f"✅ Stooq: ${results['Stooq']:.2f}")
        except Exception as e:
            print(f"❌ Stooq: {e}")
    
    # Alpha Vantage
    if "alpha_vantage" in extractor.get_supported_sources():
        try:
            av_data = extractor.download_historical_prices(symbol, period=period, source="alpha_vantage")
            results["Alpha Vantage"] = av_data.close.iloc[-1]
            print(f"✅ Alpha Vantage: ${results['Alpha Vantage']:.2f}")
        except Exception as e:
            print(f"❌ Alpha Vantage: {e}")
    
    if len(results) > 1:
        print(f"\n📈 Comparación de precios de cierre:")
        for source, price in results.items():
            print(f"   {source}: ${price:.2f}")
        
        # Calcular diferencia
        prices = list(results.values())
        if len(prices) > 1:
            diff = max(prices) - min(prices)
            diff_pct = (diff / min(prices)) * 100
            print(f"\n   Diferencia: ${diff:.2f} ({diff_pct:.2f}%)")


def main():
    """Ejecuta todos los ejemplos"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO: NUEVAS FUENTES DE DATOS")
    print("=" * 60)
    
    extractor = DataExtractor()
    print(f"\n📋 Fuentes disponibles: {extractor.get_supported_sources()}")
    
    # Ejecutar ejemplos
    ejemplo_fred()
    ejemplo_stooq()
    ejemplo_alpha_vantage()
    ejemplo_comparar_fuentes()
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)
    print("\n💡 Para más información, consulta GUIA_NUEVAS_FUENTES.md")


if __name__ == "__main__":
    main()

