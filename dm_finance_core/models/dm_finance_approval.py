# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DmFinanceApprovalFlow(models.Model):
    _name = 'dm.finance.approval.flow'
    _description = 'Finance Approval Flow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'company_id, sequence, name'
    _check_company_auto = True

    name = fields.Char(string='Flow Name', required=True, translate=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        tracking=True,
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Document Model',
        required=True,
        ondelete='cascade',
        help='The business model this approval flow applies to.',
    )
    document_type = fields.Selection(
        [
            ('voucher', 'Voucher'),
            ('advance', 'Advance / Loan'),
            ('custody', 'Custody / Petty Cash'),
            ('budget', 'Budget'),
            ('asset', 'Asset'),
            ('other', 'Other'),
        ],
        string='Document Type',
        default='other',
        required=True,
    )
    amount_min = fields.Monetary(string='Minimum Amount', currency_field='currency_id')
    amount_max = fields.Monetary(string='Maximum Amount', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        store=True,
    )
    allow_self_approval = fields.Boolean(
        string='Allow Self Approval',
        help='If disabled, the requester cannot approve their own document.',
    )
    line_ids = fields.One2many(
        'dm.finance.approval.flow.line',
        'flow_id',
        string='Approval Steps',
        copy=True,
    )
    note = fields.Text(string='Notes')

    _sql_constraints = [
        (
            'dm_finance_approval_flow_name_company_uniq',
            'unique(name, company_id)',
            'Approval flow name must be unique per company.',
        ),
    ]

    @api.constrains('amount_min', 'amount_max')
    def _check_amount_range(self):
        for flow in self:
            if flow.amount_min < 0 or flow.amount_max < 0:
                raise ValidationError(_('Approval amount limits cannot be negative.'))
            if flow.amount_max and flow.amount_min > flow.amount_max:
                raise ValidationError(_('Minimum amount cannot exceed maximum amount.'))

    @api.constrains('line_ids')
    def _check_has_steps(self):
        self._validate_active_steps()

    @api.model_create_multi
    def create(self, vals_list):
        flows = super().create(vals_list)
        flows._validate_active_steps()
        return flows

    def write(self, vals):
        result = super().write(vals)
        if {'active', 'line_ids'} & set(vals):
            self._validate_active_steps()
        return result

    def _validate_active_steps(self):
        for flow in self:
            if flow.active and not flow.line_ids:
                raise ValidationError(_('An active approval flow must contain at least one approval step.'))


