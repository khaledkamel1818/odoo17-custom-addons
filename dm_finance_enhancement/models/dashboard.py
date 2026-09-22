# -*- coding: utf-8 -*-

from datetime import date

from odoo import api, fields, models


class DmFinanceEnhancementDashboard(models.AbstractModel):
    _name = 'dm.finance.enhancement.dashboard'
    _description = 'DM Finance Enhancement Dashboard'

    @api.model
    def _date_domain(self, date_from=None, date_to=None):
        domain = []
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        return domain

    @api.model
    def _sum_move_lines(self, domain, fields_to_sum=None):
        fields_to_sum = fields_to_sum or ['debit:sum', 'credit:sum', 'balance:sum']
        result = self.env['account.move.line'].read_group(domain, fields_to_sum, [])
        return result[0] if result else {}

    @api.model
    def get_dashboard_data(self, filters=None):
        filters = filters or {}
        company = self.env['res.company'].browse(filters.get('company_id')) if filters.get('company_id') else self.env.company
        today = fields.Date.context_today(self)
        fiscal_start = date(today.year, 1, 1).isoformat()
        date_from = filters.get('date_from') or fiscal_start
        date_to = filters.get('date_to') or today.isoformat()

        base_domain = [
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
        ] + self._date_domain(date_from, date_to)
        MoveLine = self.env['account.move.line']

        cash = self._sum_move_lines(base_domain + [('account_id.account_type', '=', 'asset_cash')])
        receivable = self._sum_move_lines(base_domain + [('account_id.account_type', '=', 'asset_receivable')])
        payable = self._sum_move_lines(base_domain + [('account_id.account_type', '=', 'liability_payable')])
        revenue = self._sum_move_lines(base_domain + [('account_id.internal_group', '=', 'income')])
        expense = self._sum_move_lines(base_domain + [('account_id.internal_group', '=', 'expense')])
        tax = self._sum_move_lines(base_domain + [('tax_line_id', '!=', False)])

        overdue_receivable = self._sum_move_lines([
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('date_maturity', '<', today),
            ('amount_residual', '!=', 0.0),
        ], ['amount_residual:sum'])

        bank_journals = self.env['account.journal'].search([
            ('company_id', '=', company.id),
            ('type', 'in', ['bank', 'cash']),
        ])
        bank_cards = []
        for journal in bank_journals:
            account = journal.default_account_id
            balance = 0.0
            if account:
                data = self._sum_move_lines([
                    ('company_id', '=', company.id),
                    ('parent_state', '=', 'posted'),
                    ('account_id', '=', account.id),
                ])
                balance = data.get('balance', 0.0)
            bank_cards.append({
                'id': journal.id,
                'name': journal.name,
                'type': journal.type,
                'balance': balance,
                'currency': company.currency_id.symbol or company.currency_id.name,
            })

        recent_moves = self.env['account.move'].search_read(
            [('company_id', '=', company.id), ('state', '=', 'posted')],
            ['name', 'date', 'amount_total_signed', 'move_type'],
            limit=6,
            order='date desc, id desc',
        )

        return {
            'company': {'id': company.id, 'name': company.name},
            'period': {'date_from': date_from, 'date_to': date_to},
            'currency': company.currency_id.symbol or company.currency_id.name,
            'cards': {
                'cash': cash.get('balance', 0.0),
                'revenue': abs(revenue.get('balance', 0.0)),
                'expense': expense.get('balance', 0.0),
                'net_profit': abs(revenue.get('balance', 0.0)) - expense.get('balance', 0.0),
                'receivable': receivable.get('balance', 0.0),
                'payable': abs(payable.get('balance', 0.0)),
                'tax_due': abs(tax.get('balance', 0.0)),
                'overdue_receivable': overdue_receivable.get('amount_residual', 0.0),
                'journal_items': MoveLine.search_count(base_domain),
            },
            'bank_cards': bank_cards,
            'recent_moves': recent_moves,
        }

