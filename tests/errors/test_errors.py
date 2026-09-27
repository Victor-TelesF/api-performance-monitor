"""Testes de erro para `DatasetNotFoundError` (errors/errors.py).

Cobre apenas a formatação da mensagem e o armazenamento do dataset_id;
não depende de FastAPI nem de banco de dados.
"""

from api_performance_monitor.errors.errors import DatasetNotFoundError


def test_dataset_not_found_error_message_without_id() -> None:
    """Sem dataset_id, a mensagem deve ser genérica ('Dataset não encontrado.')."""
    error = DatasetNotFoundError()

    assert str(error) == "Dataset não encontrado."


def test_dataset_not_found_error_message_with_id() -> None:
    """Com dataset_id, a mensagem deve incluir o número informado."""
    error = DatasetNotFoundError(dataset_id=42)

    assert str(error) == "Dataset 42 não encontrado."


def test_dataset_not_found_error_stores_dataset_id() -> None:
    """O atributo `dataset_id` da exceção deve guardar o valor recebido no construtor."""
    error = DatasetNotFoundError(dataset_id=42)

    assert error.dataset_id == 42
