import {mountResponsive} from './responsive';
import {mountPhone} from './phone/rect-player';
import {mountDesktop} from './desktop/rect-player';
export const views = {desktop: mountDesktop, phone: mountPhone};
export function mount() { mountResponsive('rect-player', views); }
