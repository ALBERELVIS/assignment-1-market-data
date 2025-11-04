"""
Script para ejecutar el programa principal desde la raíz del proyecto
Este archivo permite ejecutar el programa sin problemas de importación
Instala automáticamente las dependencias si faltan usando install_dependencies.py
"""

import sys
from pathlib import Path

# Importar funciones de instalación desde el módulo dedicado
from install_dependencies import check_and_install

# Verificar e instalar dependencias antes de continuar
if not check_and_install():
    print("\n⚠️  No se pudieron instalar las dependencias.")
    print("Por favor, ejecuta manualmente: pip install -r requirements.txt")
    print("O ejecuta: python install_dependencies.py")
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
