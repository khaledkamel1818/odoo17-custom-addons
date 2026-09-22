# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    hr_workspace_name = fields.Char(
        string='اسم منصة الموارد البشرية',
        default='منصة الموارد البشرية',
        translate=True,
    )
    hr_workspace_attendance_enabled = fields.Boolean(
        string='تفعيل الحضور من المنصة',
        default=True,
    )
    hr_workspace_gps_required = fields.Boolean(
        string='اشتراط GPS للحضور والانصراف', default=True,
    )
    hr_workspace_gps_max_accuracy = fields.Float(
        string='أقصى هامش لدقة GPS (متر)', default=150.0,
    )
    hr_workspace_geofence_required = fields.Boolean(
        string='اشتراط البصمة داخل موقع معتمد', default=True,
    )
    hr_workspace_self_service_enabled = fields.Boolean(
        string='تفعيل الخدمة الذاتية',
        default=True,
    )
    hr_workspace_compliance_enabled = fields.Boolean(
        string='إظهار جاهزية ملف الموظف',
        default=True,
    )
