import React, {useEffect, useMemo, useState} from 'react';
import {
	AbsoluteFill,
	Audio,
	continueRender,
	delayRender,
	Easing,
	interpolate,
	random,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {useAudioData, visualizeAudio} from '@remotion/media-utils';
import type {CortoProps, Escena, Subtitulo} from './tipos';

// ------------------------------------------------------------------ marca
const C = {
	bg: '#12151c',
	bgDeep: '#0c0f15',
	ink: '#e7eaf0',
	muted: '#9aa3b5',
	deep: '#8fb2dc',
	deepBg: '#1f2b3c',
	ochre: '#e3a95f',
};
const DISPLAY = 'Gloock, Georgia, serif';
const BODY = 'Mulish, system-ui, sans-serif';
const MONO = 'JetBrainsMono, monospace';

// Zona segura: TikTok tapa arriba (~250 px), abajo (~450 px) y la columna derecha (~130 px).
const CX = 525;

// ------------------------------------------------------------------ fuentes
export const useFuentes = () => {
	const [handle] = useState(() => delayRender('Cargando fuentes'));
	useEffect(() => {
		const fuentes = [
			new FontFace('Gloock', `url(${staticFile('fuentes/Gloock-Regular.ttf')})`),
			new FontFace('Mulish', `url(${staticFile('fuentes/Mulish-Variable.ttf')})`, {weight: '200 1000'}),
			new FontFace('JetBrainsMono', `url(${staticFile('fuentes/JetBrainsMono-Medium.ttf')})`),
			new FontFace('Caveat', `url(${staticFile('fuentes/Caveat-Variable.ttf')})`, {weight: '400 700'}),
		];
		Promise.all(fuentes.map((f) => f.load()))
			.then((cargadas) => {
				cargadas.forEach((f) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(f));
				continueRender(handle);
			})
			.catch((e) => {
				console.error(e);
				continueRender(handle);
			});
	}, [handle]);
};

// ------------------------------------------------------------------ texto
export type Token = {w: string; resaltada: boolean; salto?: boolean; pegada?: boolean};

export const tokenizar = (texto: string): Token[] => {
	const out: Token[] = [];
	let resaltada = false;
	for (const parte of texto.split(/(\*|\n)/)) {
		if (parte === '*') {
			resaltada = !resaltada;
		} else if (parte === '\n') {
			out.push({w: '', resaltada: false, salto: true});
		} else if (parte) {
			const pegar = !/^\s/.test(parte);
			parte
				.split(/\s+/)
				.filter(Boolean)
				.forEach((w, i) => {
					const esPuntuacion = /^[.,;:!?…»)\]]+$/.test(w);
					out.push({w, resaltada, pegada: i === 0 && pegar && esPuntuacion && out.length > 0});
				});
		}
	}
	// une la puntuación suelta a la palabra anterior
	const unidos: Token[] = [];
	for (const t of out) {
		if (t.pegada && unidos.length && !unidos[unidos.length - 1].salto) {
			unidos[unidos.length - 1] = {...unidos[unidos.length - 1], w: unidos[unidos.length - 1].w + t.w};
		} else {
			unidos.push(t);
		}
	}
	return unidos;
};

const tamFuente = (tokens: Token[]) => {
	const letras = tokens.reduce((n, t) => n + t.w.length + 1, 0);
	const lineas = tokens.filter((t) => t.salto).length + 1;
	let tam = letras <= 16 ? 132 : letras <= 26 ? 116 : letras <= 40 ? 100 : letras <= 60 ? 88 : letras <= 85 ? 76 : 66;
	if (lineas >= 3) tam = Math.min(tam, 76);
	return tam;
};

