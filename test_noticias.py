"""
Script de prueba para verificar que las funciones de noticias funcionan correctamente
Prueba las funciones 4 (recomendaciones), 5 (noticias) y 7 (todos los datos)
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_extractor import DataExtractor

def test_funcion_5_noticias():
    """Prueba la función 5: Extraer noticias"""
    print("=" * 60)
    print("TEST 1: Función 5 - Extraer Noticias")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbol = "AAPL"  # Apple como prueba
    limit = 5
    
    print(f"\nObteniendo {limit} noticias para {symbol}...")
    
    try:
        news = extractor.get_news(symbol, limit=limit, source="yahoo")
        
        print(f"\nOK: {len(news)} noticias encontradas")
        
        if news:
            print("\nNoticias obtenidas:")
            for i, item in enumerate(news, 1):
                print(f"\n   {i}. {item.title}")
                print(f"      - Fecha: {item.date}")
                if item.summary:
                    summary_short = item.summary[:100] if len(item.summary) > 100 else item.summary
                    print(f"      - Resumen: {summary_short}...")
                if item.url:
                    print(f"      - URL: {item.url[:80]}...")
            return True
        else:
            print("\nAVISO: No se encontraron noticias")
            return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_funcion_4_recomendaciones():
    """Prueba la función 4: Recomendaciones"""
    print("\n" + "=" * 60)
    print("TEST 2: Función 4 - Recomendaciones")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbol = "AAPL"
    
    print(f"\nObteniendo recomendaciones para {symbol}...")
    
    try:
        recommendations = extractor.get_recommendations(symbol, source="yahoo")
        
        print(f"\nOK: {len(recommendations)} recomendaciones encontradas")
        
        if recommendations:
            print("\nRecomendaciones obtenidas:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"\n   {i}. {rec.firm}")
                print(f"      - Rating: {rec.rating}")
                print(f"      - Fecha: {rec.date}")
                if rec.target_price:
                    print(f"      - Precio objetivo: ${rec.target_price:.2f}")
            return True
        else:
            print("\nAVISO: No se encontraron recomendaciones")
            return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_funcion_7_todos_los_datos():
    """Prueba la función 7: Todos los datos (incluyendo noticias)"""
    print("\n" + "=" * 60)
    print("TEST 3: Función 7 - Todos los Datos (incluyendo noticias)")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbol = "AAPL"
    news_limit = 5
    
    print(f"\nObteniendo todos los datos para {symbol}...")
    print(f"   Incluyendo: precios, noticias ({news_limit}), recomendaciones, info")
    
    try:
        all_data = extractor.get_all_data(
            symbol=symbol,
            source="yahoo",
            include_news=True,
            include_recommendations=True,
            include_info=True,
            news_limit=news_limit
        )
        
        print(f"\nOK: Datos obtenidos exitosamente")
        print(f"\nResumen:")
        print(f"   - Precios: {'OK' if all_data['prices'] else 'FAIL'}")
        if all_data['prices']:
            print(f"     Dias: {len(all_data['prices'])}")
        
        print(f"   - Noticias: {len(all_data['news'])}")
        if all_data['news']:
            print("\nNoticias encontradas:")
            for i, item in enumerate(all_data['news'][:3], 1):
                print(f"   {i}. {item.title}")
                print(f"      Fecha: {item.date}")
        
        print(f"   - Recomendaciones: {len(all_data['recommendations'])}")
        if all_data['recommendations']:
            print("\nRecomendaciones encontradas:")
            for i, rec in enumerate(all_data['recommendations'][:3], 1):
                print(f"   {i}. {rec.firm} - {rec.rating}")
        
        print(f"   - Info empresa: {'OK' if all_data['company_info'] else 'FAIL'}")
        
        # Verificar que las noticias se obtuvieron correctamente
        if len(all_data['news']) > 0:
            print("\nTEST EXITOSO: Las noticias se obtuvieron correctamente en get_all_data")
            return True
        else:
            print("\nTEST PARCIAL: get_all_data funciono pero no obtuvo noticias")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("PRUEBAS DE FUNCIONES DE NOTICIAS")
    print("=" * 60)
    print("\nProbando funciones 4, 5 y 7 relacionadas con noticias...")
    
    resultados = {
        "Función 5 (Noticias)": test_funcion_5_noticias(),
        "Función 4 (Recomendaciones)": test_funcion_4_recomendaciones(),
        "Función 7 (Todos los datos)": test_funcion_7_todos_los_datos()
    }
    
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    for test_name, resultado in resultados.items():
        status = "PASO" if resultado else "FALLO"
        print(f"{test_name}: {status}")
    
    total_pasados = sum(resultados.values())
    total_tests = len(resultados)
    
    print(f"\nTotal: {total_pasados}/{total_tests} tests pasaron")
    
    if total_pasados == total_tests:
        print("\nTODOS LOS TESTS PASARON! Las funciones funcionan correctamente.")
    else:
        print("\nAlgunos tests fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()

