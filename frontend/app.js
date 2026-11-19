const API = "/api";
const REFRESCO_MS = 10000;

const dinero = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const $ = (id) => document.getElementById(id);

let intervalo = null;

function fmtDinero(valor) {
  return dinero.format(Number(valor) || 0);
}

function fmtHora(iso) {
  if (!iso) return "--:--";
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime())
    ? "--:--"
    : fecha.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

function fmtFecha(iso) {
  if (!iso) return "--";
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime())
    ? "--"
    : fecha.toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit" });
}

function toast(mensaje, tipo = "ok") {
  const el = $("toast");
  el.textContent = mensaje;
  el.className = `toast visible ${tipo}`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => {
    el.className = "toast";
  }, 4200);
}

async function api(ruta, opciones = {}) {
  const respuesta = await fetch(API + ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });

  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      if (cuerpo && cuerpo.detail) {
        detalle = typeof cuerpo.detail === "string"
          ? cuerpo.detail
          : JSON.stringify(cuerpo.detail);
      }
    } catch (_) {
      /* respuesta sin JSON */
    }
    throw new Error(detalle);
  }

  if (respuesta.status === 204) return null;
  return respuesta.json();
}

function setConexion(estado) {
  const caja = $("conexion");
  caja.className = `conexion ${estado}`;
  $("conexion-texto").textContent =
    estado === "ok" ? "Base de datos conectada" : "Sin conexión a la base de datos";
}

async function verificarSalud() {
  try {
    const respuesta = await fetch("/health", { cache: "no-store" });
    setConexion(respuesta.ok ? "ok" : "error");
  } catch (_) {
    setConexion("error");
  }
}

function renderMapa(celdas) {
  const mapa = $("mapa");
  mapa.innerHTML = "";

  if (!celdas.length) {
    mapa.innerHTML = '<p class="vacio">No hay celdas configuradas.</p>';
    return;
  }

  for (const celda of celdas) {
    const ocupada = celda.estado === "ocupado";
    const tarjeta = document.createElement("article");
    tarjeta.className = `celda ${ocupada ? "ocupada" : "libre"}`;
    tarjeta.innerHTML = `
      <div class="celda-num">CELDA ${String(celda.numero).padStart(2, "0")}</div>
      ${ocupada
        ? `<div class="celda-placa">${celda.placa ?? "—"}</div>
           <div class="celda-info">${celda.tipo ?? ""} · ${celda.horas_en_curso ?? 1} h</div>`
        : `<div class="celda-libre">LIBRE</div>`}
    `;
    mapa.appendChild(tarjeta);
  }
}

function renderLiquidacion(data) {
  $("stat-cobrado").textContent = fmtDinero(data.total_cobrado);

  $("liq-stats").innerHTML = `
    <span class="chip">Atendidos <strong>${data.vehiculos_atendidos}</strong></span>
    <span class="chip">En curso <strong>${data.vehiculos_en_curso}</strong></span>
    <span class="chip">Cobrado <strong>${fmtDinero(data.total_cobrado)}</strong></span>
    <span class="chip">Proyectado <strong>${fmtDinero(data.total_proyectado)}</strong></span>
  `;

  const cuerpo = $("liq-body");

  if (!data.movimientos.length) {
    cuerpo.innerHTML = '<tr><td colspan="8" class="vacio">Sin movimientos hoy.</td></tr>';
    return;
  }

  cuerpo.innerHTML = data.movimientos
    .map((movimiento) => {
      const enCurso = !movimiento.hora_salida;
      const total = enCurso
        ? movimiento.total_proyectado
        : movimiento.total_pagado;
      const horas = enCurso ? movimiento.horas_en_curso : movimiento.horas;

      return `
        <tr>
          <td><strong>${movimiento.placa}</strong></td>
          <td>${movimiento.tipo}</td>
          <td>${movimiento.celda}</td>
          <td>${fmtHora(movimiento.hora_ingreso)}</td>
          <td>${fmtHora(movimiento.hora_salida)}</td>
          <td>${horas ?? "—"}</td>
          <td>${fmtDinero(total)}</td>
          <td>
            <span class="estado-pill ${enCurso ? "curso" : "pagado"}">
              ${enCurso ? "EN CURSO" : "PAGADO"}
            </span>
          </td>
        </tr>`;
    })
    .join("");
}

