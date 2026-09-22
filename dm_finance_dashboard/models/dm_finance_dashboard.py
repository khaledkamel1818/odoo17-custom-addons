# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, api, fields, models


class DmFinanceDashboard(models.AbstractModel):
    _name = 'dm.finance.dashboard'
    _description = 'لوحة الحسابات الاحترافية'

    @api.model
    def _company_domain(self, field='company_id'):
        return [(field, 'in', self.env.companies.ids)]

    @api.model
    def _format_money(self, amount, currency=None):
        currency = currency or self.env.company.currency_id
        return '%s %s' % ('{:,.2f}'.format(amount or 0.0), currency.symbol or currency.name)

    @api.model
    def _selection_label(self, model_name, field_name, value):
        if not value:
            return ''
        field = self.env[model_name]._fields[field_name]
        return dict(field._description_selection(self.env)).get(value, value)

    @api.model
    def _normalize_act_window(self, action):
        if not action:
            return action
        if action.get('type') == 'ir.actions.act_window' and not action.get('views'):
            view_modes = (action.get('view_mode') or 'tree,form').split(',')
            action['views'] = [(False, mode.strip()) for mode in view_modes if mode.strip()]
        action.setdefault('context', {})
        action.setdefault('target', 'current')
        return action

    @api.model
    def _action_from_xmlid(self, xmlid):
        return self._normalize_act_window(self.env['ir.actions.actions'].sudo()._for_xml_id(xmlid))

    @api.model
    def _sum_moves(self, domain, field_name='amount_residual_signed'):
        result = self.env['account.move'].sudo().read_group(domain, [field_name + ':sum'], [])
        return round(result[0].get(field_name, 0.0) or 0.0, 2) if result else 0.0

    @api.model
    def _sum_move_lines(self, domain):
        result = self.env['account.move.line'].sudo().read_group(domain, ['balance:sum'], [])
        return round(result[0].get('balance', 0.0) or 0.0, 2) if result else 0.0

    @api.model
    def _count(self, model, domain):
        return self.env[model].sudo().search_count(domain)

    @api.model
    def _state_tone(self, state):
        if state in ('posted', 'paid', 'in_payment', 'approved'):
            return 'success'
        if state in ('draft', 'not_paid', 'partial'):
            return 'warning'
        if state in ('overdue', 'rejected', 'cancelled'):
            return 'danger'
        if state in ('under_approval',):
            return 'info'
        return 'muted'

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        company = self.env.company
        currency = company.currency_id

        posted_customer_domain = self._company_domain() + [
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
        ]
        posted_vendor_domain = self._company_domain() + [
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
        ]
        open_receivable_domain = posted_customer_domain + [
            ('payment_state', 'in', ['not_paid', 'partial']),
        ]
        open_payable_domain = posted_vendor_domain + [
            ('payment_state', 'in', ['not_paid', 'partial']),
        ]
        overdue_receivable_domain = open_receivable_domain + [
            ('invoice_date_due', '!=', False),
            ('invoice_date_due', '<', today),
        ]
        overdue_payable_domain = open_payable_domain + [
            ('invoice_date_due', '!=', False),
            ('invoice_date_due', '<', today),
        ]
        month_customer_domain = posted_customer_domain + [
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<', next_month),
        ]
        month_vendor_domain = posted_vendor_domain + [
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<', next_month),
        ]
        cash_line_domain = [
            ('parent_state', '=', 'posted'),
            ('company_id', 'in', self.env.companies.ids),
            ('account_id.account_type', '=', 'asset_cash'),
        ]
        voucher_domain = self._company_domain()

        receivables = abs(self._sum_moves(open_receivable_domain))
        payables = abs(self._sum_moves(open_payable_domain))
        overdue_receivables = abs(self._sum_moves(overdue_receivable_domain))
        overdue_payables = abs(self._sum_moves(overdue_payable_domain))
        month_revenue = abs(self._sum_moves(month_customer_domain, 'amount_total_signed'))
        month_bills = abs(self._sum_moves(month_vendor_domain, 'amount_total_signed'))
        cash_balance = self._sum_move_lines(cash_line_domain)

        posted_invoices_count = self._count('account.move', posted_customer_domain)
        posted_bills_count = self._count('account.move', posted_vendor_domain)
        draft_moves_count = self._count('account.move', self._company_domain() + [('state', '=', 'draft')])
        pending_vouchers_count = self._count('dm.finance.voucher', voucher_domain + [('state', '=', 'under_approval')])

        return {
            'user': {
                'name': self.env.user.name,
                'company': company.name,
                'currency': currency.name,
            },
            'period': {
                'today': fields.Date.to_string(today),
                'month_start': fields.Date.to_string(month_start),
            },
            'metrics': [
                {
                    'key': 'cash',
                    'label': _('رصيد النقد والبنوك'),
                    'value': self._format_money(cash_balance, currency),
                    'icon': 'fa-university',
                    'tone': 'teal',
                    'action': 'journals',
                },
                {
                    'key': 'receivables',
                    'label': _('ذمم العملاء المفتوحة'),
                    'value': self._format_money(receivables, currency),
                    'icon': 'fa-arrow-circle-down',
                    'tone': 'blue',
                    'action': 'customer_invoices',
                },
                {
                    'key': 'payables',
                    'label': _('ذمم الموردين المفتوحة'),
                    'value': self._format_money(payables, currency),
                    'icon': 'fa-arrow-circle-up',
                    'tone': 'amber',
                    'action': 'vendor_bills',
                },
                {
                    'key': 'overdue',
                    'label': _('مستحقات متأخرة'),
                    'value': self._format_money(overdue_receivables + overdue_payables, currency),
                    'icon': 'fa-exclamation-triangle',
                    'tone': 'red',
                    'action': 'overdue',
                },
                {
                    'key': 'pending_vouchers',
                    'label': _('سندات بانتظار الاعتماد'),
                    'value': pending_vouchers_count,
                    'icon': 'fa-check-square-o',
                    'tone': 'violet',
                    'action': 'vouchers_pending',
                },
                {
                    'key': 'draft_moves',
                    'label': _('قيود وفواتير غير مرحلة'),
                    'value': draft_moves_count,
                    'icon': 'fa-pencil-square-o',
                    'tone': 'slate',
                    'action': 'journal_entries',
                },
            ],
            'quick_actions': [
                {'key': 'new_customer_invoice', 'label': _('فاتورة عميل'), 'icon': 'fa-file-text-o', 'description': _('إنشاء مطالبة بيع جديدة')},
                {'key': 'new_vendor_bill', 'label': _('فاتورة مورد'), 'icon': 'fa-shopping-bag', 'description': _('تسجيل مصروف أو فاتورة شراء')},
                {'key': 'new_payment_voucher', 'label': _('سند صرف'), 'icon': 'fa-money', 'description': _('طلب صرف مع مسار موافقة')},
                {'key': 'new_receipt_voucher', 'label': _('سند قبض'), 'icon': 'fa-download', 'description': _('تسجيل قبض أو تحصيل')},
            ],
            'cashflow': {
                'month_revenue': self._format_money(month_revenue, currency),
                'month_bills': self._format_money(month_bills, currency),
                'net': self._format_money(month_revenue - month_bills, currency),
                'posted_invoices': posted_invoices_count,
                'posted_bills': posted_bills_count,
            },
            'receivable_health': {
                'open': self._format_money(receivables, currency),
                'overdue': self._format_money(overdue_receivables, currency),
                'open_count': self._count('account.move', open_receivable_domain),
                'overdue_count': self._count('account.move', overdue_receivable_domain),
            },
            'payable_health': {
                'open': self._format_money(payables, currency),
                'overdue': self._format_money(overdue_payables, currency),
                'open_count': self._count('account.move', open_payable_domain),
                'overdue_count': self._count('account.move', overdue_payable_domain),
            },
            'voucher_pipeline': self._get_voucher_pipeline(voucher_domain),
            'recent_invoices': self._get_recent_invoices(),
            'recent_vouchers': self._get_recent_vouchers(voucher_domain),
            'alerts': self._get_alerts(overdue_receivables, overdue_payables, pending_vouchers_count, draft_moves_count, currency),
        }

    @api.model
    def _get_voucher_pipeline(self, base_domain):
        Voucher = self.env['dm.finance.voucher'].sudo()
        states = ['draft', 'under_approval', 'approved', 'posted', 'rejected', 'cancelled']
        return [{
            'state': state,
            'label': self._selection_label('dm.finance.voucher', 'state', state),
            'count': Voucher.search_count(base_domain + [('state', '=', state)]),
            'tone': self._state_tone(state),
        } for state in states]

    @api.model
    def _get_recent_invoices(self):
        moves = self.env['account.move'].sudo().search(self._company_domain() + [
            ('move_type', 'in', ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']),
        ], order='invoice_date desc, id desc', limit=6)
        currency = self.env.company.currency_id
        return [{
            'id': move.id,
            'name': move.name if move.name and move.name != '/' else move.ref or _('بدون رقم'),
            'partner': move.partner_id.name or _('بدون شريك'),
            'date': fields.Date.to_string(move.invoice_date or move.date),
            'due': fields.Date.to_string(move.invoice_date_due) if move.invoice_date_due else '',
            'type': self._selection_label('account.move', 'move_type', move.move_type),
            'amount': self._format_money(abs(move.amount_total_signed), currency),
            'payment_state': self._selection_label('account.move', 'payment_state', move.payment_state),
            'tone': self._state_tone(move.payment_state),
        } for move in moves]

    @api.model
    def _get_recent_vouchers(self, base_domain):
        vouchers = self.env['dm.finance.voucher'].sudo().search(base_domain, order='date desc, id desc', limit=6)
        return [{
            'id': voucher.id,
            'name': voucher.name,
            'date': fields.Date.to_string(voucher.date),
            'partner': voucher.partner_id.name or _('بدون شريك'),
            'type': self._selection_label('dm.finance.voucher', 'voucher_type', voucher.voucher_type),
            'amount': self._format_money(voucher.amount_total, voucher.currency_id),
            'state': self._selection_label('dm.finance.voucher', 'state', voucher.state),
            'tone': self._state_tone(voucher.state),
        } for voucher in vouchers]

    @api.model
    def _get_alerts(self, overdue_receivables, overdue_payables, pending_vouchers_count, draft_moves_count, currency):
        alerts = []
        if overdue_receivables:
            alerts.append({
                'level': 'danger',
                'title': _('تحصيلات متأخرة'),
                'message': _('يوجد ذمم عملاء متأخرة بقيمة %s.') % self._format_money(overdue_receivables, currency),
                'action': 'overdue_receivables',
            })
        if overdue_payables:
            alerts.append({
                'level': 'warning',
                'title': _('مدفوعات مورّدين متأخرة'),
                'message': _('يوجد فواتير موردين متأخرة بقيمة %s.') % self._format_money(overdue_payables, currency),
                'action': 'overdue_payables',
            })
        if pending_vouchers_count:
            alerts.append({
                'level': 'info',
                'title': _('سندات تنتظر الاعتماد'),
                'message': _('%s سند/سندات تحتاج مراجعة واعتماد.') % pending_vouchers_count,
                'action': 'vouchers_pending',
            })
        if draft_moves_count:
            alerts.append({
                'level': 'muted',
                'title': _('مسودات مالية'),
                'message': _('%s قيد/فاتورة ما زالت في المسودة.') % draft_moves_count,
                'action': 'journal_entries',
            })
        return alerts[:5]

    @api.model
    def open_action(self, action_key):
        today = fields.Date.context_today(self)
        company_domain = [('company_id', 'in', self.env.companies.ids)]
        action_map = {
            'customer_invoices': 'account.action_move_out_invoice_type',
            'vendor_bills': 'account.action_move_in_invoice_type',
            'journal_entries': 'account.action_move_journal_line',
            'journals': 'account.action_account_journal_form',
            'payments': 'account.action_account_payments',
            'vouchers': 'dm_finance_voucher.dm_finance_voucher_action',
            'vouchers_pending': 'dm_finance_voucher.dm_finance_voucher_action',
        }
        if action_key in action_map:
            action = self._action_from_xmlid(action_map[action_key])
            if action_key == 'vouchers_pending':
                action['domain'] = company_domain + [('state', '=', 'under_approval')]
            return action
        if action_key in ('overdue', 'overdue_receivables'):
            action = self._action_from_xmlid('account.action_move_out_invoice_type')
            action['domain'] = company_domain + [
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', today),
            ]
            return action
        if action_key == 'overdue_payables':
            action = self._action_from_xmlid('account.action_move_in_invoice_type')
            action['domain'] = company_domain + [
                ('state', '=', 'posted'),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', today),
            ]
            return action
        if action_key == 'new_customer_invoice':
            action = self._action_from_xmlid('account.action_move_out_invoice_type')
            action.update({
                'views': [(False, 'form')],
                'view_mode': 'form',
                'context': {'default_move_type': 'out_invoice'},
            })
            return action
        if action_key == 'new_vendor_bill':
            action = self._action_from_xmlid('account.action_move_in_invoice_type')
            action.update({
                'views': [(False, 'form')],
                'view_mode': 'form',
                'context': {'default_move_type': 'in_invoice'},
            })
            return action
        if action_key in ('new_payment_voucher', 'new_receipt_voucher'):
            voucher_type = 'payment' if action_key == 'new_payment_voucher' else 'receipt'
            return {
                'name': _('سند صرف') if voucher_type == 'payment' else _('سند قبض'),
                'type': 'ir.actions.act_window',
                'res_model': 'dm.finance.voucher',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'target': 'current',
                'context': {'default_voucher_type': voucher_type},
            }
        return False
