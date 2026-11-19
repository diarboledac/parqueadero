"""Rutas HTTP de la API del Parqueadero SGP-8."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .schemas import (
    ConfigOut,
    ConfigUpdate,
    EstadoOut,
    FacturaOut,
    IngresoRequest,
    LiquidacionOut,
    MovimientoOut,
    SalidaRequest,
    TicketOut,
)
from .service import (
    DatosInvalidos,
    ParqueaderoError,
    ParqueaderoLleno,
    ParqueaderoService,
    PlacaDuplicada,
    VehiculoNoEncontrado,
)

router = APIRouter(prefix="/api", tags=["parqueadero"])


def get_service(request: Request) -> ParqueaderoService:
    return request.app.state.service


@router.get("/estado", response_model=EstadoOut)
def estado(service: ParqueaderoService = Depends(get_service)) -> dict:
    return service.estado()


@router.post("/ingresos", response_model=TicketOut, status_code=201)
def ingresar(
    payload: IngresoRequest,
    service: ParqueaderoService = Depends(get_service),
) -> dict:
    try:
        return service.ingresar(payload.placa, payload.tipo)
    except PlacaDuplicada as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ParqueaderoLleno as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (DatosInvalidos, ParqueaderoError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/salidas", response_model=FacturaOut)
def salir(
    payload: SalidaRequest,
    service: ParqueaderoService = Depends(get_service),
) -> dict:
    try:
        return service.salir(payload.placa)
    except VehiculoNoEncontrado as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DatosInvalidos as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ParqueaderoError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/liquidacion", response_model=LiquidacionOut)
def liquidacion(
    fecha: date | None = Query(default=None, description="Fecha YYYY-MM-DD"),
    service: ParqueaderoService = Depends(get_service),
) -> dict:
    return service.liquidacion(fecha)


@router.get("/historial", response_model=list[MovimientoOut])
def historial(
    limite: int = Query(default=50, ge=1, le=500),
    service: ParqueaderoService = Depends(get_service),
) -> list[dict]:
    return service.historial(limite)


@router.get("/config", response_model=ConfigOut)
def config(service: ParqueaderoService = Depends(get_service)) -> dict:
    return service.config()


@router.put("/config", response_model=ConfigOut)
def actualizar_config(
    payload: ConfigUpdate,
    service: ParqueaderoService = Depends(get_service),
) -> dict:
    try:
        return service.actualizar_config(payload.model_dump(exclude_none=True))
    except DatosInvalidos as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
