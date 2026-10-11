import {PHONE} from '../lib/media';
/** Swap only the presentation. The mounted controller, URL, audio and engine state survive. */
export function mountResponsive(name: string, views: Record<'phone' | 'desktop', (host: HTMLElement) => void | (() => void)>) {
 const host = document.querySelector<HTMLElement>(`[data-interactive="${name}"]`)!;
 const query = matchMedia(PHONE);
 let cleanup: void | (() => void);
 const choose = () => {
  cleanup?.();
  host.classList.toggle('phone-view', query.matches);
  host.dataset.view = query.matches ? 'phone' : 'desktop';
  cleanup = views[query.matches ? 'phone' : 'desktop'](host);
  window.dispatchEvent(new Event('resize'));
 };
 choose();
 query.addEventListener('change', choose);
}
