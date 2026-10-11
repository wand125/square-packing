// Phones: tables marked pop (DataTable pop="1,2") show each row as a compact item made of the listed columns;
// tapping a row opens a popup with every column (labelled) and the row's details. Wider screens keep the table.
import {PHONE} from '../lib/media';
const tables = document.querySelectorAll<HTMLTableElement>('table[data-pop]');
if (tables.length) {
 const pop = document.createElement('dialog'); pop.className = 'issue-pop row-pop';
 pop.innerHTML = '<button type="button" class="issue-pop-x" aria-label="close">✕</button><div class="issue-pop-body"></div>';
 document.body.append(pop);
 const body = pop.querySelector('.issue-pop-body')!;
 pop.querySelector('.issue-pop-x')!.addEventListener('click', () => pop.close());
 pop.addEventListener('click', e => { if (e.target === pop) pop.close(); });
 tables.forEach(table => {
  const show = (table.dataset.pop || '1').split(',').map(Number);
  table.querySelectorAll<HTMLTableRowElement>('tbody > tr:not(.x)').forEach(tr => {
   tr.classList.add('pop-row');
   tr.querySelectorAll(':scope > td').forEach((td, i) => { if (!show.includes(i + 1)) td.classList.add('pop-more'); });
  });
  table.addEventListener('click', e => {
   if (!matchMedia(PHONE).matches) return;
   const tr = (e.target as Element).closest<HTMLTableRowElement>('tr.pop-row'); if (!tr || (e.target as Element).closest('a,button,input')) return;
   e.stopPropagation();
   const parts = [...tr.querySelectorAll(':scope > td')].map(td => {
    const c = td.cloneNode(true) as Element, label = c.querySelector('.cell-label'); const l = label ? label.innerHTML : ''; label?.remove();
    return c.innerHTML.trim() ? `<dt>${l}</dt><dd>${c.innerHTML}</dd>` : '';
   }).join('');
   const x = tr.nextElementSibling as HTMLElement | null, detail = x && x.classList.contains('x') ? x.querySelector('td')!.innerHTML : '';
   body.innerHTML = `<dl class="row-pop-dl">${parts}</dl>${detail}`;
   pop.showModal();
  }, true);
 });
}
