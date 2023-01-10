# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)


# READONLY_FIELD_STATES = {
#     state: [('readonly', True)]
#     for state in {'quotation', 'sale', 'done', 'cancel'}
# }

class HousingBatch(models.Model):
    _name = 'jt.housing.batch'
    _description = 'Housing batch'
    _order = 'planned_delivery_date desc, name'
    _check_company_auto = True  
    _inherit = 'mail.thread'

    name = fields.Char('Batch name', required=True, readonly=True, index=True, default=lambda self: _('New'))
    description = fields.Char('Description')
    planned_delivery_date = fields.Date('Planned delivery date', tracking=True)

    color = fields.Integer('color')

    housing_project_id = fields.Many2one('jt.housing.project', string='Housing project', readonly=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', related='housing_project_id.partner_id')
    entity_ids = fields.One2many('jt.housing.entity', 'batch_id', string='Entities', tracking=True, domain="[('housing_project_id', '=', housing_project_id)]") 
    entity_count = fields.Char(compute='_compute_entity_count', string='Entity Count')

    order_ids = fields.One2many('sale.order', 'housing_batch_id', string='Orders')
    quotation_count = fields.Integer(compute='_compute_sale_count', string="Number of Quotations")
    sale_order_count = fields.Integer(compute='_compute_sale_count', string="Number of Sale Orders")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('sale', 'Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, compute='_get_batch_status', store=True, copy=False, index=True, tracking=3)
    
    readonly_state = fields.Char(compute='_compute_readonly_state', string='Readonly State')
    
    @api.depends('state')
    def _compute_readonly_state(self):
        for hb in self:
            hb.readonly_state = False
            if hb.state in ['quotation', 'sale', 'done', 'cancel']:
                hb.readonly_state = True

    @api.depends('order_ids.state')
    def _get_batch_status(self):
        self.ensure_one()
        self.state = 'draft'
        if self.quotation_count > 0:
            self.state = 'quotation'
        if self.sale_order_count > 0:
            if self.sale_order_count != 1:
                _logger.warn("more than one sale order ....")
                return
            sale_orders = self.order_ids.filtered_domain(self.housing_project_id._get_sale_order_domain())
            _logger.info("state found to be %s", sale_orders[0].state)
            self.state = sale_orders[0].state


    @api.depends('entity_ids')
    def _compute_entity_count(self):
        for hb in self:
            hb.entity_count = len(hb.entity_ids)

    @api.depends('order_ids.state', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_count(self):
        for batch in self:
            sale_orders = batch.order_ids.filtered_domain(batch.housing_project_id._get_sale_order_domain())
            batch.sale_order_count = len(sale_orders)
            batch.quotation_count = len(batch.order_ids.filtered_domain(batch.housing_project_id._get_quotation_domain()))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            vals['name'] = self.env['ir.sequence'].next_by_code('jt.housing.batch', sequence_date=seq_date) or _('New')
        result = super(HousingBatch, self).create(vals)
        return result

    def open_housing_batch_entities(self):
        self.ensure_one()
        return {
            'name': 'Entities',
            'res_model': 'jt.housing.entity',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('jt_mrp_housing.housing_entity_view_tree').id, 'tree'), (False, 'form')],
            'context': {
                'default_housing_project_id': self.housing_project_id.id,
                'default_batch_id': self.id,
            },
            'domain': [
                ['housing_project_id', '=', self.housing_project_id.id],
                ['batch_id', '=', self.id]
            ],            
        }

    def action_create_quotation(self):
        # action = self.env["ir.actions.actions"]._for_xml_id("jt_mrp_housing.sale_action_quotations_new")
        # action['context'] = self._prepare_quotation_context()

        lines = self.env['jt.housing.bom.line'].search([('entity_id', 'in', self.entity_ids.ids)])

        if not lines:
            return None

        sale_order_vals = {
            'name': self.env['ir.sequence'].next_by_code('sale.order'),
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'company_id': self.housing_project_id.company_id.id or self.env.company.id,
            'client_order_ref': ("%s: %s" % (self.housing_project_id.name, self.name)),
            'partner_shipping_id': self.housing_project_id.default_delivery_partner_id.id,
            'analytic_account_id': self.housing_project_id.analytic_account_id.id,
            'housing_batch_id': self.id,
            'incoterm': self.housing_project_id.incoterm_id.id,
            'commitment_date': self.planned_delivery_date,
        }    

        sale_order = self.env["sale.order"].create(sale_order_vals)

        products = lines.mapped('product_id')
        for product in products:            
            qty = sum(lines.search([('product_id.id', '=', product.id)]).mapped('product_qty'))
            _logger.info("product %s needs %s in total", product.name, qty)
            order_line_vals = {
                'name': product.display_name,
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': qty,
            }
            order_line = self.env["sale.order.line"].create(order_line_vals)

        view = self.env.ref("sale.view_order_form")

        return {
            "name": "New Quotation",
            "view_mode": "form",
            "view_id": view.id,
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
            "res_id": sale_order.id,
            "context": self.env.context,
        }    


    # def merge_duplicate_product_lines(self, res):
    #     for line in res.order_line:
    #         if line.id in res.order_line.ids:
    #             line_ids = res.order_line.filtered(lambda m: m.product_id.id == line.product_id.id)
    #             quantity = 0
    #             for qty in line_ids:
    #                 quantity += qty.product_uom_qty
    #                 line_ids[0].write({'product_uom_qty': quantity, 'order_id': line_ids[0].order_id.id})
    #                 line_ids[1:].unlink()

    def _prepare_quotation_context(self):
        self.ensure_one()
        quotation_context = self.housing_project_id._prepare_quotation_context()
        quotation_context['default_origin'] = self.name
        quotation_context['default_housing_batch_id'] = self.id
        return quotation_context

    def action_view_sale_quotation(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = self.housing_project_id._prepare_quotation_context()
        action['context']['search_default_draft'] = 1
        action['domain'] = expression.AND([[('housing_batch_id', '=', self.id)], self.housing_project_id._get_quotation_domain()])
        quotations = self.order_ids.filtered_domain(self.housing_project_id._get_quotation_domain())
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    def action_view_sale_order(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['context'] = {
            'search_default_partner_id': self.housing_project_id.partner_id.id,
            'default_partner_id': self.housing_project_id.partner_id.id,
            'default_housing_batch_id': self.id,
        }
        action['domain'] = expression.AND([[('housing_batch_id', '=', self.id)], self.housing_project_id._get_sale_order_domain()])
        orders = self.order_ids.filtered_domain(self.housing_project_id._get_sale_order_domain())
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action           