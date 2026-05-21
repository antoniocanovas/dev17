/** @odoo-module **/

import MainComponent from '@stock_barcode/components/main';
import { patch } from '@web/core/utils/patch';

patch(MainComponent.prototype, {
    async pallet2pack(ev) {
        ev.stopPropagation();
        await this.env.model.save();
        await this.orm.call(this.resModel, 'action_pallet2pack', [[this.resId]]);
        await this._onRefreshState({});
    },
});
