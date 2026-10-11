import {mountShared} from '../shared/certificate';
import {layout, bi} from './layout';
export function mountPhone(host: HTMLElement) {
 const l = layout();
 const fig = host.querySelector('.cv-fig')!;
 l.move(host.querySelector('[data-o="m"]')!.closest('dl')!, fig);
 const heading = host.querySelector('.cv-main > h2')!;
 const states = document.createElement('details'); states.className = 'phone-section';
 const summary = document.createElement('summary'); summary.innerHTML = heading.innerHTML;
 states.append(summary); l.add(states, heading.parentElement!);
 l.move(heading, states); (heading as HTMLElement).hidden = true;
 l.move(host.querySelector('[data-states]')!, states);
 const scan = document.createElement('details'); scan.className = 'phone-section';
 scan.innerHTML = `<summary>${bi('Scan this direction', 'この角度を走査')}</summary>`;
 const scanButton = host.querySelector('#cv-scan')!.parentElement!;
 const scanResult = scanButton.nextElementSibling!;
 const note = scanResult.nextElementSibling!;
 l.add(scan, host.querySelector('.cv-side')!);
 l.move(host.querySelector('[data-kind="rect"]')!, scan);
 l.move(scanButton, scan); l.move(scanResult, scan); l.move(note, scan);
 mountShared(host);
 return () => { (heading as HTMLElement).hidden = false; l.cleanup(); };
}
