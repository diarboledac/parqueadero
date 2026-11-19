# ================================================
# SISTEMA DE PARQUEADERO SGP-8 (8 CELDAS)
# ================================================

from datetime import datetime

# Precios por hora
PRECIO_CARRO = 3000
PRECIO_MOTO = 1500

# Capacidad máxima
TOTAL_CELDAS = 8

# Vectores (listas) para almacenar la información
celdas = []          # Estado de cada celda
vehiculos = []       # Vehículos actualmente parqueados
historial_dia = []   # Vehículos que se parquearon en el día

# --------------------------------------------------
# 1. VECTORES: crear las celdas del parqueadero
# --------------------------------------------------
def crear_celdas():
    global celdas
    celdas = []
    for i in range(1, TOTAL_CELDAS + 1):
        celda = {
            "numero": i,
            "estado": "libre",   # libre / ocupado
            "placa": None,
            "tipo": None,
            "hora_ingreso": None,
            "posicion": None
        }
        celdas.append(celda)

# --------------------------------------------------
# 2. PREGUNTAR CUÁNTOS PUESTOS TIENE EL PARQUEADERO
# --------------------------------------------------
def configurar_puestos():
    global TOTAL_CELDAS
    try:
        n = int(input("¿Cuántos puestos tiene el parqueadero? "))
        if n <= 0:
            print("⚠ Debe ser mayor a 0. Se usarán 8 por defecto.")
            n = 8
        TOTAL_CELDAS = n
        crear_celdas()
        print(f"✔ Parqueadero configurado con {TOTAL_CELDAS} puestos.")
    except ValueError:
        print("⚠ Entrada inválida. Se usarán 8 puestos por defecto.")
        TOTAL_CELDAS = 8
        crear_celdas()

# --------------------------------------------------
# 3. Y 4. DIGITAR PLACA Y POSICIÓN
# --------------------------------------------------
def ingresar_vehiculo():
    print("\n--- INGRESO DE VEHÍCULO ---")

    placa = input("Digite la placa: ").upper().strip()
    if not placa:
        print("⚠ Placa inválida.")
        return

    for v in vehiculos:
        if v["placa"] == placa:
            print("⚠ Esa placa ya está registrada en el parqueadero.")
            return

    tipo = input("Tipo de vehículo (carro/moto): ").lower().strip()
    if tipo not in ("carro", "moto"):
        print("⚠ Tipo inválido. Debe ser 'carro' o 'moto'.")
        return

    try:
        posicion = int(input(f"Digite la posición (1-{TOTAL_CELDAS}): "))
    except ValueError:
        print("⚠ Posición inválida.")
        return

    if posicion < 1 or posicion > TOTAL_CELDAS:
        print("⚠ Posición fuera de rango.")
        return

    celda = celdas[posicion - 1]
    if celda["estado"] == "ocupado":
        print(f"⚠ La celda {posicion} ya está ocupada por {celda['placa']}.")
        return

    hora = datetime.now()
    celda["estado"] = "ocupado"
    celda["placa"] = placa
    celda["tipo"] = tipo
    celda["hora_ingreso"] = hora
    celda["posicion"] = posicion

    registro = {
        "placa": placa,
        "tipo": tipo,
        "posicion": posicion,
        "hora_ingreso": hora,
        "pagado": False   # 🔹 NUEVO: al entrar aún no ha pagado
    }
    vehiculos.append(registro)
    historial_dia.append(registro)

    print(f"✔ Vehículo {placa} ingresado en la celda {posicion} a las {hora.strftime('%H:%M:%S')}.")

# --------------------------------------------------
# 🔹 MAPA DE CELDAS EN MATRIZ BONITA
# --------------------------------------------------
def dibujar_matriz():
    columnas = 4
    print("\n        ╔══════════════════════════════════════════════════════╗")
    print("        ║            MAPA DEL PARQUEADERO SGP-8                ║")
    print("        ╚══════════════════════════════════════════════════════╝")

    for i in range(0, TOTAL_CELDAS, columnas):
        fila = celdas[i:i + columnas]

        linea_top = "        "
        for _ in fila:
            linea_top += "┌────────────┐  "
        print(linea_top)

        linea_mid = "        "
        for c in fila:
            if c["estado"] == "libre":
                linea_mid += f"│  [{c['numero']:>2}] LIBRE │  "
            else:
                linea_mid += f"│  [{c['numero']:>2}] OCUP. │  "
        print(linea_mid)

        linea_sub = "        "
        for c in fila:
            if c["estado"] == "ocupado":
                linea_sub += f"│ {c['placa']:<10} │  "
            else:
                linea_sub += f"│    ----    │  "
        print(linea_sub)

        linea_bot = "        "
        for _ in fila:
            linea_bot += "└────────────┘  "
        print(linea_bot)
        print()

# --------------------------------------------------
# 5. MENÚ: MOSTRAR OCUPADOS / LIBRES
# --------------------------------------------------
def mostrar_estado():
    print("\n--- ESTADO DEL PARQUEADERO ---")
    libres = 0
    ocupados = 0
    dibujar_matriz()

    for c in celdas:
        if c["estado"] == "libre":
            libres += 1
        else:
            ocupados += 1

    print(f"Resumen -> Libres: {libres} | Ocupados: {ocupados} | Total: {TOTAL_CELDAS}")

