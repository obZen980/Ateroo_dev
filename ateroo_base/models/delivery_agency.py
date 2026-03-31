import json
from ast import literal_eval
from odoo import models, fields, _, api


class DeliveryAgency(models.Model):
    _name = 'delivery.agency'
    _description = 'Delivery agency'
    _order = 'is_favorite desc, id'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', stored=True)
    parent_id = fields.Many2one('delivery.agency', 'Parent Agency')
    child_ids = fields.One2many('delivery.agency', 'parent_id', ondelete='cascade')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    agency_latitude = fields.Float('Latitude', digits=(10, 7))
    agency_longitude = fields.Float('Longitude', digits=(10, 7))
    zone_id = fields.Many2one('delivery.tarif.zone', string='Zone')
    color = fields.Integer('Color')
    kanban_dashboard_graph = fields.Text(compute='_compute_kanban_dashboard_graph')
    is_favorite = fields.Boolean('Favorites')
    count_new = fields.Integer(compute='_compute_package_count')
    count_deliver = fields.Integer(compute='_compute_package_count')\


    @api.depends_context('name', 'parent_id.name')
    def _compute_display_name(self):
        for rec in self:
            temp = rec
            hierarchy = []
            while temp.parent_id:
                hierarchy.append(rec.parent_id)
                temp = rec.parent_id
            hierarchy.append(rec)
            if len(hierarchy) > 1:
                rec.display_name = ' / '.join(list(map(lambda r: r.name, hierarchy)))
            else:
                rec.display_name = rec.name

    def _compute_package_count(self):
        package_obj = self.env['delivery.package']
        for rec in self:
            rec.count_new = package_obj.search_count([('state', 'in', ['draft', 'reception'])])
            rec.count_deliver = package_obj.search_count([('state', 'in', ['ready', 'planned'])])

    def action_view_delivery_agency(self):
        return {
            'name': _('Agency'),
            'view_mode': 'form',
            'res_model': 'delivery.agency',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }

    def _get_aggregated_records_by_date(self):
        records = self.env['delivery.package']._read_group(
            [
                ('agency_id', 'in', self.ids),
                ('state', 'not in', ['new'])
            ],
            ['agency_id'],
            ['date' + ':array_agg'],
        )
        agency_id_to_dates = {i: [] for i in self.ids}
        agency_id_to_dates.update({r[0].id: r[1] for r in records})
        return [(i, d, self.env._('Delivery package')) for i, d in agency_id_to_dates.items()]

    def _compute_kanban_dashboard_graph(self):
        grouped_records = self._get_aggregated_records_by_date()
        summaries = {}
        for agency_id, dates, data_series_name in grouped_records:
            summaries[agency_id] = {
                'data_series_name': data_series_name,
                'total_before': 0,
                'total_yesterday': 0,
                'total_today': 0,
                'total_day_1': 0,
                'total_day_2': 0,
                'total_after': 0,
            }
            for p_date in dates:
                date_category = self.env["delivery.package"].calculate_date_category(p_date)
                if date_category:
                    summaries[agency_id]['total_' + date_category] += 1

        self._prepare_graph_data(summaries)

    def _prepare_graph_data(self, summaries):

        data_category_mapping = {
            'total_before': {'label': _('Before'), 'type': 'past'},
            'total_yesterday': {'label': _('J-1'), 'type': 'past'},
            'total_today': {'label': _('Today'), 'type': 'present'},
            'total_day_1': {'label': _('J + 1'), 'type': 'future'},
            'total_day_2': {'label': _('J + 2'), 'type': 'future'},
            'total_after': {'label': _('After'), 'type': 'future'},
        }

        for agency in self:
            agency_summary = summaries.get(agency.id)
            empty = all(agency_summary[k] == 0 for k in data_category_mapping)
            graph_data = [{
                'key': _('Sample data') if empty else agency_summary['data_series_name'],
                'agency_id': None if empty else agency.id,
                'values': [
                    dict(v, value=agency_summary[k], type='sample' if empty else v['type'])
                    for k, v in data_category_mapping.items()
                ],
            }]
            agency.kanban_dashboard_graph = json.dumps(graph_data)

    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        context = self.env.context.copy()
        context.update(literal_eval(action['context']))
        action['context'] = context
        return action

    def action_view_all_package(self):
        return self._get_action('ateroo_base.action_delivery_package')

    def action_view_new_package(self):
        return self.with_context(search_default_new_package=True)._get_action('ateroo_base.action_delivery_package')

    def action_view_delivery_package(self):
        return self.with_context(search_default_ready_delivery=True)._get_action('ateroo_base.action_delivery_package')

    def action_view_package_new(self):
         return {
                 'name': _('New package'),
                 'view_mode': 'list,form',
                 'res_model': 'delivery.package',
                 'domain': [('state', 'in', ['draft', 'reception'])],
                 'type': 'ir.actions.act_window',
             }

    def action_view_package_deliver(self):
        return {
            'name': _('New package'),
            'view_mode': 'list,form',
            'res_model': 'delivery.package',
            'domain': [('state', 'in', ['ready', 'planned'])],
            'type': 'ir.actions.act_window',

        }