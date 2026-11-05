// Ilustraciones de línea para el estilo pizarra.
// Lienzo de 800 × 620. rough.js les da el aspecto de dibujado a mano;
// cada trazo se anima en orden, como si lo dibujara un lápiz.
import rough from 'roughjs';
import {getLength} from '@remotion/paths';

export const TINTA = '#1f2b3c';
export const OCRE = '#b5772a';
export const AZUL = '#2c4a6e';

export type Trazo = {d: string; color: string; ancho: number; largo: number};
export type TextoDibujo = {texto: string; x: number; y: number; tam: number; color: string};
export type Dibujo = {trazos: Trazo[]; textos: TextoDibujo[]};

type P = [number, number];

const crear = (semilla: number) => {
	const g = rough.generator();
	const trazos: Trazo[] = [];
	const textos: TextoDibujo[] = [];
	let n = 0;
	const base = (color: string, extra: Record<string, unknown> = {}) => ({
		seed: semilla * 100 + ++n,
		roughness: 1.25,
		bowing: 1.1,
		stroke: color,
		strokeWidth: 4,
		...extra,
	});
	const agregar = (drawable: ReturnType<typeof g.line>, color: string, ancho = 5) => {
		for (const p of g.toPaths(drawable)) {
			if (!p.d || p.stroke === 'none') continue;
			trazos.push({d: p.d, color: p.stroke === color ? color : p.stroke, ancho, largo: getLength(p.d)});
		}
	};
	const api = {
		linea: (a: P, b: P, color = TINTA, ancho = 5) => agregar(g.line(a[0], a[1], b[0], b[1], base(color)), color, ancho),
		circulo: (c: P, diametro: number, color = TINTA, ancho = 5, relleno?: string) =>
			agregar(
				g.circle(c[0], c[1], diametro, base(color, relleno ? {fill: relleno, fillStyle: 'hachure', hachureGap: 9, fillWeight: 3} : {})),
				color,
				ancho,
			),
		elipse: (c: P, w: number, h: number, color = TINTA, ancho = 5) => agregar(g.ellipse(c[0], c[1], w, h, base(color)), color, ancho),
		curva: (puntos: P[], color = TINTA, ancho = 5) => agregar(g.curve(puntos, base(color)), color, ancho),
		camino: (d: string, color = TINTA, ancho = 5) => agregar(g.path(d, base(color)), color, ancho),
		rect: (x: number, y: number, w: number, h: number, color = TINTA, ancho = 5) =>
			agregar(g.rectangle(x, y, w, h, base(color)), color, ancho),
		poligono: (puntos: P[], color = TINTA, relleno?: string, gap = 12, angulo = -41) =>
			agregar(
				g.polygon(
					puntos,
					base(color, relleno ? {fill: relleno, fillStyle: 'hachure', hachureGap: gap, hachureAngle: angulo, fillWeight: 3} : {}),
				),
				color,
				4,
			),
		flecha: (puntos: P[], color = OCRE, ancho = 5) => {
			api.curva(puntos, color, ancho);
			const [a, b] = [puntos[puntos.length - 2], puntos[puntos.length - 1]];
			const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
			for (const d of [2.6, -2.6]) {
				api.linea(b, [b[0] + 30 * Math.cos(ang + d), b[1] + 30 * Math.sin(ang + d)], color, ancho);
			}
		},
		texto: (texto: string, x: number, y: number, tam = 46, color = TINTA) => textos.push({texto, x, y, tam, color}),
		// figura de palitos con los pies en (x, y)
		persona: (x: number, y: number, s = 1, brazo: 'abajo' | 'senala' | 'arriba' = 'abajo') => {
			api.circulo([x, y - 150 * s], 54 * s);
			api.linea([x, y - 123 * s], [x, y - 55 * s]);
			api.linea([x, y - 55 * s], [x - 28 * s, y]);
			api.linea([x, y - 55 * s], [x + 28 * s, y]);
			api.linea([x, y - 108 * s], [x - 38 * s, y - 68 * s]);
			if (brazo === 'senala') api.linea([x, y - 108 * s], [x + 85 * s, y - 112 * s]);
			else if (brazo === 'arriba') api.linea([x, y - 108 * s], [x + 40 * s, y - 150 * s]);
			else api.linea([x, y - 108 * s], [x + 38 * s, y - 68 * s]);
		},
		resultado: (): Dibujo => ({trazos, textos}),
	};
	return api;
};

