# -*- coding: utf-8 -*-

import base64

from odoo import http
from odoo.http import request


class DmFinanceXlsxExportController(http.Controller):

    @http.route('/dm_finance_enhancement/report/xlsx/<int:wizard_id>', type='http', auth='user')
    def export_finance_report_xlsx(self, wizard_id, **kwargs):
        wizard = request.env['dm.finance.report.wizard'].browse(wizard_id).exists()
        if not wizard:
            return request.not_found()
        content = base64.b64decode(wizard._build_xlsx_content())
        filename = '%s.xlsx' % (wizard.report_type or 'finance_report')
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
        ]
        return request.make_response(content, headers)

