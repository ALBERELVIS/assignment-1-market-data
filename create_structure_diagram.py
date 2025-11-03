"""
Script para crear un diagrama de estructura del proyecto.
Genera un diagrama visual mostrando las clases, sus relaciones y dependencias.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Crear figura
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Colores
colors = {
    'extractor': '#E8F4F8',
    'datamodel': '#FFF4E6',
    'portfolio': '#E8F5E9',
    'utils': '#F3E5F5',
    'plots': '#FFE0E0'
}

# Definir cajas con sus posiciones
boxes = {
    'ExtractorBase': {'pos': (1.5, 8), 'size': (1.5, 0.8), 'color': colors['extractor']},
    'YFinanceExtractor': {'pos': (1.5, 6.5), 'size': (1.5, 0.8), 'color': colors['extractor']},
    'PriceSeries': {'pos': (4.5, 8), 'size': (1.5, 0.8), 'color': colors['datamodel']},
    'Portfolio': {'pos': (4.5, 6.5), 'size': (1.5, 0.8), 'color': colors['datamodel']},
    'MonteCarloSimulation': {'pos': (7.5, 8), 'size': (1.5, 0.8), 'color': colors['portfolio']},
    'utils.py': {'pos': (1.5, 4.5), 'size': (1.5, 0.8), 'color': colors['utils']},
    'plots.py': {'pos': (4.5, 4.5), 'size': (1.5, 0.8), 'color': colors['plots']},
    'download_price_series': {'pos': (1.5, 3), 'size': (1.5, 0.6), 'color': colors['extractor']},
}

# Dibujar cajas
for name, props in boxes.items():
    x, y = props['pos']
    w, h = props['size']
    color = props['color']
    
    fancy_box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.1",
        edgecolor='black',
        facecolor=color,
        linewidth=1.5
    )
    ax.add_patch(fancy_box)
    
    # Texto
    ax.text(x, y, name, ha='center', va='center', 
            fontsize=9, fontweight='bold', wrap=True)

# Flechas de herencia
arrows = [
    # YFinanceExtractor hereda de ExtractorBase
    ((1.5, 7.3), (1.5, 7.7)),
    # Portfolio contiene PriceSeries
    ((4.5, 7.3), (4.5, 7.7)),
    # Portfolio usa MonteCarloSimulation
    ((6.0, 6.9), (7.0, 7.5)),
    # ExtractorBase usa utils
    ((1.5, 6.1), (1.5, 5.0)),
    # PriceSeries usa utils
    ((4.5, 7.3), (4.5, 5.0)),
    # Portfolio usa plots
    ((5.5, 6.5), (5.5, 5.0)),
    # download_price_series usa extractores
    ((1.5, 5.3), (1.5, 4.0)),
]

# Dibujar flechas
for start, end in arrows:
    arrow = FancyArrowPatch(
        start, end,
        arrowstyle='->',
        mutation_scale=20,
        linewidth=1.5,
        color='#333333',
        zorder=1
    )
    ax.add_patch(arrow)

# Título
ax.text(5, 9.5, 'Estructura del Proyecto - Market Data Toolkit', 
        ha='center', va='center', fontsize=16, fontweight='bold')

# Leyenda de módulos
legend_elements = [
    mpatches.Patch(facecolor=colors['extractor'], edgecolor='black', label='Extractor Module'),
    mpatches.Patch(facecolor=colors['datamodel'], edgecolor='black', label='Data Models'),
    mpatches.Patch(facecolor=colors['portfolio'], edgecolor='black', label='Portfolio Analysis'),
    mpatches.Patch(facecolor=colors['utils'], edgecolor='black', label='Utilities'),
    mpatches.Patch(facecolor=colors['plots'], edgecolor='black', label='Visualizations'),
]

ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

# Notas
notes = [
    "• ExtractorBase: Clase abstracta base para extractores",
    "• YFinanceExtractor: Implementación para Yahoo Finance",
    "• PriceSeries: Dataclass para series de precios individuales",
    "• Portfolio: Dataclass para carteras (contiene múltiples PriceSeries)",
    "• MonteCarloSimulation: Clase para simulaciones de Monte Carlo",
    "• utils.py: Funciones de limpieza y validación",
    "• plots.py: Funciones de visualización",
]

y_pos = 2.5
for note in notes:
    ax.text(0.2, y_pos, note, ha='left', va='center', fontsize=8)
    y_pos -= 0.25

plt.tight_layout()
plt.savefig('docs/structure_diagram.png', dpi=300, bbox_inches='tight')
print("Diagrama de estructura guardado en docs/structure_diagram.png")
plt.close()

