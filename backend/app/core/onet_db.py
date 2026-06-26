"""O*NET Postgres connection from [onet] in config.toml."""

from __future__ import annotations

import psycopg

from app.core.config import config


def connect() -> psycopg.Connection:
    return psycopg.connect(config.onet.conninfo())
