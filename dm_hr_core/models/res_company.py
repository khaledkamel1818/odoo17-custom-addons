# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_social_insurance_scheme_id = fields.Many2one(
        'dm.hr.social.insurance.scheme',
        string='نظام التأمينات الاجتماعية الافتراضي',
        ondelete='restrict',
    )
    dm_attendance_late_grace_minutes = fields.Integer(string='فترة السماح للتأخير (دقيقة)', default=15)
    dm_attendance_early_leave_grace_minutes = fields.Integer(string='فترة السماح للخروج المبكر (دقيقة)', default=15)
    dm_attendance_absence_policy = fields.Text(string='سياسة الغياب')
    dm_attendance_block_on_approved_leave = fields.Boolean(
        string='منع تسجيل الحضور أثناء إجازة معتمدة',
        default=True,
    )
    dm_attendance_mobile_enabled = fields.Boolean(string='تفعيل حضور الموبايل', default=True)
    dm_attendance_mobile_correction_enabled = fields.Boolean(string='تفعيل تصحيح الحضور من الموبايل', default=True)
    dm_attendance_manager_notifications = fields.Boolean(string='إشعار المدير بطلبات الاعتماد', default=True)
