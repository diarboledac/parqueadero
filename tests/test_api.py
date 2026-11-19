"""Tests de los endpoints HTTP del Parqueadero SGP-8."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import get_service
from app.service import ParqueaderoService
from tests.fakes import FakeRepo


@pytest.fixture
def client():
    app = create_app(enable_db=False)
    servicio = ParqueaderoService(FakeRepo(total=3))
    app.dependency_overrides[get_service] = lambda: servicio

    with TestClient(app) as cliente:
        yield cliente


def test_health(client):
    respuesta = client.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_estado_inicial(client):
    respuesta = client.get("/api/estado")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total"] == 3
    assert datos["libres"] == 3
    assert datos["config"]["precio_carro"] == 3000


def test_ingreso_y_salida(client):
    respuesta = client.post(
        "/api/ingresos", json={"placa": "ABC123", "tipo": "carro"}
    )
    assert respuesta.status_code == 201
    ticket = respuesta.json()
    assert ticket["celda"] == 1

    respuesta = client.post("/api/salidas", json={"placa": "ABC123"})
    assert respuesta.status_code == 200
    factura = respuesta.json()
    assert factura["horas"] == 1
    assert factura["total"] == 3000

    estado = client.get("/api/estado").json()
    assert estado["libres"] == 3


def test_ingreso_duplicado(client):
    client.post("/api/ingresos", json={"placa": "ABC123", "tipo": "carro"})

    respuesta = client.post(
        "/api/ingresos", json={"placa": "ABC123", "tipo": "moto"}
    )

    assert respuesta.status_code == 409


def test_salida_inexistente(client):
    respuesta = client.post("/api/salidas", json={"placa": "ZZZ999"})

    assert respuesta.status_code == 404


def test_liquidacion(client):
    client.post("/api/ingresos", json={"placa": "ABC123", "tipo": "carro"})

    respuesta = client.get("/api/liquidacion")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["vehiculos_en_curso"] == 1
    assert datos["movimientos"][0]["placa"] == "ABC123"


def test_historial(client):
    client.post("/api/ingresos", json={"placa": "ABC123", "tipo": "carro"})
    client.post("/api/salidas", json={"placa": "ABC123"})

    respuesta = client.get("/api/historial?limite=10")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["pagado"] is True


def test_config(client):
    respuesta = client.get("/api/config")
    assert respuesta.status_code == 200
    assert respuesta.json()["precio_carro"] == 3000

    respuesta = client.put("/api/config", json={"precio_carro": 4500})
    assert respuesta.status_code == 200
    assert respuesta.json()["precio_carro"] == 4500
