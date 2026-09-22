# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DmFinanceVoucher(models.Model):
    _name = 'dm.finance.voucher'
    _description = 'Finance Voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _check_company_auto = True

    name = fields.Char(
        string='Voucher Number',
        default='/',
        copy=False,
        readonly=True,
        tracking=True,
    )
    voucher_type = fields.Selection(
        [
            ('receipt', 'Receipt Voucher'),
            ('payment', 'Payment Voucher'),
            ('transfer', 'Transfer Voucher'),
        ],
        string='Voucher Type',
        required=True,
        default='payment',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('under_approval', 'Under Approval'),
            ('approved', 'Approved'),
            ('posted', 'Posted'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    date = fields.Date(string='Voucher Date', default=fields.Date.context_today, required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
        tracking=True,
    )
    branch_id = fields.Many2one(
        'dm.finance.branch',
        string='Finance Branch',
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        check_company=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        tracking=True,
        help='Customer, vendor, employee contact, or other party related to this voucher.',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]",
        check_company=True,
        tracking=True,
    )
    destination_journal_id = fields.Many2one(
        'account.journal',
        string='Destination Journal',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]",
        check_company=True,
        tracking=True,
        help='Required only for transfer vouchers.',
    )
    amount_total = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_amount_total',
        store=True,
        tracking=True,
    )
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    cheque_number = fields.Char(string='Cheque Number', tracking=True)
    cheque_date = fields.Date(string='Cheque Date', tracking=True)
    bank_reference = fields.Char(string='Bank Reference', tracking=True)
    narration = fields.Text(string='Narration')
    line_ids = fields.One2many(
        'dm.finance.voucher.line',
        'voucher_id',
        string='Voucher Lines',
        copy=True,
    )
    approval_request_id = fields.Many2one(
        'dm.finance.approval.request',
        string='Approval Request',
        readonly=True,
        copy=False,
    )
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True, copy=False)

    _sql_constraints = [
        (
            'dm_finance_voucher_name_company_uniq',
            'unique(name, company_id)',
            'Voucher number must be unique per company.',
        ),
    ]

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        for voucher in self:
            voucher.amount_total = sum(voucher.line_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = sequence.next_by_code('dm.finance.voucher') or '/'
        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {
            'voucher_type', 'date', 'company_id', 'currency_id', 'branch_id',
            'partner_id', 'journal_id', 'destination_journal_id',
            'payment_reference', 'cheque_number', 'cheque_date', 'bank_reference',
            'narration', 'line_ids',
        }
        if protected_fields & set(vals):
            locked = self.filtered(lambda voucher: voucher.state not in ('draft', 'rejected'))
            if locked:
                raise UserError(_('Only draft or rejected vouchers can be edited.'))
        return super().write(vals)

    def unlink(self):
        locked = self.filtered(lambda voucher: voucher.state not in ('draft', 'cancelled'))
        if locked:
            raise UserError(_('Only draft or cancelled vouchers can be deleted.'))
        return super().unlink()

    @api.constrains('amount_total', 'line_ids')
    def _check_amount_total(self):
        for voucher in self:
            if voucher.line_ids and voucher.amount_total <= 0:
                raise ValidationError(_('Voucher total amount must be greater than zero.'))

    @api.constrains('voucher_type', 'journal_id', 'destination_journal_id')
    def _check_journals(self):
        for voucher in self:
            if voucher.voucher_type in ('receipt', 'payment') and not voucher.journal_id:
                raise ValidationError(_('Journal is required for receipt and payment vouchers.'))
            if voucher.voucher_type == 'transfer':
                if not voucher.journal_id or not voucher.destination_journal_id:
                    raise ValidationError(_('Source and destination journals are required for transfer vouchers.'))
                if voucher.journal_id == voucher.destination_journal_id:
                    raise ValidationError(_('Source and destination journals must be different.'))

    @api.constrains('branch_id', 'company_id')
    def _check_branch_company(self):
        for voucher in self:
            if voucher.branch_id and voucher.branch_id.company_id != voucher.company_id:
                raise ValidationError(_('The finance branch must belong to the voucher company.'))

    def action_submit(self):
        for voucher in self:
            if voucher.state not in ('draft', 'rejected'):
                raise UserError(_('Only draft or rejected vouchers can be submitted.'))
            voucher._check_ready_for_submit()
            request = voucher._ensure_approval_request()
            request.action_submit()
            voucher.write({'state': 'under_approval'})

    def action_cancel(self):
        for voucher in self:
            if voucher.state == 'posted':
                raise UserError(_('Posted vouchers cannot be cancelled. Use a controlled reversal.'))
            voucher.write({'state': 'cancelled'})
            if voucher.approval_request_id and voucher.approval_request_id.state not in ('approved', 'cancelled'):
                voucher.approval_request_id.action_cancel()

    def action_reset_to_draft(self):
        for voucher in self:
            if voucher.state not in ('rejected', 'cancelled'):
                raise UserError(_('Only rejected or cancelled vouchers can be reset to draft.'))
            voucher.write({'state': 'draft'})

    def action_post(self):
        raise UserError(_(
            'Accounting posting for finance vouchers is not enabled yet. '
            'Approve the voucher accounting matrix first, then enable the posting adapter.'
        ))

    def _check_ready_for_submit(self):
        for voucher in self:
            if not voucher.line_ids:
                raise UserError(_('Add at least one voucher line before submitting.'))
            if voucher.amount_total <= 0:
                raise UserError(_('Voucher total amount must be greater than zero.'))
            if self.env['ir.config_parameter'].sudo().get_param('dm_finance.require_branch') and not voucher.branch_id:
                raise UserError(_('Finance branch is required by finance settings.'))

    def _ensure_approval_request(self):
        self.ensure_one()
        if self.approval_request_id:
            return self.approval_request_id
        flow = self._find_approval_flow()
        request = self.env['dm.finance.approval.request'].create({
            'request_name': self.display_name,
            'res_model': self._name,
            'res_id': self.id,
            'company_id': self.company_id.id,
            'flow_id': flow.id,
        })
        self.approval_request_id = request
        return request

    def _find_approval_flow(self):
        self.ensure_one()
        model = self.env['ir.model']._get(self._name)
        flows = self.env['dm.finance.approval.flow'].search([
            ('model_id', '=', model.id),
            ('document_type', '=', 'voucher'),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ], order='amount_min desc, sequence, id')
        flow = flows.filtered(
            lambda candidate:
            (not candidate.amount_min or candidate.amount_min <= self.amount_total)
            and (not candidate.amount_max or candidate.amount_max >= self.amount_total)
        )[:1]
        if not flow:
            raise UserError(_('No active finance approval flow is configured for this voucher amount.'))
        return flow

    def _approval_approved(self):
        for voucher in self:
            if voucher.state == 'under_approval':
                voucher.write({'state': 'approved'})

    def _approval_rejected(self):
        for voucher in self:
            if voucher.state == 'under_approval':
                voucher.write({'state': 'rejected'})


class DmFinanceVoucherLine(models.Model):
    _name = 'dm.finance.voucher.line'
    _description = 'Finance Voucher Line'
    _order = 'voucher_id, sequence, id'
    _check_company_auto = True

    voucher_id = fields.Many2one(
        'dm.finance.voucher',
        string='Voucher',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(related='voucher_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='voucher_id.currency_id', store=True, readonly=True)
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        check_company=True,
        required=True,
    )
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    analytic_distribution = fields.Json(string='Analytic Distribution')

    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_('Voucher line amount must be greater than zero.'))
