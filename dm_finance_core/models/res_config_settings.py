# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dm_finance_require_branch = fields.Boolean(
        string='Require Branch on Finance Documents',
        config_parameter='dm_finance_core.require_branch',
        help='When enabled, finance documents introduced by DM Finance modules must carry a branch.',
    )
    dm_finance_prevent_self_approval = fields.Boolean(
        string='Prevent Self Approval',
        default=True,
        config_parameter='dm_finance_core.prevent_self_approval',
    )
    dm_finance_require_attachment_on_submit = fields.Boolean(
        string='Require Attachments on Submission',
        config_parameter='dm_finance_core.require_attachment_on_submit',
    )
    dm_finance_default_branch_id = fields.Many2one(
        'dm.finance.branch',
        string='Default Finance Branch',
        config_parameter='dm_finance_core.default_branch_id',
    )