# --------------------------------------------------
# 6. SACAR VEHÍCULO  🔹 CON VERIFICACIÓN DE PAGO
# --------------------------------------------------
def sacar_vehiculo():
    print("\n--- RETIRO DE VEHÍCULO ---")
    placa = input("Digite la placa a retirar: ").upper().strip()

    for v in vehiculos:
        if v["placa"] == placa:
            hora_salida = datetime.now()
            tiempo = hora_salida - v["hora_ingreso"]
            horas = max(1, int(tiempo.total_seconds() // 3600) + (1 if tiempo.total_seconds() % 3600 else 0))

            precio_hora = PRECIO_CARRO if v["tipo"] == "carro" else PRECIO_MOTO
            total = horas * precio_hora

            # 🔹 Mostrar la cuenta antes de cobrar
            print("\n" + "-" * 45)
            print(f"   Placa        : {v['placa']}")
            print(f"   Tipo         : {v['tipo']}")
            print(f"   Celda        : {v['posicion']}")
            print(f"   Hora ingreso : {v['hora_ingreso'].strftime('%H:%M:%S')}")
            print(f"   Hora salida  : {hora_salida.strftime('%H:%M:%S')}")
            print(f"   Horas        : {horas}")
            print(f"   TOTAL A PAGAR: ${total:,}")
            print("-" * 45)

            # 🔹 VERIFICACIÓN DE PAGO
            while True:
                pago = input("¿El cliente YA pagó? (s/n): ").lower().strip()
                if pago in ("s", "si", "sí"):
                    v["pagado"] = True
                    break
                elif pago in ("n", "no"):
                    print("No se puede retirar el vehículo sin pagar.")
                    print("   Cobre primero y vuelva a intentarlo.\n")
                    return
                else:
                    print(" Responda 's' o 'n'.")

            # Guardar datos de salida en el historial
            v["hora_salida"] = hora_salida
            v["horas"] = horas
            v["total_pagado"] = total

            # Liberar la celda
            celda = celdas[v["posicion"] - 1]
            celda["estado"] = "libre"
            celda["placa"] = None
            celda["tipo"] = None
            celda["hora_ingreso"] = None
            celda["posicion"] = None

            vehiculos.remove(v)

            print(f"\n✔ Vehículo {placa} retirado de la celda {v['posicion']}.")
            print(f"   Pago confirmado: SÍ ✅")
            print(f"   TOTAL COBRADO  : ${total:,}")
            return

    print("⚠ No se encontró un vehículo con esa placa.")

# --------------------------------------------------
# 7. LIQUIDAR (cierre del sistema)
# --------------------------------------------------
def liquidar():
    print("\n" + "=" * 70)
    print("              LIQUIDACIÓN / CIERRE DE CAJA DEL DÍA")
    print("=" * 70)

    if not historial_dia:
        print("\n⚠ No se registraron vehículos en el día.")
        print("\nCerrando sistema... ¡Hasta pronto! 👋")
        return

    print(f"\n{'#':<4}{'PLACA':<10}{'TIPO':<8}{'CELDA':<7}{'INGRESO':<10}{'SALIDA':<10}{'HRS':<5}{'VALOR':<12}{'ESTADO':<12}")
    print("-" * 78)

    total_general = 0
    total_cobrado = 0
    pendientes = 0
    sin_pagar = 0

    for i, v in enumerate(historial_dia, start=1):
        hora_ing = v["hora_ingreso"].strftime("%H:%M:%S")

        if "hora_salida" in v:
            hora_sal = v["hora_salida"].strftime("%H:%M:%S")
            horas = v["horas"]
            valor = v["total_pagado"]
            estado = "PAGADO" if v.get("pagado") else "SIN PAGAR"
            if v.get("pagado"):
                total_cobrado += valor
            else:
                sin_pagar += 1
        else:
            hora_sal = "--:--:--"
            tiempo = datetime.now() - v["hora_ingreso"]
            horas = max(1, int(tiempo.total_seconds() // 3600) + (1 if tiempo.total_seconds() % 3600 else 0))
            precio_hora = PRECIO_CARRO if v["tipo"] == "carro" else PRECIO_MOTO
            valor = horas * precio_hora
            estado = "EN CURSO"
            pendientes += 1

        total_general += valor
        print(f"{i:<4}{v['placa']:<10}{v['tipo']:<8}{v['posicion']:<7}{hora_ing:<10}{hora_sal:<10}{horas:<5}${valor:<11,}{estado:<12}")

    print("-" * 78)
    print(f"\n📊 RESUMEN DEL DÍA")
    print(f"   Vehículos atendidos      : {len(historial_dia)}")
    print(f"   Vehículos aún en parqueo : {pendientes}")
    print(f"   Vehículos sin pagar      : {sin_pagar}")
    print(f"   Total cobrado (pagados)  : ${total_cobrado:,}")
    print(f"   Total proyectado (todos) : ${total_general:,}")

    print("\n" + "=" * 70)
    print("Cerrando sistema... ¡Hasta pronto! 👋")
    print("=" * 70)

# --------------------------------------------------
# MENÚ PRINCIPAL
# --------------------------------------------------
def menu():
    configurar_puestos()

    while True:
        print("\n========= MENÚ PARQUEADERO SGP-8 =========")
        print("1. Ingresar vehículo")
        print("2. Ver ocupados / libres (mapa)")
        print("3. Sacar vehículo")
        print("4. Liquidar (cierre de caja)")
        print("5. Salir")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            ingresar_vehiculo()
        elif opcion == "2":
            mostrar_estado()
        elif opcion == "3":
            sacar_vehiculo()
        elif opcion == "4":
            liquidar()
            break
        elif opcion == "5":
            print("Saliendo sin liquidar... 👋")
            break
        else:
            print("⚠ Opción inválida.")

# Punto de entrada
if __name__ == "__main__":
    menu()