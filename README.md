# Mesa Viva — menú de restaurante con realidad aumentada

Sitio estático. Una sola base de código sirve a todos los restaurantes; cada
cliente es un archivo JSON más sus modelos.

```
index.html              la app (no cambia por cliente)
assets/app.css
assets/app.js
data/casa-anacaona.json un cliente
data/parada-47.json     otro cliente
models/*.glb            modelos para Android y para la vista 3D en la página
models/*.usdz           los mismos modelos para AR en iPhone
render.yaml             configuración del hosting
build_models.py         genera los .glb de demostración
glb_a_usdz.py           convierte .glb a .usdz
build_demo.py           empaqueta todo en un .html autocontenido
```

Cada restaurante se abre en `https://tudominio.com/?r=casa-anacaona`, y con la
mesa: `?r=casa-anacaona&mesa=12`. Ese es el enlace que va en el QR de la mesa.

---

## 1. Subirlo a GitHub

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Menú AR: app, dos clientes y modelos 3D"
git branch -M main
```

Creá el repo vacío en GitHub (sin README ni .gitignore, para que no choque) y:

```bash
git remote add origin https://github.com/TU-USUARIO/menu-ar.git
git push -u origin main
```

Si te pide contraseña, GitHub ya no las acepta: usá un
[personal access token](https://github.com/settings/tokens) como contraseña,
o instalá el [GitHub CLI](https://cli.github.com) y corré `gh auth login`.

Con `gh` instalado, todo lo anterior es un solo comando:

```bash
gh repo create menu-ar --public --source=. --push
```

## 2. Desplegarlo en Render

El repo ya trae `render.yaml`, así que Render se configura solo.

1. Entrá a [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
2. Conectá tu cuenta de GitHub y elegí el repo `menu-ar`.
3. Render lee `render.yaml`, te muestra un servicio estático llamado `menu-ar`
   y le das **Apply**.
4. En un minuto tenés `https://menu-ar-XXXX.onrender.com`.

Si preferís hacerlo a mano: **New** → **Static Site**, `Build Command` vacío y
`Publish Directory` en `.`. Pero entonces las cabeceras de `render.yaml` no se
aplican y hay que cargarlas en Settings → Headers.

Ojo con una cosa: `staticPublishPath: .` publica la raíz del repo, así que el
README y los scripts `.py` también quedan accesibles por URL. Acá no importa
—es un repo público— pero el día que guardes algo privado en el repo, mové
`index.html`, `assets/`, `data/` y `models/` a una carpeta `public/` y cambiá
`staticPublishPath` a `./public`.

**Dos cosas a favor de Render acá.** Los sitios estáticos salen por CDN y **no se
duermen** como los web services del plan gratis, así que un cliente que escanea
el QR a las 11 de la noche no espera 30 segundos. Y el HTTPS viene incluido en el
subdominio `onrender.com`, que es obligatorio: sin HTTPS no hay cámara ni AR.

Cada `git push` a `main` redespliega solo.

### Probar que quedó bien

Abrí en el **celular** (no en la computadora)
`https://tu-sitio.onrender.com/?r=casa-anacaona` y tocá un plato con la etiqueta
3D. Deberías ver el botón **Ver en mi mesa**.

Si el botón no aparece, la app te dice por qué en texto. Las causas reales son
casi siempre estas:

| Síntoma | Causa | Arreglo |
|---|---|---|
| No aparece el botón en iPhone | falta el `.usdz` o el campo `usdz` en el JSON | correr `glb_a_usdz.py` y agregarlo |
| No aparece en Android | el dispositivo no soporta ARCore | no tiene arreglo; la app lo explica |
| No aparece en ningún lado | estás entrando por HTTP o por `file://` | usar la URL `https://` |
| El plato sale gigante o enano | el modelo no está en metros | ver *Escala*, más abajo |
| El plato flota o se hunde | el origen no está en la base | ver *Origen*, más abajo |

