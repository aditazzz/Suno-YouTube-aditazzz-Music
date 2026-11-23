import React from 'react';
import { Fmt } from '../theme';
import { Shot } from '../timing';

export type ShotProps = { shot: Shot; fmt: Fmt; slate: boolean };
/**
 * One shot of the film.
 *  stage:  the picture, drawn on the 2560x1440 stage (plates, inserts, in-world type). 9:16 reframes this layer.
 *  screen: optional screen-space layer drawn AFTER the reframe in the output format's own coordinates
 *          (2560x1440 for 16:9, 1080x1920 for 9:16; check useFmt()/props.fmt). For type that must sit in the
 *          9:16 safe zone instead of being cropped with the picture.
 *  cx916:  optional 9:16 crop centre (0..1 of the stage width) as a function of the shot-local frame, for a crop
 *          that follows the action; default is the shot's cx916 from shots.json / plates_override.json.
 */
export type ShotDef = { stage: React.FC<ShotProps>; screen?: React.FC<ShotProps>; cx916?: (f: number, shot: ShotProps['shot']) => number };
