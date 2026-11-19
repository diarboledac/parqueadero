"""Repositorio falso en memoria para tests sin PostgreSQL."""

from __future__ import annotations

import math
from datetime import datetime, timezone


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _horas_desde(desde: datetime) -> int:
    segundos = (_ahora() - desde).total_seconds()
    return max(1, math.ceil(segundos / 3600))


class FakeRepo:
    def __init__(self, total: int = 3, precios: dict | None = None) -> None:
        precios = precios or {}
        self.config = {
            "precio_carro": str(precios.get("carro", 3000)),
            "precio_moto": str(precios.get("moto", 1500)),
            "total_celdas": str(total),
        }
        self.celdas = {
            numero: {
                "numero": numero,
                "estado": "libre",
                "placa": None,
                "tipo": None,
                "hora_ingreso": None,
                "horas_en_curso": None,
            }
            for numero in range(1, total + 1)
        }
        self.vehiculos: list[dict] = []
        self._siguiente_id = 1

    def sembrar_config(self, settings) -> None:
        return None

    def obtener_config(self) -> dict[str, str]:
        return dict(self.config)

    def actualizar_config(self, clave: str, valor: str) -> None:
        self.config[clave] = str(valor)

    def precio_hora(self, tipo: str) -> int:
        clave = "precio_carro" if tipo == "carro" else "precio_moto"
        return int(self.config[clave])

    def sincronizar_celdas(self, total: int) -> None:
        for numero in range(1, total + 1):
            self.celdas.setdefault(
                numero,
                {
                    "numero": numero,
                    "estado": "libre",
                    "placa": None,
                    "tipo": None,
                    "hora_ingreso": None,
                    "horas_en_curso": None,
                },
            )
        for numero in list(self.celdas):
            if numero > total and self.celdas[numero]["estado"] == "libre":
                del self.celdas[numero]

    def listar_celdas(self) -> list[dict]:
        resultado = []
        for celda in sorted(self.celdas.values(), key=lambda c: c["numero"]):
            copia = dict(celda)
            if copia["hora_ingreso"] is not None:
                copia["horas_en_curso"] = _horas_desde(copia["hora_ingreso"])
            resultado.append(copia)
        return resultado

    def celda_libre(self) -> int | None:
        for numero in sorted(self.celdas):
            if self.celdas[numero]["estado"] == "libre":
                return numero
        return None

    def vehiculo_activo(self, placa: str) -> dict | None:
        for vehiculo in self.vehiculos:
            if vehiculo["placa"] == placa and vehiculo["hora_salida"] is None:
                copia = dict(vehiculo)
                copia["horas_en_curso"] = _horas_desde(vehiculo["hora_ingreso"])
                return copia
        return None

    def registrar_ingreso(self, placa: str, tipo: str, celda: int) -> dict:
        hora = _ahora()
        self.celdas[celda].update(
            {
                "estado": "ocupado",
                "placa": placa,
                "tipo": tipo,
                "hora_ingreso": hora,
                "horas_en_curso": 1,
            }
        )
        vehiculo = {
            "id": self._siguiente_id,
            "placa": placa,
            "tipo": tipo,
            "celda": celda,
            "hora_ingreso": hora,
            "hora_salida": None,
            "horas": None,
            "total_pagado": None,
            "pagado": False,
        }
        self._siguiente_id += 1
        self.vehiculos.append(vehiculo)
        return {
            "id": vehiculo["id"],
            "placa": placa,
            "tipo": tipo,
            "celda": celda,
            "hora_ingreso": hora,
        }

    def registrar_salida(self, vehiculo_id: int, precio_hora: int) -> dict:
        vehiculo = next(
            (
                v
                for v in self.vehiculos
                if v["id"] == vehiculo_id and v["hora_salida"] is None
            ),
            None,
        )
        if vehiculo is None:
            raise ValueError("El vehiculo ya no esta activo.")

        hora_salida = _ahora()
        horas = _horas_desde(vehiculo["hora_ingreso"])
        total = horas * precio_hora

        vehiculo.update(
            {
                "hora_salida": hora_salida,
                "horas": horas,
                "total_pagado": total,
                "pagado": True,
            }
        )
        self.celdas[vehiculo["celda"]].update(
            {
                "estado": "libre",
                "placa": None,
                "tipo": None,
                "hora_ingreso": None,
                "horas_en_curso": None,
            }
        )

        return {**vehiculo, "total": total, "precio_hora": precio_hora}

    def liquidacion(self, fecha, zona_horaria: str) -> list[dict]:
        resultado = []
        for vehiculo in self.vehiculos:
            copia = dict(vehiculo)
            copia.setdefault("horas_en_curso", None)
            if copia["hora_salida"] is None:
                copia["horas_en_curso"] = _horas_desde(copia["hora_ingreso"])
            resultado.append(copia)
        return resultado

    def historial(self, limite: int = 50) -> list[dict]:
        return [dict(v) for v in self.vehiculos[-limite:]]
