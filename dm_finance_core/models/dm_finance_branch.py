# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmFinanceBranch(models.Model):
    _name = 'dm.finance.branch'
    _description = 'Finance Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'company_id, sequence, code, name'
    _check_company_auto = True

    name = fields.Char(string='Branch Name', required=True, translate=True, tracking=True)
    code = fields.Char(string='Branch Code', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    manager_id = fields.Many2one(
        'res.users',
        string='Branch Manager',
        domain="[('share', '=', False)]",
        tracking=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        check_company=True,
        help='Optional analytic account used to map this branch into analytic reporting.',
    )
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.company.country_id)
    note = fields.Text(string='Notes')

    _sql_constraints = [
        (
            'dm_finance_branch_code_company_uniq',
            'unique(code, company_id)',
            'Branch code must be unique per company.',
        ),
    ]

    @api.constrains('code')
    def _check_code(self):
        for branch in self:
            if not branch.code or not branch.code.strip():
                raise ValidationError(_('Branch code is required.'))

    @api.constrains('manager_id', 'company_id')
    def _check_manager_company(self):
        for branch in self:
            if branch.manager_id and branch.company_id not in branch.manager_id.company_ids:
                raise ValidationError(_('The branch manager must be allowed on the branch company.'))

    def name_get(self):
        return [(branch.id, '[%s] %s' % (branch.code, branch.name)) for branch in self]
