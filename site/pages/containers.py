"""Containers page: the non-square containers, their optimal packings and the certificates' weighted points."""
import json

from lib import BLOB, bi, e

NAMES = {
    'triangle': ('Equilateral triangle (side)', '正三角形（辺）'),
    'right-isosceles': ('Right isosceles triangle (leg)', '直角二等辺三角形（脚）'),
    'hexagon': ('Regular hexagon (side)', '正六角形（辺）'),
    'domino': ('1×2 rectangle (short side)', '1×2 の長方形（短い辺）'),
}
SRC = [  # path, label, container, n (None: every n)
    ('problems/triangle/checker/SPEC.md', 'triangle/checker/SPEC.md', 'triangle', None),
    ('problems/triangle/SERIES.md', 'triangle/SERIES.md', 'triangle', None),
    ('problems/triangle/certificates/n6/PROOF.md', 'triangle n6/PROOF.md', 'triangle', 6),
    ('problems/right-isosceles/README.md', 'right-isosceles/README.md', 'right-isosceles', None),
    ('problems/right-isosceles/checker/SPEC.md', 'right-isosceles/checker/SPEC.md', 'right-isosceles', None),
    ('problems/hexagon/n3/PROOF.md', 'hexagon n3/PROOF.md', 'hexagon', None),
    ('problems/domino/certificates/n4/PROOF.md', 'domino n4/PROOF.md', 'domino', None),
]


