import {mountResponsive} from './responsive';
import {mountPhone} from './phone/rect-regions';
import {mountDesktop} from './desktop/rect-regions';
export const views = {desktop: mountDesktop, phone: mountPhone};
export function mount() { mountResponsive('rect-regions', views); }
