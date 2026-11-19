# Parqueadero SGP-8

Demo web de control de parqueadero con **FastAPI** y **PostgreSQL gestionado en Aiven**.

## Funcionalidades

- Mapa visual del parqueadero en tiempo real (celdas libres y ocupadas).
- Registro de ingreso de carros y motos con asignación automática de celda.
- Registro de salida con cálculo de horas, cobro y factura.
- Liquidación del día: atendidos, en curso, cobrado y proyectado.
- Historial de movimientos.
- Configuración de tarifas y capacidad desde la API.
- Persistencia real: los datos viven en PostgreSQL (Aiven), no en memoria.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 + FastAPI |
| Base de datos | PostgreSQL en Aiven (`psycopg` 3 + pool) |
| Frontend | HTML5, CSS y JavaScript (sin frameworks) |
| Tests | pytest + httpx |

## Estructura

```
parqueadero/
├── app/
│   ├── config.py        # Variables de entorno
│   ├── database.py      # Pool de conexiones y esquema SQL
│   ├── repository.py    # Operaciones PostgreSQL
│   ├── service.py       # Reglas de negocio
│   ├── schemas.py       # Modelos Pydantic
│   ├── routes.py        # Endpoints REST
│   └── main.py          # Factory de FastAPI
├── frontend/            # Interfaz web (mapa, ingreso, salida, liquidación)
├── tests/               # Tests de negocio y de API
├── legacy/main_cli.py   # Versión anterior en consola (referencia)
├── requirements.txt
└── .env.example
```

## Puesta en marcha

### 1. Instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar la conexión

Copia `.env.example` como `.env` y pega el **Service URI** de tu PostgreSQL en Aiven:

```env
DATABASE_URL="postgresql://avnadmin:CLAVE@HOST.aivencloud.com:PUERTO/defaultdb?sslmode=require"
```

> El archivo `.env` está ignorado por git. Nunca subas credenciales reales.

### 3. Ejecutar

```bash
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- Aplicación web: <http://127.0.0.1:8000>
- Documentación interactiva de la API: <http://127.0.0.1:8000/docs>
- Salud: <http://127.0.0.1:8000/health>

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/estado` | Mapa y resumen de celdas |
| POST | `/api/ingresos` | Registrar ingreso `{ "placa": "ABC123", "tipo": "carro" }` |
| POST | `/api/salidas` | Registrar salida y generar factura `{ "placa": "ABC123" }` |
| GET | `/api/liquidacion?fecha=YYYY-MM-DD` | Liquidación del día |
| GET | `/api/historial?limite=50` | Últimos movimientos |
| GET | `/api/config` | Tarifas y capacidad |
| PUT | `/api/config` | Actualizar tarifas/capacidad |

## Reglas de negocio

- Carro: **$3.000/hora**. Moto: **$1.500/hora** (configurables).
- La fracción de hora se cobra completa (mínimo 1 hora).
- Una placa no puede tener dos ingresos activos al mismo tiempo.
- Al registrar la salida, la celda queda libre y se genera la factura.
- La capacidad y las tarifas se guardan en la tabla `configuracion`.

## Tests

```bash
.venv\Scripts\pytest
```

Los tests usan un repositorio en memoria, por lo que no necesitan conexión a Aiven.

## Base de datos

El esquema se crea automáticamente al iniciar la aplicación:

- `configuracion` — tarifas y capacidad.
- `celdas` — estado actual de cada celda.
- `vehiculos` — ingresos, salidas, horas y valores pagados.

## Seguridad

- `.env` y `.env.*` están ignorados (excepto `.env.example`).
- La conexión usa `sslmode=require`.
- Las placas se validan y normalizan antes de llegar a la base de datos.
- Las consultas usan parámetros (`%s`), evitando inyección SQL.
