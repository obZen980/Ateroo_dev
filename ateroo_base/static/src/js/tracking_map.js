import { Component, onMounted, useRef, onPatched} from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class TrackingMap extends Component {
    static template = "ateroo_base.TrackingMap";
    static props = {
        ...standardFieldProps,
        type: { type: String, optional: true },
    };
    setup() {
        this.mapRef = useRef("map");
        this.map = null;
        this.orm = useService("orm");
        this.marker = null;
        onMounted(async () => {
            if(this.props.type == 'latitude' || this.props.type == 'longitude'){
                const lat = this.props.record.data.map_latitude || 0;
                const lng = this.props.record.data.map_longitude || 0;
                 this.initMap(lat, lng);
                 this.setAgencyMap();
            }
            if(this.props.type == 'address' ){
                const coord = await this.setMarkerFromAddress(this.props.record.data[this.props.name])
                if(coord && coord.length){
                    this.initMap(coord[0], coord[1]);
                    this.setAgencyMap();
                }
            }
            if(this.props.type == 'location'){
                const lat = this.props.record.data.latitude || 0;
                const lng = this.props.record.data.longitude || 0;
                this.initMap(lat, lng);
                this.map.on('click', (e) => {
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;

                    console.log("Clicked at:", lat, lng);
                    if (this.marker) {
                        this.map.removeLayer(this.marker);
                    }
                    this.props.record.update({ ['latitude']: lat });
                    this.props.record.update({['longitude']: lng})

                    this.marker = L.marker([lat, lng]).addTo(this.map);
                });
            }
            if(this.props.type == 'route'){
                this.initMap(0,0);
                L.Routing.control({
                    waypoints: [
                        L.latLng(this.props.record.data['departure_latitude'], this.props.record.data['departure_longitude']),
                        L.latLng(this.props.record.data['destination_latitude'], this.props.record.data['destination_longitude']),
                    ],
                    routeWhileDragging: false,
                }).addTo(this.map);
            }
        });
        onPatched(() =>{
            const lat = this.props.record.data.map_latitude;
            const lng = this.props.record.data.map_longitude;
            if (this.marker && lat && lng) {
                this.marker.setLatLng([lat, lng]);
                this.map.panTo([lat, lng]);
            }
        });
    }
    initMap(lat=0, lng=0) {
        this.map = L.map(this.mapRef.el).setView([lat, lng], 15);
        if(lat && lng){
            this.marker = L.marker([lat, lng]).addTo(this.map);
        }


        /* -------- Base maps -------- */

        // Standard OpenStreetMap
        const streetMap = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors",
                maxZoom: 19,
            }
        ).addTo(this.map);

        // Satellite-style (actually satellite imagery, not pure OSM)
        const satellite = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            {
                attribution: "Tiles &copy; Esri",
                maxZoom: 19,
            }
        );

        /* -------- Overlay maps -------- */

        // Labels (OSM-based)
        const labels = L.tileLayer(
            "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors, HOT",
                maxZoom: 19,
            }
        );

        // Roads emphasis (Carto)
        const roads = L.tileLayer(
            "https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap &copy; CARTO",
                maxZoom: 19,
            }
        );

        const baseMaps = {
            "Street Map (OSM)": streetMap,
            "Satellite": satellite,
        };

        const overlayMaps = {
            "Labels": labels,
            "Roads": roads,
        };

        L.control.layers(baseMaps, overlayMaps).addTo(this.map);
    }
    async setMarkerFromAddress(address) {
        const result = await rpc("/osm/geocode", {
            address: address
        });
        if (!result || !result.length) {
            return;
        }
        const lat = parseFloat(result[0].lat);
        const lng = parseFloat(result[0].lon);
        return [lat, lng]
    }

    async setAgencyMap(){
        const agencies = await this.orm.call('delivery.agency', "search_read", [], {
                domain: [["parent_id", "=", false]],
                fields: ["agency_latitude", "agency_longitude", "name"],
            })

        const customIcon = L.icon({
            iconUrl: '/ateroo_base/static/src/img/moving-truck.png',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
        });
        const locations = agencies.map(r => {
            return Object.assign({}, {lat: r.agency_latitude, lng: r.agency_longitude, name: r.name})
        })
        locations.forEach(loc => {
            L.marker([loc.lat, loc.lng], { icon: customIcon })
                .addTo(this.map)
               .bindTooltip(loc.name, {
                    permanent: true,
                    direction: "top",
                    offset: [0, -10],
                });

        });
    }
}

export const trackingMap = {
    component: TrackingMap,
    extractProps: ({attrs, options}, dynamicInfo) => {
        return {
            type: options.type || "[]",
        }
    },
}
//https://www.openstreetmap.org/#map=18/-18.858037/47.552905&layers=G

registry.category("fields").add("tracking_map", trackingMap);