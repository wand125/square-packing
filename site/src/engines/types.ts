/** Runtime data shapes shared by the desktop and future phone views. */
export type Point = [number, number];
export type Square = [number, number, number]; // centre x, centre y, angle (radians)
export type WeightedPoint = [number, number, number];
export type WeightedRegion = [number, number, number, number, number];
export interface Bilingual { en: string; ja: string }
export interface Packing { box: Point; squares: Square[] }
export interface Family { a: number[]; box: Point[]; squares: Square[][] }
export interface Witness extends Packing { a: number; b: number; [key: string]: unknown }
export interface Piece {
 key: string; pts: Point[]; a0: number; a1: number; a_text: string;
 kind: string; source: string; basis: Bilingual; name?: string; formula?: string;
 param?: Bilingual; note?: Bilingual; family?: Family; witnesses: Witness[];
 status: ({kind: string; key: string} & Bilingual)[];
 formula_full?: {a: string; b: string; constraints?: string[]; param?: Bilingual};
 friedman?: string[];
}
export interface Edge { k: number; ymax?: number; pieces: Piece[]; status?: Bilingual }
export interface Regions { ks: Edge[] }
export interface Projection { X: (x: number) => number; Y: (y: number) => number; px: number }
export interface Pose { x: number; y: number; a: number }
export interface Container {
 poly: Point[]; points: WeightedPoint[]; pairs: Point[]; packing?: Point[][];
 cont: string; n: number; L: number; claim: string; weight: string;
 symmetry: string; cert: string; stage?: Bilingual; pnote?: Bilingual; docs: string[];
}
export interface Measure {
 L: number; B: number; step?: number; last?: number;
 atoms?: WeightedPoint[]; segs?: WeightedRegion[]; rects?: WeightedRegion[];
 atoms_d4?: WeightedPoint[]; segs_d4?: WeightedRegion[]; rects_d4?: WeightedRegion[];
 total_mass: string; id?: string; dmin?: number; dmax?: number; rad?: number; wmax?: number;
 angle_lower_bound?: number[];
}
export interface Frame { a: number; box: Point; sq: Square[] }
export interface Segment {
 kind: 'run' | 'step' | 'wind' | 'fade'; p: Piece; t0: number; t1: number;
 fr?: Frame[]; from?: Frame; to?: Frame; quick?: boolean; after?: boolean;
}
export interface Timeline { segments: Segment[]; duration: number }
