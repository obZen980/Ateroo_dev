/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import {
    Component,
    onWillStart,
    useState,
} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class AterooTourComponent extends Component{
    static template = 'ateroo.Tourtemplate';
    static props = { record: {type: Object} };
    setup(){
        this.orm = useService("orm");
        this.action = useService("action");
        this.action_start = this.action_start.bind(this);
        this.state = useState({
            tours: null,
        })
        onWillStart(async () => {
            this.state.tours  = await this.getTourRecords(this.props.record);
        });
    }

    async getTourRecords(record){
        const type = this.env.model.root.data['type'];
        const result = await this.orm.call('delivery.tour', 'fetch_package_pickings', [false, record.resId, type], {});
        return result
    }
    async action_start(ev){
        let $el = ev.target;
        const pick = $el.getAttribute("pick")
        await this.orm.call('delivery.picking', 'action_start', [parseInt(pick)], {})
        this.state.tours = await this.getTourRecords(this.props.record);
        await this.env.model.root.save()
        this.env.model.root.load()
    }
    async action_done(ev){
        let $el = ev.target;
        const pick = $el.getAttribute("pick")
        await this.orm.call('delivery.picking', 'action_done', [parseInt(pick)], {})
        this.state.tours = await this.getTourRecords(this.props.record);
        await this.env.model.root.save()
        this.env.model.root.load()
    }
    displayOnMap(ev){
        let $el = ev.target;
        const pick = $el.getAttribute("pick");
        this.action.doAction({
                type: "ir.actions.act_window",
                res_model: 'wizard.map',
                views: [[false, "form"]],
                target: "new",
                context: {'default_pick_id':  parseInt(pick)}
            });
    }

}

export const aterooTourComponent =  {
    component: AterooTourComponent
}

export class AterooTourListRenderer extends ListRenderer{
//    static rowsTemplate = "ateroo.ListRenderer.Rows";
    static recordRowTemplate = "ateroo.ListRenderer.RecordRow";
    static components = {
        ...ListRenderer.components,
        AterooTourComponent
    }
}

export class AterooTourListFieldOne2Many extends X2ManyField {
    static components = {
        ...X2ManyField.components,
        ListRenderer: AterooTourListRenderer,
    };
}

export const aterooTourListFieldOne2Many = {
    ...x2ManyField,
    component: AterooTourListFieldOne2Many,
    additionalClasses: [...x2ManyField.additionalClasses || [], "o_field_one2many"],
};

registry.category("fields").add("ateroo_tour_component", aterooTourComponent);
registry.category("fields").add("ateroo_tour_list_one2many", aterooTourListFieldOne2Many);
