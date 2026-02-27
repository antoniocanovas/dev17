/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useBus, useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class UnbuildBarcodeHandler extends Component {
    static props = {
        action: { type: Object },
        actionId: { type: Number, optional: true },
        className: { type: String },
        globalState: { type: Object, optional: true },
    };
    static template = "mrp_autounbuild.UnbuildBarcodeHandler";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.state = useState({ lot_name: "", input_value: "" });

        onWillStart(() => {
            const fileExtension = new Audio().canPlayType("audio/ogg") ? "ogg" : "mp3";
            this.sounds = {
                error: new Audio(`/stock_barcode/static/src/audio/error.${fileExtension}`),
                success: new Audio(`/mail/static/src/audio/ting.${fileExtension}`),
            };
            this.sounds.error.load();
            this.sounds.success.load();
        });

        const barcodeService = useService("barcode");
        useBus(barcodeService.bus, "barcode_scanned", (ev) => this.onBarcodeScanned(ev.detail.barcode));
    }

    _playSound(type) {
        if (this.sounds && this.sounds[type]) {
            this.sounds[type].currentTime = 0;
            this.sounds[type].play();
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            this.onManualConfirm();
        }
    }

    onManualConfirm() {
        const barcode = this.state.input_value.trim();
        if (barcode) {
            this.state.input_value = "";
            this.onBarcodeScanned(barcode);
        }
    }

    async onBarcodeScanned(barcode) {
        this.state.lot_name = barcode;
        const lotResult = await this.orm.searchRead(
            "stock.lot",
            [["name", "=", barcode]],
            ["product_id", "display_name", "company_id"]
        );

        if (!lotResult.length) {
            this.notification.add(_t("Lot/Serial number not found."), { type: "danger" });
            this._playSound("error");
            return;
        }
        const lot = lotResult[0];
        const [productId] = lot.product_id;
        const productInfo = (await this.orm.read("product.product", [productId], ["product_tmpl_id"]))[0];
        const productTmplId = productInfo.product_tmpl_id[0];
        const companyId = lot.company_id ? lot.company_id[0] : false;

        const bomResult = await this.orm.searchRead("mrp.bom", [
            "|",
                ["product_id", "=", productId],
            "&",
                ["product_tmpl_id", "=", productTmplId],
                ["product_id", "=", false],
            ["type", "=", "normal"],
            "|",
                ["company_id", "=", companyId],
                ["company_id", "=", false]
        ], ["id"], { limit: 1 });

        if (!bomResult.length) {
            this.notification.add(_t("Product has no bill of materials."), { type: "danger" });
            this._playSound("error");
            return;
        }

        try {
            await this.orm.call("mrp.unbuild", "action_unbuild_from_barcode", [lot.id]);
            this.notification.add(_t("Lot %s successfully unbuilt.", lot.display_name), { type: "success" });
            this._playSound("success");
        } catch (e) {
            const message = e.data?.message || e.message || _t("Unknown error");
            this.notification.add(_t("An error occurred: %s", message), { type: "danger" });
            this._playSound("error");
        }
    }
}

registry.category("actions").add("stock_barcode_unbuild_client_action", UnbuildBarcodeHandler);
