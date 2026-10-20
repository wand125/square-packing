import {PREVIEW} from './sitemap';
export interface PageDescription {file: string; en: string; ja: string; descEn: string; descJa: string; group: 'exp' | 'out'}
const entries: [string,string,string,string,string,'exp'|'out'][] = [
 ['certificate.html','Certificate','証明書の中身','Published square-container certificates drawn on [0, L]², with the mass a square captures.','公開した正方形の容器の証明書を [0, L]² に描き、正方形が拾う質量を出す。','exp'],
 ['containers.html','Other containers','正方形以外の容器','Triangles, the hexagon and the 1×2 rectangle: packings and certificate points.','三角形・六角形・1×2 の長方形：詰め方と証明書の点。','exp'],
 ['rect-regions.html','Rectangles','長方形の容器','For each k, the edge of the rectangles that hold k unit squares, piece by piece, with certified packings.','k ごとに、単位正方形が k 個入る長方形の端を、片ごとに証明書付きの配置とともに示す。','exp'],
 ['rect-player.html','Player','再生','The box shrinks along the edge from the square to the strip, and the squares follow; one short film per k.','箱が正方形から帯まで端に沿って縮み、正方形がそれについていく。k ごとの短い映像。','exp'],
 ['cubes.html','Cubes in a cube','立方体の容器','The optimal packings of 9 and 10 unit cubes in the cube of side 2 + 1/√2, in 3D, with the 8 points of the lower bound.','辺 2 + 1/√2 の立方体に単位立方体 9 個・10 個を入れる最適な配置を 3D で、下界の 8 点とともに示す。','exp'],
 ['cubes4-survey.html','4-cubes, k = 17–30','4 次元 k = 17〜30','Packings of 17 to 30 unit 4-cubes with exact certificates, drawn as a parallel projection that turns in four dimensions; k = 27 to 30 are new records.','単位 4 次元立方体 17〜30 個の配置を厳密な証明書とともに、4 次元で回る平行投影の図で示す。k = 27〜30 は新記録。','exp'],
 ['explain.html','How it works (preview)','仕組み (preview)','The core square and the angle net, the branch and bound over centres, the k² − c lift.','芯の正方形と角度の網、中心の分枝限定、k² − c の持ち上げ。','exp'],
 ['themes.html','Themes','Themes','The tracking issues: goal, method, completed stages.','追跡用 Issue：目指すもの・方法・済んだ段階。','out'],
 ['results.html','Results','Results','Every certificate and proof: claim, method, check command and release asset.','すべての証明書と証明：主張・手法・検算のコマンド・Release の資産。','out'],
 ['releases.html','Releases','Release','The published releases and the results each carries.','公開した Release と、それぞれが含む結果。','out'],
 ['methods.html','Methods','Methods','Each method: what the certificate contains, where it was used, origin and code.','手法ごと：証明書の中身・使った対象・出典・コード。','out'],
 ['verify.html','Verify','Verify','How to check a certificate yourself: steps, requirements, checkers, releases.','自分で検算する方法：手順・必要なもの・検査器・Release。','out'],
 ['about.html','Credits','クレジット','Credits, related repositories, moved repositories and licenses.','クレジット・関連リポジトリ・移したリポジトリ・ライセンス。','out']
];
export const pageDescriptions: PageDescription[] = entries.filter(p => PREVIEW || !['explain.html','short.html'].includes(p[0])).map(([file,en,ja,descEn,descJa,group]) => ({file,en,ja,descEn,descJa,group}));
