"""
Debug: Simular exactamente lo que hace el menú principal
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_extractor import DataExtractor

def debug_get_news():
    """Debug exacto de lo que hace el menú"""
    print("=" * 60)
    print("DEBUG: Simulando llamada desde el menú")
    print("=" * 60)
    
    extractor = DataExtractor()
    symbol = "AAPL"
    limit = 5
    source = "yahoo"
    
    print(f"\nLlamando: extractor.get_news(symbol='{symbol}', limit={limit}, source='{source}')")
    
    try:
        news = extractor.get_news(symbol, limit=limit, source=source)
        
        print(f"\nResultado: {len(news)} noticias obtenidas")
        
        if news:
            print("\nDetalles de cada noticia:")
            for i, item in enumerate(news, 1):
                print(f"\n  Noticia {i}:")
                print(f"    - Tipo: {type(item)}")
                print(f"    - Título (raw): {repr(item.title)}")
                print(f"    - Título (str): {str(item.title)}")
                print(f"    - Título vacío?: {not item.title or not item.title.strip()}")
                print(f"    - Fecha: {item.date}")
                print(f"    - Resumen (len): {len(item.summary) if item.summary else 0}")
                print(f"    - URL: {item.url[:80] if item.url else 'None'}...")
        else:
            print("\nNo se obtuvieron noticias")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_get_news()

