import {mountShared} from '../shared/rect-regions';
import {layout} from './layout';
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const card = host.querySelector('.pcard')!;
 // Keep the packing inside the selection panel so All/cell visibility remains shared.
 l.move(host.querySelector('canvas.pk')!, card, card.firstChild);
 mountShared(host);
 return () => l.cleanup();
}
