# Videos: formato sin cara

`hacer_video.py` arma el video vertical (1080×1920) con el texto animado, la marca del canal y una barra de progreso. El mismo archivo sirve para TikTok, Shorts y Reels. Tiene tres modos:

| Modo | Comando | Qué hace |
|---|---|---|
| **Con tu voz** | `--audio voz.m4a` | Usa tu grabación, con subtítulos sincronizados. Es lo que mejor rinde y lo más seguro para monetizar. |
| **Sin voz** | `--sin-voz` | Video para leer: frase grande + texto completo debajo, sin audio. Agregá música al publicar, desde la biblioteca de TikTok/Instagram/YouTube. |
| **Voz artificial** | `--voz-ia` | Narra con una voz sintética (Piper, se genera en la computadora, gratis). Calidad básica y acento de España. `--velocidad 1.1` la hace un poco más lenta. |

> **Si usás voz artificial:** al publicar en TikTok activá la etiqueta de "contenido generado por IA" (Más opciones → Contenido generado por IA). En YouTube, los videos con voz sintética y solo texto pueden considerarse contenido poco original al pedir la monetización; para el canal largo conviene tu voz.

Lo que sigue explica el modo con tu voz.

```
videos/
├── hacer_video.py        # la herramienta
├── fuentes/              # Gloock y Mulish (licencia OFL, libres)
└── cortos/
    └── 01-nada-es-personal/
        ├── escenas.txt   # qué se ve y qué se dice en cada escena
        └── voz.m4a       # tu grabación (la agregás vos)
```

## 1. Grabar la voz (10 minutos por corto)

**Dónde:** el lugar más "blando" de tu casa. Un clóset con ropa o un cuarto con cortinas, cama y almohadones es ideal. Evitá baños y cocinas: rebotan el sonido.

**Con qué:** la app de notas de voz del celular alcanza (en iPhone, *Notas de voz*; en Android, *Grabadora*). Si en algún momento querés mejorar, un micrófono de solapa de los baratos ya hace una gran diferencia.

**Cómo:**
1. Poné el celular en modo avión (sin notificaciones ni vibraciones).
2. Sostenelo a unos 15–20 cm de la boca, un poco de costado, para que no le pegue el aire de las "p" y las "b".
3. Abrí el `escenas.txt` del corto y leé **solo las líneas `voz:`**, en orden.
4. **Entre una escena y la siguiente, hacé una pausa de 1 segundo completo.** Así la herramienta sabe dónde cambiar el texto. Dentro de una misma escena, hablá normal.
5. Si te equivocás, no cortes: hacé una pausa de 3 segundos y repetí la escena desde el principio. Avisame y la recorto.
6. Hablá un poco más lento de lo que te parece natural, y con energía, como si se lo contaras a un amigo. Sonreír mientras hablás se nota en la voz.

**Antes del primer corto:** grabá 20 segundos de prueba y escuchalos con auriculares. Si se oye eco o ruido de fondo, cambiá de lugar.

## 2. Pasarme el audio

Cualquiera de estas opciones sirve:

- **Adjuntarlo acá en el chat** con Claude.
- **Subirlo a GitHub:** en la carpeta del corto (por ejemplo `videos/cortos/01-nada-es-personal/`), *Add file → Upload files*, con el nombre `voz.m4a` (o `.mp3`, `.wav`).

## 3. Generar el video

```bash
# Vista previa muda (sin audio, tiempos estimados)
python3 videos/hacer_video.py videos/cortos/01-nada-es-personal/escenas.txt

# Video final con tu voz
python3 videos/hacer_video.py videos/cortos/01-nada-es-personal/escenas.txt --audio videos/cortos/01-nada-es-personal/voz.m4a

# Con música de fondo muy baja (opcional, siempre libre de derechos)
python3 videos/hacer_video.py ... --audio voz.m4a --musica fondo.mp3
```

La herramienta:
- limpia la voz (quita graves molestos y ruido de fondo, recorta silencios al inicio y al final),
- la normaliza al volumen que recomiendan TikTok y YouTube (−14 LUFS),
- detecta tus pausas de 1 segundo para cambiar de escena en el momento justo,
- genera `video.mp4` y `portada.png` (la imagen de miniatura) en la carpeta del corto.

Los videos generados no se guardan en GitHub porque pesan mucho; se vuelven a generar en segundos.

> **Música:** TikTok e Instagram tienen bibliotecas de música con licencia para agregar al publicar; es lo más seguro. Si usás `--musica`, que sea de una fuente libre de derechos (por ejemplo, la Biblioteca de audio de YouTube) y revisá su licencia.

## 4. Antes de publicar

- [ ] Mirá el video completo con sonido y sin sonido (mucha gente lo ve en silencio).
- [ ] Revisá que los subtítulos coincidan con lo que decís.
- [ ] Escribí la descripción con 3–5 hashtags del tema (#inteligenciaemocional, #crecimientopersonal, #psicologia…).
- [ ] Si el corto viene de un libro, nombrá al autor en la descripción.
- [ ] Subí el mismo archivo a TikTok, YouTube Shorts e Instagram Reels.

## Formato de `escenas.txt`

```
titulo: Título del video
pilar: Nada es personal

[escena]
pantalla: Texto grande en pantalla, las *palabras entre asteriscos* van en ocre
voz: Lo que decís en voz alta durante esta escena.

[escena]
pantalla: Una línea
Otra línea debajo
voz: ...
```

- Las líneas que empiezan con `#` son comentarios.
- `pantalla` admite varias líneas; el tamaño de letra se ajusta solo.
- Lo ideal es que `pantalla` sea corto (3–8 palabras): la idea clave, no la frase entera. Los subtítulos ya muestran todo lo que decís.
