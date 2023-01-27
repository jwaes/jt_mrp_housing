from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager

class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        HousingProject = request.env['jt.housing.project']

        if 'housing_project_count' in counters:
            values['housing_project_count'] = HousingProject.search_count(self._prepare_housing_projects_domain(partner)) \
                if HousingProject.check_access_rights('read', raise_exception=False) else 0
        # if 'order_count' in counters:
        #     values['order_count'] = SaleOrder.search_count(self._prepare_orders_domain(partner)) \
        #         if SaleOrder.check_access_rights('read', raise_exception=False) else 0

        return values

    def _prepare_housing_projects_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        ]    

    @http.route(['/my/housing/projects', '/my/housing/projects/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_housing_projects(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        HousingProject = request.env['jt.housing.project']

        domain = self._prepare_housing_projects_domain(partner)

        # count for pager
        housing_projects_count = HousingProject.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/housing/projects",
            total=housing_projects_count,
            page=page,
            step=self._items_per_page
        )        

        housing_projects = HousingProject.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_housing_projects_history'] = housing_projects.ids[:100]
        # request.session['my_quotations_history'] = quotations.ids[:100]        
        
        values.update({
            'housing_projects': housing_projects,
            'page_name': 'housing_projects',
            'pager': pager,
            'default_url': '/my/housing/projects',
            # 'searchbar_sortings': searchbar_sortings,
            # 'sortby': sortby,
        })
        return request.render("jt_mrp_housing.portal_my_housing_projects", values)

    @http.route(['/my/housing/project/<int:housing_project_id>'], type='http', auth="user", website=True)
    def portal_my_housing_project_page(self, housing_project_id, report_type=None, message=False, download=False, **kw):
        partner = request.env.user.partner_id
        HousingProject = request.env['jt.housing.project']

        housing_project = HousingProject.browse(housing_project_id)

        values = self._prepare_portal_layout_values()
        values.update({
            'hp': housing_project,
            'page_name': 'housing_projects',
            'default_url': '/my/housing/projects',
        })
        history = request.session.get('my_housing_projects_history', [])
        values.update(get_records_pager(history, housing_project))
        return request.render("jt_mrp_housing.portal_my_housing_project", values)


    @http.route(['/my/housing/project/<int:housing_project_id>/entities', '/my/housing/project/<int:housing_project_id>/entities/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_housing_project_entities(self, housing_project_id, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        HousingProject = request.env['jt.housing.project']
        housing_project = HousingProject.browse(housing_project_id)

        values.update({
            'hp': housing_project,
            'page_name': 'housing_project_entities',
            'default_url': '/my/housing/projects',

        })
        return request.render("jt_mrp_housing.portal_my_housing_project_entities", values)        