// ------------------------------------------------------------------ fondo
const Fondo: React.FC<{energia: number}> = ({energia}) => {
	const frame = useCurrentFrame();
	const t = frame / 30;
	const blob = (color: string, x: number, y: number, r: number, ax: number, ay: number, vel: number, fase: number, op: number) => (
		<div
			style={{
				position: 'absolute',
				left: x + ax * Math.sin(t * vel + fase) - r,
				top: y + ay * Math.cos(t * vel * 0.8 + fase) - r,
				width: r * 2,
				height: r * 2,
				borderRadius: '50%',
				background: `radial-gradient(circle, ${color} 0%, transparent 68%)`,
				opacity: op,
			}}
		/>
	);
	const particulas = useMemo(
		() =>
			new Array(60).fill(0).map((_, i) => ({
				x: random(`x${i}`) * 1080,
				y: random(`y${i}`) * 1920,
				r: 1.5 + random(`r${i}`) * 3,
				v: 10 + random(`v${i}`) * 28,
				f: random(`f${i}`) * 6.28,
			})),
		[],
	);
	return (
		<AbsoluteFill style={{background: `linear-gradient(170deg, ${C.bg} 0%, ${C.bgDeep} 100%)`, overflow: 'hidden'}}>
			{blob('rgba(227,169,95,0.55)', 860, 300, 620, 160, 90, 0.35, 0, 0.5)}
			{blob('rgba(70,110,170,0.55)', 180, 1550, 700, 140, 120, 0.28, 2, 0.55)}
			{/* luz que respira con la voz, detrás del texto */}
			{blob('rgba(227,169,95,0.5)', CX, 830, 520 + energia * 90, 40, 30, 0.5, 4, 0.12 + energia * 0.28)}
			{particulas.map((p, i) => {
				const y = (((p.y - t * p.v) % 1920) + 1920) % 1920;
				const x = p.x + 16 * Math.sin(t * 0.6 + p.f);
				const brillo = 0.25 + 0.5 * (0.5 + 0.5 * Math.sin(t * 1.6 + p.f * 3));
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: x,
							top: y,
							width: p.r * 2,
							height: p.r * 2,
							borderRadius: '50%',
							background: 'radial-gradient(circle, #f6dcb0 0%, #f0d2a4 45%, transparent 100%)',
							opacity: brillo * 0.7,
						}}
					/>
				);
			})}
			{/* grano de película */}
			<AbsoluteFill
				style={{
					backgroundImage: `url(${staticFile('grano.png')})`,
					backgroundPosition: `${random(`gx${frame % 6}`) * 512}px ${random(`gy${frame % 6}`) * 512}px`,
					opacity: 0.06,
					mixBlendMode: 'overlay',
				}}
			/>
			{/* viñeta */}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
		</AbsoluteFill>
	);
};

// ------------------------------------------------------------------ cabecera
const Cabecera: React.FC<{pilar: string}> = ({pilar}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 200}, durationInFrames: 20});
	return (
		<div style={{position: 'absolute', top: 285, left: CX - 400, width: 800, textAlign: 'center'}}>
			<div
				style={{
					fontFamily: MONO,
					fontSize: 30,
					letterSpacing: '0.24em',
					color: C.ochre,
					opacity: s,
					transform: `translateY(${(1 - s) * -20}px)`,
				}}
			>
				EL OBSERVADOR INTERIOR
			</div>
			<div
				style={{
					display: 'inline-block',
					marginTop: 14,
					padding: '6px 22px',
					borderRadius: 99,
					background: C.deepBg,
					color: C.deep,
					fontFamily: BODY,
					fontWeight: 800,
					fontSize: 28,
					letterSpacing: '0.08em',
					textTransform: 'uppercase',
					opacity: spring({frame: frame - 6, fps, config: {damping: 200}, durationInFrames: 20}),
				}}
			>
				{pilar}
			</div>
		</div>
	);
};

