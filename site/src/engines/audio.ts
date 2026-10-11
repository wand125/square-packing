export interface Options {
  T: number;
  audio: HTMLAudioElement;
  blobUrl: string | null;
  endTimer: ReturnType<typeof setTimeout> | null;
  loadSeq: number;
  musicT: number;
  enabled: boolean;
  title: (text: string) => void;
  playing: boolean;
  ready: boolean;
  speed: number;
  t: number;
}
/** Extracted from the original desktop viewer; arithmetic, sample ordering and tolerances are unchanged.
 * Options are explicit per-call dependencies supplied by the view; there is no framework or global page state. */

export function music(options: Options): any { return options.ready && options.enabled && options.speed === 1; }

export function loadMusic(options: Options, k: number): any {
    // the score: bright style, wind-up D (a break before each pop)
    options.audio.pause(); options.ready = false;
    var want = ++options.loadSeq;
    // a score is written to one timeline: if the timeline of k has changed since (new data), the score would drift, so it is not played
    if (!options.musicT || Math.abs((options.musicT[k] || -1) - options.T) > 0.05) { options.title('the score does not match this timeline'); return; }
    options.title('');
    // the score's own timeline length in the address, so a re-scored file is never taken from a cache
    var src = 'data/music/k' + k + '-normal-D.mp3?t=' + options.musicT[k];
    // loaded whole into memory, so that seeking works on any server (a server without range requests restarts at 0)
    fetch(src, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.blob(); }).then(function (b) {
      if (want !== options.loadSeq) return;   // a newer choice was made meanwhile
      if (options.blobUrl) URL.revokeObjectURL(options.blobUrl);
      options.blobUrl = URL.createObjectURL(b);
      options.audio.oncanplaythrough = function () { if (want !== options.loadSeq) return; options.audio.oncanplaythrough = null; options.ready = true; if (options.playing && music(options)) startMusic(options); };
      options.audio.src = options.blobUrl; options.audio.load();
    }).catch(function () { if (want === options.loadSeq) { options.ready = false; } });
  }

export function startMusic(options: Options): any { options.endTimer !== null && clearTimeout(options.endTimer); if (music(options)) { if (Math.abs(options.audio.currentTime - options.t) > 0.05) options.audio.currentTime = options.t; options.audio.play().catch(function () {}); } }

export function stopMusic(options: Options): any { if (options.audio) options.audio.pause(); }