### Dominio propio

En Render: Settings → Custom Domains. Apuntás un `CNAME` de `menu.tudominio.com`
a la URL de `onrender.com` y el certificado se emite solo. Vale la pena hacerlo
antes de imprimir los QR: un QR impreso con la URL vieja no se puede cambiar.

---

## 3. Dar de alta un restaurante nuevo

1. Copiá `data/casa-anacaona.json` a `data/nuevo-cliente.json`.
2. Cambiá `nombre`, `bajada`, `acento` (el color de la marca) y los platos.
3. Poné los `.glb` y `.usdz` en `models/`.
4. `git push`. Render redespliega solo.
5. Generá el QR apuntando a `https://tudominio.com/?r=nuevo-cliente&mesa=1`, uno por mesa.

Campos de cada plato:

| campo | obligatorio | notas |
|---|---|---|
| `id` | sí | identificador estable, se usa para las métricas |
| `categoria` | sí | agrupa y genera los filtros automáticamente |
| `nombre`, `precio` | sí | `precio` es número; el formato lo pone `moneda` |
| `descripcion` | no | 1–2 líneas, se recorta en la lista |
| `marcas` | no | etiquetas: "Sin gluten", "Picante", "El más pedido" |
| `modelo` | no | ruta al `.glb`. Sin este campo el plato sale sin 3D |
| `usdz` | no | ruta al `.usdz`, necesario para AR en iPhone |

Un plato sin `modelo` se muestra igual, con un marcador neutro. Podés lanzar con
seis platos escaneados y agregar el resto después.

---

## 4. Por qué hacen falta dos formatos

En Android, `<model-viewer>` lanza **Scene Viewer** con el `.glb`. En iPhone lanza
**AR Quick Look**, que solo acepta `.usdz`. Son dos archivos por plato, siempre.

El repo trae `glb_a_usdz.py`, que hace la conversión sin necesidad de una Mac:

```bash
pip install trimesh usd-core pillow
python3 glb_a_usdz.py models/*.glb
```

Convierte geometría, normales, coordenadas UV, texturas y materiales
`UsdPreviewSurface`, y deja el paquete con `metersPerUnit = 1` y eje Y hacia
arriba, que es lo que Quick Look espera. En macOS también sirve
`xcrun usdzconvert`.

## 5. Pipeline de modelos 3D

Acá está el trabajo real del negocio. El sitio se arma una vez; los modelos se
producen por cliente.

**Captura.** Fotogrametría con celular: el plato sobre una mesa lisa, luz pareja
sin sol directo, 60–100 fotos dando dos vueltas completas (una a la altura del
plato, otra a 45°). Apps: Polycam, RealityScan, Scaniverse. Un plato son unos
10–15 minutos. El plato tiene que verse como sale a la mesa, no como queda
después de 20 minutos bajo las luces.

**Limpieza.** En Blender: borrar el piso capturado, cerrar huecos, recortar a la
vajilla. Bajar de ~500k a 20–40k triángulos con el modificador Decimate.

**Escala.** El paso que más se olvida. Scene Viewer y Quick Look leen
**1 unidad = 1 metro**. Un plato llano son 0.27 m de diámetro, un bol 0.17 m, un
vaso 0.08 × 0.15 m. Si el modelo viene en centímetros, el cliente ve un mofongo
de tres metros flotando en el restaurante. Medí el plato real con cinta.

**Origen.** Dejalo en el centro de la base (y = 0). Si no, el plato aparece
hundido en la mesa o flotando encima.

**Optimización.** Sin esto, un `.glb` de fotogrametría pesa 40–80 MB y es
inusable con los datos móviles de un cliente:

```bash
npm i -g @gltf-transform/cli
gltf-transform optimize entrada.glb salida.glb \
  --texture-compress ktx2 --texture-size 1024 --compress meshopt
```

