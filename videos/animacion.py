"""Modo animado para hacer_video.py.

Capas: fondo con luces que se mueven y partículas, texto que entra palabra por
palabra (las resaltadas con rebote y subrayado), salida suave entre escenas,
subtítulos tipo karaoke y un cierre con el logo del ojo.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

import hacer_video as hv

W, H = hv.W, hv.H
OUTRO = 2.6          # segundos del cierre con el logo
SALIDA = 0.28        # segundos de salida del texto al final de cada escena


# ---------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.9):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def alfa(sprite, a):
    if a >= 0.999:
        return sprite
    r, g, b, al = sprite.split()
    return Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * a))))


def pegar(frame, sprite, x, y, a=1.0, escala=1.0):
    if a <= 0.003:
        return
    if abs(escala - 1) > 0.004:
        w, h = sprite.size
        nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
        x += (w - nw) / 2
        y += (h - nh) / 2
        sprite = sprite.resize((nw, nh), Image.BILINEAR)
    frame.alpha_composite(alfa(sprite, a), (int(round(x)), int(round(y))))


def sprite_texto(texto, f, color, pad=12):
    caja = f.getbbox(texto)
    w, h = caja[2] + pad * 2, caja[3] + pad * 2
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad, pad), texto, font=f, fill=color)
    return im, pad


# ---------------------------------------------------------------- fondo
class Fondo:
    ESC = 4  # el fondo se dibuja a 1/4 y se escala: las luces son difusas

    def __init__(self, semilla=7):
        rnd = random.Random(semilla)
        w, h = W // self.ESC, H // self.ESC
        self.base = Image.new("RGB", (w, h), hv.BG)
        self.luces = []
        for color, radio, fuerza in (((90, 64, 32), 150, 150), ((36, 56, 86), 170, 170),
                                     ((70, 52, 30), 110, 110)):
            # lienzo de 3 radios: el desenfoque cabe entero y no deja bordes rectos
            m = Image.new("L", (radio * 3, radio * 3), 0)
            ImageDraw.Draw(m).ellipse((radio * 0.95, radio * 0.95, radio * 2.05, radio * 2.05), fill=fuerza)
            m = m.filter(ImageFilter.GaussianBlur(radio * 0.2))
            capa = Image.new("RGBA", m.size, color + (0,))
            capa.putalpha(m)
            self.luces.append((capa, rnd.uniform(0, 6.28), rnd.uniform(0.05, 0.11)))
        self.particulas = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.6, 4.2),
                            rnd.uniform(12, 34), rnd.uniform(0, 6.28)) for _ in range(46)]

    def frame(self, t):
        bg = self.base.copy().convert("RGBA")
        w, h = bg.size
        caminos = ((0.78, 0.18, 0.22, 0.10), (0.18, 0.80, 0.20, 0.08), (0.55, 0.55, 0.30, 0.16))
        for (capa, fase, vel), (cx, cy, ax, ay) in zip(self.luces, caminos):
            x = (cx + ax * math.sin(t * vel * 6.28 + fase)) * w - capa.width / 2
            y = (cy + ay * math.cos(t * vel * 5.0 + fase)) * h - capa.height / 2
            bg.alpha_composite(capa, (int(x), int(y)))
        frame = bg.resize((W, H), Image.BILINEAR)
        d = ImageDraw.Draw(frame)
        for x0, y0, r, vel, fase in self.particulas:
            y = (y0 - t * vel) % H
            x = x0 + 14 * math.sin(t * 0.6 + fase)
            brillo = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(t * 1.7 + fase * 3))
            c = tuple(int(b + (i - b) * brillo) for b, i in zip(hv.BG, (227, 200, 160)))
            d.ellipse((x - r, y - r, x + r, y + r), fill=c + (255,))
        return frame


# ---------------------------------------------------------------- escenas
class Palabra:
    def __init__(self, sprite, x, y, resaltada, inicio, ancho_texto, pad, linea_y, tam):
        self.sprite, self.x, self.y = sprite, x, y
        self.resaltada, self.inicio = resaltada, inicio
        self.ancho_texto, self.pad, self.linea_y, self.tam = ancho_texto, pad, linea_y, tam


def palabras_escena(texto, a, b, cy, max_h, tam_max):
    toks = hv.tokens(texto)
    for tam in range(tam_max, 44, -4):
        f = hv.fuente("display", tam)
        lineas = hv.envolver(toks, f, hv.TEXT_W)
        alto_l = int(tam * 1.18)
        if len(lineas) * alto_l <= max_h and all(hv.ancho_linea(l, f) <= hv.TEXT_W for l in lineas):
            break
    esp = f.getlength(" ")
    total = sum(len(l) for l in lineas)
    paso = min(0.11, 1.1 / max(total, 1))
    out, y, i = [], cy - len(lineas) * alto_l / 2, 0
    for l in lineas:
        x = hv.TEXT_CX - hv.ancho_linea(l, f) / 2
        for j, (w, r) in enumerate(l):
            if w.startswith("\x00"):
                x -= esp
                w = w[1:]
            spr, pad = sprite_texto(w, f, hv.OCHRE if r else hv.INK)
            out.append(Palabra(spr, x - pad, y - pad, r, a + 0.1 + i * paso, f.getlength(w), pad, y, tam))
            x += f.getlength(w) + esp
            i += 1
        y += alto_l
    return out


class Subtitulo:
    """Un trozo de subtítulo con la palabra actual iluminada."""

    def __init__(self, texto, t0, t1, f):
        self.t0, self.t1 = t0, t1
        ws = texto.split()
        tam = 46
        while True:
            esp = f.getlength(" ")
            ancho = sum(f.getlength(w) for w in ws) + esp * (len(ws) - 1)
            if ancho <= 860 or tam <= 30:
                break
            tam -= 2
            f = hv.fuente("body", tam, 800)
        x0 = hv.TEXT_CX - ancho / 2
        y0 = hv.SUB_Y
        self.caja = (x0 - 24, y0 - 10, x0 + ancho + 24, y0 + 62)
        self.base = Image.new("RGBA", (int(ancho + 48), 72 + 12), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.base)
        d.rounded_rectangle((0, 0, ancho + 48, 72), 20, fill=(12, 14, 19, 210))
        self.encendidas, x, tiempos, acum = [], 24, [], 0
        largos = [len(w) + 1 for w in ws]
        for w, n in zip(ws, largos):
            d.text((x, 10), w, font=f, fill=hv.INK)
            spr, pad = sprite_texto(w, f, hv.OCHRE, pad=0)
            self.encendidas.append((spr, x0 - 24 + x, y0))
            tiempos.append(t0 + (t1 - t0) * acum / sum(largos))
            acum += n
            x += f.getlength(w) + esp
        self.tiempos = tiempos

    def dibujar(self, frame, t):
        a = ease_out((t - self.t0) / 0.12)
        pegar(frame, self.base, self.caja[0], self.caja[1], a)
        idx = max(i for i, ti in enumerate(self.tiempos) if ti <= t or i == 0)
        spr, x, y = self.encendidas[idx]
        pegar(frame, spr, x, y, a)


# ---------------------------------------------------------------- logo
def sprite_ojo(ancho):
    x = 3
    n = int(ancho * x)
    im = Image.new("RGBA", (n, int(n * 0.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, w = n / 2, n * 0.3, n * 0.86
    alto = w * 0.36
    r = (w ** 2 / 4 + alto ** 2) / (2 * alto)
    ang = math.degrees(math.asin(w / 2 / r))
    g = int(n * 0.042)
    d.arc((cx - r, cy - alto, cx + r, cy - alto + 2 * r), 270 - ang, 270 + ang, fill=hv.INK, width=g)
    d.arc((cx - r, cy + alto - 2 * r, cx + r, cy + alto), 90 - ang, 90 + ang, fill=hv.INK, width=g)
    ir = n * 0.168
    d.ellipse((cx - ir, cy - ir, cx + ir, cy + ir), fill=hv.OCHRE)
    p = ir * 0.42
    d.ellipse((cx - p, cy - p, cx + p, cy + p), fill=hv.BG)
    return im.resize((int(ancho), int(ancho * 0.6)), Image.LANCZOS)


# ---------------------------------------------------------------- animador
class Animador:
    def __init__(self, meta, escenas, bloques, total):
        self.total = total
        self.fondo = Fondo()
        self.fija = hv.capa_fija(meta)
        caja = self.fija.getbbox()
        self.fija_spr = self.fija.crop(caja)
        self.fija_pos = caja[:2]
        fsub = hv.fuente("body", 46, 800)
        self.escenas = []
        for n, ((a, b), e) in enumerate(zip(bloques, escenas)):
            pals = palabras_escena(e["pantalla"], a, b, hv.MAIN_CY, hv.MAIN_MAX_H, 104)
            subs, t = [], a
            trozos = hv.trozos_subtitulo(e["voz"]) if e["voz"] else []
            habla = max(b - a - 0.4, 0.5)
            pesos = [max(len(x), 1) for x in trozos]
            for tr, p in zip(trozos, pesos):
                dur = habla * p / sum(pesos)
                subs.append(Subtitulo(tr, t, t + dur, fsub))
                t += dur
            ultima = n == len(escenas) - 1
            self.escenas.append((a, b, pals, subs, ultima))
        self.fin_escenas = bloques[-1][1]
        self.ojo = sprite_ojo(560)
        f1 = hv.fuente("display", 64)
        f2 = hv.fuente("body", 40, 700)
        self.nombre, _ = sprite_texto("El Observador Interior", f1, hv.INK)
        self.seguir, _ = sprite_texto("Seguí para más", f2, hv.OCHRE)

    def _escena(self, frame, d, t, a, b, pals, ultima):
        salida = 1.0 if ultima else clamp((b - t) / SALIDA)
        if t >= self.fin_escenas:
            salida = clamp(1 - (t - self.fin_escenas) / 0.35)
        dy_salida = (1 - salida) * -26
        for p in pals:
            k = (t - p.inicio) / 0.38
            if k <= 0:
                continue
            e = ease_out(k)
            escala = 1.0
            if p.resaltada:
                escala = 0.6 + 0.4 * ease_back((t - p.inicio) / 0.5)
            pegar(frame, p.sprite, p.x, p.y + (1 - e) * 34 + dy_salida, e * salida, escala)
            if p.resaltada:
                u = ease_out((t - p.inicio - 0.25) / 0.4) * salida
                if u > 0.01:
                    y = p.linea_y + p.tam * 1.08 + dy_salida
                    color = tuple(int(c * u + bg * (1 - u)) for c, bg in zip(hv.OCHRE, hv.BG))
                    d.rounded_rectangle((p.x + p.pad, y, p.x + p.pad + p.ancho_texto * u, y + 6), 3,
                                        fill=color + (255,))

    def _cierre(self, frame, t):
        k = t - self.fin_escenas
        if k <= 0.2:
            return
        k -= 0.2
        e = ease_back(k / 0.6, 1.4)
        ojo = self.ojo
        # parpadeo
        if 1.2 < k < 1.45:
            s = abs((k - 1.325) / 0.125)
            ojo = ojo.resize((ojo.width, max(4, int(ojo.height * max(s, 0.08)))), Image.BILINEAR)
        x = hv.TEXT_CX - ojo.width / 2
        y = 760 - ojo.height / 2
        pegar(frame, ojo, x, y, ease_out(k / 0.4), max(e, 0.05))
        a2 = ease_out((k - 0.45) / 0.4)
        pegar(frame, self.nombre, hv.TEXT_CX - self.nombre.width / 2, 1010 + (1 - a2) * 20, a2)
        a3 = ease_out((k - 0.75) / 0.4)
        pegar(frame, self.seguir, hv.TEXT_CX - self.seguir.width / 2, 1110 + (1 - a3) * 20, a3)

    def frame(self, t):
        frame = self.fondo.frame(t)
        frame.alpha_composite(self.fija_spr, self.fija_pos)
        d = ImageDraw.Draw(frame)
        d.rectangle((0, 0, int(W * clamp(t / self.total)), 7), fill=hv.OCHRE + (255,))
        actual = None
        for esc in self.escenas:
            if esc[0] <= t or esc is self.escenas[0]:
                actual = esc
        a, b, pals, subs, ultima = actual
        self._escena(frame, d, t, a, b, pals, ultima)
        if t < self.fin_escenas:
            for s in subs:
                if s.t0 <= t < s.t1:
                    s.dibujar(frame, t)
                    break
        self._cierre(frame, t)
        return frame

    def portada(self):
        a, b, pals, _, _ = self.escenas[0]
        return self.frame(min(b - 0.5, a + 2.5)).convert("RGB")
