from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    company_code = fields.Char('Short code')