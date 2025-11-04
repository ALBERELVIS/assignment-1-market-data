"""
Script para ejecutar el programa principal desde la raíz del proyecto
Este archivo permite ejecutar el programa sin problemas de importación
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Ahora importar y ejecutar
from main import main

if __name__ == "__main__":
    main()

