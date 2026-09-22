# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DmHrOrgChartController(http.Controller):

    @http.route('/dm_hr_core/org_chart/data', type='json', auth='user')
    def org_chart_data(self, company_id=False, branch_id=False, search=False):
        return request.env['dm.hr.branch'].dm_org_chart_data(
            company_id=company_id,
            branch_id=branch_id,
            search=search,
        )
