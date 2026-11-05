#!/usr/bin/env python3
"""Genera videos verticales (1080x1920) para El Observador Interior.

Uso:
    python3 videos/hacer_video.py videos/cortos/01-nada-es-personal/escenas.txt
    python3 videos/hacer_video.py ESCENAS --audio voz.m4a [--musica fondo.mp3]

    python3 videos/hacer_video.py ESCENAS --sin-voz
    python3 videos/hacer_video.py ESCENAS --voz-ia

Sin opciones genera una vista previa muda con tiempos estimados.
--sin-voz arma un video para leer (frase grande + texto completo debajo),
sin audio: la música se agrega al publicar en TikTok/Instagram/YouTube.
--voz-ia narra las escenas con una voz sintética en español latinoamericano
(Kokoro, se ejecuta local). --voz alex | dora.
Con --audio limpia y normaliza la voz, detecta las pausas largas entre
escenas para sincronizar el texto y arma el video final.

Requisitos: Python 3 con Pillow, y ffmpeg/ffprobe en el PATH.
"""
import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- estilo
W, H, FPS = 1080, 1920, 30
BG = (18, 21, 28)
INK = (231, 234, 240)
MUTED = (154, 163, 181)
DEEP = (143, 178, 220)
OCHRE = (227, 169, 95)

# Zonas seguras de TikTok/Reels/Shorts: arriba ~250 px, abajo ~450 px,
# columna de iconos a la derecha ~130 px.
TEXT_CX = 525
TEXT_W = 800
MAIN_CY = 840
MAIN_MAX_H = 760
SUB_Y = 1330

FADE = 0.35          # segundos de entrada de cada escena
WPS = 2.6            # palabras por segundo para estimar (≈155 por minuto)
TAIL = 1.2           # segundos extra al final

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / "fuentes"


def fuente(nombre, tam, peso=None):
    rutas = {
        "display": FUENTES / "Gloock-Regular.ttf",
        "body": FUENTES / "Mulish-Variable.ttf",
        "mono": Path("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"),
    }
    ruta = rutas[nombre]
    if not ruta.exists():
        ruta = rutas["body"]
        peso = peso or 600
    f = ImageFont.truetype(str(ruta), tam)
    if peso and ruta.name.startswith("Mulish"):
        f.set_variation_by_axes([peso])
    return f


# ---------------------------------------------------------------- escenas
def leer_escenas(ruta):
    """Formato:
        titulo: ...
        pilar: ...
        [escena]
        pantalla: texto grande (las *palabras entre asteriscos* van en ocre)
        voz: lo que se dice en voz alta
    Las líneas sin 'clave:' continúan la clave anterior (salto de línea).
    """
    meta, escenas, actual, clave = {}, [], None, None
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower() == "[escena]":
            actual = {"pantalla": "", "voz": ""}
            escenas.append(actual)
            clave = None
            continue
        m = re.match(r"^(\w+)\s*:\s*(.*)$", s)
        destino = actual if actual is not None else meta
        if m and m.group(1).lower() in ("titulo", "pilar", "pantalla", "voz", "pausa"):
            clave = m.group(1).lower()
            destino[clave] = m.group(2)
        elif clave:
            sep = "\n" if clave == "pantalla" else " "
            destino[clave] = (destino.get(clave, "") + sep + s).strip()
    if not escenas:
        sys.exit("No encontré ninguna [escena] en " + str(ruta))
    return meta, escenas


def palabras(t):
    return len(re.findall(r"\w+", t))


# ---------------------------------------------------------------- audio
def duracion(ruta):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(ruta)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def limpiar_voz(entrada, salida):
    filtros = ("highpass=f=80,lowpass=f=12000,afftdn=nf=-25,"
               "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,"
               "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.3,areverse,"
               "loudnorm=I=-14:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(entrada), "-af", filtros,
                    "-ar", "48000", "-ac", "1", str(salida)], check=True)


