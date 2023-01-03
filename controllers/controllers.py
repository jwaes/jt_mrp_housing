# -*- coding: utf-8 -*-
# from odoo import http


# class JtMrpHousing(http.Controller):
#     @http.route('/jt_mrp_housing/jt_mrp_housing', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jt_mrp_housing/jt_mrp_housing/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jt_mrp_housing.listing', {
#             'root': '/jt_mrp_housing/jt_mrp_housing',
#             'objects': http.request.env['jt_mrp_housing.jt_mrp_housing'].search([]),
#         })

#     @http.route('/jt_mrp_housing/jt_mrp_housing/objects/<model("jt_mrp_housing.jt_mrp_housing"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jt_mrp_housing.object', {
#             'object': obj
#         })
