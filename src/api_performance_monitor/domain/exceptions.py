"""Exceções lançadas quando uma regra de ``LatencyDataset`` é violada.

Todas herdam de ``DomainError``, permitindo tratar qualquer erro do domínio
com um único ``except DomainError`` quando o detalhe não for necessário.
"""


class DomainError(Exception):
    """Base dos erros de validação e operação; não carrega um resultado."""


class EmptyLatencyDatasetError(DomainError):
    """O construtor recebeu uma coleção sem nenhuma medição."""


class InvalidLatencyError(DomainError):
    """Uma medição não é um número real, finito e não negativo."""


class LatencyNotFoundError(DomainError):
    """``remove`` tentou excluir uma latência ausente da coleção."""


class InsufficientMeasurementsError(DomainError):
    """Variância ou desvio amostral recebeu menos de duas medições."""


class DatasetWouldBecomeEmptyError(DomainError):
    """``remove`` tentou excluir a única medição restante."""


class InvalidPercentileError(DomainError):
    """O percentual não é real e finito dentro do intervalo de 0 a 100."""


class InvalidThresholdError(DomainError):
    """O limite de comparação não é real, finito e não negativo."""
