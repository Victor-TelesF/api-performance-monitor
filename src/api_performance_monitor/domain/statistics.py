"""Cálculos internos sobre sequências não vazias de latências validadas.

As funções não modificam a sequência recebida. ``LatencyDataset`` valida
os argumentos antes de chamá-las e expõe os resultados na API pública.
"""

from collections import Counter
from collections.abc import Sequence

import numpy as np

from .exceptions import InsufficientMeasurementsError


def modes(values: Sequence[float]) -> tuple[float, ...]:
    """Devolve as latências com maior frequência, em ordem crescente.

    ``Counter`` conta quantas vezes cada valor aparece. Se todas as frequências
    forem iguais, devolve uma tupla vazia por não haver moda significativa.
    """
    frequencies = Counter(values)
    highest_frequency = max(frequencies.values())
    if highest_frequency == 1 or len(set(frequencies.values())) == 1:
        return ()
    return tuple(sorted(value for value, count in frequencies.items() if count == highest_frequency))


def percentile(values: Sequence[float], percent: float) -> float:
    """Devolve o percentil ``percent`` da sequência, como ``float``.

    ``numpy.percentile`` ordena os valores para o cálculo e interpola
    linearmente quando o percentual cai entre duas posições observadas.
    ``percent`` já deve estar validado no intervalo de 0 a 100.
    """
    return float(np.percentile(values, percent))


def variance(values: Sequence[float], *, sample: bool = False) -> float:
    """Devolve a variância em ms² calculada com ``numpy.var``.

    ``ddof=0`` divide por N para a população; ``ddof=1`` divide por N−1 para
    uma amostra. Com ``sample=True`` e menos de duas medições, lança
    ``InsufficientMeasurementsError``.
    """
    if sample and len(values) < 2:
        raise InsufficientMeasurementsError(
            "A variância amostral exige pelo menos duas medições."
        )
    return float(np.var(values, ddof=1 if sample else 0))


def outliers(values: Sequence[float]) -> tuple[float, ...]:
    """Devolve medições fora dos limites de 1,5 × IQR, na ordem original.

    O IQR é Q3 − Q1. Retorna valores estritamente abaixo de Q1 − 1,5 × IQR
    ou acima de Q3 + 1,5 × IQR, incluindo ocorrências repetidas. Se não
    houver valores assim, devolve ``()``.
    """
    first = percentile(values, 25)
    third = percentile(values, 75)
    spread = third - first
    lower = first - 1.5 * spread
    upper = third + 1.5 * spread
    return tuple(value for value in values if value < lower or value > upper)
