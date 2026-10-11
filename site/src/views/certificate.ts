import {mountResponsive} from './responsive';
import {mountPhone} from './phone/certificate';
import {mountDesktop} from './desktop/certificate';
export const views = {desktop: mountDesktop, phone: mountPhone};
export function mount() { mountResponsive('certificate', views); }
