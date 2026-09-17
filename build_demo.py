"""Empaqueta el sitio en un solo .html autocontenido (modelos en base64)."""
import base64, json, os, re

RAIZ = os.path.dirname(os.path.abspath(__file__))
leer = lambda *p: open(os.path.join(RAIZ, *p), encoding="utf-8").read()

def glb_datauri(ruta):
    with open(os.path.join(RAIZ, ruta), "rb") as f:
        return "data:model/gltf-binary;base64," + base64.b64encode(f.read()).decode()

# Menús con los modelos incrustados
menus, cache = {}, {}
for arch in ("casa-anacaona", "parada-47"):
    d = json.loads(leer("data", f"{arch}.json"))
    for plato in d["platos"]:
        # Quick Look (iOS) no acepta data URIs, así que en el demo embebido
        # no ofrecemos usdz. En el sitio desplegado sí funciona.
        plato.pop("usdz", None)
        if plato.get("modelo"):
            r = plato["modelo"]
            if r not in cache:
                cache[r] = glb_datauri(r)
            plato["modelo"] = cache[r]
    menus[arch] = d

html = leer("index.html")
css = leer("assets", "app.css")
js = leer("assets", "app.js")

html = html.replace(
    '<link rel="stylesheet" href="assets/app.css">',
    "<style>\n" + css + "\n</style>")

selector = """
  <div class="demo-sel">
    <span>Demo multi-restaurante</span>
    <button type="button" onclick="cargarRestaurante('casa-anacaona')">Casa Anacaona</button>
    <button type="button" onclick="cargarRestaurante('parada-47')">Parada 47</button>
  </div>
"""
html = html.replace(
    '    Menú en 3D por <strong>Mesa Viva</strong>',
    '    Menú en 3D por <strong>Mesa Viva</strong>' + selector)

html = html.replace(
    '<script src="assets/app.js"></script>',
    "<script>window.MENUS = " + json.dumps(menus, ensure_ascii=False) + ";</script>\n"
    "<script>\n" + js + "\n</script>")

html = html.replace("</style>", """
.demo-sel { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 7px;
  align-items: center; justify-content: center; }
.demo-sel span { width: 100%; font-size: 11px; color: #5d5147; margin-bottom: 3px; }
.demo-sel button { font: inherit; font-size: 12px; color: var(--humo);
  background: var(--carbon); border: 1px solid var(--borde); border-radius: 999px;
  padding: 5px 13px; cursor: pointer; }
.demo-sel button:hover { color: var(--mantel); border-color: var(--humo-2); }
</style>""")

salida = "/mnt/user-data/outputs/menu-ar-demo.html"
os.makedirs(os.path.dirname(salida), exist_ok=True)
open(salida, "w", encoding="utf-8").write(html)
print(f"{salida}  —  {os.path.getsize(salida)/1024:.0f} KB")