// ------------------------------------------------------------------ escena
const TextoEscena: React.FC<{escena: Escena; ultima: boolean; finEscenas: number}> = ({escena, ultima, finEscenas}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f0 = Math.round(escena.inicio * fps);
	const f1 = Math.round((ultima ? finEscenas : escena.fin) * fps);
	const local = frame - f0;
	const tokens = useMemo(() => tokenizar(escena.pantalla), [escena.pantalla]);
	const tam = tamFuente(tokens);
	const salida = interpolate(frame, [f1 - 9, f1], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.in(Easing.cubic),
	});
	const zoom = interpolate(local, [0, (f1 - f0) || 1], [1, 1.045], {extrapolateRight: 'clamp'});
	const palabras = tokens.filter((t) => !t.salto).length;
	const paso = Math.max(2, Math.min(4, Math.floor(36 / Math.max(palabras, 1))));

	let i = -1;
	return (
		<div
			style={{
				position: 'absolute',
				left: CX - 410,
				width: 820,
				top: 470,
				height: 760,
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				opacity: 1 - salida,
				filter: salida > 0 ? `blur(${salida * 10}px)` : undefined,
				transform: `translateY(${-salida * 50}px) scale(${zoom})`,
			}}
		>
			<div
				style={{
					fontFamily: DISPLAY,
					fontSize: tam,
					lineHeight: 1.14,
					color: C.ink,
					textAlign: 'center',
					textWrap: 'balance' as React.CSSProperties['textWrap'],
					textShadow: '0 6px 30px rgba(0,0,0,0.45)',
				}}
			>
				{tokens.map((t, k) => {
					if (t.salto) return <br key={k} />;
					i += 1;
					const inicio = 3 + i * paso;
					const s = spring({frame: local - inicio, fps, config: {damping: 14, stiffness: 120, mass: 0.7}});
					const suave = spring({frame: local - inicio, fps, config: {damping: 200}, durationInFrames: 14});
					const numero = t.resaltada && /^\d+\.?$/.test(t.w);
					const marcador = spring({frame: local - inicio - 8, fps, config: {damping: 200}, durationInFrames: 16});
					const estilo: React.CSSProperties = {
						display: 'inline-block',
						position: 'relative',
						isolation: 'isolate',
						margin: `0 ${tam * 0.13}px`,
						opacity: suave,
						filter: suave < 1 ? `blur(${(1 - suave) * 14}px)` : undefined,
						transform: `translateY(${(1 - suave) * 46}px) scale(${t.resaltada ? 0.7 + 0.3 * s : 1})`,
					};
					if (numero) {
						const d = tam * 1.05;
						return (
							<span key={k} style={{...estilo, verticalAlign: 'middle', marginRight: tam * 0.22}}>
								<span
									style={{
										display: 'inline-flex',
										alignItems: 'center',
										justifyContent: 'center',
										width: d,
										height: d,
										borderRadius: '50%',
										background: C.ochre,
										color: C.bg,
										fontFamily: BODY,
										fontWeight: 900,
										fontSize: tam * 0.6,
										transform: `rotate(${(1 - s) * -90}deg)`,
										boxShadow: `0 0 ${30 * s}px rgba(227,169,95,0.45)`,
									}}
								>
									{t.w.replace('.', '')}
								</span>
							</span>
						);
					}
					return (
						<span key={k} style={{...estilo, color: t.resaltada ? C.ochre : C.ink}}>
							{t.resaltada && (
								<span
									style={{
										position: 'absolute',
										left: -tam * 0.06,
										right: -tam * 0.06,
										bottom: tam * 0.06,
										height: tam * 0.3,
										background: 'rgba(227,169,95,0.24)',
										borderRadius: tam * 0.08,
										transform: `scaleX(${marcador})`,
										transformOrigin: 'left center',
										zIndex: -1,
									}}
								/>
							)}
							{t.w}
						</span>
					);
				})}
			</div>
		</div>
	);
};

// ------------------------------------------------------------------ subtítulos
const Subtitulos: React.FC<{subs: Subtitulo[]}> = ({subs}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const sub = subs.find((s) => s.inicio <= t && t < s.fin);
	if (!sub) return null;
	const entrada = spring({frame: frame - Math.round(sub.inicio * fps), fps, config: {damping: 200}, durationInFrames: 6});
	let activa = 0;
	sub.palabras.forEach((p, i) => {
		if (p.t <= t) activa = i;
	});
	const letras = sub.palabras.reduce((n, p) => n + p.w.length + 1, 0);
	const tam = letras > 34 ? 40 : 46;
	return (
		<div style={{position: 'absolute', top: 1320, left: CX - 450, width: 900, display: 'flex', justifyContent: 'center'}}>
			<div
				style={{
					padding: '10px 26px 14px',
					borderRadius: 22,
					background: 'rgba(10,12,17,0.78)',
					border: '1px solid rgba(255,255,255,0.06)',
					fontFamily: BODY,
					fontWeight: 800,
					fontSize: tam,
					color: C.ink,
					textAlign: 'center',
					opacity: entrada,
					transform: `translateY(${(1 - entrada) * 12}px)`,
				}}
			>
				{sub.palabras.map((p, i) => {
					const on = i === activa;
					return (
						<span
							key={i}
							style={{
								display: 'inline-block',
								margin: '0 0.24em',
								color: on ? C.ochre : i < activa ? C.ink : 'rgba(231,234,240,0.72)',
								transform: `translateY(${on ? -3 : 0}px)`,
							}}
						>
							{p.w}
						</span>
					);
				})}
			</div>
		</div>
	);
};

// ------------------------------------------------------------------ destello entre escenas
const Destello: React.FC<{inicios: number[]}> = ({inicios}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = inicios.map((s) => frame - Math.round(s * fps)).find((d) => d >= -4 && d < 14);
	if (f === undefined) return null;
	const x = interpolate(f, [-4, 14], [-700, 1300]);
	return (
		<div
			style={{
				position: 'absolute',
				top: -200,
				left: x,
				width: 360,
				height: 2400,
				transform: 'rotate(18deg)',
				background: 'linear-gradient(90deg, transparent, rgba(227,169,95,0.10), transparent)',
			}}
		/>
	);
};

