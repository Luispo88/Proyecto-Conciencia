export type PalabraTiempo = {w: string; t: number};

export type Subtitulo = {
	inicio: number;
	fin: number;
	palabras: PalabraTiempo[];
};

export type Escena = {
	inicio: number;
	fin: number;
	pantalla: string; // *resaltado* y \n para saltos de línea
	dibujo?: string; // ilustración para el estilo pizarra (ver dibujos.ts)
	subtitulos: Subtitulo[];
};

export type CortoProps = {
	titulo: string;
	pilar: string;
	audio: string | null; // ruta dentro de public/
	duracion: number; // segundos, incluye el cierre
	finEscenas: number; // segundos
	escenas: Escena[];
};
