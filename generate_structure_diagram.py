"""
Script para generar el diagrama de estructura del proyecto usando FossFLOW.
"""

from fossflow import FossFlow
import os

# Crear instancia de FossFlow
flow = FossFlow()

# Configurar el directorio del proyecto
project_dir = os.path.join(os.path.dirname(__file__), 'src')

# Generar diagrama
flow.generate_flowchart(
    project_dir=project_dir,
    output_file='docs/structure_diagram.png',
    format='png'
)

print("Diagrama de estructura generado en docs/structure_diagram.png")