// ------------------------------------------------------------------ cierre
const Cierre: React.FC<{desde: number}> = ({desde}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = frame - Math.round(desde * fps);
	if (f < 0) return null;
	const trazo = interpolate(f, [4, 30], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
	const iris = spring({frame: f - 20, fps, config: {damping: 9, stiffness: 120}});
	const parpadeo = interpolate(f, [52, 57, 62], [1, 0.08, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const texto = spring({frame: f - 30, fps, config: {damping: 200}, durationInFrames: 18});
	const sigue = spring({frame: f - 40, fps, config: {damping: 200}, durationInFrames: 18});
	const halo = 0.5 + 0.5 * Math.sin(f / 7);
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 560, left: CX - 280, width: 560, height: 336}}>
				<div
					style={{
						position: 'absolute',
						inset: -120,
						borderRadius: '50%',
						background: 'radial-gradient(circle, rgba(227,169,95,0.35), transparent 65%)',
						opacity: iris * (0.6 + 0.4 * halo),
					}}
				/>
				<svg viewBox="0 0 500 300" width={560} height={336} style={{transform: `scaleY(${parpadeo})`, overflow: 'visible'}}>
					<path
						d="M 30 150 Q 250 -40 470 150 Q 250 340 30 150 Z"
						fill="none"
						stroke={C.ink}
						strokeWidth={14}
						strokeLinejoin="round"
						pathLength={1}
						strokeDasharray={1}
						strokeDashoffset={trazo}
					/>
					<circle cx={250} cy={150} r={62 * iris} fill={C.ochre} />
					<circle cx={250} cy={150} r={26 * iris} fill={C.bg} />
				</svg>
			</div>
			<div
				style={{
					position: 'absolute',
					top: 960,
					left: CX - 450,
					width: 900,
					textAlign: 'center',
					fontFamily: DISPLAY,
					fontSize: 72,
					color: C.ink,
					opacity: texto,
					transform: `translateY(${(1 - texto) * 24}px)`,
				}}
			>
				El Observador Interior
			</div>
			<div
				style={{
					position: 'absolute',
					top: 1070,
					left: CX - 450,
					width: 900,
					textAlign: 'center',
					fontFamily: BODY,
					fontWeight: 800,
					fontSize: 42,
					color: C.ochre,
					opacity: sigue,
					transform: `translateY(${(1 - sigue) * 24}px)`,
				}}
			>
				Seguí para más
			</div>
		</AbsoluteFill>
	);
};

// ------------------------------------------------------------------ energía de la voz
const ConAudio: React.FC<{audio: string; children: (energia: number) => React.ReactNode}> = ({audio, children}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const datos = useAudioData(staticFile(audio));
	let energia = 0;
	if (datos) {
		const v = visualizeAudio({fps, frame, audioData: datos, numberOfSamples: 32, smoothing: true});
		energia = Math.min(1, (v.slice(0, 12).reduce((a, b) => a + b, 0) / 12) * 4);
	}
	return <>{children(energia)}</>;
};

// ------------------------------------------------------------------ composición
export const Corto: React.FC<CortoProps> = (props) => {
	useFuentes();
	const frame = useCurrentFrame();
	const {fps, durationInFrames} = useVideoConfig();
	const t = frame / fps;
	const idx = Math.max(
		0,
		props.escenas.findIndex((e, i) => t < e.fin || i === props.escenas.length - 1),
	);
	const escena = props.escenas[idx];
	const enCierre = t >= props.finEscenas;

	const contenido = (energia: number) => (
		<AbsoluteFill>
			<Fondo energia={energia} />
			<Cabecera pilar={props.pilar} />
			<Destello inicios={props.escenas.slice(1).map((e) => e.inicio)} />
			{t < props.finEscenas + 0.4 && (
				<TextoEscena
					key={idx}
					escena={escena}
					ultima={idx === props.escenas.length - 1}
					finEscenas={props.finEscenas}
				/>
			)}
			{!enCierre && <Subtitulos subs={escena.subtitulos} />}
			<Cierre desde={props.finEscenas + 0.15} />
			<div
				style={{
					position: 'absolute',
					top: 0,
					left: 0,
					height: 8,
					width: `${(frame / durationInFrames) * 100}%`,
					background: C.ochre,
					boxShadow: '0 0 16px rgba(227,169,95,0.7)',
				}}
			/>
			{props.audio && <Audio src={staticFile(props.audio)} />}
		</AbsoluteFill>
	);

	return props.audio ? <ConAudio audio={props.audio}>{contenido}</ConAudio> : contenido(0);
};
