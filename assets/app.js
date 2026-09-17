/* Menú AR — núcleo compartido por todos los restaurantes.
   Los datos vienen de data/<slug>.json; este archivo nunca se toca por cliente. */

const params = new URLSearchParams(location.search);
let SLUG = params.get('r') || location.hash.replace('#', '') || 'casa-anacaona';
const MESA = params.get('mesa');

const $ = (s, n = document) => n.querySelector(s);
const el = (t, cls) => { const n = document.createElement(t); if (cls) n.className = cls; return n; };

const ICONO_PLATO =
  '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="1.4"><ellipse cx="12" cy="12" rx="9" ry="9"/><ellipse cx="12" cy="12" rx="4.6" ry="4.6"/></svg>';

const ICONO_CUBO =
  '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2.4" stroke-linejoin="round"><path d="M12 2.6 21 7.4v9.2L12 21.4 3 16.6V7.4z"/>' +
  '<path d="M3 7.4 12 12l9-4.6M12 12v9.4"/></svg>';

const ICONO_CAMARA =
  '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M3 8.5h3l1.6-2.4h8.8L18 8.5h3v10H3z"/><circle cx="12" cy="13" r="3.4"/></svg>';

let datos, categoriaActiva = 'todo';

/* ── Carga ───────────────────────────────────────────────── */
async function iniciar() {
  try {
    datos = window.MENUS?.[SLUG] || await (await fetch(`data/${SLUG}.json`)).json();
  } catch {
    $('#lista').innerHTML =
      '<p class="aviso" style="margin:24px 20px">No pudimos cargar este menú. ' +
      'Verifica el enlace del código QR o pide ayuda al personal.</p>';
    return;
  }
  if (datos.acento) document.documentElement.style.setProperty('--maduro', datos.acento);
  pintarCabecera();
  $('#cats-pista').innerHTML = '';
  categoriaActiva = 'todo';
  pintarCategorias();
  pintarLista();
}

/* Cambiar de restaurante sin recargar la página. */
window.cargarRestaurante = slug => { SLUG = slug; location.hash = slug; iniciar(); };

function pintarCabecera() {
  $('#nombre').textContent = datos.nombre;
  $('#bajada').textContent = datos.bajada || '';
  document.title = `${datos.nombre} — Menú`;
  const mesa = MESA || datos.mesa;
  if (mesa) $('#mesa').textContent = `Mesa ${mesa}`;
  else $('#mesa').classList.add('oculto');

  const con3d = datos.platos.filter(p => p.modelo).length;
  $('#pista-texto').textContent = con3d
    ? `${con3d} platos los puedes ver en tamaño real sobre tu mesa.`
    : 'Menú digital.';
  if (!con3d) $('#pista').classList.add('oculto');
}

/* ── Categorías ──────────────────────────────────────────── */
function pintarCategorias() {
  const pista = $('#cats-pista');
  const cats = ['todo', ...new Set(datos.platos.map(p => p.categoria))];
  cats.forEach(c => {
    const b = el('button', 'cat');
    b.type = 'button';
    b.role = 'tab';
    b.textContent = c === 'todo' ? 'Todo el menú' : c;
    b.setAttribute('aria-selected', c === categoriaActiva);
    b.onclick = () => {
      categoriaActiva = c;
      [...pista.children].forEach(x => x.setAttribute('aria-selected', x === b));
      pintarLista();
      window.scrollTo({ top: pista.parentElement.offsetTop, behavior: 'smooth' });
    };
    pista.append(b);
  });
}

/* ── Lista ───────────────────────────────────────────────── */
function pintarLista() {
  const lista = $('#lista');
  lista.innerHTML = '';
  const visibles = datos.platos.filter(
    p => categoriaActiva === 'todo' || p.categoria === categoriaActiva);

  const porCategoria = new Map();
  visibles.forEach(p => {
    if (!porCategoria.has(p.categoria)) porCategoria.set(p.categoria, []);
    porCategoria.get(p.categoria).push(p);
  });

  porCategoria.forEach((platos, cat) => {
    const g = el('section', 'grupo');
    if (categoriaActiva === 'todo') {
      const h = el('h2');
      h.textContent = cat;
      g.append(h);
    }
    platos.forEach(p => g.append(fila(p)));
    lista.append(g);
  });
}

function fila(p) {
  const b = el('button', 'fila');
  b.type = 'button';

  const mini = el('div', 'miniatura');
  if (p.modelo) {
    const mv = document.createElement('model-viewer');
    mv.setAttribute('src', p.modelo);
    mv.setAttribute('alt', p.nombre);
    mv.setAttribute('loading', 'lazy');
    mv.setAttribute('disable-zoom', '');
    mv.setAttribute('interaction-prompt', 'none');
    mv.setAttribute('camera-orbit', '35deg 62deg 105%');
    mv.setAttribute('shadow-intensity', '0.8');
    mv.setAttribute('exposure', '1.1');
    mv.style.pointerEvents = 'none';
    mini.append(mv);
    const chip = el('span', 'chip3d');
    chip.innerHTML = ICONO_CUBO + '3D';
    mini.append(chip);
  } else {
    const ph = el('div', 'sin-modelo');
    ph.innerHTML = ICONO_PLATO;
    mini.append(ph);
  }

  const cuerpo = el('div', 'cuerpo');
  const tit = el('div', 'titulo');
  const h3 = el('h3');
  h3.textContent = p.nombre;
  const precio = el('span', 'precio');
  precio.textContent = money(p.precio);
  tit.append(h3, precio);
  cuerpo.append(tit);

  if (p.descripcion) {
    const d = el('p', 'desc');
    d.textContent = p.descripcion;
    cuerpo.append(d);
  }
  if (p.marcas?.length) cuerpo.append(marcas(p.marcas));

  b.append(mini, cuerpo);
  b.onclick = () => abrir(p);
  return b;
}

