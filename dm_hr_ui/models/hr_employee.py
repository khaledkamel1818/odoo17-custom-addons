# -*- coding: utf-8 -*-
from odoo import _, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dm_offboarding_count = fields.Integer(
        string='إنهاء الخدمة',
        compute='_compute_dm_ui_offboarding_count',
    )

    def _compute_dm_ui_offboarding_count(self):
        Offboarding = self.env['dm.hr.offboarding'].sudo()
        for employee in self:
            employee.dm_offboarding_count = Offboarding.search_count([('employee_id', '=', employee.id)])

    def action_open_offboarding_requests(self):
        self.ensure_one()
        return {
            'name': _('إنهاء الخدمة وإخلاء الطرف'),
            'type': 'ir.actions.act_window',
            'res_model': 'dm.hr.offboarding',
            'view_mode': 'kanban,tree,form,activity',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
