"""Acceso a datos PostgreSQL para el Parqueadero SGP-8."""

from __future__ import annotations

from datetime import date

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import Settings


class PostgresRepository:
    """Repositorio con todas las operaciones contra Aiven PostgreSQL."""

    def __init__(self, pool: ConnectionPool, settings: Settings) -> None:
        self.pool = pool
        self.settings = settings

    # ------------------------------------------------------------------
    # Configuracion
    # ------------------------------------------------------------------
    def sembrar_config(self, settings: Settings) -> None:
        valores = {
            "precio_carro": str(settings.precio_carro),
            "precio_moto": str(settings.precio_moto),
            "total_celdas": str(settings.total_celdas),
        }
        with self.pool.connection() as conn:
            for clave, valor in valores.items():
                conn.execute(
                    """
                    INSERT INTO configuracion (clave, valor)
                    VALUES (%s, %s)
                    ON CONFLICT (clave) DO NOTHING
                    """,
                    (clave, valor),
                )

    def obtener_config(self) -> dict[str, str]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT clave, valor FROM configuracion")
                return {fila["clave"]: fila["valor"] for fila in cur.fetchall()}

    def actualizar_config(self, clave: str, valor: str) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO configuracion (clave, valor)
                VALUES (%s, %s)
                ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
                """,
                (clave, valor),
            )

    def precio_hora(self, tipo: str) -> int:
        config = self.obtener_config()
        clave = "precio_carro" if tipo == "carro" else "precio_moto"
        defecto = self.settings.precio_carro if tipo == "carro" else self.settings.precio_moto
        return int(config.get(clave, defecto))

    # ------------------------------------------------------------------
    # Celdas
    # ------------------------------------------------------------------
    def sincronizar_celdas(self, total: int) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO celdas (numero)
                SELECT generate_series(1, %s)
                ON CONFLICT (numero) DO NOTHING
                """,
                (total,),
            )
            conn.execute(
                "DELETE FROM celdas WHERE numero > %s AND estado = 'libre'",
                (total,),
            )

    def listar_celdas(self) -> list[dict]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT numero, estado, placa, tipo, hora_ingreso,
                           CASE
                               WHEN estado = 'ocupado' AND hora_ingreso IS NOT NULL
                               THEN GREATEST(
                                   1,
                                   CEIL(EXTRACT(EPOCH FROM (now() - hora_ingreso)) / 3600.0)
                               )::int
                               ELSE NULL
                           END AS horas_en_curso
                    FROM celdas
                    ORDER BY numero
                    """
                )
                return cur.fetchall()

    def celda_libre(self) -> int | None:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT numero FROM celdas WHERE estado = 'libre' ORDER BY numero LIMIT 1"
                )
                fila = cur.fetchone()
                return fila[0] if fila else None

    def vehiculo_activo(self, placa: str) -> dict | None:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, placa, tipo, celda, hora_ingreso,
                           GREATEST(
                               1,
                               CEIL(EXTRACT(EPOCH FROM (now() - hora_ingreso)) / 3600.0)
                           )::int AS horas_en_curso
                    FROM vehiculos
                    WHERE placa = %s AND hora_salida IS NULL
                    ORDER BY hora_ingreso DESC
                    LIMIT 1
                    """,
                    (placa,),
                )
                return cur.fetchone()

    # ------------------------------------------------------------------
    # Movimientos
    # ------------------------------------------------------------------
    def registrar_ingreso(self, placa: str, tipo: str, celda: int) -> dict:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    UPDATE celdas
                    SET estado = 'ocupado', placa = %s, tipo = %s, hora_ingreso = now()
                    WHERE numero = %s AND estado = 'libre'
                    RETURNING numero, hora_ingreso
                    """,
                    (placa, tipo, celda),
                )
                actualizada = cur.fetchone()
                if actualizada is None:
                    raise ValueError("La celda ya fue ocupada por otro ingreso.")

                cur.execute(
                    """
                    INSERT INTO vehiculos (placa, tipo, celda)
                    VALUES (%s, %s, %s)
                    RETURNING id, placa, tipo, celda, hora_ingreso
                    """,
                    (placa, tipo, celda),
                )
                return cur.fetchone()

    def registrar_salida(self, vehiculo_id: int, precio_hora: int) -> dict:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, placa, tipo, celda, hora_ingreso,
                           GREATEST(
                               1,
                               CEIL(EXTRACT(EPOCH FROM (now() - hora_ingreso)) / 3600.0)
                           )::int AS horas
                    FROM vehiculos
                    WHERE id = %s AND hora_salida IS NULL
                    FOR UPDATE
                    """,
                    (vehiculo_id,),
                )
                vehiculo = cur.fetchone()
                if vehiculo is None:
                    raise ValueError("El vehiculo ya no esta activo.")

                total = vehiculo["horas"] * precio_hora
                cur.execute(
                    """
                    UPDATE vehiculos
                    SET hora_salida = now(), horas = %s, total_pagado = %s, pagado = TRUE
                    WHERE id = %s
                    RETURNING hora_salida
                    """,
                    (vehiculo["horas"], total, vehiculo_id),
                )
                salida = cur.fetchone()

                cur.execute(
                    """
                    UPDATE celdas
                    SET estado = 'libre', placa = NULL, tipo = NULL, hora_ingreso = NULL
                    WHERE numero = %s
                    """,
                    (vehiculo["celda"],),
                )

                vehiculo["hora_salida"] = salida["hora_salida"]
                vehiculo["total"] = total
                vehiculo["precio_hora"] = precio_hora
                return vehiculo

    def liquidacion(self, fecha: date, zona_horaria: str) -> list[dict]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, placa, tipo, celda, hora_ingreso, hora_salida, horas,
                           COALESCE(total_pagado, 0) AS total_pagado, pagado,
                           CASE
                               WHEN hora_salida IS NULL
                               THEN GREATEST(
                                   1,
                                   CEIL(EXTRACT(EPOCH FROM (now() - hora_ingreso)) / 3600.0)
                               )::int
                               ELSE NULL
                           END AS horas_en_curso
                    FROM vehiculos
                    WHERE (hora_ingreso AT TIME ZONE %s)::date = %s
                    ORDER BY hora_ingreso
                    """,
                    (zona_horaria, fecha),
                )
                return cur.fetchall()

    def historial(self, limite: int = 50) -> list[dict]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, placa, tipo, celda, hora_ingreso, hora_salida, horas,
                           COALESCE(total_pagado, 0) AS total_pagado, pagado,
                           NULL::int AS horas_en_curso
                    FROM vehiculos
                    ORDER BY hora_ingreso DESC
                    LIMIT %s
                    """,
                    (limite,),
                )
                return cur.fetchall()
