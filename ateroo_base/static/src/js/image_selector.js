import { ImageField, imageField } from '@web/views/fields/image/image_field';
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillRender } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ImageSelector extends Component{
    static template = "ateroo_base.image_selector";
    static components = {
        ImageField
    }
    setup(){
        this.state = useState({
            currentImage : this.defaultImage('image_1920'),
        })
    }
    getProps(field, primary=true){
        var width = primary? 512 : 180
        var height = primary? 512 : 180
        return {
            name: field,
            record: this.props.record,
            width: width,
            height: height,
            readonly: primary,
            convertToWebp: true,
            imgClass: 'img-fixed '
        }
    }
    defaultImage(field){
        return this.getProps(field, true);
    }
    selectImage(ev, field){
        var element = ev.target;
        if(element.nodeName == 'IMG'){
            this.state.currentImage = this.getProps(field, true);
        }

    }
}

export const imageSelector = {
    ...imageField,
    component: ImageSelector,
};

registry.category("fields").add("image_selector", imageSelector);