import React from 'react';
import {Composition} from 'remotion';
import {Corto} from './Corto';
import {Pizarra} from './Pizarra';
import type {CortoProps} from './tipos';

export const FPS = 30;

const ejemplo: CortoProps = {
	titulo: 'Ejemplo',
	pilar: 'Emociones',
	audio: null,
	duracion: 12,
	finEscenas: 9,
	escenas: [
		{
			inicio: 0,
			fin: 4.5,
			pantalla: 'Inteligencia emocional *no es* ser calmado',
			subtitulos: [
				{
					inicio: 0.2,
					fin: 4,
					palabras: [
						{w: 'Inteligencia', t: 0.2},
						{w: 'emocional', t: 1.0},
						{w: 'no', t: 1.8},
						{w: 'es', t: 2.1},
						{w: 'ser', t: 2.5},
						{w: 'calmado.', t: 2.9},
					],
				},
			],
		},
		{
			inicio: 4.5,
			fin: 9,
			pantalla: '*1.* Darte cuenta de lo que sentís\n*2.* Regular lo que hacés',
			subtitulos: [],
		},
	],
};

export const Root: React.FC = () => (
	<>
	<Composition
		id="Corto"
		component={Corto}
		width={1080}
		height={1920}
		fps={FPS}
		durationInFrames={Math.ceil(ejemplo.duracion * FPS)}
		defaultProps={ejemplo}
		calculateMetadata={({props}) => ({
			durationInFrames: Math.ceil(props.duracion * FPS),
		})}
	/>
	<Composition
		id="Pizarra"
		component={Pizarra}
		width={1080}
		height={1920}
		fps={FPS}
		durationInFrames={Math.ceil(ejemplo.duracion * FPS)}
		defaultProps={{...ejemplo, escenas: ejemplo.escenas.map((e, i) => ({...e, dibujo: i ? 'balanza' : 'senalar'}))}}
		calculateMetadata={({props}) => ({
			durationInFrames: Math.ceil(props.duracion * FPS),
		})}
	/>
	</>
);
