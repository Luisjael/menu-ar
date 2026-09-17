#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un PDF con una tarjeta de mesa por mesa: una hoja apaisada que se dobla
al medio y queda parada como una carpa, con el mismo QR en las dos caras para
que se vea desde cualquier lado de la mesa.

Uso:
    python3 generar_qrs.py --restaurante casa-anacaona \
        --dominio https://tu-sitio.onrender.com --mesas 12

    python3 generar_qrs.py --restaurante parada-47 \
        --dominio https://tu-sitio.onrender.com --mesas "1,2,3,Barra,Terraza 1,Terraza 2"

Requiere:  pip install reportlab qrcode pillow
"""
import argparse
import io
import json
import os

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

RAIZ = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(RAIZ, "assets", "fuentes")

NOCHE = "#17120f"
CARBON = "#211a15"
BORDE = "#3a2f26"
MANTEL = "#f7f1e5"
HUMO = "#a0917f"
HUMO2 = "#776a5c"
MADURO_POR_DEFECTO = "#f0b429"


def registrar_fuentes():
    pdfmetrics.registerFont(TTFont("Bricolage", os.path.join(FUENTES, "Bricolage-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("Bricolage-Bold", os.path.join(FUENTES, "Bricolage-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Inter", os.path.join(FUENTES, "Inter-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Inter-Medio", os.path.join(FUENTES, "Inter-Medium.ttf")))
    pdfmetrics.registerFont(TTFont("Inter-Semi", os.path.join(FUENTES, "Inter-SemiBold.ttf")))


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def generar_qr(url, color_frente="#1b1512", color_fondo="#f7f1e5"):
    """QR con corrección de errores alta: tolera grasa, brillo del laminado
    y el desgaste normal de una mesa de restaurante."""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=20, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color_frente, back_color=color_fondo).convert("RGB")
    return ImageReader(img)


def icono_cubo_lineas(c, x, y, tam, color):
    """El mismo ícono de cubo (hexágono + aristas internas) que usa la app web,
    para que el chip impreso y el de la pantalla se vean igual."""
    def conv(px, py):
        return (x + (px - 12) / 24 * tam, y - (py - 12) / 24 * tam)

    A, B, C, D, E, F, O = (
        conv(12, 2.6), conv(21, 7.4), conv(21, 16.6),
        conv(12, 21.4), conv(3, 16.6), conv(3, 7.4), conv(12, 12),
    )
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(tam * 0.1)
    c.setLineJoin(1)
    c.setLineCap(1)
    hexagono = c.beginPath()
    hexagono.moveTo(*A)
    for pt in (B, C, D, E, F):
        hexagono.lineTo(*pt)
    hexagono.close()
    c.drawPath(hexagono, stroke=1, fill=0)
    c.line(*F, *O)
    c.line(*O, *B)
    c.line(*O, *D)
    c.restoreState()


def panel(c, ox, oy, ancho, alto, *, nombre, acento, mesa, url, es_ultima_pieza):
    """Dibuja una cara completa de la carpa dentro del rectángulo (ox, oy, ancho, alto)."""
    rgb_acento = hex_rgb(acento)
    AR_TEAL = "#6fe3d2"
    AR_FONDO = "#0d3b35"

    c.saveState()
    p = c.beginPath()
    p.rect(ox, oy, ancho, alto)
    c.clipPath(p, stroke=0, fill=0)

    # Fondo
    c.setFillColor(NOCHE)
    c.rect(ox, oy, ancho, alto, fill=1, stroke=0)

    cx = ox + ancho / 2

    # Filete superior de color de marca
    c.setFillColorRGB(*rgb_acento)
    c.rect(ox, oy + alto - alto * 0.014, ancho, alto * 0.014, fill=1, stroke=0)

    # Nombre del restaurante
    y_nombre = oy + alto - alto * 0.115
    c.setFillColor(MANTEL)
    c.setFont("Bricolage-Bold", alto * 0.052)
    c.drawCentredString(cx, y_nombre, nombre)

    # Mesa
    y_mesa = y_nombre - alto * 0.075
    c.setFillColor(HUMO)
    c.setFont("Inter-Medio", alto * 0.026)
    etiqueta = "Mesa" if mesa and mesa[0].isdigit() else ""
    texto_mesa = f"{etiqueta} {mesa}".strip() if etiqueta else mesa
    c.drawCentredString(cx, y_mesa, texto_mesa.upper() if len(texto_mesa) <= 3 else texto_mesa)

    # Tarjeta clara detrás del QR: máximo contraste, máxima confiabilidad de escaneo.
    # Nada se dibuja jamás encima del propio QR: cubrir aunque sea una esquina
    # (ahí viven los patrones buscadores) puede impedir que la cámara lo lea.
    lado_qr = ancho * 0.58
    tarjeta_lado = lado_qr * 1.16
    tarjeta_y = oy + alto * 0.300
    c.setFillColor(MANTEL)
    c.roundRect(cx - tarjeta_lado / 2, tarjeta_y, tarjeta_lado, tarjeta_lado,
                radius=tarjeta_lado * 0.055, fill=1, stroke=0)

    qr_img = generar_qr(url)
    qx = cx - lado_qr / 2
    qy = tarjeta_y + (tarjeta_lado - lado_qr) / 2
    c.drawImage(qr_img, qx, qy, lado_qr, lado_qr)

    # Chip "disponible en 3D", separado del QR, en el mismo acento aguamarina
    # que usa la app para todo lo relacionado a la vista en AR.
    chip_ancho = ancho * 0.40
    chip_alto = alto * 0.034
    techo_tarjeta = tarjeta_y + tarjeta_lado
    chip_cy = (y_mesa - alto * 0.028 + techo_tarjeta) / 2
    c.setFillColor(AR_FONDO)
    c.roundRect(cx - chip_ancho / 2, chip_cy - chip_alto / 2, chip_ancho, chip_alto,
                radius=chip_alto / 2, fill=1, stroke=0)
    icono_cubo_lineas(c, cx - chip_ancho * 0.27, chip_cy, chip_alto * 0.48, AR_TEAL)
    c.setFillColor(AR_TEAL)
    c.setFont("Inter-Semi", chip_alto * 0.5)
    c.drawString(cx - chip_ancho * 0.16, chip_cy - chip_alto * 0.17, "Disponible en 3D")

    # Llamado a la acción
    y = tarjeta_y - alto * 0.05
    c.setFillColor(MANTEL)
    c.setFont("Bricolage", alto * 0.036)
    c.drawCentredString(cx, y, "Escaneá para ver el menú")

    y -= alto * 0.032
    c.setFillColorRGB(*rgb_acento)
    c.setFont("Inter-Medio", alto * 0.022)
    c.drawCentredString(cx, y, "y mirá cada plato en 3D sobre tu mesa")

    # Instrucción breve + URL de respaldo
    y = oy + alto * 0.075
    c.setFillColor(HUMO2)
    c.setFont("Inter", alto * 0.016)
    c.drawCentredString(cx, y, "Apuntá la cámara del celular al código")

    y -= alto * 0.026
    url_visible = url.split("://", 1)[-1]
    if len(url_visible) > 46:
        url_visible = url_visible[:43] + "…"
    c.setFillColor(HUMO2)
    c.setFont("Inter", alto * 0.0135)
    c.drawCentredString(cx, y, url_visible)

    # Marca de pie
    c.setFillColor(HUMO2)
    c.setFont("Inter-Medio", alto * 0.015)
    c.drawCentredString(cx, oy + alto * 0.025, "Mesa Viva")

    c.restoreState()


def marcas_de_doblez(c, cx, alto_total, alto_pagina):
    """Línea punteada vertical al centro de la hoja, con indicación de dónde doblar."""
    c.saveState()
    c.setStrokeColor(HUMO2)
    c.setDash(2, 3)
    c.setLineWidth(0.6)
    c.line(cx, alto_pagina * 0.03, cx, alto_pagina * 0.97)
    c.setDash()
    c.restoreState()


def construir_pdf(ruta_salida, *, restaurante_slug, nombre, acento, dominio, mesas, tamano_pagina):
    registrar_fuentes()
    base = landscape(A4) if tamano_pagina == "a4" else landscape(letter)
    ancho_pagina, alto_pagina = base

    c = canvas.Canvas(ruta_salida, pagesize=base)
    c.setTitle(f"Tarjetas de mesa — {nombre}")

    ancho_panel = ancho_pagina / 2

    for mesa in mesas:
        url = f"{dominio.rstrip('/')}/?r={restaurante_slug}&mesa={mesa}"
        for lado in (0, 1):
            panel(c, lado * ancho_panel, 0, ancho_panel, alto_pagina,
                  nombre=nombre, acento=acento, mesa=str(mesa), url=url,
                  es_ultima_pieza=(lado == 1))
        marcas_de_doblez(c, ancho_pagina / 2, ancho_pagina, alto_pagina)
        c.showPage()

    c.save()


def parse_mesas(valor):
    """Acepta un número (crea 1..N) o una lista separada por comas,
    donde cada elemento puede ser un número o un nombre ("Barra", "Terraza 2")."""
    valor = valor.strip()
    if valor.isdigit():
        return [str(n) for n in range(1, int(valor) + 1)]
    return [v.strip() for v in valor.split(",") if v.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--restaurante", required=True, help="slug del cliente, igual que en data/<slug>.json")
    ap.add_argument("--dominio", required=True, help="https://tu-sitio.onrender.com (o tu dominio propio)")
    ap.add_argument("--mesas", required=True, help='cantidad ("12") o lista ("1,2,3,Barra,Terraza")')
    ap.add_argument("--pagina", choices=["carta", "a4"], default="carta")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()

    ruta_json = os.path.join(RAIZ, "data", f"{args.restaurante}.json")
    datos = json.load(open(ruta_json, encoding="utf-8"))
    nombre = datos["nombre"]
    acento = datos.get("acento", MADURO_POR_DEFECTO)

    mesas = parse_mesas(args.mesas)
    salida = args.salida or os.path.join(RAIZ, "qrs", f"mesas-{args.restaurante}.pdf")
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    construir_pdf(salida, restaurante_slug=args.restaurante, nombre=nombre, acento=acento,
                  dominio=args.dominio, mesas=mesas, tamano_pagina=args.pagina)

    print(f"{len(mesas)} tarjetas de mesa -> {salida}")


if __name__ == "__main__":
    main()
