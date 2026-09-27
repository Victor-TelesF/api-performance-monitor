"""Testes do registro e da documentação do contrato comum de erro 422."""

from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from api_performance_monitor.errors.http_error_handlers import (
    handle_request_validation_error,
)
from main import app


def test_request_validation_handler_is_registered() -> None:
    """Confirma que a aplicação registra o handler do erro de requisição."""
    assert (
        app.exception_handlers[RequestValidationError]
        is handle_request_validation_error
    )


def test_openapi_documents_standard_422_schema() -> None:
    """Confirma que o OpenAPI referencia o schema comum nas respostas 422."""
    operation = app.openapi()["paths"][
        "/Datasets/measurements/contains/{dataset_id}"
    ]["get"]

    schema = operation["responses"]["422"]["content"]["application/json"]["schema"]

    assert schema == {"$ref": "#/components/schemas/ErrorResponseSchema"}


def test_invalid_query_returns_standard_422_response(client: TestClient) -> None:
    """Retorna o contrato comum de 422 quando um query param não é numérico."""
    response = client.get(
        "/Datasets/measurements/contains/1",
        params={"measurement": "invalid"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Dados de entrada inválidos."}
