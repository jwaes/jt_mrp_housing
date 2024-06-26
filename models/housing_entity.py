# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HousingEntity(models.Model):
    _name = 'jt.housing.entity'
    _description = 'Housing entity'
    _order = 'priority desc, sequence, name'
    _check_company_auto = True  
    _inherit = 'mail.thread'

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite'),
    ], default='0', string="Favorite")

    code = fields.Char('Code', required=True, tracking=True, copy=False, default=lambda self: _('New'))
    sequence = fields.Integer(
        'Sequence', default=1,
        help="Gives the sequence order when displaying.")
    description = fields.Char('Description', tracking=True)
    name = fields.Char(compute='_compute_composite_code', string='Entity code', store=True)

    housing_project_id = fields.Many2one('jt.housing.project', string='Housing project', required=True)
    batch_id = fields.Many2one('jt.housing.batch', string='Batch', copy=False, domain="[('housing_project_id', '=', project_id)]")
    planned_delivery_date = fields.Date('Planned date', related="batch_id.planned_delivery_date", readonly=True)

    bom_line_ids = fields.One2many('jt.housing.bom.line', 'entity_id', 'BoM Lines', copy=True, tracking=True)

    state = fields.Selection(related='batch_id.state')

    readonly_state = fields.Boolean(compute='_compute_readonly_state', string='readonly_state')

    bottles = fields.Integer(compute='_compute_bottles', string='Bottles', store=True)
    
    @api.depends('bom_line_ids', 'bom_line_ids.product_id', 'bom_line_ids.product_qty')
    def _compute_bottles(self):
        for entity in self:
            bottles = 0
            for bom_line in entity.bom_line_ids:
                if bom_line.product_id.bottle_equivalent > 0.0:
                    bom_line_bottles = bom_line.product_id.bottle_equivalent * bom_line.product_qty
                    bottles += bom_line_bottles
            entity.bottles = bottles
    
    
    @api.depends('batch_id', 'batch_id.readonly_state')
    def _compute_readonly_state(self):    
        for he in self:
            he.readonly_state = False
            if he.batch_id.readonly_state:
                he.readonly_state = True

    _sql_constraints = [
        ('unique_entity', 'UNIQUE(name)', 'The code must be unique for this project'),
    ]
    
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = vals.get('code')
        return super().create(vals)


    @api.depends('code','housing_project_id.composite_code')
    def _compute_composite_code(self):        
        for he in self:
            if he.housing_project_id.composite_code and he.code:
                he.name = he.housing_project_id.composite_code + "/" + re.sub(r'[^A-Z0-9\.\-]*', '', he.code.upper())
            else:
                he.name = "#/#/#"


class HousingEntityBomLine(models.Model):
    _name = 'jt.housing.bom.line'
    _description = 'Housing entity BoM line'
    _order = 'sequence, id'
    _check_company_auto = True

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    sequence = fields.Integer(
        'Sequence', default=1,
        help="Gives the sequence order when displaying.")     
    product_id = fields.Many2one('product.product', 'Component', required=True)
    product_qty = fields.Float(
        'Quantity', default=1.0,
        digits='Product Unit of Measure', required=True)
    entity_id = fields.Many2one(
        'jt.housing.entity', 'Entity',
        index=True, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        related="product_id.uom_id",)        