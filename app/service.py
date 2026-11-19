"""Reglas de negocio del Parqueadero SGP-8."""

from __future__ import annotations

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

PLACA_RE = re.compile(r"^[A-Z0-9]{5,8}$")


class ParqueaderoError(Exception):
    """Error de negocio controlado."""


class DatosInvalidos(ParqueaderoError):
    pass


class PlacaDuplicada(ParqueaderoError):
    pass


class ParqueaderoLleno(ParqueaderoError):
    pass


class VehiculoNoEncontrado(ParqueaderoError):
    pass


def normalizar_placa(placa: str) -> str:
    limpia = (placa or "").strip().upper()
    if not PLACA_RE.match(limpia):
        raise DatosInvalidos(
            "La placa debe tener entre 5 y 8 caracteres alfanumericos (ej. ABC123)."
        )
    return limpia


def validar_tipo(tipo: str) -> str:
    limpio = (tipo or "").strip().lower()
    if limpio not in ("carro", "moto"):
        raise DatosInvalidos("El tipo debe ser 'carro' o 'moto'.")
    return limpio


class ParqueaderoService:
    def __init__(self, repositorio, zona_horaria: str = "America/Bogota") -> None:
        self.repo = repositorio
        self.zona_horaria = zona_horaria

    # ------------------------------------------------------------------
    def config(self) -> dict:
        bruta = self.repo.obtener_config()
        configuracion = {
            "precio_carro": int(bruta.get("precio_carro", 3000)),
            "precio_moto": int(bruta.get("precio_moto", 1500)),
            "total_celdas": int(bruta.get("total_celdas", 8)),
        }
        return configuracion

    def estado(self) -> dict:
        celdas = self.repo.listar_celdas()
        libres = sum(1 for celda in celdas if celda["estado"] == "libre")
        return {
            "total": len(celdas),
            "libres": libres,
            "ocupados": len(celdas) - libres,
            "celdas": celdas,
            "config": self.config(),
        }

    def ingresar(self, placa: str, tipo: str) -> dict:
        placa = normalizar_placa(placa)
        tipo = validar_tipo(tipo)

        if self.repo.vehiculo_activo(placa) is not None:
            raise PlacaDuplicada(f"La placa {placa} ya esta dentro del parqueadero.")

        celda = self.repo.celda_libre()
        if celda is None:
            raise ParqueaderoLleno("No hay celdas libres en este momento.")

        try:
            return self.repo.registrar_ingreso(placa, tipo, celda)
        except ValueError as exc:
            raise ParqueaderoError(str(exc)) from exc

    def salir(self, placa: str) -> dict:
        placa = normalizar_placa(placa)
        vehiculo = self.repo.vehiculo_activo(placa)
        if vehiculo is None:
            raise VehiculoNoEncontrado(
                f"No hay un vehiculo activo con placa {placa}."
            )

        precio = self.repo.precio_hora(vehiculo["tipo"])
        try:
            return self.repo.registrar_salida(vehiculo["id"], precio)
        except ValueError as exc:
            raise ParqueaderoError(str(exc)) from exc

    def liquidacion(self, fecha: date | None = None) -> dict:
        fecha = fecha or datetime.now(ZoneInfo(self.zona_horaria)).date()
        movimientos = self.repo.liquidacion(fecha, self.zona_horaria)

        atendidos = [m for m in movimientos if m["hora_salida"] is not None]
        en_curso = [m for m in movimientos if m["hora_salida"] is None]

        total_cobrado = sum(float(m["total_pagado"] or 0) for m in atendidos if m["pagado"])
        total_proyectado = sum(float(m["total_pagado"] or 0) for m in atendidos)

        for movimiento in en_curso:
            precio = self.repo.precio_hora(movimiento["tipo"])
            estimado = movimiento["horas_en_curso"] * precio
            movimiento["total_proyectado"] = estimado
            total_proyectado += estimado

        return {
            "fecha": fecha,
            "vehiculos_atendidos": len(atendidos),
            "vehiculos_en_curso": len(en_curso),
            "total_cobrado": total_cobrado,
            "total_proyectado": total_proyectado,
            "movimientos": movimientos,
        }

    def historial(self, limite: int = 50) -> list[dict]:
        return self.repo.historial(limite)

    def actualizar_config(self, cambios: dict) -> dict:
        permitidos = {"precio_carro", "precio_moto", "total_celdas"}
        for clave, valor in cambios.items():
            if clave not in permitidos:
                continue
            if clave == "total_celdas":
                if valor < 1 or valor > 500:
                    raise DatosInvalidos("total_celdas debe estar entre 1 y 500.")
                self.repo.actualizar_config(clave, str(valor))
                self.repo.sincronizar_celdas(int(valor))
            else:
                if valor < 0:
                    raise DatosInvalidos(f"{clave} no puede ser negativo.")
                self.repo.actualizar_config(clave, str(valor))

        return self.config()
