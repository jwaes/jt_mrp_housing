# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class HousingProject(models.Model):
    _name = 'jt.housing.project'
    _description = 'Housing project'
    _order = 'priority desc, sequence, code'
    _check_company_auto = True  
    _inherit = 'mail.thread'  

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite'),
    ], default='0', string="Favorite")

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Sequence')
    name = fields.Char('Project name', required=True, translate=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    reference = fields.Char('Reference', tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    incoterm_id = fields.Many2one(
        'account.incoterms', 'Incoterm', required=True,
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        compute='_compute_user_id',
        store=True, readonly=False, index=True,
        tracking=2,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ))

    responsibles_ids = fields.Many2many('res.partner', string='Responsibles', tracking=True, domain="[('parent_id','=', partner_id)]")
    default_delivery_partner_id = fields.Many2one('res.partner', string='Delivery address', required=True, tracking=True, domain="[('parent_id','=', partner_id)]")
    comment = fields.Text('Comment')

    composite_code = fields.Char(compute='_compute_composite_code', string='Project code', store=True)

    entity_ids = fields.One2many('jt.housing.entity', 'project_id', string='Entities')
    entity_count = fields.Integer(compute='_compute_entity_count', string='Entity count')

    batch_ids = fields.One2many('jt.housing.batch', 'project_id', string='Batches')
    batch_count = fields.Integer(compute='_compute_batch_count', string='Batch count')
    
    quotation_count = fields.Integer(compute='_compute_sale_count', string="Number of Quotations")
    sale_order_count = fields.Integer(compute='_compute_sale_count', string="Number of Sale Orders")

    _sql_constraints = [
        ('unique_entity', 'UNIQUE(code)', 'The code must be unique for this project'),
    ]
    

    def _get_sale_order_domain(self):
        return [('state', 'not in', ('draft', 'sent', 'cancel'))]

    def _get_quotation_domain(self):
        return [('state', 'in', ('draft', 'sent'))]        

    @api.depends('batch_ids.order_ids.state', 'batch_ids.order_ids.date_order', 'batch_ids.order_ids.company_id')
    def _compute_sale_count(self):
        for project in self:
            orders = self.env['sale.order'].search([('housing_batch_id', 'in', project.batch_ids.ids)])
            project.sale_order_count = len(orders.filtered_domain(self._get_sale_order_domain()))
            project.quotation_count = len(orders.filtered_domain(self._get_quotation_domain()))

    @api.model_create_multi
    def create(self, vals_list):
        projects = super(HousingProject, self).create(vals_list)
        projects._create_analytic_account()
        return projects

    @api.depends('partner_id')
    def _compute_user_id(self):
        for project in self:
            if not project.user_id:
                project.user_id = project.partner_id.user_id or project.partner_id.commercial_partner_id.user_id or self.env.user

    @api.depends('batch_ids', 'batch_ids.entity_ids')
    def _compute_batch_count(self):
        for hp in self:
            hp.batch_count = len(hp.batch_ids)

    @api.depends('entity_ids')
    def _compute_entity_count(self):
        for hp in self:
            hp.entity_count = len(hp.entity_ids)
    
    @api.depends('partner_id.company_code', 'code')
    def _compute_composite_code(self):
        for hp in self:
            if hp.partner_id.company_code and hp.code:
                hp.composite_code = hp.partner_id.company_code + "/" + re.sub('[^A-Z0-9\.\-]*', '', hp.code.upper())
            else:
                hp.composite_code = "#/#"

    def _create_analytic_account(self):
        for hp in self:
            analytic = self.env['account.analytic.account'].create(
                {
                    'name': hp.name,
                    'code': hp.reference,
                    'company_id': hp.company_id.id,
                    # 'plan_id': plan.id,
                    'partner_id': hp.partner_id.id
                }
            )
            hp.analytic_account_id = analytic

    def _prepare_quotation_context(self):
        self.ensure_one()
        quotation_context = {
            'default_partner_id': self.partner_id.id,
            # 'default_campaign_id': self.campaign_id.id,
            # 'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            # 'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_partner_shipping_id' : self.default_delivery_partner_id.id,
            # 'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.user_id:
            quotation_context['default_user_id'] = self.user_id.id
        return quotation_context

    def open_housing_project_entities(self):
        self.ensure_one()
        return {
            'name': 'Entities',
            'res_model': 'jt.housing.entity',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('jt_mrp_housing.housing_entity_view_tree').id, 'tree'), (False, 'form')],
            'context': {
                'default_project_id': self.id,
            },
            'domain': [
                ['project_id', '=', self.id],
            ],            
        }

    def open_housing_project_batches(self):
        self.ensure_one()
        return {
            'name': 'Batches',
            'res_model': 'jt.housing.batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('jt_mrp_housing.housing_batch_view_tree').id, 'tree'), (False, 'form')],
            'context': {
                'default_project_id': self.id,
            },
            'domain': [
                ['project_id', '=', self.id],
            ],            
        }        

    def action_view_sale_quotation(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = self._prepare_quotation_context()
        action['context']['search_default_draft'] = 1
        action['domain'] = expression.AND([[('housing_batch_id', 'in', self.batch_ids.ids)], self._get_quotation_domain()])
        # quotations = self.order_ids.filtered_domain(self._get_quotation_domain())
        # if len(quotations) == 1:
        #     action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        #     action['res_id'] = quotations.id
        return action

    def action_view_sale_order(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_housing_batch_id': self.id,
        }
        action['domain'] = expression.AND([[('housing_batch_id', 'in', self.batch_ids.ids)], self._get_sale_order_domain()])
        # orders = self.order_ids.filtered_domain(self._get_sale_order_domain())
        # if len(orders) == 1:
        #     action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        #     action['res_id'] = orders.id
        return action