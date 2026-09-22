# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    dm_branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    dm_sector_id = fields.Many2one('hr.department', string='القطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    dm_department_level_id = fields.Many2one('hr.department', string='الإدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    dm_section_id = fields.Many2one('hr.department', string='القسم', related='employee_id.dm_section_id', store=True, readonly=True)
    dm_manager_id = fields.Many2one('hr.employee', string='المدير المباشر', related='employee_id.parent_id', store=True, readonly=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dm_leave_balance_line_ids = fields.Many2many(
        'hr.leave.allocation',
        compute='_compute_dm_leave_balance_lines',
        string='أرصدة الإجازات',
    )

    def _compute_dm_leave_balance_lines(self):
        Allocation = self.env['hr.leave.allocation'].sudo()
        for employee in self:
            employee.dm_leave_balance_line_ids = Allocation.search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
            ], order='date_from desc, id desc', limit=20)


class DmHrLeaveAction(models.Model):
    _name = 'dm.hr.leave.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'إجراء الرجوع/الإلغاء/قطع الإجازة'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    operation = fields.Selection([
        ('return', 'رجوع من الإجازة'),
        ('cancel', 'إلغاء قبل البداية'),
        ('interrupt', 'قطع بعد البداية'),
    ], string='نوع الإجراء', required=True, default='return', tracking=True)
    leave_id = fields.Many2one('hr.leave', string='طلب الإجازة الأصلي', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', related='leave_id.employee_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='الشركة', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', string='القطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', string='الإدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', string='القسم', related='employee_id.dm_section_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', string='المدير المباشر', related='employee_id.parent_id', store=True, readonly=True)
    actual_return_date = fields.Date(string='تاريخ الرجوع الفعلي')
    effective_last_leave_date = fields.Date(string='آخر يوم إجازة فعلي')
    reason = fields.Text(string='السبب', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('manager', 'اعتماد المدير'),
        ('hr', 'اعتماد الموارد البشرية'),
        ('approved', 'معتمد ومنفذ'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.leave.action') or 'جديد'
        return super().create(vals_list)

    @api.constrains('operation', 'leave_id', 'actual_return_date', 'effective_last_leave_date')
    def _check_dates(self):
        for rec in self:
            leave_start = rec.leave_id.request_date_from
            leave_end = rec.leave_id.request_date_to
            if rec.operation == 'cancel' and leave_start and fields.Date.today() >= leave_start:
                raise ValidationError(_('الإلغاء مخصص لما قبل بداية الإجازة. استخدم قطع الإجازة إذا بدأت فعليًا.'))
            if rec.operation in ('return', 'interrupt') and not rec.actual_return_date:
                raise ValidationError(_('يجب تحديد تاريخ الرجوع الفعلي.'))
            if rec.operation == 'interrupt' and rec.actual_return_date and leave_start and rec.actual_return_date <= leave_start:
                raise ValidationError(_('تاريخ الرجوع في القطع يجب أن يكون بعد بداية الإجازة.'))
            if rec.state != 'approved' and rec.operation == 'interrupt' and rec.actual_return_date and leave_end and rec.actual_return_date > leave_end:
                raise ValidationError(_('تاريخ الرجوع لا يمكن أن يكون بعد نهاية الإجازة الأصلية.'))

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve(self):
        flow = {'manager': 'hr', 'hr': 'approved'}
        for rec in self:
            if rec.state not in flow:
                raise UserError(_('لا يمكن اعتماد الإجراء في هذه المرحلة.'))
            rec.state = flow[rec.state]
            if rec.state == 'approved':
                rec._apply_leave_action()
            rec.message_post(body=_('تم اعتماد المرحلة الحالية.'))

    def _apply_leave_action(self):
        for rec in self:
            leave = rec.leave_id.sudo()
            if rec.operation == 'cancel':
                if leave.state not in ('refuse', 'cancel'):
                    leave.action_refuse()
                continue
            if rec.operation == 'interrupt':
                last_day = rec.actual_return_date - relativedelta(days=1)
                leave.with_context(leave_skip_state_check=True).write({'request_date_to': last_day})
                rec.effective_last_leave_date = last_day
                leave.with_context(leave_skip_state_check=True).message_post(
                    body=_('تم قطع الإجازة حسب الطلب %s. آخر يوم إجازة فعلي: %s') % (rec.name, last_day)
                )
            if rec.operation == 'return':
                leave.message_post(body=_('تم تسجيل الرجوع الفعلي من الإجازة بتاريخ %s عبر الطلب %s.') % (rec.actual_return_date, rec.name))

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrLeavePurchase(models.Model):
    _name = 'dm.hr.leave.purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'طلب شراء إجازة'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string='العقد')
    holiday_status_id = fields.Many2one('hr.leave.type', string='نوع الإجازة', required=True)
    days = fields.Float(string='عدد الأيام', required=True)
    daily_wage = fields.Monetary(string='الأجر اليومي', compute='_compute_amount', store=True)
    amount = fields.Monetary(string='القيمة التقديرية', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    reason = fields.Text(string='السبب', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', related='employee_id.dm_section_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'), ('manager', 'المدير'), ('hr', 'HR'), ('finance', 'المالية'),
        ('approved', 'معتمد'), ('rejected', 'مرفوض')
    ], default='draft', tracking=True)

    @api.depends('contract_id.wage', 'days')
    def _compute_amount(self):
        for rec in self:
            rec.daily_wage = (rec.contract_id.wage or 0.0) / 30.0 if rec.contract_id else 0.0
            rec.amount = rec.daily_wage * (rec.days or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.leave.purchase') or 'جديد'
        return super().create(vals_list)

    @api.constrains('days')
    def _check_days(self):
        for rec in self:
            if rec.days <= 0:
                raise ValidationError(_('عدد أيام شراء الإجازة يجب أن يكون أكبر من صفر.'))

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve(self):
        flow = {'manager': 'hr', 'hr': 'finance', 'finance': 'approved'}
        for rec in self:
            if rec.state not in flow:
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            rec.state = flow[rec.state]
            rec.message_post(body=_('تم اعتماد المرحلة الحالية.'))

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrLeaveBalanceRequest(models.Model):
    _name = 'dm.hr.leave.balance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'طلب إضافة رصيد إجازة'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    holiday_status_id = fields.Many2one('hr.leave.type', string='نوع الإجازة', required=True, domain="[('requires_allocation','=','yes')]")
    days = fields.Float(string='عدد الأيام', required=True)
    date_from = fields.Date(string='بداية الصلاحية', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='نهاية الصلاحية')
    reason = fields.Text(string='سبب الإضافة', required=True)
    allocation_id = fields.Many2one('hr.leave.allocation', string='الرصيد الناتج', readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', related='employee_id.dm_section_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'), ('hr', 'اعتماد الموارد البشرية'), ('approved', 'معتمد ومنفذ'), ('rejected', 'مرفوض')
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.leave.balance.request') or 'جديد'
        return super().create(vals_list)

    @api.constrains('days')
    def _check_days(self):
        for rec in self:
            if rec.days <= 0:
                raise ValidationError(_('عدد الأيام يجب أن يكون أكبر من صفر.'))

    def action_submit(self):
        self.write({'state': 'hr'})

    def action_approve(self):
        for rec in self:
            if rec.state != 'hr':
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            allocation = self.env['hr.leave.allocation'].sudo().create({
                'private_name': _('إضافة رصيد معتمدة - %s') % rec.employee_id.name,
                'holiday_type': 'employee',
                'employee_id': rec.employee_id.id,
                'employee_ids': [(6, 0, [rec.employee_id.id])],
                'holiday_status_id': rec.holiday_status_id.id,
                'number_of_days': rec.days,
                'number_of_days_display': rec.days,
                'allocation_type': 'regular',
                'date_from': rec.date_from,
                'date_to': rec.date_to,
                'notes': rec.reason,
                'dm_allocation_origin': 'manual_hr',
            })
            allocation.action_validate()
            rec.write({'state': 'approved', 'allocation_id': allocation.id})
            rec.message_post(body=_('تم اعتماد إضافة الرصيد وإنشاء تخصيص إجازة.'))

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrEmployeeFinancialRequest(models.Model):
    _name = 'dm.hr.employee.financial.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'طلبات السلف والقروض للموظفين'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    request_type = fields.Selection([('advance', 'سلفة'), ('loan', 'قرض')], string='نوع الطلب', required=True, default='advance', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string='العقد')
    amount = fields.Monetary(string='المبلغ', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    reason = fields.Text(string='السبب', required=True)
    deduction_method = fields.Selection([('fixed', 'أقساط متساوية'), ('manual', 'يدوي')], string='طريقة الخصم', default='fixed', required=True)
    installment_count = fields.Integer(string='عدد الأقساط', default=1, required=True)
    first_installment_date = fields.Date(string='تاريخ أول قسط', required=True, default=fields.Date.context_today)
    installment_ids = fields.One2many('dm.hr.employee.financial.installment', 'request_id', string='جدول الأقساط')
    paid_amount = fields.Monetary(string='المدفوع', compute='_compute_amounts', store=True)
    balance_amount = fields.Monetary(string='الرصيد المتبقي', compute='_compute_amounts', store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', related='employee_id.dm_section_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'), ('manager', 'المدير'), ('hr', 'HR'), ('finance', 'المالية'),
        ('approved', 'معتمد ومجدول'), ('settled', 'مسوى'), ('rejected', 'مرفوض'), ('cancelled', 'ملغي')
    ], default='draft', tracking=True)

    @api.depends('installment_ids.amount', 'installment_ids.state', 'amount')
    def _compute_amounts(self):
        for rec in self:
            rec.paid_amount = sum(rec.installment_ids.filtered(lambda l: l.state == 'paid').mapped('amount'))
            rec.balance_amount = (rec.amount or 0.0) - rec.paid_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.employee.financial.request') or 'جديد'
        return super().create(vals_list)

    @api.constrains('amount', 'installment_count')
    def _check_financial_values(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('المبلغ يجب أن يكون أكبر من صفر.'))
            if rec.installment_count <= 0:
                raise ValidationError(_('عدد الأقساط يجب أن يكون أكبر من صفر.'))

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve(self):
        flow = {'manager': 'hr', 'hr': 'finance', 'finance': 'approved'}
        for rec in self:
            if rec.state not in flow:
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            rec.state = flow[rec.state]
            if rec.state == 'approved':
                rec._generate_installments()
            rec.message_post(body=_('تم اعتماد المرحلة الحالية.'))

    def _generate_installments(self):
        for rec in self:
            if rec.installment_ids:
                continue
            amount = round(rec.amount / rec.installment_count, 2)
            total = 0.0
            lines = []
            for idx in range(rec.installment_count):
                line_amount = amount
                if idx == rec.installment_count - 1:
                    line_amount = rec.amount - total
                total += line_amount
                lines.append((0, 0, {
                    'sequence': idx + 1,
                    'due_date': rec.first_installment_date + relativedelta(months=idx),
                    'amount': line_amount,
                    'state': 'not_due',
                }))
            rec.write({'installment_ids': lines})

    def action_mark_settled(self):
        for rec in self:
            rec.installment_ids.filtered(lambda l: l.state != 'paid').write({'state': 'cancelled'})
            rec.state = 'settled'

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class DmHrEmployeeFinancialInstallment(models.Model):
    _name = 'dm.hr.employee.financial.installment'
    _inherit = ['mail.thread']
    _description = 'أقساط السلف والقروض'
    _order = 'due_date, sequence, id'

    request_id = fields.Many2one('dm.hr.employee.financial.request', string='الطلب المالي', required=True, ondelete='cascade')
    sequence = fields.Integer(string='القسط')
    employee_id = fields.Many2one('hr.employee', related='request_id.employee_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', related='request_id.company_id', store=True, readonly=True)
    due_date = fields.Date(string='تاريخ الاستحقاق', required=True)
    amount = fields.Monetary(string='المبلغ', required=True)
    currency_id = fields.Many2one('res.currency', related='request_id.currency_id', store=True, readonly=True)
    payment_date = fields.Date(string='تاريخ السداد')
    notes = fields.Text(string='ملاحظات التسوية')
    state = fields.Selection([
        ('not_due', 'غير مستحق'),
        ('due', 'مستحق'),
        ('paid', 'مدفوع'),
        ('cancelled', 'ملغي'),
    ], default='not_due', tracking=True)

    def action_mark_due(self):
        self.write({'state': 'due'})

    def action_mark_paid(self):
        self.write({'state': 'paid', 'payment_date': fields.Date.context_today(self)})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