def silencios(ruta, minimo=0.6):
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(ruta), "-af",
         f"silencedetect=noise=-35dB:d={minimo}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return [(a, b) for a, b in zip(ini, fin)]


def tiempos(escenas, total=None, sil=None):
    """Devuelve (inicio, fin) de cada escena y cómo se calcularon."""
    pesos = [max(palabras(e["voz"]), 1) / WPS + float(e.get("pausa") or 0.6)
             for e in escenas]
    n = len(escenas)
    if total is None:
        cortes, t = [], 0.0
        for p in pesos:
            cortes.append(t)
            t += p
        cortes.append(t)
        return list(zip(cortes[:-1], cortes[1:])), "estimado (sin audio)"

    sil = [s for s in (sil or []) if 0.3 < s[0] and s[1] < total - 0.3]
    if len(sil) >= n - 1:
        # Para cada corte esperado, la pausa larga más cercana.
        esperados, acum = [], 0.0
        for p in pesos[:-1]:
            acum += p
            esperados.append(acum / sum(pesos) * total)
        candidatos = sorted(sil, key=lambda s: s[1] - s[0], reverse=True)[: max(n - 1, 2 * (n - 1))]
        elegidos, usados = [], set()
        for e in esperados:
            mejor = min((i for i in range(len(candidatos)) if i not in usados),
                        key=lambda i: abs((candidatos[i][0] + candidatos[i][1]) / 2 - e))
            usados.add(mejor)
            elegidos.append(candidatos[mejor])
        elegidos.sort()
        cortes = [0.0] + [b - 0.15 for _, b in elegidos] + [total]
        if all(b > a for a, b in zip(cortes, cortes[1:])):
            return list(zip(cortes[:-1], cortes[1:])), f"sincronizado con {n - 1} pausas del audio"

    escala = total / sum(pesos)
    cortes, t = [], 0.0
    for p in pesos:
        cortes.append(t)
        t += p * escala
    cortes.append(total)
    return list(zip(cortes[:-1], cortes[1:])), "proporcional (no encontré todas las pausas)"


LECTURA_WPS = 2.4   # palabras por segundo al leer en pantalla


def tiempos_lectura(escenas):
    cortes, t = [], 0.0
    for e in escenas:
        dur = max(3.5, palabras(e["voz"]) / LECTURA_WPS + 1.5)
        cortes.append((t, t + dur))
        t += dur
    return cortes


KOKORO_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
KOKORO_DIR = AQUI / "voces" / "kokoro"
KOKORO_ARCHIVOS = ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
VOCES = {"alex": "em_alex", "dora": "ef_dora"}


def sintetizar(escenas, carpeta, voz="alex", pausa=0.45, velocidad=1.0):
    """Narra cada escena con Kokoro (español latinoamericano) y devuelve (wav, bloques)."""
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except ImportError:
        sys.exit("Falta instalar la voz: pip install kokoro-onnx soundfile")
    KOKORO_DIR.mkdir(parents=True, exist_ok=True)
    for nombre in KOKORO_ARCHIVOS:
        destino = KOKORO_DIR / nombre
        if not destino.exists():
            print(f"Descargando {nombre}…")
            subprocess.run(["curl", "-sSfL", "-o", str(destino), KOKORO_URL + nombre], check=True)
    k = Kokoro(str(KOKORO_DIR / KOKORO_ARCHIVOS[0]), str(KOKORO_DIR / KOKORO_ARCHIVOS[1]))

    tmp = carpeta / ".voz-ia"
    tmp.mkdir(exist_ok=True)
    partes, bloques, t = [], [], 0.0
    silencio = tmp / "pausa.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                    "-t", str(pausa), str(silencio)], check=True)
    for i, e in enumerate(escenas):
        crudo, wav = tmp / f"{i}-crudo.wav", tmp / f"{i}.wav"
        muestras, sr = k.create(e["voz"], voice=VOCES.get(voz, voz), speed=1 / velocidad, lang="es-419")
        sf.write(str(crudo), muestras, sr)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(crudo), "-ar", "48000", "-ac", "1",
                        str(wav)], check=True)
        d = duracion(wav)
        bloques.append((t, t + d + pausa))
        partes += [wav, silencio]
        t += d + pausa
    lista = tmp / "lista.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in partes))
    salida = carpeta / "voz-ia.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", str(salida)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    return salida, bloques


