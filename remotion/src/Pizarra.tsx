// Estilo pizarra: un lápiz dibuja una ilustración por escena y escribe la idea a mano.
import React, {useMemo} from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {getPointAtLength} from '@remotion/paths';
import {tokenizar, useFuentes} from './Corto';
import {AZUL, dibujo, OCRE, TINTA} from './dibujos';
import type {CortoProps, Escena, Subtitulo} from './tipos';

const PAPEL = '#f7f1e6';
const MANO = 'Caveat, cursive';
const MONO = 'JetBrainsMono, monospace';
const BODY = 'Mulish, system-ui, sans-serif';
const DISPLAY = 'Gloock, Georgia, serif';
const CX = 525;

// lienzo de los dibujos (800 × 620) dentro del cuadro de video
const LIENZO = {x: CX - 430, y: 440, w: 860, h: 666};
const PANEO = 16; // cuadros de transición entre escenas

const clamp = (x: number) => Math.max(0, Math.min(1, x));

// ------------------------------------------------------------------ lápiz
const Lapiz: React.FC<{x: number; y: number; opacidad: number; vaiven: number}> = ({x, y, opacidad, vaiven}) => (
	<g transform={`translate(${x} ${y}) rotate(${-38 + vaiven})`} opacity={opacidad}>
		<g transform="translate(0 0)">
			{/* sombra */}
			<rect x={14} y={-6} width={260} height={30} rx={6} fill="rgba(0,0,0,0.10)" transform="translate(8 14)" />
			{/* punta de grafito y madera */}
			<polygon points="0,0 34,-11 34,11" fill="#e8c9a0" />
			<polygon points="0,0 12,-4 12,4" fill={TINTA} />
			{/* cuerpo */}
			<rect x={34} y={-13} width={190} height={26} fill={OCRE} />
			<rect x={34} y={-13} width={190} height={8} fill="#c98a3a" />
			{/* virola y goma */}
			<rect x={224} y={-14} width={22} height={28} fill="#9aa3b5" />
			<rect x={246} y={-13} width={26} height={26} rx={5} fill="#d98b8b" />
		</g>
	</g>
);

// ------------------------------------------------------------------ escena

const tiemposEscena = (escena: Escena, fps: number, fin: number) => {
	const f0 = Math.round(escena.inicio * fps);
	const f1 = Math.round(fin * fps);
	const dur = f1 - f0;
	const dibujar = Math.max(30, Math.min(110, dur * 0.5));
	const ini = f0 + PANEO - 2;
	const textoIni = ini + dibujar * 0.55;
	return {f0, f1, ini, dibujar, textoIni, dur};
};

