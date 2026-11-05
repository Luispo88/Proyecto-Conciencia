# Cortos animados con Remotion

Versión de los cortos con animaciones más fluidas, hecha con [Remotion](https://www.remotion.dev) (videos programados con React). Remotion es gratis para personas individuales y empresas pequeñas; revisá su licencia si el proyecto crece a un equipo.

## Qué tiene

- **Fondo vivo:** luces que se desplazan, partículas que flotan, grano de película y viñeta.
- **Luz que respira con la voz:** el brillo detrás del texto se mueve según el volumen de la narración.
- **Texto:** cada palabra entra con desenfoque y un leve resorte; las palabras resaltadas llevan un marcador ocre que se dibuja detrás; los números (`*1.*`) se convierten en círculos ocres que giran al entrar.
- **Cámara:** un acercamiento muy lento durante cada escena y una salida con desenfoque hacia arriba.
- **Destello** de luz diagonal en cada cambio de escena.
- **Subtítulos tipo karaoke:** la palabra que se dice se ilumina en ocre.
- **Cierre de 3 s:** el ojo del logo se dibuja con un trazo, el iris aparece con rebote, parpadea, y aparecen "El Observador Interior" y "Seguí para más".

## Cómo se genera

Desde la raíz del proyecto, con la herramienta de siempre y la opción `--remotion`:

```bash
python3 videos/hacer_video.py videos/cortos/02-que-es-la-inteligencia-emocional/escenas.txt --voz-ia --voz alex --remotion
```

`hacer_video.py` se encarga de la voz, los tiempos y los subtítulos; escribe `props-remotion.json` en la carpeta del corto y llama a Remotion para dibujar el video. Sale `video-voz-alex-remotion.mp4` y la `portada.png`.

También funciona con tu voz: `--audio voz.m4a --remotion`.

**Tiempo:** cada corto tarda varios minutos en renderizarse (Remotion dibuja cada cuadro en un navegador).

## Ver y ajustar las animaciones

```bash
cd remotion
npm install        # solo la primera vez
npm run studio     # abre el editor de Remotion en el navegador
```

En el estudio podés elegir el corto pegando su `props-remotion.json` en el panel de props y mover la línea de tiempo cuadro por cuadro.

## Archivos

```
remotion/
├── src/Corto.tsx        # todas las animaciones
├── src/Root.tsx         # la composición (1080×1920, 30 fps)
├── src/tipos.ts         # formato de las props
├── public/fuentes/      # Gloock, Mulish, JetBrains Mono (licencia OFL)
└── public/audio/        # audios copiados al renderizar (no se suben a GitHub)
```
