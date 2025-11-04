"""
Script para ejecutar el programa principal desde la raíz del proyecto
Este archivo permite ejecutar el programa sin problemas de importación
Instala automáticamente las dependencias si faltan
"""

import sys
import subprocess
from pathlib import Path


def ensure_dependencies():
    """
    Verifica e instala dependencias automáticamente si faltan
    """
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
    }
    
    missing = []
    for package_name, module_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("=" * 60)
        print("INSTALANDO DEPENDENCIAS FALTANTES")
        print("=" * 60)
        print(f"Faltan: {', '.join(missing)}")
        print("Instalando automáticamente desde requirements.txt...\n")
        
        requirements_file = Path(__file__).parent / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ])
                print("\n✅ Dependencias instaladas correctamente")
                print("=" * 60)
                return True
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error instalando dependencias: {e}")
                print("Intenta ejecutar manualmente: pip install -r requirements.txt")
                return False
        else:
            print("❌ No se encontró requirements.txt")
            return False
    
    return True


# Verificar e instalar dependencias antes de continuar
if not ensure_dependencies():
    print("\n⚠️  No se pudieron instalar las dependencias.")
    print("Por favor, ejecuta manualmente: pip install -r requirements.txt")
    sys.exit(1)

# Agregar el directorio raíz del proyecto al path
# Esto permite que Python reconozca 'src' como un paquete
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar main como módulo desde el paquete src
# Usar importación normal para que Python reconozca src como paquete
from src.main import main

if __name__ == "__main__":
    main()
