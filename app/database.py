"""Conexion y esquema de la base de datos PostgreSQL (Aiven)."""

from __future__ import annotations

from psycopg_pool import ConnectionPool

from .config import Settings

ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS celdas (
    numero INTEGER PRIMARY KEY,
    estado TEXT NOT NULL DEFAULT 'libre'
        CHECK (estado IN ('libre', 'ocupado')),
    placa TEXT,
    tipo TEXT CHECK (tipo IN ('carro', 'moto')),
    hora_ingreso TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id BIGSERIAL PRIMARY KEY,
    placa TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('carro', 'moto')),
    celda INTEGER NOT NULL REFERENCES celdas (numero),
    hora_ingreso TIMESTAMPTZ NOT NULL DEFAULT now(),
    hora_salida TIMESTAMPTZ,
    horas INTEGER,
    total_pagado NUMERIC(12, 2),
    pagado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_vehiculo_activo_placa
    ON vehiculos (placa)
    WHERE hora_salida IS NULL;

CREATE INDEX IF NOT EXISTS idx_vehiculos_ingreso
    ON vehiculos (hora_ingreso);

CREATE INDEX IF NOT EXISTS idx_vehiculos_salida
    ON vehiculos (hora_salida);
"""


def crear_pool(settings: Settings) -> ConnectionPool:
    """Crea un pool de conexiones a Aiven PostgreSQL."""
    pool = ConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=5,
        timeout=15,
        open=False,
        kwargs={"connect_timeout": 15},
    )
    pool.open(wait=True, timeout=20)
    return pool


def inicializar_esquema(pool: ConnectionPool) -> None:
    with pool.connection() as conn:
        conn.execute(ESQUEMA_SQL)
