from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    housing_batch_id = fields.Many2one(
        'jt.housing.batch', string='Housing batch', copy=False, tracking=True)

    housing_project_id = fields.Many2one('jt.housing.project', string='Housing Project', copy=False, tracking=True)

    def go_to_housing_batch(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': self.housing_batch_id.id,
                'res_model': 'jt.housing.batch',
                }