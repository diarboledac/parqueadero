"""Tests de las reglas de negocio del Parqueadero SGP-8."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.service import (
    DatosInvalidos,
    ParqueaderoLleno,
    ParqueaderoService,
    PlacaDuplicada,
    VehiculoNoEncontrado,
)
from tests.fakes import FakeRepo


def test_ingreso_asigna_primera_celda_libre():
    servicio = ParqueaderoService(FakeRepo(total=3))

    ticket = servicio.ingresar("abc123", "carro")

    assert ticket["placa"] == "ABC123"
    assert ticket["celda"] == 1
    estado = servicio.estado()
    assert estado["libres"] == 2
    assert estado["ocupados"] == 1


def test_no_permite_placa_duplicada():
    servicio = ParqueaderoService(FakeRepo())
    servicio.ingresar("ABC123", "carro")

    with pytest.raises(PlacaDuplicada):
        servicio.ingresar("abc123", "moto")


def test_parqueadero_lleno():
    servicio = ParqueaderoService(FakeRepo(total=1))
    servicio.ingresar("ABC123", "carro")

    with pytest.raises(ParqueaderoLleno):
        servicio.ingresar("XYZ789", "moto")


@pytest.mark.parametrize(
    ("placa", "tipo"),
    [
        ("A1", "carro"),
        ("ABC123", "bicicleta"),
        ("", "carro"),
    ],
)
def test_datos_invalidos(placa, tipo):
    servicio = ParqueaderoService(FakeRepo())

    with pytest.raises(DatosInvalidos):
        servicio.ingresar(placa, tipo)


def test_salida_calcula_horas_y_total():
    repo = FakeRepo(total=2)
    servicio = ParqueaderoService(repo)
    ticket = servicio.ingresar("ABC123", "carro")

    vehiculo = next(v for v in repo.vehiculos if v["id"] == ticket["id"])
    vehiculo["hora_ingreso"] = datetime.now(timezone.utc) - timedelta(
        hours=2, minutes=10
    )

    factura = servicio.salir("ABC123")

    assert factura["horas"] == 3
    assert factura["precio_hora"] == 3000
    assert factura["total"] == 9000
    assert repo.celdas[factura["celda"]]["estado"] == "libre"


def test_salida_vehiculo_inexistente():
    servicio = ParqueaderoService(FakeRepo())

    with pytest.raises(VehiculoNoEncontrado):
        servicio.salir("ZZZ999")


def test_liquidacion_resumen():
    servicio = ParqueaderoService(FakeRepo(total=3))
    servicio.ingresar("ABC123", "carro")
    servicio.ingresar("XYZ789", "moto")
    servicio.salir("XYZ789")

    liquidacion = servicio.liquidacion()

    assert liquidacion["vehiculos_atendidos"] == 1
    assert liquidacion["vehiculos_en_curso"] == 1
    assert liquidacion["total_cobrado"] == 1500
    assert liquidacion["total_proyectado"] >= 1500


def test_configuracion_actualizable():
    servicio = ParqueaderoService(FakeRepo(total=2))

    config = servicio.actualizar_config({"precio_carro": 4500, "total_celdas": 4})

    assert config["precio_carro"] == 4500
    assert config["total_celdas"] == 4
    assert len(servicio.estado()["celdas"]) == 4
