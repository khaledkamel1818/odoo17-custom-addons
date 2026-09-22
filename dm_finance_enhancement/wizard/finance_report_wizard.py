# -*- coding: utf-8 -*-

import base64
import io
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmFinanceReportWizard(models.TransientModel):
    _name = 'dm.finance.report.wizard'
    _description = 'Dynamic Finance Report Wizard'

    report_type = fields.Selection(
        selection=[
            ('profit_loss', 'Profit and Loss'),
            ('balance_sheet', 'Balance Sheet'),
            ('trial_balance', 'Trial Balance'),
            ('general_ledger', 'General Ledger'),
            ('partner_ledger', 'Partner Ledger'),
            ('aged_receivable', 'Aged Receivable'),
            ('aged_payable', 'Aged Payable'),
            ('cash_flow', 'Cash Flow'),
            ('tax_report', 'Tax Report'),
            ('vat_return', 'VAT Return'),
            ('zakat_income', 'Zakat and Income Summary'),
            ('bank_reconciliation', 'Bank Reconciliation'),
            ('fixed_assets', 'Fixed Assets'),
            ('annual_closing', 'Annual Closing'),
        ],
        string='Report',
        required=True,
        default='trial_balance',
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(month=1, day=1),
    )
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    branch_id = fields.Many2one('dm.finance.branch', string='Branch', domain="[('company_id', '=', company_id)]")
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    account_ids = fields.Many2many('account.account', string='Accounts')
    partner_ids = fields.Many2many('res.partner', string='Partners')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center')
    hide_zero = fields.Boolean(string='Hide Zero Balance Accounts', default=True)
    comparison_date_from = fields.Date(string='Comparison From')
    comparison_date_to = fields.Date(string='Comparison To')
    line_ids = fields.One2many('dm.finance.report.wizard.line', 'wizard_id', string='Preview Lines')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise ValidationError(_('From Date must be before To Date.'))

    def _base_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('parent_state', '=', 'posted'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.analytic_account_id:
            domain.append(('analytic_distribution', 'ilike', '"%s"' % self.analytic_account_id.id))
        return domain

    def _get_account_group_domain(self):
        mapping = {
            'profit_loss': [('account_id.internal_group', 'in', ('income', 'expense'))],
            'balance_sheet': [('account_id.internal_group', 'in', ('asset', 'liability', 'equity'))],
            'trial_balance': [],
            'general_ledger': [],
            'partner_ledger': [('partner_id', '!=', False)],
            'aged_receivable': [('account_id.account_type', '=', 'asset_receivable')],
            'aged_payable': [('account_id.account_type', '=', 'liability_payable')],
            'cash_flow': [('account_id.account_type', '=', 'asset_cash')],
            'tax_report': [('tax_line_id', '!=', False)],
            'vat_return': [('tax_line_id', '!=', False)],
            'zakat_income': [('account_id.internal_group', 'in', ('income', 'expense'))],
        }
        return mapping.get(self.report_type, [])

    def _get_lines_data(self):
        self.ensure_one()
        if self.report_type == 'fixed_assets':
            assets = self.env['account.asset.asset'].search([
                ('company_id', '=', self.company_id.id),
            ])
            return [{
                'name': asset.name,
                'account_id': asset.category_id.account_asset_id.id if asset.category_id.account_asset_id else False,
                'partner_id': False,
                'debit': asset.value or 0.0,
                'credit': asset.salvage_value or 0.0,
                'balance': asset.value_residual or 0.0,
            } for asset in assets]
        if self.report_type == 'bank_reconciliation':
            reconciliations = self.env['dm.finance.bank.reconciliation'].search([
                ('company_id', '=', self.company_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ])
            return [{
                'name': '%s - %s' % (rec.name, rec.journal_id.name),
                'account_id': rec.journal_id.default_account_id.id if rec.journal_id.default_account_id else False,
                'partner_id': False,
                'debit': rec.matched_count,
                'credit': rec.unmatched_count,
                'balance': rec.line_count,
            } for rec in reconciliations]
        if self.report_type == 'annual_closing':
            closings = self.env['dm.finance.annual.closing'].search([
                ('company_id', '=', self.company_id.id),
                ('date_from', '>=', self.date_from),
                ('date_to', '<=', self.date_to),
            ])
            return [{
                'name': closing.name,
                'account_id': closing.retained_earnings_account_id.id,
                'partner_id': False,
                'debit': closing.net_result > 0 and closing.net_result or 0.0,
                'credit': closing.net_result < 0 and abs(closing.net_result) or 0.0,
                'balance': closing.net_result,
            } for closing in closings]
        domain = self._base_domain() + self._get_account_group_domain()
        groupby = ['account_id']
        if self.report_type in ('partner_ledger', 'aged_receivable', 'aged_payable'):
            groupby = ['partner_id', 'account_id']
        rows = self.env['account.move.line'].read_group(
            domain,
            ['debit:sum', 'credit:sum', 'balance:sum', 'amount_currency:sum'],
            groupby,
            lazy=False,
        )
        lines = []
        for row in rows:
            account = row.get('account_id')
            partner = row.get('partner_id')
            debit = row.get('debit', 0.0)
            credit = row.get('credit', 0.0)
            balance = row.get('balance', 0.0)
            if self.hide_zero and not debit and not credit and not balance:
                continue
            name_parts = []
            if partner:
                name_parts.append(partner[1])
            if account:
                name_parts.append(account[1])
            lines.append({
                'name': ' / '.join(name_parts) or _('Total'),
                'account_id': account and account[0] or False,
                'partner_id': partner and partner[0] or False,
                'debit': debit,
                'credit': credit,
                'balance': balance,
            })
        return lines

    def action_preview(self):
        for wizard in self:
            wizard.line_ids.unlink()
            wizard.line_ids = [(0, 0, line) for line in wizard._get_lines_data()]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print_pdf(self):
        self.ensure_one()
        self.line_ids.unlink()
        self.line_ids = [(0, 0, line) for line in self._get_lines_data()]
        self.env['dm.finance.audit.log'].log_event(
            'report_export',
            dict(self._fields['report_type'].selection).get(self.report_type, self.report_type),
            self,
            _('PDF report generated.'),
        )
        return self.env.ref('dm_finance_enhancement.action_report_dm_finance_dynamic').report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        self.env['dm.finance.audit.log'].log_event(
            'report_export',
            dict(self._fields['report_type'].selection).get(self.report_type, self.report_type),
            self,
            _('XLSX report exported.'),
        )
        return {
            'type': 'ir.actions.act_url',
            'url': '/dm_finance_enhancement/report/xlsx/%s' % self.id,
            'target': 'self',
        }

    def get_report_payload(self):
        self.ensure_one()
        return {
            'wizard': self,
            'report_title': dict(self._fields['report_type'].selection).get(self.report_type, self.report_type),
            'lines': self.line_ids or self.env['dm.finance.report.wizard.line'].create([
                dict(line, wizard_id=self.id) for line in self._get_lines_data()
            ]),
        }

    def _build_xlsx_content(self):
        self.ensure_one()
        try:
            import xlsxwriter
        except Exception as exc:
            raise ValidationError(_('xlsxwriter is required to export Excel files: %s') % exc)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Finance Report')[:31])
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#EAF4F1', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        cell_format = workbook.add_format({'border': 1})
        title = dict(self._fields['report_type'].selection).get(self.report_type, self.report_type)
        sheet.merge_range(0, 0, 0, 4, title, title_format)
        sheet.write(1, 0, _('Company'), header_format)
        sheet.write(1, 1, self.company_id.name, cell_format)
        sheet.write(2, 0, _('Period'), header_format)
        sheet.write(2, 1, '%s - %s' % (self.date_from, self.date_to), cell_format)
        headers = [_('Name'), _('Account'), _('Partner'), _('Debit'), _('Credit'), _('Balance')]
        for col, header in enumerate(headers):
            sheet.write(4, col, header, header_format)
        lines = self.line_ids or self.env['dm.finance.report.wizard.line'].create([
            dict(line, wizard_id=self.id) for line in self._get_lines_data()
        ])
        row_index = 5
        for line in lines:
            sheet.write(row_index, 0, line.name or '', cell_format)
            sheet.write(row_index, 1, line.account_id.display_name if line.account_id else '', cell_format)
            sheet.write(row_index, 2, line.partner_id.display_name if line.partner_id else '', cell_format)
            sheet.write_number(row_index, 3, line.debit, money_format)
            sheet.write_number(row_index, 4, line.credit, money_format)
            sheet.write_number(row_index, 5, line.balance, money_format)
            row_index += 1
        sheet.set_column(0, 2, 28)
        sheet.set_column(3, 5, 16)
        workbook.close()
        return base64.b64encode(output.getvalue())


class DmFinanceReportWizardLine(models.TransientModel):
    _name = 'dm.finance.report.wizard.line'
    _description = 'Dynamic Finance Report Line'

    wizard_id = fields.Many2one('dm.finance.report.wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Name')
    account_id = fields.Many2one('account.account', string='Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    debit = fields.Monetary(string='Debit', currency_field='currency_id')
    credit = fields.Monetary(string='Credit', currency_field='currency_id')
    balance = fields.Monetary(string='Balance', currency_field='currency_id')
    currency_id = fields.Many2one(related='wizard_id.company_id.currency_id')
