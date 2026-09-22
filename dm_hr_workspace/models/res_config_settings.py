# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_workspace_name = fields.Char(
        related='company_id.hr_workspace_name',
        readonly=False,
    )
    hr_workspace_attendance_enabled = fields.Boolean(
        related='company_id.hr_workspace_attendance_enabled',
        readonly=False,
    )
    hr_workspace_gps_required = fields.Boolean(
        related='company_id.hr_workspace_gps_required', readonly=False,
    )
    hr_workspace_gps_max_accuracy = fields.Float(
        related='company_id.hr_workspace_gps_max_accuracy', readonly=False,
    )
    hr_workspace_geofence_required = fields.Boolean(
        related='company_id.hr_workspace_geofence_required', readonly=False,
    )
    hr_workspace_self_service_enabled = fields.Boolean(
        related='company_id.hr_workspace_self_service_enabled',
        readonly=False,
    )
    hr_workspace_compliance_enabled = fields.Boolean(
        related='company_id.hr_workspace_compliance_enabled',
        readonly=False,
    )
