"""Rectangles player: for k squares, the box moving from the square down the edge to the 1-wide strip, with its packing."""
from lib import PREVIEW, bi


def build():
    ks = '<button type="button" data-k="all">' + bi('All', 'すべて') + '</button>' + ''.join(f'<button type="button" data-k="{k}">{k}</button>' for k in range(2, 16)) + (('<span class="pv-l">preview</span>' + ''.join(f'<button type="button" data-k="{k}" class="pv">{k}</button>' for k in range(16, 21))) if PREVIEW else '')
    return f'''<div class="cv" id="rp">
<p><a class="btn" data-o="back" href="rect-regions.html">← {bi("Rectangles", "長方形の容器")}</a></p>
<div class="bar rr-sel">{ks}</div>
<div class="rp-col">
<canvas aria-label="player"></canvas>
<div class="rp-side">
<div class="bar"><button type="button" data-o="home" title="back to the start" aria-label="back to the start">⏮</button><button type="button" data-o="play">▶</button><button type="button" data-o="restart">↻ {bi("from the start", "最初から再生")}</button>
<input type="range" data-o="scrub" min="0" max="1000" value="0" aria-label="time">
<span class="num dim" data-o="len"></span>
<label data-o="musl" class="off"><input type="checkbox" data-o="mus" checked disabled> {bi("music", "音楽")}</label>
<button type="button" data-o="rec">● {bi("record", "録画")}</button></div>
<p class="note">{bi("The box runs from the square (a = b) down the edge where k squares begin to fit, to the strip of width 1; b is drawn upright. The squares follow the sampled packings of each piece (illustrations, not certificates); colour shows the tilt, blue axis-parallel to red-violet at 45°. Where the arrangement changes a lot, the box winds up (squeezed and shaking) and the squares pop over. Below the box: the edge with the current point (click to jump) and the timeline (click to seek). Record saves the whole frame as a video. Music (where a score exists, played at 1×) is written to the timeline of each k: phrases follow the pieces, the wind-ups and pops are scored.",
  "箱は正方形（a = b）から、k 個が入り始める端に沿って幅 1 の帯まで進む。b を縦にとる。正方形は各片の配置の標本に沿って動き（作図であって証明書ではない）、色は傾き（軸に平行で青、45° で赤紫）。並びが大きく変わる所では、箱が縮んで震える溜めのあと、正方形が弾けて入れ替わる。箱の下：今の点つきの端（押すとそこへ）とタイムライン（押すとその時刻へ）。録画は枠全体を動画として保存する。音楽（曲がある k で、1× のとき）は各 k の時刻表に合わせて作曲したもので、片ごとのフレーズ、溜めと弾けに合わせてある。")}</p>
</div></div></div>
<script src="viz/rect-player.js" defer></script>'''
