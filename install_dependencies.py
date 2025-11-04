"""
Script para instalar dependencias automáticamente
Se ejecuta automáticamente antes de importar los módulos
"""

import subprocess
import sys
from pathlib import Path


def install_requirements():
    """
    Instala las dependencias desde requirements.txt si no están instaladas
    """
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("⚠️  No se encontró requirements.txt")
        return False
    
    print("=" * 60)
    print("INSTALANDO DEPENDENCIAS")
    print("=" * 60)
    print("\nInstalando paquetes desde requirements.txt...")
    print("(Esto puede tardar unos minutos la primera vez)\n")
    
    try:
        # Ejecutar pip install
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Dependencias instaladas correctamente")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias:")
        print(e.stderr)
        print("\nIntenta ejecutar manualmente:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def check_and_install():
    """
    Verifica si las dependencias están instaladas e instala si faltan
    """
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
    }
    
    missing_packages = []
    
    # Verificar qué paquetes faltan
    for package_name, module_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    # Si faltan paquetes, instalar
    if missing_packages:
        print(f"\n⚠️  Faltan las siguientes dependencias: {', '.join(missing_packages)}")
        print("Instalando automáticamente...\n")
        return install_requirements()
    else:
        return True


if __name__ == "__main__":
    # Si se ejecuta directamente, instalar dependencias
    install_requirements()

