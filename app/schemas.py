"""Esquemas Pydantic para la API del Parqueadero SGP-8."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConfigOut(BaseModel):
    precio_carro: int
    precio_moto: int
    total_celdas: int


class ConfigUpdate(BaseModel):
    precio_carro: int | None = Field(default=None, ge=0)
    precio_moto: int | None = Field(default=None, ge=0)
    total_celdas: int | None = Field(default=None, ge=1, le=500)


class CeldaOut(BaseModel):
    numero: int
    estado: Literal["libre", "ocupado"]
    placa: str | None = None
    tipo: Literal["carro", "moto"] | None = None
    hora_ingreso: datetime | None = None
    horas_en_curso: int | None = None


class EstadoOut(BaseModel):
    total: int
    libres: int
    ocupados: int
    celdas: list[CeldaOut]
    config: ConfigOut


class IngresoRequest(BaseModel):
    placa: str = Field(min_length=5, max_length=8, examples=["ABC123"])
    tipo: Literal["carro", "moto"] = Field(examples=["carro"])


class SalidaRequest(BaseModel):
    placa: str = Field(min_length=5, max_length=8, examples=["ABC123"])


class TicketOut(BaseModel):
    id: int
    placa: str
    tipo: Literal["carro", "moto"]
    celda: int
    hora_ingreso: datetime


class FacturaOut(BaseModel):
    id: int
    placa: str
    tipo: Literal["carro", "moto"]
    celda: int
    hora_ingreso: datetime
    hora_salida: datetime
    horas: int
    precio_hora: int
    total: int


class MovimientoOut(BaseModel):
    id: int
    placa: str
    tipo: Literal["carro", "moto"]
    celda: int
    hora_ingreso: datetime
    hora_salida: datetime | None = None
    horas: int | None = None
    total_pagado: float | None = None
    pagado: bool
    horas_en_curso: int | None = None
    total_proyectado: float | None = None


class LiquidacionOut(BaseModel):
    fecha: date
    vehiculos_atendidos: int
    vehiculos_en_curso: int
    total_cobrado: float
    total_proyectado: float
    movimientos: list[MovimientoOut]
