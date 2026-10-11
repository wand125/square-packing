"""Rectangles page (themes 15 and 16): for k = 2 .. 20 squares, the edge where k squares begin to fit, its pieces,
the certified packings, and for k <= 10 the proof status of Friedman's pieces of S_(k-1)."""
from lib import PREVIEW, bi

FRIEDMAN = 'https://erich-friedman.github.io/mathmagic/0610.html'


def build():
    sel = '<button type="button" data-sel="all">' + bi('All', 'すべて') + '</button>' + ''.join(f'<button type="button" data-sel="{k}">{k}</button>' for k in range(2, 16)) + (('<span class="pv-l">preview</span>' + ''.join(f'<button type="button" data-sel="{k}" class="pv">{k}</button>' for k in range(16, 21))) if PREVIEW else '')
    meta = ''.join(f'<div><dt>{bi(en, ja)}</dt><dd data-o="{k}"></dd></div>' for k, en, ja in [
        ('src', 'Source', '出どころ'), ('basis', 'Basis', '根拠'), ('st', 'Proof below', '下側の証明')])
    return f'''<p class="note full">{bi("s(a, b) is the largest number of unit squares (any position and angle) that fit in an a × b rectangle, a ≤ b. The edge for k separates the rectangles that hold k squares from those that do not (shaded). For k ≤ 10 the edge is from Friedman's table (Math Magic, June 2010), which gives no proofs; the \"Proof below\" column is our own check. For k ≥ 11 the edge is our construction: each piece comes with a packing of k squares; nothing is claimed below the edge.",
  "s(a, b) は、a × b の長方形（a ≤ b）に入る単位正方形の最大個数（位置・角度は自由）。k 個の端は、k 個入る長方形と、入らない長方形（網かけ）の境目。k ≤ 10 の端は Friedman の表（Math Magic、2010 年 6 月）によるもので、表に証明はない。「下側の証明」の欄は当方の検証。k ≥ 11 の端は当方の構成で、各片の長方形に k 個入る配置を示す。端より下で入らないことは主張しない。")}
 <a href="{FRIEDMAN}">Friedman, Math Magic, June 2010</a></p>
<div class="bar rr-sel">{sel}</div>
<div class="cv" id="rr">
<h2><span data-o="rh"></span></h2>
<div class="cv-grid">
<div class="cv-fig"><canvas class="reg" aria-label="edge"></canvas>
<div class="bar rr-ctl" data-o="ctl"><button type="button" data-c="first" title="first piece (left end)" aria-label="first piece"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M4 4 V16 M17 10 H8 M12 5.5 L7.5 10 L12 14.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" data-c="prev" title="previous piece" aria-label="previous piece"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M17 10 H3.5 M8 5.5 L3.5 10 L8 14.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" data-c="next" title="next piece" aria-label="next piece"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M3 10 H16.5 M12 5.5 L16.5 10 L12 14.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" data-c="last" title="last piece (right end)" aria-label="last piece"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M16 4 V16 M3 10 H12 M8 5.5 L12.5 10 L8 14.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" data-c="play" title="move the point along the edge" aria-label="move the point along the edge"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M5 3.5 L16.5 10 L5 16.5 Z"/></svg></button></div>
</div>
<div class="cv-side">
<p class="num dim" data-o="leg" hidden></p>
<div data-o="zoom" hidden><canvas class="zm" aria-label="magnified"></canvas>
<p class="num dim" data-o="zt">{bi("Move the pointer over the plot, right of the diagonal a = b, to magnify that part here.", "グラフの対角線 a = b より右をポインタでなぞると、その部分をここに拡大する。")}</p></div>
<div data-o="pside" class="pcard">
<div class="pc-h"><b class="num" data-o="key"></b><a class="btn" data-o="playp" href="rect-player.html">▶ {bi("Player", "プレイヤー")}</a></div>
<div class="pc-f num" data-o="f"></div>
<div class="ffw" data-o="ffw" hidden></div>
<div class="pc-r num" data-o="range"></div>
<dl class="pc-s">{meta}</dl>
<div class="pc-p"><canvas class="pk" aria-label="packing"></canvas>
<div class="pc-pi"><div class="dim pc-l">{bi("Certified packings", "証明書の配置")}</div><div class="bar rr-w" data-o="wbar"></div>
<div class="num"><span class="dim">(b, a)</span> <span data-o="ab">–</span></div>
<p class="num dim" data-o="pk"></p></div></div>
</div></div></div>
<div data-o="ptab">
<h3>{bi("Pieces", "片")}</h3>
<div class="wrap"><table class="wide"><thead><tr><th>{bi("Piece", "片")}</th><th>{bi("Range of a", "a の範囲")}</th><th>{bi("Proof below", "下側の証明")}</th><th>{bi("Edge", "端の式")}</th><th>{bi("Basis", "根拠")}</th></tr></thead>
<tbody id="rr-rows"></tbody></table></div>
<p class="note full">{bi("Each certified packing is a rational placement checked by two checkers (verify_fast and verify.py --exact). For k ≤ 10 it is taken at the middle of Friedman's piece with one side fixed and the other minimized.",
  "証明書の配置は有理数の配置で、2 つの検査器（verify_fast と verify.py --exact）で検査した。k ≤ 10 では Friedman の片の中ほどで一方の辺を固定し、他方を最小化したもの。")}</p>
</div></p>
</div>
<script src="viz/rect-regions.js" defer></script>'''