async function cargarEstado() {
  const estado = await api("/estado");

  $("stat-libres").textContent = estado.libres;
  $("stat-ocupados").textContent = estado.ocupados;
  $("stat-total").textContent = estado.total;
  $("precio-carro").textContent = fmtDinero(estado.config.precio_carro);
  $("precio-moto").textContent = fmtDinero(estado.config.precio_moto);

  renderMapa(estado.celdas);
}

async function cargarLiquidacion() {
  const liquidacion = await api("/liquidacion");
  renderLiquidacion(liquidacion);
}

async function refrescarTodo() {
  try {
    await Promise.all([cargarEstado(), cargarLiquidacion()]);
  } catch (error) {
    toast(error.message, "error");
  }
}

function mostrarFactura(factura) {
  $("factura-contenido").innerHTML = `
    <div class="factura">
      <div class="factura-fila"><span>Placa</span><strong>${factura.placa}</strong></div>
      <div class="factura-fila"><span>Tipo</span><strong>${factura.tipo}</strong></div>
      <div class="factura-fila"><span>Celda</span><strong>${factura.celda}</strong></div>
      <div class="factura-fila"><span>Ingreso</span><span>${fmtFecha(factura.hora_ingreso)} ${fmtHora(factura.hora_ingreso)}</span></div>
      <div class="factura-fila"><span>Salida</span><span>${fmtFecha(factura.hora_salida)} ${fmtHora(factura.hora_salida)}</span></div>
      <div class="factura-fila"><span>Horas cobradas</span><strong>${factura.horas}</strong></div>
      <div class="factura-fila"><span>Precio por hora</span><strong>${fmtDinero(factura.precio_hora)}</strong></div>
    </div>
    <div class="factura-total">
      <span>Total pagado</span>
      <span>${fmtDinero(factura.total)}</span>
    </div>
  `;
  $("modal-factura").classList.remove("oculto");
}

function cerrarModal() {
  $("modal-factura").classList.add("oculto");
}

async function manejarIngreso(evento) {
  evento.preventDefault();
  const placa = $("placa-ingreso").value.trim().toUpperCase();
  const tipo = $("tipo-ingreso").value;

  try {
    const ticket = await api("/ingresos", {
      method: "POST",
      body: JSON.stringify({ placa, tipo }),
    });
    toast(`Ingreso registrado: ${ticket.placa} en celda ${ticket.celda}.`, "ok");
    $("placa-ingreso").value = "";
    await refrescarTodo();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function manejarSalida(evento) {
  evento.preventDefault();
  const placa = $("placa-salida").value.trim().toUpperCase();

  try {
    const factura = await api("/salidas", {
      method: "POST",
      body: JSON.stringify({ placa }),
    });
    mostrarFactura(factura);
    $("placa-salida").value = "";
    await refrescarTodo();
  } catch (error) {
    toast(error.message, "error");
  }
}

function actualizarReloj() {
  const ahora = new Date();
  $("reloj").textContent = ahora.toLocaleTimeString("es-CO", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function iniciar() {
  $("form-ingreso").addEventListener("submit", manejarIngreso);
  $("form-salida").addEventListener("submit", manejarSalida);
  $("btn-refrescar").addEventListener("click", refrescarTodo);
  $("btn-liquidar").addEventListener("click", cargarLiquidacion);
  $("btn-cerrar-modal").addEventListener("click", cerrarModal);
  $("btn-cerrar-modal-2").addEventListener("click", cerrarModal);
  $("modal-factura").addEventListener("click", (evento) => {
    if (evento.target.id === "modal-factura") cerrarModal();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") cerrarModal();
  });

  actualizarReloj();
  setInterval(actualizarReloj, 1000);

  verificarSalud();
  refrescarTodo();

  if (intervalo) clearInterval(intervalo);
  intervalo = setInterval(() => {
    verificarSalud();
    refrescarTodo();
  }, REFRESCO_MS);
}

document.addEventListener("DOMContentLoaded", iniciar);