const EscenaPizarra: React.FC<{escena: Escena; fin: number}> = ({escena, fin}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const dib = useMemo(() => dibujo(escena.dibujo), [escena.dibujo]);
	const {ini, dibujar, textoIni} = tiemposEscena(escena, fps, fin);

	// progreso del dibujo, repartido según el largo de cada trazo
	const total = dib ? dib.trazos.reduce((n, t) => n + t.largo, 0) : 0;
	const avance = clamp((frame - ini) / dibujar);
	const largoHecho = Easing.inOut(Easing.quad)(avance) * total;

	let acum = 0;
	const trazos = dib
		? dib.trazos.map((t, i) => {
				const local = clamp((largoHecho - acum) / t.largo);
				acum += t.largo;
				return (
					<path
						key={i}
						d={t.d}
						fill="none"
						stroke={t.color}
						strokeWidth={t.ancho}
						strokeLinecap="round"
						strokeLinejoin="round"
						strokeDasharray={`${t.largo} ${t.largo}`}
						strokeDashoffset={t.largo * (1 - local)}
					/>
				);
			})
		: null;

	const textosDib = dib
		? dib.textos.map((t, i) => {
				const a = clamp((frame - (ini + dibujar * (0.7 + i * 0.12))) / 10);
				return (
					<text
						key={i}
						x={t.x}
						y={t.y}
						fontFamily={MANO}
						fontWeight={700}
						fontSize={t.tam}
						fill={t.color}
						textAnchor="middle"
						style={{clipPath: `inset(0 ${(1 - a) * 100}% 0 0)`}}
					>
						{t.texto}
					</text>
				);
			})
		: null;

	// texto escrito a mano, palabra por palabra
	const tokens = tokenizar(escena.pantalla);
	const letras = tokens.reduce((n, t) => n + t.w.length + 1, 0);
	const tam = letras <= 20 ? 104 : letras <= 34 ? 92 : letras <= 52 ? 80 : 68;
	const velocidad = Math.max(0.55, Math.min(1.4, 30 / Math.max(letras, 1))); // cuadros por letra
	let cursor = textoIni;

	return (
		<AbsoluteFill>
			<svg
				viewBox="0 0 800 620"
				style={{position: 'absolute', left: LIENZO.x, top: LIENZO.y, width: LIENZO.w, height: LIENZO.h, overflow: 'visible'}}
			>
				{trazos}
				{textosDib}
			</svg>
			<div
				style={{
					position: 'absolute',
					left: CX - 420,
					width: 840,
					top: dib ? 1080 : 620,
					textAlign: 'center',
					fontFamily: MANO,
					fontWeight: 700,
					fontSize: dib ? tam : tam * 1.3,
					lineHeight: 1.02,
					color: TINTA,
				}}
			>
				{tokens.map((t, k) => {
					if (t.salto) return <br key={k} />;
					const dur = (t.w.length + 1) * velocidad * 1.6;
					const p = clamp((frame - cursor) / dur);
					const inicio = cursor;
					cursor += dur;
					const subrayado = clamp((frame - inicio - dur) / 8);
					return (
						<span
							key={k}
							style={{
								display: 'inline-block',
								position: 'relative',
								margin: '0 0.12em',
								color: t.resaltada ? OCRE : TINTA,
								// margen amplio para tildes, signos y trazos que sobresalen; sin recorte al terminar
								clipPath: p >= 1 ? undefined : `inset(-60% ${(1 - p) * 115 - 15}% -60% -15%)`,
							}}
						>
							{t.w}
							{t.resaltada && (
								<svg
									viewBox="0 0 100 12"
									preserveAspectRatio="none"
									style={{position: 'absolute', left: 0, right: 0, bottom: '-0.02em', width: '100%', height: '0.16em', overflow: 'visible'}}
								>
									<path
										d={`M 2 ${6 + random(`u${k}`) * 3} Q 50 ${2 + random(`v${k}`) * 4} 98 ${5 + random(`w${k}`) * 4}`}
										stroke={OCRE}
										strokeWidth={4}
										fill="none"
										strokeLinecap="round"
										vectorEffect="non-scaling-stroke"
										pathLength={1}
										strokeDasharray="1 1"
										strokeDashoffset={1 - subrayado}
									/>
								</svg>
							)}
						</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

// posición del lápiz: la punta del trazo que se está dibujando
const posicionLapiz = (escena: Escena, frame: number, fps: number, fin: number) => {
	const dib = dibujo(escena.dibujo);
	if (!dib) return null;
	const {ini, dibujar} = tiemposEscena(escena, fps, fin);
	const avance = clamp((frame - ini) / dibujar);
	if (frame < ini - 6 || frame > ini + dibujar + 8) return null;
	const total = dib.trazos.reduce((n, t) => n + t.largo, 0);
	let objetivo = Easing.inOut(Easing.quad)(avance) * total;
	let punto = {x: 0, y: 0};
	for (const t of dib.trazos) {
		if (objetivo <= t.largo) {
			punto = getPointAtLength(t.d, Math.max(0, objetivo)) ?? punto;
			break;
		}
		objetivo -= t.largo;
		punto = getPointAtLength(t.d, t.largo) ?? punto;
	}
	const op = Math.min(clamp((frame - (ini - 6)) / 6), clamp((ini + dibujar + 8 - frame) / 8));
	return {x: LIENZO.x + (punto.x / 800) * LIENZO.w, y: LIENZO.y + (punto.y / 620) * LIENZO.h, op};
};

// ------------------------------------------------------------------ subtítulos
const Subtitulos: React.FC<{subs: Subtitulo[]}> = ({subs}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const sub = subs.find((s) => s.inicio <= t && t < s.fin);
	if (!sub) return null;
	let activa = 0;
	sub.palabras.forEach((p, i) => {
		if (p.t <= t) activa = i;
	});
	return (
		<div style={{position: 'absolute', top: 1360, left: CX - 450, width: 900, display: 'flex', justifyContent: 'center'}}>
			<div
				style={{
					padding: '8px 22px 10px',
					borderRadius: 18,
					background: 'rgba(31,43,60,0.88)',
					fontFamily: BODY,
					fontWeight: 800,
					fontSize: 38,
					color: '#e7eaf0',
				}}
			>
				{sub.palabras.map((p, i) => (
					<span key={i} style={{margin: '0 0.2em', color: i === activa ? '#e3a95f' : '#e7eaf0'}}>
						{p.w}
					</span>
				))}
			</div>
		</div>
	);
};

// ------------------------------------------------------------------ cierre
const CierrePizarra: React.FC<{desde: number}> = ({desde}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f0 = Math.round(desde * fps);
	const escena: Escena = {inicio: desde, fin: desde + 3, pantalla: '', dibujo: 'ojo', subtitulos: []};
	const a = clamp((frame - f0 - PANEO - 40) / 12);
	const b = clamp((frame - f0 - PANEO - 52) / 12);
	return (
		<AbsoluteFill>
			<EscenaPizarra escena={escena} fin={desde + 3} />
			<div style={{position: 'absolute', top: 1110, left: CX - 450, width: 900, textAlign: 'center', fontFamily: DISPLAY, fontSize: 70, color: TINTA, opacity: a}}>
				El Observador Interior
			</div>
			<div style={{position: 'absolute', top: 1200, left: CX - 450, width: 900, textAlign: 'center', fontFamily: MANO, fontWeight: 700, fontSize: 64, color: OCRE, opacity: b}}>
				Seguí para más
			</div>
		</AbsoluteFill>
	);
};

// ------------------------------------------------------------------ composición
export const Pizarra: React.FC<CortoProps> = (props) => {
	useFuentes();
	const frame = useCurrentFrame();
	const {fps, durationInFrames} = useVideoConfig();
	const t = frame / fps;
	const n = props.escenas.length;
	const cierre: Escena = {inicio: props.finEscenas, fin: props.duracion, pantalla: '', dibujo: 'ojo', subtitulos: []};
	const todas = [...props.escenas, cierre];
	const idx = Math.max(0, todas.findIndex((e, i) => t < e.fin || i === todas.length - 1));
	const finDe = (i: number) => (i < n ? (i === n - 1 ? props.finEscenas : props.escenas[i].fin) : props.duracion);

	// paneo: la cámara se desplaza por una pizarra larga
	const local = frame - Math.round(todas[idx].inicio * fps);
	const paneo = idx > 0 ? interpolate(local, [0, PANEO], [1, 0], {extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)}) : 0;

	const capa = (i: number, dx: number) => (
		<AbsoluteFill key={i} style={{transform: `translateX(${dx}px)`}}>
			{i < n ? <EscenaPizarra escena={todas[i]} fin={finDe(i)} /> : <CierrePizarra desde={props.finEscenas} />}
		</AbsoluteFill>
	);

	const lapiz = idx < n ? posicionLapiz(todas[idx], frame, fps, finDe(idx)) : posicionLapiz(cierre, frame, fps, props.duracion);
	const vaiven = Math.sin(frame / 2.2) * 3;

	return (
		<AbsoluteFill style={{background: PAPEL}}>
			{/* textura de papel */}
			<AbsoluteFill style={{backgroundImage: `url(${staticFile('grano.png')})`, opacity: 0.05}} />
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 60%, rgba(120,90,50,0.16) 100%)'}} />

			{/* marca */}
			<div style={{position: 'absolute', top: 290, left: CX - 400, width: 800, textAlign: 'center'}}>
				<div style={{fontFamily: MONO, fontSize: 30, letterSpacing: '0.24em', color: OCRE}}>EL OBSERVADOR INTERIOR</div>
				<div
					style={{
						display: 'inline-block',
						marginTop: 12,
						padding: '6px 22px',
						borderRadius: 99,
						background: 'rgba(44,74,110,0.12)',
						color: AZUL,
						fontFamily: BODY,
						fontWeight: 800,
						fontSize: 28,
						letterSpacing: '0.08em',
						textTransform: 'uppercase',
					}}
				>
					{props.pilar}
				</div>
			</div>

			{paneo > 0 && capa(idx - 1, -1080 * (1 - paneo))}
			{capa(idx, 1080 * paneo)}

			{t < props.finEscenas && <Subtitulos subs={props.escenas[Math.min(idx, n - 1)].subtitulos} />}

			<svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
				{lapiz && paneo === 0 && <Lapiz x={lapiz.x} y={lapiz.y} opacidad={lapiz.op} vaiven={vaiven} />}
			</svg>

			<div style={{position: 'absolute', top: 0, left: 0, height: 8, width: `${(frame / durationInFrames) * 100}%`, background: OCRE}} />
			{props.audio && <Audio src={staticFile(props.audio)} />}
		</AbsoluteFill>
	);
};

