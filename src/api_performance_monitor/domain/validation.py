"""Validação dos valores recebidos e conversão para ``float``.

``Number`` aceita números reais de Python/NumPy e ``Decimal``. Booleanos são
rejeitados, embora em Python ``bool`` seja uma subclasse de ``int``.
"""

from decimal import Decimal, InvalidOperation
from math import isfinite
from numbers import Real
from typing import TypeAlias

from .exceptions import InvalidLatencyError, InvalidPercentileError, InvalidThresholdError

Number: TypeAlias = Real | Decimal


def _nonnegative_finite(value: Number, error: type[Exception], name: str) -> float:
    """Converte um número real válido para ``float`` ou lança ``error``.

    Exige valor não negativo e finito; ``name`` identifica o campo na mensagem.
    A comparação antes da conversão impede aceitar ``Decimal`` negativo tão
    pequeno que seria arredondado para ``-0.0``.
    """
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise error(f"{name} deve ser um número real, finito e não negativo.")
    try:
        if value < 0:
            raise error(f"{name} deve ser um número real, finito e não negativo.")
        number = float(value)
    except (OverflowError, ValueError, TypeError, InvalidOperation) as exc:
        raise error(f"{name} deve ser um número real, finito e não negativo.") from exc
    if not isfinite(number):
        raise error(f"{name} deve ser um número real, finito e não negativo.")
    return number


def validate_latency(value: Number) -> float:
    """Devolve a medição em ms como ``float`` ou lança ``InvalidLatencyError``."""
    return _nonnegative_finite(value, InvalidLatencyError, "A latência")


def validate_threshold(value: Number) -> float:
    """Devolve o limite em ms como ``float`` ou lança ``InvalidThresholdError``."""
    return _nonnegative_finite(value, InvalidThresholdError, "O limite")


def validate_percentile(value: Number) -> float:
    """Devolve um percentual entre 0 e 100 como ``float``.

    Rejeita booleanos, números fora do intervalo, NaN e infinitos com
    ``InvalidPercentileError``. Compara o valor original antes da conversão
    para não aceitar por arredondamento um ``Decimal`` acima de 100.
    """
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise InvalidPercentileError("O percentil deve ser um número entre 0 e 100.")
    try:
        if not 0 <= value <= 100:
            raise InvalidPercentileError("O percentil deve ser um número entre 0 e 100.")
        number = float(value)
    except (OverflowError, ValueError, TypeError, InvalidOperation) as exc:
        raise InvalidPercentileError("O percentil deve ser um número entre 0 e 100.") from exc
    if not isfinite(number):
        raise InvalidPercentileError("O percentil deve ser um número entre 0 e 100.")
    return number
