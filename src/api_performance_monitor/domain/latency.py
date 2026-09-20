"""Interface para armazenar medições e consultar suas estatísticas.

As medições são guardadas como ``float`` em milissegundos. Os cálculos que usam
NumPy ficam em ``statistics.py``; esta classe oferece nomes voltados ao domínio.
"""

from collections.abc import Iterable
from math import sqrt

import numpy as np

from . import statistics
from .exceptions import (
    DatasetWouldBecomeEmptyError,
    EmptyLatencyDatasetError,
    InvalidLatencyError,
    LatencyNotFoundError,
)
from .validation import Number, validate_latency, validate_percentile, validate_threshold


class LatencyDataset:
    """Coleção não vazia de latências na ordem em que foram recebidas.

    O construtor copia os valores para uma tupla interna. A coleção só muda por
    ``add`` e ``remove``; consultar ``measurements`` não permite alterá-la.
    Resultados de latência e dispersão são ``float``; contagens são ``int``
    e operações que listam medições devolvem tuplas.
    """

    def __init__(self, measurements: Iterable[Number]) -> None:
        """Cria o dataset a partir de uma sequência ou outro iterável de números.

        Aceita números reais e ``Decimal``; converte cada medição para ``float``.
        Rejeita coleção vazia, valores negativos, booleanos, NaN e infinitos
        com exceções do domínio. Não devolve valor.
        """
        try:
            self._measurements = tuple(validate_latency(value) for value in measurements)
        except TypeError as exc:
            raise InvalidLatencyError("As medições devem formar uma coleção de números.") from exc
        if not self._measurements:
            raise EmptyLatencyDatasetError("O dataset precisa de pelo menos uma medição.")

    @property
    def measurements(self) -> tuple[float, ...]:
        """Devolve as latências em ms como tupla imutável, na ordem original."""
        return self._measurements

    def add(self, latency: Number) -> None:
        """Valida e acrescenta uma latência em ms ao fim da coleção; devolve ``None``."""
        self._measurements += (validate_latency(latency),)

    def remove(self, latency: Number) -> None:
        """Remove a primeira ocorrência da latência informada; devolve ``None``.

        Lança ``LatencyNotFoundError`` se o valor não existir e
        ``DatasetWouldBecomeEmptyError`` se for a última medição.
        """
        value = validate_latency(latency)
        try:
            index = self._measurements.index(value)
        except ValueError as exc:
            raise LatencyNotFoundError(f"A latência {value} ms não foi encontrada.") from exc
        if len(self._measurements) == 1:
            raise DatasetWouldBecomeEmptyError("A última medição não pode ser removida.")
        self._measurements = self._measurements[:index] + self._measurements[index + 1 :]

    def contains(self, latency: Number) -> bool:
        """Devolve ``True`` se houver pelo menos uma ocorrência exata do valor em ms."""
        return validate_latency(latency) in self._measurements

    def count_occurrences(self, latency: Number) -> int:
        """Devolve quantas medições são exatamente iguais ao valor em ms."""
        return self._measurements.count(validate_latency(latency))

    def count(self) -> int:
        """Devolve a quantidade total de medições, incluindo valores repetidos."""
        return len(self._measurements)

    def total(self) -> float:
        """Devolve a soma de todas as latências, em ms."""
        return float(sum(self._measurements))

    def minimum(self) -> float:
        """Devolve a menor latência observada, em ms."""
        return min(self._measurements)

    def maximum(self) -> float:
        """Devolve a maior latência observada, em ms."""
        return max(self._measurements)

    def amplitude(self) -> float:
        """Devolve a diferença entre a maior e a menor latência, em ms."""
        return self.maximum() - self.minimum()

    def mean(self) -> float:
        """Devolve a média aritmética das latências, em ms.

        Usa ``numpy.mean``: soma as medições e divide pela quantidade delas.
        """
        return float(np.mean(self._measurements))

    def median(self) -> float:
        """Devolve a mediana (p50), em ms: metade das medições fica até esse valor."""
        return self.percentile(50)

    def mode(self) -> tuple[float, ...]:
        """Devolve as latências mais frequentes, em ordem crescente.

        Se todas as latências distintas ocorrerem com a mesma frequência,
        devolve ``()``: não há uma moda significativa neste critério.
        """
        return statistics.modes(self._measurements)

    def variance(self, *, sample: bool = False) -> float:
        """Devolve a dispersão quadrática em ms².

        Com ``sample=False``, divide a soma dos desvios quadráticos por N
        (variância populacional). Com ``sample=True``, divide por N−1
        (variância amostral) e exige ao menos duas medições.
        """
        return statistics.variance(self._measurements, sample=sample)

    def standard_deviation(self, *, sample: bool = False) -> float:
        """Devolve a raiz da variância, em ms; usa a mesma opção ``sample``.

        O resultado volta à unidade original das latências e indica o
        espalhamento típico em torno da média.
        """
        return sqrt(self.variance(sample=sample))

    def first_quartile(self) -> float:
        """Devolve Q1 (p25), em ms: cerca de 25% das medições ficam até ele."""
        return self.percentile(25)

    def second_quartile(self) -> float:
        """Devolve Q2 (p50), em ms; é o mesmo valor da mediana."""
        return self.percentile(50)

    def third_quartile(self) -> float:
        """Devolve Q3 (p75), em ms: cerca de 75% das medições ficam até ele."""
        return self.percentile(75)

    def interquartile_range(self) -> float:
        """Devolve Q3 − Q1, em ms, medindo a dispersão da metade central."""
        return self.third_quartile() - self.first_quartile()

    def percentile(self, percent: Number) -> float:
        """Devolve o percentil solicitado, em ms.

        ``percent`` vai de 0 a 100, inclusive; 95 corresponde ao p95.
        Usa interpolação linear do NumPy quando a posição cai entre duas
        medições. Um percentual inválido gera ``InvalidPercentileError``.
        """
        return statistics.percentile(self._measurements, validate_percentile(percent))

    def p50(self) -> float:
        """Devolve o percentil 50, em ms; equivale à mediana."""
        return self.percentile(50)

    def p90(self) -> float:
        """Devolve o percentil 90, em ms, usando interpolação linear."""
        return self.percentile(90)

    def p95(self) -> float:
        """Devolve o percentil 95, em ms, usando interpolação linear."""
        return self.percentile(95)

    def p99(self) -> float:
        """Devolve o percentil 99, em ms, usando interpolação linear."""
        return self.percentile(99)

    def outliers(self) -> tuple[float, ...]:
        """Devolve possíveis outliers em ms, preservando ordem e repetições.

        Considera valores abaixo de Q1 − 1,5 × IQR ou acima de Q3 + 1,5 × IQR.
        Devolve ``()`` se nenhuma medição estiver fora desses limites.
        """
        return statistics.outliers(self._measurements)

    def count_above(self, threshold: Number) -> int:
        """Devolve quantas medições são estritamente maiores que o limite em ms.

        O limite deve ser um número real, finito e não negativo.
        """
        limit = validate_threshold(threshold)
        return sum(value > limit for value in self._measurements)

    def proportion_above(self, threshold: Number) -> float:
        """Devolve a fração de medições acima do limite, entre 0.0 e 1.0.

        Por exemplo, 0.25 significa que 25% das medições excedem o limite.
        """
        return self.count_above(threshold) / self.count()

    def count_at_or_below(self, threshold: Number) -> int:
        """Devolve quantas medições são menores ou iguais ao limite em ms."""
        return self.count() - self.count_above(threshold)
