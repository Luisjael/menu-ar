#!/usr/bin/env python3
"""
Convierte modelos .glb a .usdz para AR Quick Look (iPhone/iPad).

En Android <model-viewer> lanza Scene Viewer con el .glb. En iOS lanza
AR Quick Look, que solo acepta .usdz. Sin este archivo, en iPhone el plato
se ve en 3D dentro de la página pero no hay botón de AR.

Uso:
    python3 glb_a_usdz.py models/*.glb
    python3 glb_a_usdz.py models/mofongo.glb -o otra/carpeta

Requiere:  pip install trimesh usd-core pillow
"""
import argparse, os, shutil, sys, tempfile

import numpy as np
import trimesh
from pxr import Usd, UsdGeom, UsdShade, UsdUtils, Sdf, Gf


def _limpiar(nombre):
    """Los nombres de prim en USD solo aceptan alfanuméricos y guion bajo."""
    s = "".join(c if c.isalnum() or c == "_" else "_" for c in str(nombre))
    return ("m_" + s) if not s or s[0].isdigit() else s


def _color_base(visual):
    """Devuelve (r, g, b) en 0..1, más rugosidad y metalicidad."""
    rgb, rough, metal = (0.8, 0.8, 0.8), 0.6, 0.0
    material = getattr(visual, "material", None)
    if material is not None:
        base = getattr(material, "baseColorFactor", None)
        if base is not None:
            base = np.asarray(base, dtype=float)
            if base.max() > 1.0:
                base = base / 255.0
            rgb = tuple(float(v) for v in base[:3])
        if getattr(material, "roughnessFactor", None) is not None:
            rough = float(material.roughnessFactor)
        if getattr(material, "metallicFactor", None) is not None:
            metal = float(material.metallicFactor)
    return rgb, rough, metal


def _textura(visual, carpeta, indice):
    """Guarda la textura de color como PNG y devuelve su ruta, o None."""
    material = getattr(visual, "material", None)
    imagen = getattr(material, "baseColorTexture", None) if material else None
    if imagen is None:
        imagen = getattr(material, "image", None) if material else None
    if imagen is None:
        return None
    ruta = os.path.join(carpeta, f"tex_{indice}.png")
    try:
        imagen.convert("RGB").save(ruta)
    except Exception:
        return None
    return ruta


def _material(stage, ruta_prim, visual, carpeta, indice, uv):
    rgb, rough, metal = _color_base(visual)
    material = UsdShade.Material.Define(stage, ruta_prim)
    shader = UsdShade.Shader.Define(stage, f"{ruta_prim}/Surface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(rough)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metal)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0)

    png = _textura(visual, carpeta, indice) if uv is not None else None
    if png:
        lector = UsdShade.Shader.Define(stage, f"{ruta_prim}/uvReader")
        lector.CreateIdAttr("UsdPrimvarReader_float2")
        lector.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
        lector.CreateOutput("result", Sdf.ValueTypeNames.Float2)

        tex = UsdShade.Shader.Define(stage, f"{ruta_prim}/diffuseTexture")
        tex.CreateIdAttr("UsdUVTexture")
        tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(os.path.basename(png))
        tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
            lector.CreateOutput("result", Sdf.ValueTypeNames.Float2))
        tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
        tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")
        tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
            tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3))
    else:
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))

    material.CreateSurfaceOutput().ConnectToSource(
        shader.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    return material


def convertir(ruta_glb, ruta_usdz):
    escena = trimesh.load(ruta_glb, force="scene")
    mallas = escena.dump(concatenate=False)
    if not mallas:
        raise ValueError("el archivo no tiene geometría")

    tmp = tempfile.mkdtemp(prefix="usdz_")
    try:
        usda = os.path.join(tmp, "modelo.usda")
        stage = Usd.Stage.CreateNew(usda)

        # AR Quick Look asume metros y eje Y hacia arriba, igual que glTF.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

        raiz = UsdGeom.Xform.Define(stage, "/Modelo")
        stage.SetDefaultPrim(raiz.GetPrim())

        usados = set()
        for i, malla in enumerate(mallas):
            nombre = _limpiar(getattr(malla, "metadata", {}).get("name", f"malla_{i}"))
            while nombre in usados:
                nombre += "_"
            usados.add(nombre)

            ruta = f"/Modelo/{nombre}"
            geom = UsdGeom.Mesh.Define(stage, ruta)
            geom.CreatePointsAttr([Gf.Vec3f(*map(float, v)) for v in malla.vertices])
            geom.CreateFaceVertexCountsAttr([3] * len(malla.faces))
            geom.CreateFaceVertexIndicesAttr(
                [int(x) for x in malla.faces.reshape(-1)])
            geom.CreateExtentAttr([Gf.Vec3f(*map(float, malla.bounds[0])),
                                   Gf.Vec3f(*map(float, malla.bounds[1]))])
            # Sin esto, Quick Look subdivide la malla y el plato sale deformado.
            geom.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)

            normales = geom.CreateNormalsAttr(
                [Gf.Vec3f(*map(float, n)) for n in malla.vertex_normals])
            geom.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
            del normales

            uv = getattr(malla.visual, "uv", None)
            if uv is not None and len(uv) == len(malla.vertices):
                primvars = UsdGeom.PrimvarsAPI(geom)
                pv = primvars.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray,
                                            UsdGeom.Tokens.vertex)
                pv.Set([Gf.Vec2f(float(a), float(b)) for a, b in uv])
            else:
                uv = None

            mat = _material(stage, f"/Modelo/Materiales/{nombre}_mat",
                            malla.visual, tmp, i, uv)
            UsdShade.MaterialBindingAPI.Apply(geom.GetPrim())
            UsdShade.MaterialBindingAPI(geom).Bind(mat)

        stage.GetRootLayer().Save()
        del stage

        salida_tmp = os.path.join(tmp, "salida.usdz")
        if not UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(usda), salida_tmp):
            raise RuntimeError("UsdUtils no pudo empaquetar el .usdz")

        os.makedirs(os.path.dirname(os.path.abspath(ruta_usdz)) or ".", exist_ok=True)
        shutil.move(salida_tmp, ruta_usdz)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Convierte .glb a .usdz para AR en iOS")
    ap.add_argument("entradas", nargs="+", help="archivos .glb")
    ap.add_argument("-o", "--salida", help="carpeta de salida (por defecto, la misma)")
    args = ap.parse_args()

    fallos = 0
    for entrada in args.entradas:
        carpeta = args.salida or os.path.dirname(entrada) or "."
        destino = os.path.join(carpeta, os.path.splitext(os.path.basename(entrada))[0] + ".usdz")
        try:
            convertir(entrada, destino)
            print(f"  {os.path.basename(destino):24s} {os.path.getsize(destino)/1024:7.1f} KB")
        except Exception as e:
            fallos += 1
            print(f"  {os.path.basename(entrada):24s} ERROR: {e}", file=sys.stderr)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
