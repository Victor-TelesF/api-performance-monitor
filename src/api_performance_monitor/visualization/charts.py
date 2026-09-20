"""Gráficos de latência construídos com Matplotlib.

Cada função recebe um ``LatencyDataset`` e devolve uma ``Figure``. A ``Figure``
é o objeto que contém o gráfico; ela pode ser exportada com ``figure_to_png``.
As funções não usam ``pyplot`` nem abrem uma janela automaticamente.
"""

from collections import Counter

import numpy as np
from matplotlib.figure import Figure

from api_performance_monitor.domain import LatencyDataset


def create_latency_histogram(
    dataset: LatencyDataset, bins: int | None = None, *, show_percentiles: bool = True
) -> Figure:
    """Devolve um histograma das latências em uma ``Figure``.

    Cada barra conta medições dentro de um intervalo de latências em ms.
    ``bins`` define quantos intervalos usar; ``None`` deixa o NumPy escolher
    automaticamente. Com ``show_percentiles=True``, linhas verticais marcam
    p50, p90, p95 e p99. Não exibe nem salva a figura.

    Lança ``ValueError`` se ``bins`` não for um inteiro positivo ou ``None``.
    """
    if bins is not None and (isinstance(bins, bool) or not isinstance(bins, int) or bins < 1):
        raise ValueError("A quantidade de bins deve ser um inteiro positivo.")

    figure = Figure(figsize=(9, 5), layout="constrained")
    axes = figure.subplots()
    axes.hist(dataset.measurements, bins=bins if bins is not None else "auto", edgecolor="white")
    if show_percentiles:
        for label, value, color in (
            ("p50", dataset.p50(), "tab:green"),
            ("p90", dataset.p90(), "tab:orange"),
            ("p95", dataset.p95(), "tab:red"),
            ("p99", dataset.p99(), "tab:purple"),
        ):
            axes.axvline(value, color=color, linestyle="--", label=f"{label}: {value:g} ms")
        axes.legend()
    axes.set(title="Distribuição das latências", xlabel="Latência (ms)", ylabel="Frequência")
    axes.grid(axis="y", alpha=0.25)
    return figure


def create_latency_boxplot(dataset: LatencyDataset) -> Figure:
    """Devolve uma ``Figure`` com boxplot das latências em ms.

    A caixa representa Q1 a Q3, a linha interna representa a mediana e
    pontos além dos limites de 1,5 × IQR aparecem como possíveis outliers.
    Não exibe nem salva a figura.
    """
    figure = Figure(figsize=(7, 4), layout="constrained")
    axes = figure.subplots()
    axes.boxplot(dataset.measurements, patch_artist=True, whis=1.5)
    axes.set(title="Boxplot das latências", ylabel="Latência (ms)", xticks=[1], xticklabels=["Requisições"])
    axes.grid(axis="y", alpha=0.25)
    return figure


def create_latency_timeline(dataset: LatencyDataset) -> Figure:
    """Devolve uma ``Figure`` com latência por posição da medição.

    O eixo X começa em 1 e segue a ordem de chegada, não horários reais.
    O eixo Y mostra milissegundos, permitindo observar picos e tendências.
    Não exibe nem salva a figura.
    """
    figure = Figure(figsize=(9, 4), layout="constrained")
    axes = figure.subplots()
    order = range(1, dataset.count() + 1)
    axes.plot(order, dataset.measurements, marker="o", linewidth=1)
    axes.set(title="Latência por ordem da medição", xlabel="Ordem da medição", ylabel="Latência (ms)")
    axes.grid(alpha=0.25)
    return figure


def create_cumulative_distribution(dataset: LatencyDataset) -> Figure:
    """Devolve uma ``Figure`` com a distribuição acumulada empírica.

    Para cada latência distinta X, o eixo Y mostra a porcentagem de
    medições menores ou iguais a X. ``numpy.unique`` agrupa repetições e
    ``numpy.cumsum`` acumula suas contagens. A linha em degraus representa
    essa porcentagem, de 0 a 100%. Não exibe nem salva a figura.
    """
    values, frequencies = np.unique(dataset.measurements, return_counts=True)
    percentages = np.cumsum(frequencies) / dataset.count() * 100
    figure = Figure(figsize=(9, 4), layout="constrained")
    axes = figure.subplots()
    axes.step(values, percentages, where="post")
    axes.scatter(values, percentages, s=16)
    axes.set(
        title="Distribuição acumulada das latências",
        xlabel="Latência (ms)",
        ylabel="Requisições até esta latência (%)",
        ylim=(0, 105),
    )
    axes.grid(alpha=0.25)
    return figure


def create_latency_frequency_chart(dataset: LatencyDataset) -> Figure:
    """Devolve uma ``Figure`` com a contagem exata de cada latência.

    ``Counter`` agrupa valores idênticos; cada barra representa um valor
    distinto em ms e sua quantidade de ocorrências. É mais legível com
    poucos valores distintos. Não exibe nem salva a figura.
    """
    frequencies = Counter(dataset.measurements)
    values = sorted(frequencies)
    figure = Figure(figsize=(9, 4), layout="constrained")
    axes = figure.subplots()
    positions = range(len(values))
    axes.bar(positions, [frequencies[value] for value in values])
    axes.set_xticks(list(positions), [f"{value:g}" for value in values], rotation=45)
    axes.set(title="Frequência das latências", xlabel="Latência (ms)", ylabel="Ocorrências")
    axes.grid(axis="y", alpha=0.25)
    return figure