# ---------------------------------------------------------------- dibujo
def fondo():
    img = Image.new("RGB", (W, H), BG)
    brillo = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(brillo)
    d.ellipse((520, -260, 1400, 620), fill=70)
    d.ellipse((-420, 1250, 420, 2150), fill=38)
    brillo = brillo.filter(ImageFilter.GaussianBlur(170))
    ocre = Image.new("RGB", (W, H), (70, 52, 30))
    azul = Image.new("RGB", (W, H), (31, 43, 60))
    img = Image.composite(ocre, img, brillo.point(lambda v: min(255, v * 2) if v else 0).crop((0, 0, W, H)))
    mask2 = brillo.copy()
    mask2.paste(0, (0, 0, W, 1100))
    img = Image.composite(azul, img, mask2.point(lambda v: min(255, v * 3)))
    return img


def tokens(texto):
    """Separa el texto en (palabra, resaltada) y saltos de línea.
    La puntuación que queda pegada a un resaltado se une a la palabra anterior."""
    out, resalta = [], False
    for parte in re.split(r"(\*|\n)", texto):
        if parte == "*":
            resalta = not resalta
        elif parte == "\n":
            out.append(("\n", False))
        else:
            pegar = bool(parte) and not parte[0].isspace()
            for j, w in enumerate(parte.split()):
                if j == 0 and pegar and out and out[-1][0] != "\n" and re.fullmatch(r"[.,;:!?…»)\]]+", w):
                    out.append(("\x00" + w, resalta))
                else:
                    out.append((w, resalta))
    return out


def ancho_linea(l, f):
    total = 0.0
    for i, (w, _) in enumerate(l):
        if w.startswith("\x00"):
            total += f.getlength(w[1:])
        else:
            total += f.getlength(w) + (f.getlength(" ") if i else 0)
    return total


def envolver(toks, f, ancho):
    lineas, linea, esp = [], [], f.getlength(" ")
    for w, r in toks:
        if w == "\n":
            lineas.append(linea)
            linea = []
            continue
        prueba = ancho_linea(linea + [(w, r)], f)
        if linea and prueba > ancho and not w.startswith("\x00"):
            lineas.append(linea)
            linea = []
        linea.append((w, r))
    if linea:
        lineas.append(linea)
    return lineas


def capa_principal(texto, cy=MAIN_CY, max_h=MAIN_MAX_H, tam_max=104):
    toks = tokens(texto)
    for tam in range(tam_max, 44, -4):
        f = fuente("display", tam)
        lineas = envolver(toks, f, TEXT_W)
        alto_l = int(tam * 1.18)
        if len(lineas) * alto_l <= max_h and all(ancho_linea(l, f) <= TEXT_W for l in lineas):
            break
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    esp = f.getlength(" ")
    y = cy - len(lineas) * alto_l / 2
    for l in lineas:
        x = TEXT_CX - ancho_linea(l, f) / 2
        for i, (w, r) in enumerate(l):
            if w.startswith("\x00"):
                x -= esp
                w = w[1:]
            d.text((x, y), w, font=f, fill=OCHRE if r else INK)
            x += f.getlength(w) + esp
        y += alto_l
    return capa


def trozos_subtitulo(voz, max_letras=30):
    ws = voz.split()
    out, actual = [], []
    for w in ws:
        if actual and len(" ".join(actual + [w])) > max_letras:
            out.append(" ".join(actual))
            actual = []
        actual.append(w)
        if re.search(r"[.,;:?!…]$", w) and len(actual) >= 3:
            out.append(" ".join(actual))
            actual = []
    if actual:
        if out and len(actual) <= 2 and len(out[-1]) + len(" ".join(actual)) < 36:
            out[-1] += " " + " ".join(actual)
        else:
            out.append(" ".join(actual))
    return out