def build():
    names = json.dumps({k: bi(*v) for k, v in NAMES.items()}, ensure_ascii=False)
    kv = ''.join(f'<dt>{bi(en, ja)}</dt><dd data-f="{k}"{" class=\"num\"" if k in ("L", "w") else ""}></dd>' for k, en, ja in [
        ('claim', 'Result', '結果'), ('L', 'Side', '辺'), ('pts', 'Certificate points', '証明書の点'), ('w', 'Total weight', '総重み'),
        ('sym', 'Symmetry', '対称'), ('cert', 'Certificate file', '証明書のファイル'), ('pack', 'Packing', '詰め方'), ('docs', 'Documents', '文書')])
    src = ''.join(f'<a href="{BLOB}{p}" data-cont="{c}"{f" data-n=\"{n}\"" if n else ""}>{e(t)}</a>' for p, t, c, n in SRC)
    return f'''<div class="cv" id="ct" data-blob="{BLOB}" data-names="{e(names)}">
<div class="ct-pick"></div>
<div class="cv-grid">
<div class="cv-fig"><canvas aria-label="container"></canvas>
<div class="bar">
<label><input type="checkbox" data-show="pack" checked> {bi("packing", "詰め方")}</label>
<label><input type="checkbox" data-show="pts" checked> {bi("certificate points", "証明書の点")}</label>
<label><input type="checkbox" data-show="sq" checked> {bi("test square", "試す正方形")}</label>
</div>
</div>
<div class="cv-side">
<dl class="kv">{kv}</dl>
<label><input type="checkbox" id="ct-keep" checked> {bi("keep the test square inside the container while dragging", "ドラッグ中も試す正方形を容器の中に留める")}</label>
<label class="cv-r">{bi("Angle", "角度")} <input type="range" id="ct-a" min="0" max="90" value="0" step="0.1" list="ct-ticks"><datalist id="ct-ticks"><option value="0"></option><option value="15"></option><option value="30"></option><option value="45"></option><option value="60"></option><option value="75"></option><option value="90"></option></datalist></label>
<dl class="kv">
<dt>{bi("Centre", "中心")}</dt><dd class="num" data-o="c"></dd>
<dt>{bi("Angle", "角度")}</dt><dd class="num" data-o="a"></dd>
<dt>{bi("Weight inside", "含む重み")}</dt><dd class="num" data-o="m"></dd>
<dt>{bi("Position", "位置")}</dt><dd data-o="fit"></dd>
</dl>

<p class="note" data-when="stage" data-cont="triangle">{bi("Here the certificate also has exclusion boxes: boxes of poses (centre range × angle range) that it leaves to later stages. Near the packing the weight can be below 1.",
  "この証明書には除外箱（exclusion boxes）がある。後の段に回す姿勢（中心の範囲 × 角度の範囲）の箱。詰め方の近くでは重みが 1 未満になることがある。")}</p>
<p class="note" data-when="stage" data-cont="hexagon">{bi("Here the certificate also has excused boxes: boxes of poses (centre range × angle range) that it leaves to the second stage. Near the pinwheel the weight can be below 1.",
  "この証明書には免除箱（excused boxes）がある。第 2 段に回す姿勢（中心の範囲 × 角度の範囲）の箱。風車の近くでは重みが 1 未満になることがある。")}</p>
</div></div>
<h2>{bi("How the lower bounds are proved", "下界の示し方")}</h2>
<ul class="tight">
<li data-cont="triangle">{bi("s(n) is the smallest side of an equilateral triangle that holds n non-overlapping unit squares (any position, any angle).", "s(n) は、重ならない単位正方形 n 個（位置・角度は自由）が入る正三角形の最小の辺。")}</li>
<li data-cont="right-isosceles">{bi("s(n) is the smallest leg of a right isosceles triangle that holds n non-overlapping unit squares (any position, any angle).", "s(n) は、重ならない単位正方形 n 個（位置・角度は自由）が入る直角二等辺三角形の最小の脚。")}</li>
<li data-cont="hexagon">{bi("s(n) is the smallest side of a regular hexagon that holds n non-overlapping unit squares (any position, any angle).", "s(n) は、重ならない単位正方形 n 個（位置・角度は自由）が入る正六角形の最小の辺。")}</li>
<li data-cont="domino">{bi("s(n) is the smallest short side v of a rectangle [0, 2v] × [0, v] that holds n non-overlapping unit squares (any position, any angle).", "s(n) は、重ならない単位正方形 n 個（位置・角度は自由）が入る長方形 [0, 2v] × [0, v] の最小の短い辺 v。")}</li>
<li>{bi("A certificate lists points with rational weights and total weight below n. The checker proves exactly that every closed unit square inside the container, at any position and angle, contains points of total weight at least 1. n disjoint squares would then contain weight at least n.",
  "証明書は有理数の重みの点を並べ、総重みは n 未満。検査器は、容器の中の閉じた単位正方形がどの位置・角度でも重み 1 以上の点を含むことを厳密に示す。互いに重ならない n 個の正方形は合わせて n 以上を含むことになる。")}</li>
<li data-when="pairs">{bi("Lemma P: take two points at distance exactly 1. If the line through them crosses a square between two opposite edges, and that crossing meets the segment between the points, the square contains one of the two points (the crossing has length at least 1).",
  "補題 P：距離がちょうど 1 の 2 点をとる。2 点を通る直線が正方形を向かい合う 2 辺の間で横切り、その横切る部分が 2 点を結ぶ線分と交わるなら、正方形は 2 点のどちらかを含む（横切る部分の長さは 1 以上）。")}</li>
<li data-when="stage" data-cont="triangle">{bi("One certificate is not enough for n = 6: the first certificate leaves out boxes of poses near the packing, and a tree of further certificates with obstacle points and a lemma on three squares closes them.",
  "n = 6 は証明書 1 つでは足りない。最初の証明書が詰め方の近くの姿勢の箱を除き、障害点つきの後の証明書の木と 3 個の正方形についての補題で閉じる。")}</li>
<li data-when="stage" data-cont="hexagon">{bi("One certificate is not enough: stage 1 leaves out 742 boxes of poses near the pinwheel, and stage 2 closes each box by interval branch and bound and the local lemma near the pinwheel.",
  "証明書 1 つでは足りない。第 1 段が風車の近くの姿勢の箱 742 個を除き、第 2 段がそれぞれの箱を区間の分枝限定と風車の近くの局所補題で閉じる。")}</li>
</ul>
<p class="links-inline">{src}</p>
</div>
<script src="viz/containers.js" defer></script>'''
