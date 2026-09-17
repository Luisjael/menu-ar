"""
Genera modelos .glb estilizados de platos, a ESCALA REAL en metros.
Origen en la base (y=0) y centrado en XZ, que es lo que Scene Viewer
y Quick Look necesitan para apoyar bien sobre la mesa detectada.
"""
import numpy as np, trimesh, os

OUT = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUT, exist_ok=True)


def mat(hexcolor, rough=0.6, metal=0.0):
    h = hexcolor.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=rgb + [255],
        roughnessFactor=rough,
        metallicFactor=metal,
        doubleSided=False,
    )


def paint(mesh, hexcolor, rough=0.6, metal=0.0):
    mesh.visual = trimesh.visual.TextureVisuals(material=mat(hexcolor, rough, metal))
    return mesh


def revolve(profile, sections=48):
    """profile = [(radio, altura), ...] de abajo hacia arriba"""
    return trimesh.creation.revolve(np.array(profile, dtype=float), sections=sections)


def at(mesh, x=0.0, y=0.0, z=0.0):
    mesh.apply_translation([x, y, z])
    return mesh


def cyl(r, h, hexcolor, sections=28, rough=0.6):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([0, 0, h / 2])
    return paint(m, hexcolor, rough)


def ball(r, hexcolor, sub=2, rough=0.55):
    m = trimesh.creation.icosphere(subdivisions=sub, radius=r)
    return paint(m, hexcolor, rough)


def plato(diam=0.27, color="#F4F1EC"):
    """Plato llano de loza, diámetro real de plato principal."""
    r = diam / 2
    prof = [
        (0.0, 0.000), (r * 0.30, 0.000), (r * 0.34, 0.004),
        (r * 0.62, 0.006), (r * 0.88, 0.020), (r * 1.00, 0.026),
        (r * 0.99, 0.024), (r * 0.86, 0.015), (r * 0.58, 0.002),
        (r * 0.30, 0.0015), (0.0, 0.0015),
    ]
    return paint(revolve(prof, 56), color, rough=0.35)


def bol(diam=0.17, alto=0.075, color="#E8E2D6"):
    r = diam / 2
    prof = [
        (0.0, 0.0), (r * 0.42, 0.0), (r * 0.45, 0.006),
        (r * 0.62, 0.022), (r * 0.88, 0.055), (r * 1.00, alto),
        (r * 0.94, alto), (r * 0.80, 0.052), (r * 0.55, 0.020),
        (r * 0.38, 0.008), (0.0, 0.008),
    ]
    return paint(revolve(prof, 52), color, rough=0.32)


def export(nombre, partes):
    escena = trimesh.Scene()
    for i, m in enumerate(partes):
        escena.add_geometry(m, node_name=f"p{i}")
    # trimesh trabaja en Z-up; glTF es Y-up. Rotar -90 en X.
    escena.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    ruta = os.path.join(OUT, f"{nombre}.glb")
    escena.export(ruta)
    kb = os.path.getsize(ruta) / 1024
    b = escena.bounds
    print(f"{nombre:16s} {kb:6.1f} KB   {(b[1]-b[0])[0]*100:5.1f} x "
          f"{(b[1]-b[0])[1]*100:5.1f} x {(b[1]-b[0])[2]*100:5.1f} cm")


# ── 1. Mofongo con camarones ───────────────────────────────────────────────
p = [plato(0.26)]
mof = revolve([(0.0, 0.002), (0.052, 0.002), (0.056, 0.020),
               (0.050, 0.052), (0.034, 0.070), (0.0, 0.074)], 40)
p.append(paint(mof, "#C9A15C", rough=0.85))
rng = np.random.default_rng(7)
for i in range(7):
    a = i / 7 * 2 * np.pi + 0.3
    rad = 0.030 + rng.random() * 0.012
    cam = trimesh.creation.capsule(radius=0.0085, height=0.024, count=[8, 10])
    cam.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2.4, [1, 0, 0]))
    cam.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1]))
    p.append(paint(at(cam, np.cos(a) * rad, np.sin(a) * rad, 0.072), "#E8734A", rough=0.45))
for i in range(5):
    a = i / 5 * 2 * np.pi
    p.append(paint(at(trimesh.creation.box([0.014, 0.004, 0.003]),
                      np.cos(a) * 0.07, np.sin(a) * 0.07, 0.010), "#6C8F3E", rough=0.7))
export("mofongo", p)

# ── 2. Pescado a la parrilla ───────────────────────────────────────────────
p = [plato(0.28, "#2E2A26")]
cuerpo = trimesh.creation.icosphere(subdivisions=2, radius=0.045)
cuerpo.apply_scale([2.1, 0.62, 0.42])
p.append(paint(at(cuerpo, 0, 0, 0.022), "#D9C9A8", rough=0.5))
cola = trimesh.creation.box([0.030, 0.006, 0.042])
cola.apply_transform(trimesh.transformations.rotation_matrix(0.25, [0, 1, 0]))
p.append(paint(at(cola, -0.104, 0, 0.026), "#C4B08C", rough=0.55))
for i in range(4):
    p.append(paint(at(trimesh.creation.box([0.028, 0.0035, 0.0035]),
                      -0.03 + i * 0.022, 0, 0.041), "#6B4A2E", rough=0.9))
lim = trimesh.creation.cylinder(radius=0.022, height=0.008, sections=24)
lim.apply_scale([1, 1, 1])
p.append(paint(at(lim, 0.085, 0.052, 0.006), "#EBC442", rough=0.45))
for i in range(6):
    a = i / 6 * 2 * np.pi
    p.append(paint(at(trimesh.creation.box([0.016, 0.006, 0.006]),
                      -0.055 + np.cos(a) * 0.028, 0.048 + np.sin(a) * 0.016, 0.008),
                   "#4F7A32", rough=0.75))
