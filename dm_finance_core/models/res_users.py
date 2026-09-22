# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    dm_finance_branch_ids = fields.Many2many(
        'dm.finance.branch',
        'dm_finance_branch_res_users_rel',
        'user_id',
        'branch_id',
        string='Allowed Finance Branches',
        help='Branches this user may access for DM Finance documents.',
    )
    dm_finance_default_branch_id = fields.Many2one(
        'dm.finance.branch',
        string='Default Finance Branch',
    )

    @api.constrains('dm_finance_default_branch_id', 'dm_finance_branch_ids', 'company_ids')
    def _check_dm_finance_default_branch(self):
        for user in self:
            branch = user.dm_finance_default_branch_id
            if not branch:
                continue
            if branch not in user.dm_finance_branch_ids:
                raise ValidationError('Default finance branch must be one of the allowed finance branches.')
            if branch.company_id not in user.company_ids:
                raise ValidationError('Default finance branch company must be allowed for the user.')
