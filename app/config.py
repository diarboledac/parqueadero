"""Configuracion de la aplicacion Parqueadero SGP-8."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _limpiar(valor: str | None) -> str:
    return (valor or "").strip().strip('"').strip("'")


def _normalizar_url(url: str) -> str:
    """psycopg acepta ambos esquemas, pero normalizamos a postgresql://."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str
    precio_carro: int
    precio_moto: int
    total_celdas: int
    app_host: str
    app_port: int
    zona_horaria: str


def get_settings() -> Settings:
    database_url = _normalizar_url(_limpiar(os.getenv("DATABASE_URL")))
    if not database_url:
        raise RuntimeError(
            "Falta DATABASE_URL. Copia .env.example a .env y configura la "
            "cadena de conexion de Aiven PostgreSQL."
        )

    return Settings(
        database_url=database_url,
        precio_carro=int(_limpiar(os.getenv("PRECIO_CARRO")) or "3000"),
        precio_moto=int(_limpiar(os.getenv("PRECIO_MOTO")) or "1500"),
        total_celdas=int(_limpiar(os.getenv("TOTAL_CELDAS")) or "8"),
        app_host=_limpiar(os.getenv("APP_HOST")) or "127.0.0.1",
        app_port=int(_limpiar(os.getenv("APP_PORT")) or "8000"),
        zona_horaria=_limpiar(os.getenv("ZONA_HORARIA")) or "America/Bogota",
    )