function marcas(lista) {
  const c = el('div', 'marcas');
  lista.forEach(m => {
    const s = el('span', 'marca-item');
    s.textContent = m;
    c.append(s);
  });
  return c;
}

const money = n =>
  (datos.moneda || 'RD$') + ' ' + n.toLocaleString('es-DO');

/* ── Hoja de detalle ─────────────────────────────────────── */
const hoja = $('#hoja'), velo = $('#velo');
let ultimoFoco = null;

function abrir(p) {
  ultimoFoco = document.activeElement;
  const escenario = $('#escenario');
  escenario.innerHTML = '';

  $('#d-nombre').textContent = p.nombre;
  $('#d-precio').textContent = money(p.precio);
  $('#d-desc').textContent = p.descripcion || '';
  $('#d-marcas').replaceWith(Object.assign(marcas(p.marcas || []), { id: 'd-marcas' }));

  const btn = $('#btn-ar'), nota = $('#nota-ar'), aviso = $('#aviso');
  btn.classList.add('oculto');
  nota.classList.add('oculto');
  aviso.classList.add('oculto');
  $('#gira').classList.toggle('oculto', !p.modelo);

  if (!p.modelo) {
    escenario.innerHTML = `<div class="sin-modelo" style="border-radius:0">${ICONO_PLATO}</div>`;
    aviso.textContent = 'Este plato todavía no tiene modelo 3D. Pronto lo vas a poder ver en tu mesa.';
    aviso.classList.remove('oculto');
  } else {
    const mv = document.createElement('model-viewer');
    mv.setAttribute('src', p.modelo);
    if (p.usdz) mv.setAttribute('ios-src', p.usdz);
    mv.setAttribute('alt', `Modelo 3D de ${p.nombre}`);
    mv.setAttribute('camera-controls', '');
    mv.setAttribute('touch-action', 'pan-y');
    mv.setAttribute('auto-rotate', '');
    mv.setAttribute('auto-rotate-delay', '2600');
    mv.setAttribute('rotation-per-second', '14deg');
    mv.setAttribute('camera-orbit', '28deg 66deg 110%');
    mv.setAttribute('min-camera-orbit', 'auto 12deg auto');
    mv.setAttribute('max-camera-orbit', 'auto 92deg auto');
    mv.setAttribute('shadow-intensity', '1');
    mv.setAttribute('shadow-softness', '0.75');
    mv.setAttribute('exposure', '1.15');
    mv.setAttribute('ar', '');
    mv.setAttribute('ar-modes', 'webxr scene-viewer quick-look');
    mv.setAttribute('ar-placement', 'floor');
    mv.setAttribute('ar-scale', 'fixed');   // tamaño real: el cliente no puede reescalar
    escenario.append(mv);

    mv.addEventListener('load', () => {
      if (mv.canActivateAR) {
        btn.classList.remove('oculto');
        nota.classList.remove('oculto');
        btn.onclick = () => { registrar(p); mv.activateAR(); };
      } else {
        aviso.textContent = esMovil()
          ? 'Tu navegador no soporta AR. Abre este menú en Chrome (Android) o Safari (iPhone) para ver el plato en tu mesa.'
          : 'El modo AR funciona en celular. Aquí puedes girar el plato arrastrando con el mouse.';
        aviso.classList.remove('oculto');
      }
    }, { once: true });
  }

  velo.setAttribute('data-abierto', '');
  hoja.setAttribute('data-abierto', '');
  document.body.style.overflow = 'hidden';
  $('#cerrar').focus();
}

function cerrar() {
  velo.removeAttribute('data-abierto');
  hoja.removeAttribute('data-abierto');
  document.body.style.overflow = '';
  setTimeout(() => { $('#escenario').innerHTML = ''; }, 350);
  ultimoFoco?.focus();
}

const esMovil = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

/* Conteo local de aperturas de AR por plato. En producción esto va a
   un endpoint del restaurante; es la métrica que se le vende. */
function registrar(p) {
  try {
    const k = `ar:${SLUG}`;
    const s = JSON.parse(localStorage.getItem(k) || '{}');
    s[p.id] = (s[p.id] || 0) + 1;
    localStorage.setItem(k, JSON.stringify(s));
  } catch { /* modo privado: seguimos igual */ }
}

$('#cerrar').onclick = cerrar;
velo.onclick = cerrar;
addEventListener('keydown', e => { if (e.key === 'Escape' && hoja.hasAttribute('data-abierto')) cerrar(); });

$('#btn-ar').innerHTML = ICONO_CAMARA + '<span>Ver en mi mesa</span>';

iniciar();