def capa_subtitulo(texto, f):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    lineas = envolver(tokens(texto), f, 880)
    alto = 66
    y = SUB_Y
    for l in lineas:
        s = " ".join(w for w, _ in l).replace(" \x00", "")
        ancho = f.getlength(s)
        x = TEXT_CX - ancho / 2
        d.rounded_rectangle((x - 22, y - 8, x + ancho + 22, y + alto - 6), 18, fill=(12, 14, 19, 200))
        d.text((x, y), s, font=f, fill=INK)
        y += alto + 6
    return capa


def capa_lectura(texto):
    """Texto completo de la escena, para los videos sin voz."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for tam in range(46, 30, -2):
        f = fuente("body", tam, 600)
        lineas = envolver(tokens(texto), f, TEXT_W)
        alto = int(tam * 1.42)
        if len(lineas) * alto <= 330:
            break
    y = 1110
    for l in lineas:
        s = " ".join(w for w, _ in l).replace(" \x00", "")
        d.text((TEXT_CX - f.getlength(s) / 2, y), s, font=f, fill=(205, 211, 222))
        y += alto
    return capa


def capa_fija(meta):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    fm = fuente("mono", 30)
    marca = "EL OBSERVADOR INTERIOR"
    espaciado = 5
    ancho = sum(fm.getlength(c) + espaciado for c in marca) - espaciado
    x = TEXT_CX - ancho / 2
    for c in marca:
        d.text((x, 300), c, font=fm, fill=OCHRE)
        x += fm.getlength(c) + espaciado
    if meta.get("pilar"):
        fp = fuente("body", 30, 700)
        t = meta["pilar"].upper()
        a = fp.getlength(t)
        d.rounded_rectangle((TEXT_CX - a / 2 - 20, 352, TEXT_CX + a / 2 + 20, 400), 24, fill=(31, 43, 60, 255))
        d.text((TEXT_CX - a / 2, 358), t, font=fp, fill=DEEP)
    return capa


def con_alfa(capa, a):
    if a >= 1:
        return capa
    r, g, b, al = capa.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


# ---------------------------------------------------------------- remotion
REMOTION = AQUI.parent / "remotion"
CROMO_SISTEMA = Path("/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell")
CIERRE_REMOTION = 3.0


def render_remotion(meta, escenas, bloques, audio_wav, carpeta, salida):
    """Arma las props y renderiza con Remotion (remotion/)."""
    import json
    import os
    import shutil

    slug = carpeta.name
    audio_rel = None
    if audio_wav:
        (REMOTION / "public" / "audio").mkdir(parents=True, exist_ok=True)
        audio_rel = f"audio/{slug}.wav"
        shutil.copy(audio_wav, REMOTION / "public" / audio_rel)

    datos = []
    for (a, b), e in zip(bloques, escenas):
        trozos = trozos_subtitulo(e["voz"]) if e["voz"] else []
        habla = max(b - a - 0.4, 0.5)
        total_letras = sum(max(len(x), 1) for x in trozos) or 1
        subs, t = [], a + 0.05
        for tr in trozos:
            dur = habla * max(len(tr), 1) / total_letras
            ws = tr.split()
            largos = [len(w) + 1 for w in ws]
            palabras_t, acum = [], 0
            for w, n in zip(ws, largos):
                palabras_t.append({"w": w, "t": round(t + dur * acum / sum(largos), 3)})
                acum += n
            subs.append({"inicio": round(t, 3), "fin": round(t + dur, 3), "palabras": palabras_t})
            t += dur
        datos.append({"inicio": round(a, 3), "fin": round(b, 3), "pantalla": e["pantalla"], "subtitulos": subs})

    fin = bloques[-1][1]
    props = {"titulo": meta.get("titulo", ""), "pilar": meta.get("pilar", ""), "audio": audio_rel,
             "duracion": round(fin + CIERRE_REMOTION, 3), "finEscenas": round(fin, 3), "escenas": datos}
    ruta_props = carpeta / "props-remotion.json"
    ruta_props.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")

    if not (REMOTION / "node_modules").exists():
        print("Instalando Remotion (solo la primera vez)…")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=REMOTION, check=True)
    env = dict(os.environ)
    if CROMO_SISTEMA.exists() and "REMOTION_CHROME" not in env:
        env["REMOTION_CHROME"] = str(CROMO_SISTEMA)
    print("Renderizando con Remotion…")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "Corto", str(Path(salida).resolve()),
                    f"--props={ruta_props.resolve()}", "--log=warn"], cwd=REMOTION, env=env, check=True)
    # portada: un cuadro de la primera escena
    subprocess.run(["npx", "remotion", "still", "src/index.ts", "Corto", str((carpeta / "portada.png").resolve()),
                    f"--props={ruta_props.resolve()}", f"--frame={int(min(bloques[0][1] - 0.4, 2.5) * 30)}",
                    "--log=warn"], cwd=REMOTION, env=env, check=True)
    print(f"Listo: {salida}")
    return salida


# ---------------------------------------------------------------- render
def render(escenas_ruta, audio=None, musica=None, salida=None, sin_voz=False, voz_ia=False,
           voz="alex", velocidad=1.0, animado=False, remotion=False):
    escenas_ruta = Path(escenas_ruta)
    meta, escenas = leer_escenas(escenas_ruta)
    carpeta = escenas_ruta.parent
    nombre = ("video-sin-voz.mp4" if sin_voz else f"video-voz-{voz}.mp4" if voz_ia
              else "video.mp4" if audio else "vista-previa.mp4")
    if animado:
        nombre = nombre.replace(".mp4", "-animado.mp4")
    if remotion:
        nombre = nombre.replace(".mp4", "-remotion.mp4")
    salida = Path(salida) if salida else carpeta / nombre

    voz_limpia = None
    if sin_voz:
        bloques, modo = tiempos_lectura(escenas), f"lectura ({LECTURA_WPS} palabras/s)"
    elif voz_ia:
        print("Generando la narración con voz sintética…")
        voz_limpia, bloques = sintetizar(escenas, carpeta, voz, velocidad=velocidad)
        modo = "voz sintética (tiempos exactos)"
    elif audio:
        voz_limpia = carpeta / "voz-limpia.wav"
        print("Limpiando y normalizando la voz…")
        limpiar_voz(audio, voz_limpia)
        total = duracion(voz_limpia)
        bloques, modo = tiempos(escenas, total, silencios(voz_limpia))
    else:
        bloques, modo = tiempos(escenas)
    if remotion:
        return render_remotion(meta, escenas, bloques, voz_limpia, carpeta, salida)

    animador = None
    if animado:
        import animacion
        total_video = bloques[-1][1] + animacion.OUTRO
        animador = animacion.Animador(meta, escenas, bloques, total_video)
    else:
        total_video = bloques[-1][1] + TAIL
    print(f"Tiempos: {modo}. Duración: {total_video:.1f} s")
    for i, ((a, b), e) in enumerate(zip(bloques, escenas), 1):
        print(f"  escena {i}: {a:5.1f}–{b:5.1f} s  {e['pantalla'][:50]!r}")

    base = fondo().convert("RGBA")
    base.alpha_composite(capa_fija(meta))
    fsub = fuente("body", 46, 800)

    capas = []
    for (a, b), e in zip(bloques, escenas):
        if sin_voz:
            capas.append((a, b, capa_principal(e["pantalla"], cy=720, max_h=560, tam_max=96),
                          [(a + 0.5, b, capa_lectura(e["voz"]))] if e["voz"] else []))
            continue
        trozos = trozos_subtitulo(e["voz"]) if e["voz"] else []
        habla = max(b - a - 0.35, 0.5)
        pesos = [max(len(t), 1) for t in trozos]
        subs, t = [], a
        for tr, p in zip(trozos, pesos):
            dur = habla * p / sum(pesos)
            subs.append((t, t + dur, capa_subtitulo(tr, fsub)))
            t += dur
        capas.append((a, b, capa_principal(e["pantalla"]), subs))

    # Portada para la miniatura
    if animador:
        animador.portada().save(carpeta / "portada.png")
    else:
        portada = base.copy()
        portada.alpha_composite(capas[0][2])
        portada.convert("RGB").save(carpeta / "portada.png")

    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if voz_limpia:
        cmd += ["-i", str(voz_limpia)]
        if musica:
            cmd += ["-stream_loop", "-1", "-i", str(musica), "-filter_complex",
                    "[2:a]volume=0.10,afade=t=out:st=%.2f:d=1.5[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]"
                    % max(total_video - 1.5, 0), "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a"]
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{total_video:.2f}", str(salida)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    n_frames = math.ceil(total_video * FPS)
    for i in range(n_frames):
        t = i / FPS
        if animador:
            proc.stdin.write(animador.frame(t).convert("RGB").tobytes())
            continue
        frame = base.copy()
        # barra de progreso
        d = ImageDraw.Draw(frame)
        d.rectangle((0, 0, int(W * min(t / total_video, 1)), 7), fill=OCHRE + (255,))
        idx = max(j for j, c in enumerate(capas) if c[0] <= t or j == 0)
        a, b, principal, subs = capas[idx]
        k = min(max((t - a) / FADE, 0), 1)
        k = 1 - (1 - k) ** 3
        if k < 1:
            capa = con_alfa(principal, k)
            frame.alpha_composite(capa, (0, int((1 - k) * 40)))
        else:
            frame.alpha_composite(principal)
        for s0, s1, sc in subs:
            if s0 <= t < s1:
                if sin_voz and t - s0 < 0.4:
                    frame.alpha_composite(con_alfa(sc, (t - s0) / 0.4))
                else:
                    frame.alpha_composite(sc)
                break
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg falló al generar el video")
    print(f"Listo: {salida}")
    print(f"Portada: {carpeta / 'portada.png'}")
    return salida


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("escenas", help="archivo escenas.txt")
    p.add_argument("--audio", help="grabación de tu voz (m4a, mp3, wav…)")
    p.add_argument("--musica", help="música libre de derechos (opcional, va muy baja)")
    p.add_argument("--salida", help="ruta del mp4 (por defecto, junto a escenas.txt)")
    modo = p.add_mutually_exclusive_group()
    modo.add_argument("--sin-voz", action="store_true", help="video para leer, sin narración")
    modo.add_argument("--voz-ia", action="store_true", help="narración con voz sintética en español latino (Kokoro)")
    p.add_argument("--voz", default="alex", choices=sorted(VOCES),
                   help="con --voz-ia: alex (masculina) o dora (femenina)")
    p.add_argument("--velocidad", type=float, default=1.0,
                   help="con --voz-ia: más de 1 habla más lento, menos de 1 más rápido")
    p.add_argument("--animado", action="store_true",
                   help="fondo en movimiento, texto palabra por palabra, subtítulos karaoke y cierre con logo")
    p.add_argument("--remotion", action="store_true",
                   help="renderiza con Remotion (remotion/): animaciones más fluidas")
    a = p.parse_args()
    if a.audio and (a.sin_voz or a.voz_ia):
        p.error("--audio no se combina con --sin-voz ni con --voz-ia")
    render(a.escenas, a.audio, a.musica, a.salida, a.sin_voz, a.voz_ia, a.voz, a.velocidad, a.animado, a.remotion)


if __name__ == "__main__":
    main()