export("pescado", p)

# ── 3. Sancocho (bol) ──────────────────────────────────────────────────────
p = [bol(0.18, 0.082, "#B8402F")]
caldo = trimesh.creation.cylinder(radius=0.076, height=0.004, sections=44)
p.append(paint(at(caldo, 0, 0, 0.056), "#C98A34", rough=0.25))
rng = np.random.default_rng(3)
trozos = [("#E3B64F", 0.013), ("#D9DCC4", 0.011), ("#8A5A32", 0.012),
          ("#E3B64F", 0.010), ("#6C8F3E", 0.009), ("#8A5A32", 0.013),
          ("#D9DCC4", 0.010)]
for i, (c, r) in enumerate(trozos):
    a = i / len(trozos) * 2 * np.pi + 0.4
    d = 0.018 + rng.random() * 0.030
    b = trimesh.creation.box([r * 1.7, r * 1.5, r * 1.2])
    b.apply_transform(trimesh.transformations.rotation_matrix(rng.random() * 3, [0, 0, 1]))
    p.append(paint(at(b, np.cos(a) * d, np.sin(a) * d, 0.058), c, rough=0.7))
export("sancocho", p)

# ── 4. Hamburguesa ─────────────────────────────────────────────────────────
p = [paint(revolve([(0.0, 0.0), (0.085, 0.0), (0.088, 0.004),
                    (0.086, 0.010), (0.0, 0.011)], 40), "#3A3632", rough=0.3)]
pan_b = revolve([(0.0, 0.011), (0.053, 0.011), (0.056, 0.020),
                 (0.050, 0.030), (0.0, 0.031)], 40)
p.append(paint(pan_b, "#D2A05A", rough=0.8))
p.append(paint(at(cyl(0.056, 0.008, "#5E8C3A"), 0, 0, 0.030), "#5E8C3A", rough=0.6))
carne = cyl(0.055, 0.020, "#5A3A28", 36, rough=0.85)
p.append(at(carne, 0, 0, 0.038))
queso = trimesh.creation.box([0.106, 0.106, 0.004])
p.append(paint(at(queso, 0, 0, 0.060), "#EFB427", rough=0.4))
for i in range(3):
    a = i / 3 * 2 * np.pi
    p.append(paint(at(cyl(0.030, 0.006, "#C3402E"), np.cos(a) * 0.014,
                      np.sin(a) * 0.014, 0.062), "#C3402E", rough=0.5))
pan_t = revolve([(0.0, 0.068), (0.056, 0.068), (0.058, 0.080),
                 (0.050, 0.098), (0.030, 0.108), (0.0, 0.110)], 44)
p.append(paint(pan_t, "#C98F45", rough=0.75))
for i in range(9):
    a = i / 9 * 2 * np.pi
    d = 0.016 + (i % 3) * 0.010
    s = ball(0.0022, "#F7F0DC", 1)
    p.append(at(s, np.cos(a) * d, np.sin(a) * d, 0.104 - (d * 0.35)))
for i, x in enumerate([0.09, 0.105, 0.098]):
    p.append(paint(at(trimesh.creation.box([0.012, 0.011, 0.060]),
                      x - 0.02, 0.042 + i * 0.012, 0.042), "#E0A43A", rough=0.8))
export("hamburguesa", p)

# ── 5. Flan ────────────────────────────────────────────────────────────────
p = [paint(revolve([(0.0, 0.0), (0.072, 0.0), (0.074, 0.005),
                    (0.0, 0.006)], 40), "#EFEAE0", rough=0.3)]
caramelo = revolve([(0.0, 0.006), (0.052, 0.006), (0.050, 0.009), (0.0, 0.009)], 36)
p.append(paint(caramelo, "#8C4A1E", rough=0.25))
flan = revolve([(0.0, 0.008), (0.048, 0.008), (0.047, 0.026),
                (0.040, 0.044), (0.036, 0.048), (0.0, 0.049)], 44)
p.append(paint(flan, "#E8C67A", rough=0.4))
p.append(paint(at(ball(0.010, "#F7F3EA", 2), 0.0, 0.0, 0.052), "#F7F3EA", rough=0.85))
p.append(paint(at(trimesh.creation.box([0.010, 0.006, 0.004]), 0.012, 0.010, 0.058),
               "#5E7F35", rough=0.6))
export("flan", p)

# ── 6. Morir soñando (vaso) ────────────────────────────────────────────────
p = []
vaso = revolve([(0.0, 0.0), (0.033, 0.0), (0.034, 0.004),
                (0.036, 0.060), (0.039, 0.130), (0.040, 0.142),
                (0.0365, 0.142), (0.0335, 0.060), (0.0305, 0.006), (0.0, 0.006)], 48)
liq = revolve([(0.0, 0.007), (0.0332, 0.007), (0.0368, 0.120), (0.0, 0.121)], 44)
p.append(paint(liq, "#F2B95E", rough=0.15))
p.append(paint(vaso, "#DCE6EA", rough=0.05))
p.append(paint(at(trimesh.creation.cylinder(radius=0.0035, height=0.135, sections=12),
                  0.014, 0.006, 0.085), "#D8453E", rough=0.4))
p.append(paint(at(cyl(0.016, 0.010, "#E9A33A"), 0.040, 0.020, 0.130), "#E9A33A", rough=0.5))
export("morir_sonando", p)

print("\nListo.")
