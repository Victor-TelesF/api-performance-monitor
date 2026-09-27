"""Traduz erros conhecidos da aplicação para respostas HTTP padronizadas.

``register_exception_handlers`` instala os handlers uma vez na aplicação.
As rotas podem deixar essas exceções propagarem sem repetir ``try/except``.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..domain.exceptions import (
    DatasetWouldBecomeEmptyError,
    DomainError,
    LatencyNotFoundError,
)
from .errors import DatasetNotFoundError


async def handle_request_validation_error(
    _request: Request, _error: RequestValidationError
) -> JSONResponse:
    """Normaliza erros estruturais de entrada no contrato de erro da API."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Dados de entrada inválidos."},
    )


async def handle_dataset_not_found(
    _request: Request, error: DatasetNotFoundError
) -> JSONResponse:
    """Devolve HTTP 404 com a mensagem de um dataset ausente em ``detail``."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(error)},
    )


async def handle_domain_error(_request: Request, error: DomainError) -> JSONResponse:
    """Converte um erro de regra em 404, 409 ou 422, conforme o caso.

    Medição ausente vira 404; remover a última medição vira 409; entradas
    inválidas e dados insuficientes para um cálculo viram 422. A resposta
    mantém a mensagem do domínio no campo JSON ``detail``.
    """
    if isinstance(error, LatencyNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, DatasetWouldBecomeEmptyError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT

    return JSONResponse(status_code=status_code, content={"detail": str(error)})


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro da aplicação e devolve ``None``.

    Erros de validação do FastAPI e erros próprios do projeto passam a usar
    o mesmo formato de resposta, com uma ``str`` no campo ``detail``.
    """
    app.add_exception_handler(
        RequestValidationError,
        handle_request_validation_error,
    )
    app.add_exception_handler(DatasetNotFoundError, handle_dataset_not_found)
    app.add_exception_handler(DomainError, handle_domain_error)
