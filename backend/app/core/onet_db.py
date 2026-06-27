"""O*NET Postgres connection from [onet] in config.toml."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import config

if TYPE_CHECKING:
    import psycopg


def connect() -> psycopg.Connection:
    import psycopg

    return psycopg.connect(config.onet.conninfo())
