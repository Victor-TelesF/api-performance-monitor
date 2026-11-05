"""Limites dos identificadores SERIAL definidos na migração PostgreSQL."""

from typing import Annotated

from fastapi import Path

ResourceId = Annotated[int, Path(ge=1, le=2_147_483_647)]
