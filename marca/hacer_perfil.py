#!/usr/bin/env python3
"""Genera opciones de foto de perfil (1080x1080) para El Observador Interior.

Uso: python3 marca/hacer_perfil.py
Crea marca/perfil-*.png y marca/perfil-comparacion.png (vista en círculo).
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI.parent / "videos" / "fuentes"
S = 1080
X = 4  # supermuestreo para bordes suaves
N = S * X

BG = (18, 21, 28)
DEEP_BG = (31, 43, 60)
INK = (231, 234, 240)
OCHRE = (227, 169, 95)
DEEP = (44, 74, 110)
CREAM = (245, 234, 217)


def lienzo(color):
    return Image.new("RGB", (N, N), color)


def brillo(img, color, centro, radio, fuerza=110):
    m = Image.new("L", (N // 8, N // 8), 0)
    d = ImageDraw.Draw(m)
    cx, cy, r = centro[0] / 8, centro[1] / 8, radio / 8
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fuerza)
    m = m.filter(ImageFilter.GaussianBlur(radio / 20)).resize((N, N))
    return Image.composite(Image.new("RGB", (N, N), color), img, m)


def final(img):
    return img.resize((S, S), Image.LANCZOS)


def ojo(d, cx, cy, ancho, color_linea, color_iris, grosor, iris_r, pupila_color=None):
    """Ojo almendrado formado por dos arcos."""
    alto = ancho * 0.36
    # radio del arco que pasa por las comisuras y la altura
    r = (ancho ** 2 / 4 + alto ** 2) / (2 * alto)
    # arco superior: centro debajo
    d.arc((cx - r, cy - alto + 0 - 0, cx + r, cy - alto + 2 * r),
          start=270 - math.degrees(math.asin(ancho / 2 / r)),
          end=270 + math.degrees(math.asin(ancho / 2 / r)), fill=color_linea, width=grosor)
    d.arc((cx - r, cy + alto - 2 * r, cx + r, cy + alto),
          start=90 - math.degrees(math.asin(ancho / 2 / r)),
          end=90 + math.degrees(math.asin(ancho / 2 / r)), fill=color_linea, width=grosor)
    d.ellipse((cx - iris_r, cy - iris_r, cx + iris_r, cy + iris_r), fill=color_iris)
    if pupila_color:
        p = iris_r * 0.42
        d.ellipse((cx - p, cy - p, cx + p, cy + p), fill=pupila_color)


def opcion_ojo():
    img = brillo(lienzo(BG), (60, 46, 28), (N * 0.5, N * 0.5), N * 0.55, 140)
    d = ImageDraw.Draw(img)
    ojo(d, N / 2, N / 2, N * 0.66, INK, OCHRE, int(N * 0.028), N * 0.115, BG)
    return final(img)


def opcion_monograma():
    img = brillo(lienzo(BG), (60, 46, 28), (N * 0.72, N * 0.25), N * 0.6, 120)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FUENTES / "Gloock-Regular.ttf"), int(N * 0.5))
    texto = "OI"
    caja = d.textbbox((0, 0), texto, font=f)
    w, h = caja[2] - caja[0], caja[3] - caja[1]
    x, y = (N - w) / 2 - caja[0], (N - h) / 2 - caja[1]
    d.text((x, y), "O", font=f, fill=OCHRE)
    d.text((x + f.getlength("O"), y), "I", font=f, fill=INK)
    return final(img)


def opcion_circulos():
    img = lienzo(DEEP_BG)
    img = brillo(img, (52, 70, 96), (N * 0.5, N * 0.5), N * 0.5, 120)
    d = ImageDraw.Draw(img)
    c = N / 2
    for r, g, col in ((N * 0.34, 0.012, (120, 148, 186)), (N * 0.24, 0.016, INK)):
        d.ellipse((c - r, c - r, c + r, c + r), outline=col, width=int(N * g))
    r = N * 0.09
    d.ellipse((c - r, c - r, c + r, c + r), fill=OCHRE)
    return final(img)


def opcion_ojo_claro():
    img = lienzo(CREAM)
    d = ImageDraw.Draw(img)
    ojo(d, N / 2, N / 2, N * 0.66, DEEP, OCHRE, int(N * 0.03), N * 0.115, DEEP)
    return final(img)


def comparacion(rutas):
    """Muestra cada opción recortada en círculo, grande y en tamaño real de la app."""
    grande, chico, margen = 360, 56, 40
    ancho = len(rutas) * (grande + margen) + margen
    hoja = Image.new("RGB", (ancho, grande + chico + 3 * margen + 40), (250, 250, 250))
    d = ImageDraw.Draw(hoja)
    fl = ImageFont.truetype(str(FUENTES / "Mulish-Variable.ttf"), 26)
    for i, (nombre, ruta) in enumerate(rutas):
        im = Image.open(ruta)
        x = margen + i * (grande + margen)
        for tam, y in ((grande, margen), (chico, margen * 2 + grande)):
            m = Image.new("L", (tam * 4, tam * 4), 0)
            ImageDraw.Draw(m).ellipse((0, 0, tam * 4, tam * 4), fill=255)
            m = m.resize((tam, tam), Image.LANCZOS)
            hoja.paste(im.resize((tam, tam), Image.LANCZOS), (x + (grande - tam) // 2, y), m)
        d.text((x + grande / 2, margen * 2 + grande + chico + 20), nombre, font=fl,
               fill=(40, 40, 40), anchor="mt")
    return hoja


def main():
    opciones = [
        ("1 · Ojo", "perfil-1-ojo.png", opcion_ojo),
        ("2 · Monograma OI", "perfil-2-monograma.png", opcion_monograma),
        ("3 · Círculos", "perfil-3-circulos.png", opcion_circulos),
        ("4 · Ojo claro", "perfil-4-ojo-claro.png", opcion_ojo_claro),
    ]
    rutas = []
    for nombre, archivo, fn in opciones:
        ruta = AQUI / archivo
        fn().save(ruta)
        rutas.append((nombre, ruta))
        print("Creado:", ruta)
    comparacion(rutas).save(AQUI / "perfil-comparacion.png")
    print("Comparación:", AQUI / "perfil-comparacion.png")


if __name__ == "__main__":
    main()
