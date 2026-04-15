/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { floatField, FloatField }  from "@web/views/fields/float/float_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class MapLocation extends FloatField {
    static template = "ateroo_base.Location";
    static props = {
        ...FloatField.props,
        long: { type: String, optional: true },
        lat: { type: String, optional: true },
    };
    setup() {
        super.setup();
        this.displayOnMap = this.displayOnMap.bind(this);
        this.actionService = useService("action");
        console.log(this);
    }

    displayOnMap(ev){
        this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: 'wizard.map',
                views: [[false, "form"]],
                target: "new",
                context: {'model': this.env.model.config.resModel, 'record_id': this.env.model.config.resId, 'long_field': this.props.long, 'lat_field': this.props.lat
            }
        });
    }

}
export const mapLocation = {
    ...floatField,
    component: MapLocation,
    extractProps: ({attrs, options}, dynamicInfo) => {
        return {
            long: options.long_field || "",
            lat: options.lat_field || "",
        }
    },
};

registry.category("fields").add("map_location", mapLocation);