const DIBUJOS: Record<string, () => Dibujo> = {
	// Señalar a otro… y la flecha que vuelve a uno mismo
	senalar: () => {
		const d = crear(1);
		d.persona(230, 540, 1.1, 'senala');
		d.persona(590, 540, 1.1);
		d.texto('!', 640, 330, 70, TINTA);
		d.flecha([[335, 400], [450, 300], [400, 200], [280, 215], [240, 330]]);
		return d.resultado();
	},
	// Un proyector que lanza su imagen sobre otra persona
	proyector: () => {
		const d = crear(2);
		d.rect(70, 330, 200, 120);
		d.circulo([120, 290], 80);
		d.circulo([215, 290], 80);
		d.rect(270, 360, 40, 60);
		d.poligono([[315, 370], [760, 210], [760, 560], [315, 410]], OCRE, OCRE, 30, 75);
		d.persona(610, 540, 0.95);
		return d.resultado();
	},
	// La sombra (Jung): lo que llevamos y no miramos
	sombra: () => {
		const d = crear(3);
		d.circulo([120, 130], 80, OCRE);
		for (let i = 0; i < 8; i++) {
			const a = (i / 8) * Math.PI * 2;
			d.linea([120 + 55 * Math.cos(a), 130 + 55 * Math.sin(a)], [120 + 80 * Math.cos(a), 130 + 80 * Math.sin(a)], OCRE, 4);
		}
		d.linea([50, 540], [770, 540]);
		d.persona(300, 540, 1.1);
		d.poligono([[310, 540], [480, 522], [580, 500], [615, 478], [665, 480], [690, 508], [660, 540]], AZUL, AZUL, 10, -30);
		return d.resultado();
	},
	// Dos globos de diálogo que chocan
	discusion: () => {
		const d = crear(4);
		d.circulo([120, 470], 110);
		d.camino('M 50 600 Q 120 530 190 600');
		d.circulo([680, 470], 110);
		d.camino('M 610 600 Q 680 530 750 600');
		d.elipse([290, 230], 330, 170);
		d.linea([220, 305], [150, 390]);
		d.linea([150, 390], [270, 312]);
		d.elipse([520, 270], 330, 170);
		d.linea([590, 345], [660, 400]);
		d.linea([660, 400], [550, 352]);
		d.linea([210, 210], [330, 205]);
		d.linea([210, 250], [300, 248]);
		d.linea([460, 255], [590, 250]);
		d.linea([480, 295], [570, 292]);
		d.camino('M 410 120 L 385 190 L 430 182 L 400 262', OCRE, 6);
		return d.resultado();
	},
	// Una balanza: no todo lo que molesta es mío
	balanza: () => {
		const d = crear(5);
		d.linea([300, 560], [500, 560]);
		d.linea([400, 560], [400, 180]);
		d.poligono([[385, 180], [415, 180], [400, 160]], TINTA);
		d.linea([180, 230], [620, 170]);
		d.linea([195, 228], [130, 380]);
		d.linea([195, 228], [260, 380]);
		d.camino('M 110 380 Q 195 450 280 380 Z');
		d.linea([605, 172], [540, 320]);
		d.linea([605, 172], [670, 320]);
		d.camino('M 520 320 Q 605 390 690 320 Z', OCRE);
		d.texto('lo mío', 195, 500, 50, TINTA);
		d.texto('lo del otro', 605, 440, 50, OCRE);
		return d.resultado();
	},
	// Frente al espejo, con una pregunta
	espejo: () => {
		const d = crear(6);
		d.persona(200, 560, 1.05);
		d.elipse([520, 290], 270, 390);
		d.elipse([520, 290], 225, 345);
		d.linea([520, 485], [520, 560]);
		d.linea([440, 560], [600, 560]);
		d.circulo([520, 250], 70, AZUL);
		d.camino('M 470 350 Q 520 300 570 350', AZUL);
		d.texto('?', 680, 140, 120, OCRE);
		return d.resultado();
	},
	// Un comentario: invitar a responder
	comentario: () => {
		const d = crear(7);
		d.camino('M 210 140 L 590 140 Q 640 140 640 190 L 640 360 Q 640 410 590 410 L 330 410 L 240 500 L 260 410 L 210 410 Q 160 410 160 360 L 160 190 Q 160 140 210 140 Z');
		d.circulo([310, 275], 46, OCRE, 4, OCRE);
		d.circulo([400, 275], 46, OCRE, 4, OCRE);
		d.circulo([490, 275], 46, OCRE, 4, OCRE);
		d.camino('M 660 520 C 660 490 700 480 715 510 C 730 480 770 490 770 520 C 770 550 730 570 715 590 C 700 570 660 550 660 520 Z', OCRE);
		return d.resultado();
	},
	// El ojo del logo, para el cierre
	ojo: () => {
		const d = crear(8);
		d.camino('M 130 310 Q 400 90 670 310 Q 400 530 130 310 Z', TINTA, 7);
		d.circulo([400, 310], 150, OCRE, 5, OCRE);
		d.circulo([400, 310], 56, TINTA, 5, TINTA);
		return d.resultado();
	},
};

const cache: Record<string, Dibujo> = {};
export const dibujo = (nombre?: string): Dibujo | null => {
	if (!nombre || !DIBUJOS[nombre]) return null;
	if (!cache[nombre]) cache[nombre] = DIBUJOS[nombre]();
	return cache[nombre];
};

export const NOMBRES_DIBUJOS = Object.keys(DIBUJOS);
