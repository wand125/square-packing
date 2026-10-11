// Compatibility diagnostics used by the original player and its score tooling.
interface Window {
 SPTimeline: () => {k: number; T: number; hold: number; segments: {kind: string; piece: string; name: string | null; t0: number; t1: number; box0: number[]; box1: number[]}[]};
 SPAudio: () => {paused: boolean; at: number; ready: boolean; src: string};
}
