# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    social_insurance_scheme_id = fields.Many2one(
        'dm.hr.social.insurance.scheme',
        string='نظام التأمينات الاجتماعية الافتراضي',
        related='company_id.default_social_insurance_scheme_id',
        readonly=False,
        help='النظام المستخدم افتراضياً عند احتساب التأمينات الاجتماعية لفترات الرواتب الجديدة.',
    )
    dm_attendance_late_grace_minutes = fields.Integer(
        related='company_id.dm_attendance_late_grace_minutes', readonly=False,
    )
    dm_attendance_early_leave_grace_minutes = fields.Integer(
        related='company_id.dm_attendance_early_leave_grace_minutes', readonly=False,
    )
    dm_attendance_absence_policy = fields.Text(
        related='company_id.dm_attendance_absence_policy', readonly=False,
    )
    dm_attendance_block_on_approved_leave = fields.Boolean(
        related='company_id.dm_attendance_block_on_approved_leave', readonly=False,
    )
    dm_attendance_mobile_enabled = fields.Boolean(
        related='company_id.dm_attendance_mobile_enabled', readonly=False,
    )
    dm_attendance_mobile_correction_enabled = fields.Boolean(
        related='company_id.dm_attendance_mobile_correction_enabled', readonly=False,
    )
    dm_attendance_manager_notifications = fields.Boolean(
        related='company_id.dm_attendance_manager_notifications', readonly=False,
    )

    def set_values(self):
        # Persist the company-scoped setting explicitly to res.company
        # (multi-company isolated; no global sudo, no config_parameter).
        super().set_values()
        for config in self:
            if config.social_insurance_scheme_id is not None:
                config.company_id.write({
                    'default_social_insurance_scheme_id': config.social_insurance_scheme_id.id,
                })
