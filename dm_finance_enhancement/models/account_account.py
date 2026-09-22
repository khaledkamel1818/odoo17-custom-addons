# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    dm_parent_account_id = fields.Many2one(
        'account.account',
        string='Parent Account',
        index=True,
        tracking=True,
        domain="[('company_id', '=', company_id), ('id', '!=', id)]",
        help='Optional parent account used to render a professional hierarchical chart of accounts.',
    )
    dm_child_account_ids = fields.One2many('account.account', 'dm_parent_account_id', string='Child Accounts')
    dm_account_level = fields.Integer(string='Account Level', compute='_compute_dm_hierarchy', store=True)
    dm_account_group = fields.Selection(
        selection=[
            ('asset', 'Assets'),
            ('liability', 'Liabilities'),
            ('equity', 'Equity'),
            ('income', 'Revenue'),
            ('expense', 'Expenses'),
            ('off_balance', 'Off Balance'),
        ],
        string='Financial Category',
        compute='_compute_dm_hierarchy',
        store=True,
        index=True,
    )
    dm_current_debit = fields.Monetary(
        string='Debit',
        compute='_compute_dm_account_balances',
        currency_field='company_currency_id',
    )
    dm_current_credit = fields.Monetary(
        string='Credit',
        compute='_compute_dm_account_balances',
        currency_field='company_currency_id',
    )
    dm_closing_balance = fields.Monetary(
        string='Closing Balance',
        compute='_compute_dm_account_balances',
        currency_field='company_currency_id',
    )

    @api.depends('dm_parent_account_id', 'account_type', 'internal_group')
    def _compute_dm_hierarchy(self):
        for account in self:
            level = 0
            parent = account.dm_parent_account_id
            visited = set()
            while parent and parent.id not in visited and level < 20:
                visited.add(parent.id)
                level += 1
                parent = parent.dm_parent_account_id
            account.dm_account_level = level
            if account.internal_group == 'income':
                account.dm_account_group = 'income'
            elif account.internal_group in ('asset', 'liability', 'equity', 'expense', 'off_balance'):
                account.dm_account_group = account.internal_group
            else:
                account.dm_account_group = False

    def _compute_dm_account_balances(self):
        MoveLine = self.env['account.move.line']
        for account in self:
            domain = [
                ('account_id', '=', account.id),
                ('company_id', '=', account.company_id.id),
                ('parent_state', '=', 'posted'),
            ]
            grouped = MoveLine.read_group(domain, ['debit:sum', 'credit:sum', 'balance:sum'], [])
            totals = grouped[0] if grouped else {}
            account.dm_current_debit = totals.get('debit', 0.0)
            account.dm_current_credit = totals.get('credit', 0.0)
            account.dm_closing_balance = totals.get('balance', 0.0)

