"""Schemas compartilhados pelas respostas de erro da API."""

from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    """Contrato HTTP comum para erros conhecidos da aplicação."""

    detail: str