Objetivo: **menos de 3 MB por plato**. Verificá en
[modelviewer.dev/editor](https://modelviewer.dev/editor) antes de subirlo.

**Convertir a USDZ** con el script de arriba y subir ambos archivos.

Los modelos de `models/` son estilizados y generados por código
(`build_models.py`), no escaneos. Sirven para probar toda la mecánica —escala,
AR, carga, interfaz— mientras se produce el set real.

---

## 6. Tarjetas de mesa (QR) en PDF

```bash
pip install reportlab qrcode pillow
python3 generar_qrs.py --restaurante casa-anacaona \
  --dominio https://tu-sitio.onrender.com --mesas 12
```

Genera `qrs/mesas-casa-anacaona.pdf`: una página por mesa, hoja apaisada que se
dobla al medio y queda parada como una carpa, con el **mismo QR en las dos
caras** para que se lea desde cualquier lado de la mesa. Cada QR apunta a
`{dominio}/?r={slug}&mesa={N}`, así que al escanearlo el comensal entra
directo a su mesa.

```bash
--mesas 12                                   # crea las mesas 1 a 12
--mesas "1,2,3,Barra,Terraza 1,Terraza 2"    # nombres, para zonas sin numerar
--pagina a4                                  # si no imprimís en carta/letter
--salida ruta/personalizada.pdf              # por defecto: qrs/mesas-<slug>.pdf
```

**Reemplazá `--dominio` por la URL real** que te dio Render (o tu dominio
propio) antes de imprimir. Un QR con el dominio de prueba no lleva a ningún
lado.

El QR usa corrección de errores alta (nivel H): tolera el brillo del
laminado, una mancha de grasa o el roce diario sobre la mesa. El script no
dibuja nada encima del propio código —ni el logo, ni el ícono 3D— porque
cubrir aunque sea una esquina puede tapar uno de los tres patrones que la
cámara usa para encontrarlo y romper el escaneo por completo. Antes de
imprimir en cantidad, se puede confirmar que cada código decodifica bien:

```bash
pip install pdf2image pyzbar
python3 -c "
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
for i, p in enumerate(convert_from_path('qrs/mesas-casa-anacaona.pdf', dpi=150)):
    print(i+1, len(decode(p)), 'códigos leídos (debería ser 2)')
"
```

**Para imprimir:** hoja apaisada (A4 u oficio/carta según `--pagina`), sin
achicar al ajustar a página. Doblá cada hoja al medio por la línea punteada
vertical: el pliegue queda como cresta de la carpa, y las dos caras iguales
se ven desde los dos lados de la mesa. Como es un elemento que se planta una
vez y dura meses, vale la pena laminarlo o mandarlo a plastificar en una
imprenta en vez de reimprimirlo seguido.

---

## 7. Desarrollo local

Los modelos y los menús se cargan por `fetch`, así que abrir el archivo con doble
clic no funciona. Hace falta un servidor:

```bash
python3 -m http.server 8080
# http://localhost:8080/?r=casa-anacaona
```

Para probar AR desde el celular antes de desplegar necesitás HTTPS:

```bash
npx localtunnel --port 8080   # o: ngrok http 8080
```

Para generar el archivo único autocontenido, útil para mandarle el demo a un
restaurante por WhatsApp sin servidor de por medio:

```bash
python3 build_demo.py
```

## Qué falta para vender esto

- **Panel del restaurante.** `app.js` ya cuenta las aperturas de AR por plato
  (función `registrar`, hoy en `localStorage`). Apuntá eso a un endpoint y tenés
  la métrica que justifica la suscripción.
- **Editor de menú.** Hoy el cliente depende de vos para cambiar un precio. Un
  CMS liviano sobre los mismos JSON resuelve el 80%.
- **Multi-idioma.** Zona Colonial y Punta Cana tienen mucho turista; el mismo
  JSON con `nombre_en` y `descripcion_en` alcanza.
- ~~Generador de QR por mesa en PDF~~ — resuelto, ver sección 6.
