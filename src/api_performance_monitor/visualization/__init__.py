"""Interface pública para criar figuras e convertê-las em PNG em memória.

As funções de gráfico devolvem ``matplotlib.figure.Figure``; ``figure_to_png``
devolve um ``io.BytesIO`` com os bytes da imagem.
"""

from .charts import (
    create_cumulative_distribution,
    create_latency_boxplot,
    create_latency_frequency_chart,
    create_latency_histogram,
    create_latency_timeline,
)
from .export import figure_to_png

__all__ = [
    "create_cumulative_distribution",
    "create_latency_boxplot",
    "create_latency_frequency_chart",
    "create_latency_histogram",
    "create_latency_timeline",
    "figure_to_png",
]
