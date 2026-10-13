// The one list of pages: the header rows, the phone tab bar, the page lists on the top pages and the preview flags
// all come from here. file = the URL path after the base; group: 'viz' (visualize), 'out' (outcomes) or ''.
export type Page = { file: string; en: string; ja: string; title: string; group: 'viz' | 'out' | 'top' | ''; preview?: boolean };

export const PAGES: Page[] = [
  { file: 'index.html', en: 'Home', ja: 'ホーム', title: 'wand125 Square Packing', group: 'top' },
  { file: 'guide.html', en: 'Visualize', ja: 'ビジュアライズ', title: 'Square Packing Visualizations', group: 'top' },
  { file: 'outcomes.html', en: 'Outcomes', ja: '成果', title: 'Square Packing Outcomes', group: 'top' },
  { file: 'certificate.html', en: 'Certificate', ja: '証明書の中身', title: 'Certificate Viewer', group: 'viz' },
  { file: 'containers.html', en: 'Other containers', ja: '正方形以外の容器', title: 'Non-Square Containers', group: 'viz' },
  { file: 'rect-regions.html', en: 'Rectangles', ja: '長方形の容器', title: 'Squares in Rectangles', group: 'viz' },
  { file: 'explain.html', en: 'How it works (preview)', ja: '仕組み (preview)', title: 'How the Certificates Work', group: 'viz', preview: true },
  { file: 'themes.html', en: 'Themes', ja: 'Themes', title: 'Square Packing Themes', group: 'out' },
  { file: 'results.html', en: 'Results', ja: 'Results', title: 'Square Packing Results', group: 'out' },
  { file: 'releases.html', en: 'Releases', ja: 'Release', title: 'Square Packing Releases', group: 'out' },
  { file: 'methods.html', en: 'Methods', ja: 'Methods', title: 'Square Packing Methods', group: 'out' },
  { file: 'verify.html', en: 'Verify', ja: 'Verify', title: 'Checking the Certificates', group: 'out' },
  { file: 'about.html', en: 'Credits', ja: 'クレジット', title: 'Square Packing Credits', group: '' },
  { file: 'rect-player.html', en: 'Player', ja: '再生', title: 'Rectangles Player', group: '' },
  { file: 'paper-triangle.html', en: 'Equilateral triangle', ja: '正三角形', title: 'Unit Squares in an Equilateral Triangle', group: '' },
  { file: 'paper-domino.html', en: '1×2 rectangle, n = 4', ja: '1×2 長方形 n = 4', title: 'Four Unit Squares in a 1×2 Rectangle', group: '' },
  { file: 'paper-right-isosceles.html', en: 'Right isosceles triangle', ja: '直角二等辺三角形', title: 'Unit Squares in a Right Isosceles Triangle', group: '' },
  { file: 'paper-valid7.html', en: 'Valid7 and ValidTilt9', ja: 'Valid7 と ValidTilt9', title: 'Independent Checks of Valid7 and ValidTilt9', group: '' },
  { file: 'paper-closed-form-plots.html', en: 'Plots by block, k = 7 to 17', ja: 'ブロックごとの比較図', title: 'Closed-Form Bound Plots', group: '' },
  { file: 'paper-closed-form-table.html', en: 'Lower bounds for N ≤ 3600', ja: 'N ≤ 3600 の下界の表', title: 'Closed-Form Bound Table', group: '' },
  { file: 'paper-closed-form.html', en: 'Closed-form bound for s(N)', ja: 's(N) の閉じた式の下界', title: 'A Closed-Form Lower Bound for s(N)', group: '' },
  { file: 'paper-hexagon-n3.html', en: 'Hexagon, n = 3', ja: '正六角形 n = 3', title: 'Three Unit Squares in a Regular Hexagon', group: '' },
];

export const PREVIEW = process.env.SP_PREVIEW === '1';
export const url = (file: string) => import.meta.env.BASE_URL.replace(/\/?$/, '/') + (file === 'index.html' ? '' : file);
export const GH = 'https://github.com/wand125/square-packing';
