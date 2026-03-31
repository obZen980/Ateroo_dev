/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class OSMAddressAutocomplete extends CharField {
    static template = "ateroo_base.OSMAddressAutocomplete";
    setup() {
        super.setup();
        this.selectAddress = this.selectAddress.bind(this);
        this.displayOnMap = this.displayOnMap.bind(this);
        this.actionService = useService("action");
        this.state = useState({
            suggestions: []
        });
        this.timer = null;

        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            parse: (v) => this.parse(v),
        });
    }

    async onInput(ev) {
        const value = ev.target.value;
        if (value.length < 5) {
            this.state.suggestions = [];
            return;
        }
        clearTimeout(this.timer);
        this.timer = setTimeout(async () => {
                if (value.length < 5) {
                    this.state.suggestions = [];
                    return;
                }
                const results = await rpc("/osm/autocomplete", {
                    query: value
                });
                this.state.suggestions = results;
            }, 700);
    }
    displayOnMap(ev){
        this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'wizard.map',
                views: [[false, "form"]],
                target: "new",
                context: {'default_address':  this.props.record.data[this.props.name]  }
            });
    }

    selectAddress(address) {
        this.props.record.update({[this.props.name]: address.display_name});
        this.state.suggestions = [];
    }
}
export const osmAddressAutocomplete = {
    ...charField,
    component: OSMAddressAutocomplete,
};

registry.category("fields").add("osm_address_autocomplete", osmAddressAutocomplete);