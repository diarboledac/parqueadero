# Progreso del proyecto Parqueadero SGP-8

## Estado actual

Demo web completo con FastAPI + PostgreSQL (Aiven), frontend y tests.
Pendiente: verificar la conexión real a Aiven (el host configurado no
resuelve DNS desde este equipo).

## Completado

- [x] Estructura del proyecto (`app/`, `frontend/`, `tests/`, `legacy/`).
- [x] Configuración por `.env` (ignorado por git) y `.env.example`.
- [x] Pool de conexiones y esquema PostgreSQL (`celdas`, `vehiculos`, `configuracion`).
- [x] Repositorio PostgreSQL con transacciones.
- [x] Reglas de negocio (ingreso, salida, liquidación, configuración).
- [x] API REST con FastAPI y documentación automática en `/docs`.
- [x] Frontend: mapa de celdas, ingreso, salida con factura, liquidación.
- [x] Tests de servicio y de API con repositorio en memoria.
- [x] Migración del CLI anterior a `legacy/main_cli.py`.

## Próximos pasos

- [ ] Corregir/verificar el Service URI de Aiven (host actual sin DNS).
- [ ] Ejecutar migración del esquema contra Aiven (`scripts/check_db.py`).
- [ ] Verificar endpoints reales con `curl`/navegador.
- [x] Commit y push a GitHub (`770a2f2`).

## Problemas conocidos

- El host `pg-38fa4b80-unal-382e.j.aivencloud.com` devuelve `NXDOMAIN`
  incluso con Google DNS. Verificar en la consola de Aiven que el servicio
  esté activo y copiar de nuevo la Service URI.

## Última verificación

- Tests unitarios y de API: **18 passed** en 1.35 s.
- Frontend, CSS, JS, `/docs` y `/openapi.json`: HTTP 200.
- Conexión Aiven: fallida por DNS (`getaddrinfo failed` / NXDOMAIN).
