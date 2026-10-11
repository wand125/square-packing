// The phone design applies on narrow screens, and on touch screens up to tablet width; the desktop design otherwise.
// The same two queries choose the stylesheets (link media) and, in the browser, the views of the interactive pages.
export const PHONE = '(max-width: 600px), (pointer: coarse) and (max-width: 900px)';
export const DESKTOP = '(min-width: 601px) and (not (pointer: coarse)), (min-width: 901px)';
