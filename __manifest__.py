# -*- coding: utf-8 -*-
{
    'name': "jt_mrp_housing",

    'summary': "Housing projects",
    'application': True,

    'description': "",

    'author': "jaco tech",
    'website': "https://jaco.tech",
    "license": "AGPL-3",


    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.23',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','sale','sale_management','sale_stock','account_accountant','analytic','portal', 'jt_product_repeat'],

    # always loaded
    'data': [
        'security/housing_security.xml',
        'security/ir.model.access.csv',
        'report/housing_report.xml',
        'report/report_deliveryslip.xml',
        'report/sale_report_templates.xml',
        'data/ir_sequence_data.xml',
        'views/housing_batch.xml',
        'views/housing_entity.xml',
        'views/housing_project.xml',
        'views/portal_templates.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/sale_portal_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
