# -*- coding: utf-8 -*-
{
    'name': "ATEROO base",
    'summary': "Manage delivery package backend",
    'description': """
    """,
    'author': "ATEROO",
    'website': "",
    'category': 'Uncategorized',
    'licence': 'Other propriety',
    'version': '18.0.1.0.1',
    'depends': [
        'base',
        'sale',
        'hr',
    ],
    'data':[
        # data
        'data/ir_sequence.xml',
        'data/ir_sequence_tour.xml',

        # security
        'security/ir.model.access.csv',

        # views
        'views/res_partner_views.xml',
        'views/delivery_agency_views.xml',
        'views/res_users_views.xml',
        'views/delivery_transport_views.xml',
        'views/delivery_method_views.xml',
        'views/delivery_tarif_zone_views.xml',
        'views/delivery_category_views.xml',
        'views/delivery_package_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_pricelist_views.xml',
        'views/delivery_tour_views.xml',
        'views/res_city_views.xml',
        'views/res_region_views.xml',
        'wizard/wizard_map_views.xml',
        'report/delivery_package_label.xml',
        'report/delivery_package_label_action.xml',
        'views/menu_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'ateroo_base/static/src/xml/osm_address_autocomplete.xml',
            'ateroo_base/static/src/js/osm_address_autocomplete.js',
            'ateroo_base/static/src/xml/image_selector.xml',
            'ateroo_base/static/src/js/image_selector.js',
            'ateroo_base/static/src/css/image_selector.css',
            'ateroo_base/static/lib/dist/leaflet.css',
            'ateroo_base/static/lib/dist/leaflet.js',
            'ateroo_base/static/lib/dist/leaflet-routing-machine.js',
            'ateroo_base/static/lib/maplibre/maplibre-gl.css',
            'ateroo_base/static/lib/maplibre/maplibre-gl.js',
            'ateroo_base/static/src/js/tracking_map.js',
            'ateroo_base/static/src/xml/tracking_map.xml',
            'ateroo_base/static/src/js/ateroo_kanban_dashboard.js',
            'ateroo_base/static/src/js/ateroo_kanban_graph.js',
            'ateroo_base/static/src/xml/ateroo_tour_list.xml',
            'ateroo_base/static/src/js/ateroo_tour_list.js',
            'ateroo_base/static/src/xml/osm_location.xml',
            'ateroo_base/static/src/js/osm_point_location.js',
        ],
    }

}