class DmFinanceApprovalFlowLine(models.Model):
    _name = 'dm.finance.approval.flow.line'
    _description = 'Finance Approval Flow Step'
    _order = 'flow_id, sequence, id'
    _check_company_auto = True

    flow_id = fields.Many2one(
        'dm.finance.approval.flow',
        string='Approval Flow',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(related='flow_id.company_id', store=True, readonly=True)
    sequence = fields.Integer(string='Sequence', default=10, required=True)
    name = fields.Char(string='Step Name', required=True, translate=True)
    approver_type = fields.Selection(
        [
            ('finance_manager', 'Finance Manager'),
            ('branch_supervisor', 'Branch Finance Supervisor'),
            ('group', 'Security Group'),
            ('user', 'Specific User'),
        ],
        string='Approver Type',
        default='finance_manager',
        required=True,
    )
    group_id = fields.Many2one('res.groups', string='Approver Group')
    user_id = fields.Many2one(
        'res.users',
        string='Approver User',
        domain="[('share', '=', False)]",
    )
    mandatory = fields.Boolean(string='Mandatory', default=True)
    require_comment = fields.Boolean(string='Require Comment')

    @api.constrains('approver_type', 'group_id', 'user_id')
    def _check_approver_target(self):
        for line in self:
            if line.approver_type == 'group' and not line.group_id:
                raise ValidationError(_('Approver group is required for group-based approval steps.'))
            if line.approver_type == 'user' and not line.user_id:
                raise ValidationError(_('Approver user is required for user-based approval steps.'))


class DmFinanceApprovalRequest(models.Model):
    _name = 'dm.finance.approval.request'
    _description = 'Finance Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _check_company_auto = True

    request_name = fields.Char(string='Request Name', required=True, tracking=True)
    res_model = fields.Char(string='Document Model', required=True, index=True, readonly=True)
    res_id = fields.Integer(string='Document ID', required=True, index=True, readonly=True)
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        readonly=True,
        tracking=True,
    )
    flow_id = fields.Many2one(
        'dm.finance.approval.flow',
        string='Approval Flow',
        required=True,
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        check_company=True,
        readonly=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('under_approval', 'Under Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    submitted_on = fields.Datetime(string='Submitted On', readonly=True)
    approved_on = fields.Datetime(string='Approved On', readonly=True)
    rejected_on = fields.Datetime(string='Rejected On', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)
    item_ids = fields.One2many(
        'dm.finance.approval.item',
        'approval_request_id',
        string='Approval History',
        readonly=True,
    )

    _sql_constraints = [
        (
            'dm_finance_approval_request_document_uniq',
            'unique(res_model, res_id)',
            'A finance approval request already exists for this document.',
        ),
    ]

    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(_('Only draft approval requests can be submitted.'))
            request._create_approval_items()
            request.write({
                'state': 'under_approval',
                'submitted_on': fields.Datetime.now(),
            })

    def action_cancel(self):
        for request in self:
            if request.state in ('approved',):
                raise UserError(_('Approved approval requests cannot be cancelled. Use a controlled reversal on the business document.'))
            request.state = 'cancelled'

    def action_approve(self, comment=False):
        for request in self:
            item = request._get_current_pending_item()
            item._check_can_act()
            item.sudo().with_context(dm_finance_approval_engine=True).write({
                'state': 'approved',
                'date_done': fields.Datetime.now(),
                'action_done_by_id': self.env.user.id,
                'comment': comment or False,
            })
            if not request._get_current_pending_item():
                request.write({
                    'state': 'approved',
                    'approved_on': fields.Datetime.now(),
                })

    def action_reject(self, reason):
        if not reason:
            raise UserError(_('A rejection reason is required.'))
        for request in self:
            item = request._get_current_pending_item()
            item._check_can_act()
            item.sudo().with_context(dm_finance_approval_engine=True).write({
                'state': 'rejected',
                'date_done': fields.Datetime.now(),
                'action_done_by_id': self.env.user.id,
                'comment': reason,
            })
            request.write({
                'state': 'rejected',
                'rejected_on': fields.Datetime.now(),
                'rejection_reason': reason,
            })

    def _create_approval_items(self):
        Item = self.env['dm.finance.approval.item']
        for request in self:
            if request.item_ids:
                continue
            vals_list = []
            for line in request.flow_id.line_ids.sorted('sequence'):
                vals_list.append({
                    'approval_request_id': request.id,
                    'flow_line_id': line.id,
                    'sequence': line.sequence,
                    'approver_type': line.approver_type,
                    'approver_user_id': line.user_id.id,
                    'approver_group_id': line.group_id.id,
                    'state': 'pending',
                })
            Item.sudo().with_context(dm_finance_approval_engine=True).create(vals_list)

    def _get_current_pending_item(self):
        self.ensure_one()
        return self.item_ids.filtered(lambda item: item.state == 'pending').sorted('sequence')[:1]


class DmFinanceApprovalItem(models.Model):
    _name = 'dm.finance.approval.item'
    _description = 'Finance Approval Item'
    _order = 'approval_request_id, sequence, id'
    _check_company_auto = True

    approval_request_id = fields.Many2one(
        'dm.finance.approval.request',
        string='Approval Request',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(related='approval_request_id.company_id', store=True, readonly=True)
    flow_line_id = fields.Many2one('dm.finance.approval.flow.line', string='Flow Step', ondelete='restrict')
    sequence = fields.Integer(string='Sequence', default=10)
    approver_type = fields.Selection(related='flow_line_id.approver_type', store=True, readonly=True)
    approver_user_id = fields.Many2one('res.users', string='Approver User', readonly=True)
    approver_group_id = fields.Many2one('res.groups', string='Approver Group', readonly=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('skipped', 'Skipped')],
        string='Status',
        default='pending',
        required=True,
        readonly=True,
    )
    date_done = fields.Datetime(string='Action Date', readonly=True)
    action_done_by_id = fields.Many2one('res.users', string='Action Done By', readonly=True)
    comment = fields.Text(string='Comment', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('dm_finance_approval_engine'):
            raise UserError(_('Approval items can only be created by the finance approval engine.'))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get('dm_finance_approval_engine'):
            raise UserError(_('Approval items can only be updated by the finance approval engine.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get('dm_finance_approval_engine'):
            raise UserError(_('Approval items can only be removed by the finance approval engine.'))
        return super().unlink()

    def _check_can_act(self):
        for item in self:
            request = item.approval_request_id
            if item.state != 'pending':
                raise UserError(_('Only pending approval items can be acted on.'))
            if request.state != 'under_approval':
                raise UserError(_('Approval request must be under approval.'))
            if not request.flow_id.allow_self_approval and request.requester_id == self.env.user:
                raise UserError(_('You cannot approve your own finance document.'))
            if item.approver_user_id and item.approver_user_id != self.env.user:
                raise UserError(_('You are not the assigned approver for this step.'))
            if item.approver_group_id and item.approver_group_id not in self.env.user.groups_id:
                raise UserError(_('You do not belong to the required approver group.'))
