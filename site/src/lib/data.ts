/** Build-time inputs. All source file access lives here; never write to the inputs. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
export type Bi = string | { en?: string; ja?: string };
export type Source = string | string[];
export interface Certificate { id: string; claim: string; release_tag: string; assets: string[]; check: string; check_cwd: string; documents: string[] }
export interface Index { problems: Record<string, Certificate[]> }
export interface Published { id: string; class: string; cells: unknown[]; nodes: number; claim: string; data: {release_url: string}; checks: string[]; manifest: string }
export interface Theme { issue: number; url: string; state: 'open' | 'closed' | 'stopped'; title: Bi; goal?: Bi; method?: Bi; updated?: string; done?: Bi[]; working_on?: Bi[]; links?: {url: string; label: string}[]; releases?: string[] }
export interface ResultNote { consequence: Bi; source: string; review_status?: Bi }
export interface Method { name?: Bi; what?: Bi; consists?: Bi; description?: Bi; used?: Bi; used_for?: Bi; review_status?: Bi; origin?: Bi; credit?: Bi; tools?: string[]; sources?: Source; result_notes?: Record<string, ResultNote> }
export interface Release { tag: string; name?: string; date?: string }
export interface Verify { steps: ({en: string; ja?: string; cmd?: string; source?: Source})[]; tools: {path: string; what?: Bi; runtime?: string; source?: Source}[]; requirements: {tool: string; en: string; ja?: string; source?: Source}[]; releases: Release[]; n17?: Bi[] }
export interface About { author: {github: string; name: string}; credits: {who: string; for?: Bi; source?: Source}[]; related: {url: string; name: string; en: string; ja?: string}[]; moved: {note?: Bi; table: {old: string; new: string}[]}; licenses: Bi }
export type Point = [number, number];
export interface Container { poly: Point[]; packing: Point[][] | null; cont: string; n: number; claim: string }
export interface RectRegions { ks: {k: number; pieces: {witnesses: {box: Point; squares?: [number, number, number][]}[]}[]}[] }
interface Editorial { 'themes.json': {themes: Theme[]}; 'methods.json': {rows: Method[]}; 'verify.json': Verify; 'about.json': About }
const repoRoot = resolve(process.env.SP_REPO || '../sp-site');
const docsRoot = resolve(process.env.SP_DOCS || 'docs/data');
const json = <T>(root: string, file: string): T => JSON.parse(readFileSync(resolve(root, file), 'utf8'));
export const readIndex = () => json<Index>(repoRoot, 'INDEX.json');
export const readManifest = () => json<{published: Published[]}>(repoRoot, 'problems/n17/manifest.json');
export const readRepoText = (file: string) => readFileSync(resolve(repoRoot, file), 'utf8');
export const readEditorial = <K extends keyof Editorial>(file: K): Editorial[K] => json<Editorial[K]>(docsRoot, file);
interface Figures { 'containers.json': Container[]; 'rect-regions.json': RectRegions; 'cert-point-n29.json': {L: string; atoms: [number, number, number][]} }
export const readFigure = <K extends keyof Figures>(file: K): Figures[K] => json<Figures[K]>(resolve('public/data'), file);
