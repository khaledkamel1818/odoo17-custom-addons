# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class DmFinanceAnnualClosing(models.Model):
    _name = 'dm.finance.annual.closing'
    _description = 'Annual Financial Closing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_to desc, id desc'
    _check_company_auto = True

    name = fields.Char(string='Reference', required=True, default=lambda self: _('New'), tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='From Date', required=True, tracking=True)
    date_to = fields.Date(string='To Date', required=True, tracking=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Closing Journal',
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
    )
    retained_earnings_account_id = fields.Many2one(
        'account.account',
        string='Retained Earnings Account',
        required=True,
        domain="[('company_id', '=', company_id), ('account_type', 'in', ('equity', 'equity_unaffected'))]",
    )
    move_id = fields.Many2one('account.move', string='Closing Journal Entry', readonly=True, copy=False)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('generated', 'Generated'),
            ('posted', 'Posted'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    net_result = fields.Monetary(string='Net Profit/Loss', currency_field='currency_id', compute='_compute_net_result')
    currency_id = fields.Many2one(related='company_id.currency_id')
    note = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('dm.finance.annual.closing') or _('New')
        return super().create(vals_list)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('From Date must be before To Date.'))

    def _compute_net_result(self):
        for rec in self:
            rec.net_result = rec._get_income_expense_balance()

    def _get_income_expense_balance(self):
        self.ensure_one()
        grouped = self.env['account.move.line'].read_group([
            ('company_id', '=', self.company_id.id),
            ('parent_state', '=', 'posted'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('account_id.internal_group', 'in', ('income', 'expense')),
        ], ['balance:sum'], [])
        balance = grouped[0].get('balance', 0.0) if grouped else 0.0
        return -balance

    def _check_finance_manager(self):
        """Button visibility is not an RPC security boundary."""
        if not self.env.user.has_group('dm_finance_enhancement.group_finance_manager'):
            raise AccessError(_('Only finance managers can perform annual closing operations.'))

    def action_generate_closing_entry(self):
        self._check_finance_manager()
        for rec in self:
            if rec.move_id:
                raise UserError(_('A closing entry already exists.'))
            grouped = self.env['account.move.line'].read_group([
                ('company_id', '=', rec.company_id.id),
                ('parent_state', '=', 'posted'),
                ('date', '>=', rec.date_from),
                ('date', '<=', rec.date_to),
                ('account_id.internal_group', 'in', ('income', 'expense')),
            ], ['balance:sum'], ['account_id'])
            lines = []
            total_balance = 0.0
            for row in grouped:
                account_id = row['account_id'][0]
                balance = row.get('balance', 0.0)
                if not balance:
                    continue
                total_balance += balance
                lines.append((0, 0, {
                    'name': _('Annual closing reversal'),
                    'account_id': account_id,
                    'debit': balance < 0 and abs(balance) or 0.0,
                    'credit': balance > 0 and balance or 0.0,
                }))
            if not lines:
                raise UserError(_('No income or expense balances were found for this period.'))
            lines.append((0, 0, {
                'name': _('Transfer to retained earnings'),
                'account_id': rec.retained_earnings_account_id.id,
                'debit': total_balance > 0 and total_balance or 0.0,
                'credit': total_balance < 0 and abs(total_balance) or 0.0,
            }))
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': rec.date_to,
                'journal_id': rec.journal_id.id,
                'company_id': rec.company_id.id,
                'ref': rec.name,
                'line_ids': lines,
            })
            rec.write({'move_id': move.id, 'state': 'generated'})
            rec.message_post(body=_('Annual closing entry generated.'))
            self.env['dm.finance.audit.log'].log_event('annual_closing', rec.name, rec, _('Annual closing entry generated.'))
        return True

    def action_post_closing_entry(self):
        self._check_finance_manager()
        for rec in self:
            if not rec.move_id:
                raise UserError(_('Generate the closing entry first.'))
            rec.move_id.action_post()
            rec.state = 'posted'
            rec.message_post(body=_('Annual closing entry posted.'))
            self.env['dm.finance.audit.log'].log_event('annual_closing', rec.name, rec, _('Annual closing entry posted.'))
        return True

    def action_apply_lock_date(self):
        self._check_finance_manager()
        for rec in self:
            if not hasattr(rec.company_id, 'fiscalyear_lock_date'):
                raise UserError(_('Fiscal year lock date is not available in this database.'))
            rec.company_id.sudo().fiscalyear_lock_date = rec.date_to
            rec.message_post(body=_('Fiscal year lock date applied: %s') % rec.date_to)
        return True

    def action_cancel(self):
        self._check_finance_manager()
        for rec in self:
            if rec.move_id and rec.move_id.state == 'posted':
                raise UserError(_('Cancel or reverse the posted journal entry before cancelling this closing.'))
            rec.state = 'cancelled'
        return True
