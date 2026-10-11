import {mountResponsive} from './responsive';
import {mountPhone} from './phone/containers';
import {mountDesktop} from './desktop/containers';
export const views = {desktop: mountDesktop, phone: mountPhone};
export function mount() { mountResponsive('containers', views); }
