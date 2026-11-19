"""Verifica la conexion a Aiven PostgreSQL y prepara el esquema.

Uso:
    .venv\\Scripts\\python scripts/check_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.database import crear_pool, inicializar_esquema  # noqa: E402
from app.repository import PostgresRepository  # noqa: E402


def main() -> int:
    try:
        settings = get_settings()
        destino = settings.database_url.split("@")[-1]
        print(f"Conectando a: {destino}")

        pool = crear_pool(settings)
        inicializar_esquema(pool)

        repositorio = PostgresRepository(pool, settings)
        repositorio.sembrar_config(settings)
        repositorio.sincronizar_celdas(settings.total_celdas)

        with pool.connection() as conn:
            version = conn.execute("SELECT version()").fetchone()[0]
            celdas = conn.execute("SELECT count(*) FROM celdas").fetchone()[0]

        pool.close()

        print("CONEXION OK")
        print(f"PostgreSQL: {version.split(',')[0]}")
        print(f"Celdas configuradas: {celdas}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR DE CONEXION: {exc}")
        print(
            "Revisa en la consola de Aiven que el servicio este activo y que "
            "la Service URI de .env sea la actual."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
