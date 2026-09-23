# -*- coding: utf-8 -*-
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class DmHrApprovalPolicy(models.Model):
    _inherit = 'dm.hr.approval.policy'


class DmHrOffboardingType(models.Model):
    _name = 'dm.hr.offboarding.type'
    _description = 'نوع إنهاء الخدمة'
    _order = 'company_id, sequence, name'
    _check_company_auto = True

    name = fields.Char(string='النوع', required=True, translate=True)
    code = fields.Char(string='الكود', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company)
    initiated_by = fields.Selection(
        [('employee', 'الموظف'), ('hr', 'الموارد البشرية'), ('both', 'كلاهما')],
        string='مصدر الطلب',
        default='both',
        required=True,
    )
    eos_eligible = fields.Boolean(string='مستحق لمكافأة نهاية الخدمة', default=True)
    default_entitlement_ratio = fields.Float(string='نسبة الاستحقاق الافتراضية %', default=100.0)
    full_entitlement_exception = fields.Boolean(string='استثناء باستحقاق كامل')
    notice_required = fields.Boolean(string='تتطلب مدة إشعار', default=True)
    notice_days = fields.Integer(string='أيام الإشعار', default=30)
    requires_clearance = fields.Boolean(string='تتطلب إخلاء طرف', default=True)
    creates_settlement = fields.Boolean(string='تنشئ تسوية نهائية', default=True)
    can_close_contract = fields.Boolean(string='تغلق العقد بعد الإكمال', default=True)
    allow_withdrawal = fields.Boolean(string='السماح بسحب الطلب قبل الاعتماد', default=True)
    allow_archive_employee = fields.Boolean(string='أرشفة الموظف بعد الإكمال')
    payroll_earning_code = fields.Char(string='كود استحقاق الرواتب')
    payroll_deduction_code = fields.Char(string='كود حسم الرواتب')
    note = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'كود نوع إنهاء الخدمة يجب ألا يتكرر لنفس الشركة.'),
    ]


class DmHrOffboardingRule(models.Model):
    _name = 'dm.hr.offboarding.rule'
    _description = 'قواعد مكافأة نهاية الخدمة'
    _order = 'company_id, sequence, id'
    _check_company_auto = True

    name = fields.Char(string='اسم القاعدة', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', required=True, default=lambda self: self.env.company)
    first_period_years = fields.Float(string='سنوات الشريحة الأولى', default=5.0)
    first_period_month_ratio = fields.Float(string='نسبة شهر للشريحة الأولى', default=0.5)
    later_period_month_ratio = fields.Float(string='نسبة شهر لما بعد الشريحة الأولى', default=1.0)
    resignation_no_entitlement_years = fields.Float(string='لا استحقاق للاستقالة قبل', default=2.0)
    resignation_one_third_years = fields.Float(string='ثلث المكافأة حتى', default=5.0)
    resignation_two_third_years = fields.Float(string='ثلثا المكافأة حتى', default=10.0)
    include_allowances = fields.Boolean(string='احتساب البدلات ضمن الأجر الأساسي')
    daily_wage_method = fields.Selection(
        [('thirty', 'الأجر الشهري / 30'), ('calendar', 'حسب أيام الشهر')],
        string='طريقة احتساب اليوم',
        default='thirty',
        required=True,
    )
    rounding_digits = fields.Integer(string='خانات التقريب', default=2)
    allow_manual_override = fields.Boolean(string='السماح بالتعديل اليدوي', default=True)
    note = fields.Text(string='ملاحظات')

    @api.constrains('first_period_years', 'first_period_month_ratio', 'later_period_month_ratio')
    def _check_positive(self):
        for rec in self:
            if rec.first_period_years < 0 or rec.first_period_month_ratio < 0 or rec.later_period_month_ratio < 0:
                raise ValidationError(_('قيم قواعد المكافأة يجب ألا تكون سالبة.'))


class DmHrOffboarding(models.Model):
    _name = 'dm.hr.offboarding'
    _description = 'طلب إنهاء خدمة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True, index=True)
    employee_number = fields.Char(string='الرقم الوظيفي', related='employee_id.employee_number', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع', readonly=True, tracking=True)
    sector_id = fields.Many2one('hr.department', string='القطاع', readonly=True, tracking=True)
    department_level_id = fields.Many2one('hr.department', string='الإدارة', readonly=True, tracking=True)
    section_id = fields.Many2one('hr.department', string='القسم', readonly=True, tracking=True)
    unit_id = fields.Many2one('hr.department', string='الوحدة', readonly=True, tracking=True)
    job_id = fields.Many2one('hr.job', string='المنصب الوظيفي', readonly=True, tracking=True)
    manager_id = fields.Many2one('hr.employee', string='المدير المباشر', readonly=True, tracking=True)
    manager_user_id = fields.Many2one('res.users', related='manager_id.user_id', store=True, readonly=True)
    contract_id = fields.Many2one('hr.contract', string='العقد الحالي', tracking=True)
    termination_type_id = fields.Many2one('dm.hr.offboarding.type', string='نوع إنهاء الخدمة', required=True, tracking=True)
    initiated_by = fields.Selection(related='termination_type_id.initiated_by', store=True, readonly=True)
    reason = fields.Text(string='السبب', required=True, tracking=True)
    request_date = fields.Date(string='تاريخ الطلب', default=fields.Date.context_today, required=True, tracking=True)
    service_start_date = fields.Date(string='بداية الخدمة', tracking=True)
    contract_end_date = fields.Date(string='نهاية العقد', related='contract_id.date_end', store=True, readonly=True)
    requested_last_work_date = fields.Date(string='آخر يوم عمل مقترح', required=True, tracking=True)
    approved_last_work_date = fields.Date(string='آخر يوم عمل معتمد', tracking=True)
    settlement_date = fields.Date(string='تاريخ التسوية', tracking=True)
    required_notice_days = fields.Integer(string='أيام الإشعار المطلوبة', compute='_compute_notice', store=True)
    actual_notice_days = fields.Integer(string='أيام الإشعار الفعلية', compute='_compute_notice', store=True)
    notice_difference_days = fields.Integer(string='فرق الإشعار', compute='_compute_notice', store=True)
    employee_status = fields.Selection(
        [('working', 'على رأس العمل'), ('notice', 'في فترة الإشعار'), ('clearing', 'إخلاء طرف'), ('settled', 'تمت التسوية'), ('terminated', 'منتهي الخدمة')],
        string='حالة الموظف أثناء الإجراء',
        default='working',
        tracking=True,
    )
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    employee_note = fields.Text(string='ملاحظات الموظف')
    manager_note = fields.Text(string='ملاحظات المدير')
    hr_note = fields.Text(string='ملاحظات الموارد البشرية')
    finance_note = fields.Text(string='ملاحظات المالية')
    rejection_reason = fields.Text(string='سبب الرفض')
    cancel_reason = fields.Text(string='سبب الإلغاء')
    current_responsible_id = fields.Many2one('res.users', string='المسؤول الحالي', tracking=True)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مرسل'),
        ('manager_approval', 'اعتماد المدير'),
        ('hr_review', 'مراجعة الموارد البشرية'),
        ('notice_period', 'فترة الإشعار'),
        ('clearance', 'إخلاء الطرف'),
        ('finance_settlement', 'التسوية المالية'),
        ('final_approval', 'الاعتماد النهائي'),
        ('done', 'منتهي'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='draft', tracking=True, index=True)
    approval_policy_id = fields.Many2one('dm.hr.approval.policy', string='سياسة الموافقات', readonly=True)
    approval_item_ids = fields.One2many('dm.hr.offboarding.approval.item', 'offboarding_id', string='مسار الموافقات')
    clearance_line_ids = fields.One2many('dm.hr.offboarding.clearance.line', 'offboarding_id', string='بنود إخلاء الطرف')
    settlement_id = fields.Many2one('dm.hr.offboarding.settlement', string='التسوية النهائية', readonly=True, copy=False)
    settlement_count = fields.Integer(compute='_compute_counts')
    clearance_pending_count = fields.Integer(compute='_compute_counts')
    exit_interview_id = fields.Many2one('dm.hr.exit.interview', string='مقابلة الخروج', readonly=True, copy=False)
    service_years = fields.Float(string='سنوات الخدمة', compute='_compute_service_years', store=True)
    eos_base_wage = fields.Monetary(string='أجر احتساب المكافأة', compute='_compute_eos_base_wage', store=True)
    eos_manual_override = fields.Boolean(string='تعديل مكافأة نهاية الخدمة يدويًا', tracking=True)
    eos_manual_amount = fields.Monetary(string='قيمة المكافأة اليدوية', tracking=True)
    eos_manual_reason = fields.Text(string='سبب تعديل المكافأة')
    completion_executed = fields.Boolean(string='تم تنفيذ الإنهاء', readonly=True, copy=False)
    archive_employee = fields.Boolean(string='أرشفة الموظف عند الإكمال')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.offboarding') or 'جديد'
        records = super().create(vals_list)
        records._snapshot_employee_structure()
        return records

    def write(self, vals):
        locked = {'eos_manual_amount', 'eos_manual_override', 'eos_manual_reason', 'approved_last_work_date', 'termination_type_id'}
        if locked.intersection(vals) and any(r.state in ('final_approval', 'done') for r in self):
            if not self.env.user.has_group('dm_hr_offboarding.group_dm_hr_offboarding_hr_manager'):
                raise AccessError(_('لا يمكن تعديل بيانات مالية/حساسة بعد الاعتماد النهائي إلا من مدير الموارد البشرية.'))
        res = super().write(vals)
        if 'employee_id' in vals:
            self._snapshot_employee_structure()
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self._snapshot_employee_structure()

    def _snapshot_employee_structure(self):
        for rec in self.filtered('employee_id'):
            emp = rec.employee_id
            contract = rec.contract_id or self.env['hr.contract'].search([
                ('employee_id', '=', emp.id), ('state', '=', 'open')
            ], limit=1)
            vals = {
                'company_id': emp.company_id.id or self.env.company.id,
                'branch_id': emp.dm_branch_id.id,
                'sector_id': emp.dm_sector_id.id,
                'department_level_id': emp.dm_department_level_id.id,
                'section_id': emp.dm_section_id.id,
                'unit_id': emp.dm_unit_id.id,
                'job_id': emp.job_id.id,
                'manager_id': emp.parent_id.id,
                'contract_id': contract.id,
                'service_start_date': emp.join_date or contract.date_start,
            }
            if rec.id:
                super(DmHrOffboarding, rec).write(vals)
            else:
                for field, value in vals.items():
                    rec[field] = value

    @api.depends('request_date', 'requested_last_work_date', 'termination_type_id.notice_days', 'termination_type_id.notice_required')
    def _compute_notice(self):
        for rec in self:
            rec.required_notice_days = rec.termination_type_id.notice_days if rec.termination_type_id.notice_required else 0
            if rec.request_date and rec.requested_last_work_date:
                rec.actual_notice_days = max((rec.requested_last_work_date - rec.request_date).days, 0)
            else:
                rec.actual_notice_days = 0
            rec.notice_difference_days = rec.actual_notice_days - rec.required_notice_days

    @api.depends('service_start_date', 'approved_last_work_date', 'requested_last_work_date')
    def _compute_service_years(self):
        for rec in self:
            end = rec.approved_last_work_date or rec.requested_last_work_date or fields.Date.context_today(rec)
            if rec.service_start_date and end:
                rec.service_years = max((end - rec.service_start_date).days, 0) / 365.0
            else:
                rec.service_years = 0.0

    @api.depends('contract_id.wage')
    def _compute_eos_base_wage(self):
        for rec in self:
            wage = rec.contract_id.wage or 0.0
            rule = rec._get_eos_rule()
            if rule.include_allowances and rec.contract_id and hasattr(rec.contract_id, 'allowance_ids'):
                wage += sum(rec.contract_id.allowance_ids.mapped('amount'))
            rec.eos_base_wage = wage

    def _compute_counts(self):
        for rec in self:
            rec.settlement_count = 1 if rec.settlement_id else 0
            rec.clearance_pending_count = len(rec.clearance_line_ids.filtered(lambda l: l.state not in ('approved', 'waived')))

    @api.constrains('requested_last_work_date', 'request_date')
    def _check_dates(self):
        for rec in self:
            if rec.requested_last_work_date and rec.request_date and rec.requested_last_work_date < rec.request_date:
                raise ValidationError(_('آخر يوم عمل لا يمكن أن يكون قبل تاريخ الطلب.'))

    def _get_eos_rule(self):
        self.ensure_one()
        return self.env['dm.hr.offboarding.rule'].sudo().search([
            ('company_id', '=', self.company_id.id), ('active', '=', True)
        ], limit=1) or self.env['dm.hr.offboarding.rule'].sudo().search([('active', '=', True)], limit=1)

    def _find_approval_policy(self):
        self.ensure_one()
        Policy = self.env['dm.hr.approval.policy'].sudo()
        policies = Policy.search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
            ('request_type', 'in', ['offboarding', 'all']),
        ], order='request_type desc, sequence, id')
        for policy in policies:
            if policy.branch_id and policy.branch_id != self.branch_id:
                continue
            if policy.sector_id and policy.sector_id != self.sector_id:
                continue
            if policy.department_id and policy.department_id != self.department_level_id:
                continue
            if policy.section_id and policy.section_id != self.section_id:
                continue
            if policy.unit_id and policy.unit_id != self.unit_id:
                continue
            if policy.job_id and policy.job_id != self.job_id:
                continue
            if policy.min_service_years and self.service_years < policy.min_service_years:
                continue
            return policy
        return self.env['dm.hr.approval.policy']

    def _resolve_step_user(self, step):
        self.ensure_one()
        if step.approver_type == 'manager':
            return self.manager_user_id
        if step.approver_type == 'hr_officer':
            return self.env.ref('dm_hr_core.group_dm_hr_officer', raise_if_not_found=False).users[:1]
        if step.approver_type == 'hr_manager':
            return self.env.ref('dm_hr_core.group_dm_hr_manager', raise_if_not_found=False).users[:1]
        if step.approver_type == 'user':
            return step.user_id
        return self.env['res.users']

    def _build_approval_items(self):
        for rec in self:
            rec.approval_item_ids.unlink()
            policy = rec._find_approval_policy()
            rec.approval_policy_id = policy.id if policy else False
            if policy and policy.step_ids:
                for step in policy.step_ids:
                    rec.env['dm.hr.offboarding.approval.item'].create({
                        'offboarding_id': rec.id,
                        'policy_step_id': step.id,
                        'sequence': step.sequence,
                        'name': step.name,
                        'approver_user_id': rec._resolve_step_user(step).id,
                        'approver_group_id': step.group_id.id,
                        'require_comment': step.require_comment,
                        'delegate_user_id': step.delegate_user_id.id,
                        'instructions': step.instructions,
                    })

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            missing = []
            if not rec.employee_id:
                missing.append(_('الموظف'))
            if not rec.termination_type_id:
                missing.append(_('نوع إنهاء الخدمة'))
            if not rec.requested_last_work_date:
                missing.append(_('آخر يوم عمل مطلوب'))
            if missing:
                raise UserError(_(
                    'لا يمكن إرسال الطلب قبل استكمال البيانات التالية:\n- %s\n\n'
                    'أكمل البيانات ثم اضغط إرسال مرة أخرى.'
                ) % '\n- '.join(missing))
            rec._snapshot_employee_structure()
            rec._build_approval_items()
            rec.write({
                'state': 'manager_approval',
                'employee_status': 'working',
                'current_responsible_id': rec.manager_user_id.id,
                'approved_last_work_date': rec.requested_last_work_date,
            })
            rec.message_post(body=_('تم إرسال طلب إنهاء الخدمة للاعتماد.'))

    def action_approve(self):
        flow = {
            'manager_approval': ('hr_review', 'تم اعتماد المدير المباشر.'),
            'hr_review': ('notice_period', 'تمت مراجعة الموارد البشرية.'),
            'notice_period': ('clearance', 'تم اعتماد فترة الإشعار وبدء إخلاء الطرف.'),
            'clearance': ('finance_settlement', 'تم اكتمال إخلاء الطرف والانتقال للتسوية.'),
            'finance_settlement': ('final_approval', 'تم اعتماد التسوية المالية.'),
            'final_approval': ('done', 'تم الاعتماد النهائي.'),
        }
        for rec in self:
            if rec.state not in flow:
                raise UserError(_(
                    'لا يمكن اعتماد الطلب في الحالة الحالية: %s.\n\n'
                    'راجع شريط الحالة أعلى الطلب وتأكد من أن الطلب وصل إلى مرحلة اعتمادك.'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))
            if rec.state == 'clearance':
                rec._ensure_clearance_ready()
            if rec.state == 'finance_settlement':
                if rec.termination_type_id.creates_settlement and (not rec.settlement_id or rec.settlement_id.state not in ('approved', 'paid')):
                    raise UserError(_(
                        'لا يمكن الانتقال للاعتماد النهائي لأن التسوية النهائية غير معتمدة بعد.\n\n'
                        'افتح التسوية من الزر الذكي، راجع البنود، ثم اعتمدها أو سجلها كمدفوعة حسب الصلاحية.'
                    ))
            new_state, msg = flow[rec.state]
            vals = {'state': new_state}
            if new_state == 'clearance':
                rec._ensure_clearance_lines()
                vals['employee_status'] = 'clearing'
            if new_state == 'finance_settlement':
                vals['employee_status'] = 'settled'
                rec.action_generate_settlement()
            if new_state == 'done':
                rec._execute_completion()
            rec.write(vals)
            rec._mark_next_approval_item()
            rec.message_post(body=_(msg))

    def _mark_next_approval_item(self):
        for rec in self:
            pending = rec.approval_item_ids.filtered(lambda l: l.state == 'pending')[:1]
            if pending:
                pending.action_approve()

    def action_reject(self):
        self.write({'state': 'rejected'})
        self.message_post(body=_('تم رفض طلب إنهاء الخدمة.'))

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_withdraw(self):
        for rec in self:
            if rec.state not in ('submitted', 'manager_approval') or not rec.termination_type_id.allow_withdrawal:
                raise UserError(_('لا يمكن سحب هذا الطلب في مرحلته الحالية.'))
            rec.write({'state': 'cancelled', 'cancel_reason': _('تم السحب بواسطة الموظف.')})

    def _ensure_clearance_lines(self):
        for rec in self:
            if not rec.termination_type_id.requires_clearance:
                continue
            if not rec.clearance_line_ids:
                departments = self.env['dm.hr.offboarding.clearance.department'].sudo().search([
                    '|', ('company_id', '=', False), ('company_id', '=', rec.company_id.id),
                    ('active', '=', True),
                ], order='sequence, id')
                for dep in departments:
                    self.env['dm.hr.offboarding.clearance.line'].create({
                        'offboarding_id': rec.id,
                        'department_id': dep.id,
                        'responsible_user_id': dep.responsible_user_id.id,
                        'description': dep.default_description,
                        'mandatory': dep.mandatory,
                        'due_date': rec.approved_last_work_date,
                    })
            delivered = self.env['dm.hr.custody'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'delivered')])
            for custody in delivered:
                if not rec.clearance_line_ids.filtered(lambda l: l.custody_id == custody):
                    self.env['dm.hr.offboarding.clearance.line'].create({
                        'offboarding_id': rec.id,
                        'description': _('استلام عهدة: %s') % custody.display_name,
                        'mandatory': True,
                        'has_custody': True,
                        'custody_id': custody.id,
                        'due_date': rec.approved_last_work_date,
                    })

    def _ensure_clearance_ready(self):
        for rec in self:
            if rec.termination_type_id.requires_clearance:
                rec._ensure_clearance_lines()
                pending = rec.clearance_line_ids.filtered(lambda l: l.mandatory and l.state not in ('approved', 'waived'))
                if pending:
                    pending_names = '\n- '.join(pending[:8].mapped('description'))
                    more = len(pending) - 8
                    if more > 0:
                        pending_names += _('\n- و %s بنود أخرى') % more
                    raise UserError(_(
                        'لا يمكن إكمال إخلاء الطرف لأن هناك بنودًا إلزامية لم تعتمد أو تستثن بعد:\n'
                        '- %s\n\n'
                        'افتح تبويب إخلاء الطرف، واعتمد كل بند أو أدخل سبب الاستثناء للبنود التي سيتم تجاوزها.'
                    ) % pending_names)

    def action_generate_clearance(self):
        self._ensure_clearance_lines()

    def action_generate_settlement(self):
        for rec in self:
            if rec.settlement_id:
                continue
            settlement = self.env['dm.hr.offboarding.settlement'].create({'offboarding_id': rec.id})
            rec.settlement_id = settlement.id
            settlement.action_compute_lines()

    def action_open_settlement(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('التسوية النهائية'),
            'res_model': 'dm.hr.offboarding.settlement',
            'view_mode': 'form',
            'res_id': self.settlement_id.id,
        }

    def _compute_eos_amount_details(self):
        self.ensure_one()
        if not self.termination_type_id.eos_eligible:
            return 0.0, _('نوع الإنهاء غير مستحق للمكافأة.')
        if self.eos_manual_override:
            return self.eos_manual_amount, _('تم استخدام قيمة يدوية: %s') % (self.eos_manual_reason or '')
        rule = self._get_eos_rule()
        years = self.service_years
        wage = self.eos_base_wage
        first_years = min(years, rule.first_period_years)
        later_years = max(years - rule.first_period_years, 0.0)
        base = (first_years * wage * rule.first_period_month_ratio) + (later_years * wage * rule.later_period_month_ratio)
        ratio = (self.termination_type_id.default_entitlement_ratio or 0.0) / 100.0
        code = self.termination_type_id.code
        if code == 'resignation' and not self.termination_type_id.full_entitlement_exception:
            if years < rule.resignation_no_entitlement_years:
                ratio = 0.0
            elif years < rule.resignation_one_third_years:
                ratio = min(ratio, 1.0 / 3.0)
            elif years < rule.resignation_two_third_years:
                ratio = min(ratio, 2.0 / 3.0)
            else:
                ratio = min(ratio, 1.0)
        amount = round(base * ratio, rule.rounding_digits)
        explanation = _('سنوات الخدمة: %(years).2f، الأجر: %(wage).2f، أساس المكافأة: %(base).2f، نسبة الاستحقاق: %(ratio).2f%%') % {
            'years': years, 'wage': wage, 'base': base, 'ratio': ratio * 100.0,
        }
        return amount, explanation

    def _execute_completion(self):
        for rec in self:
            if rec.completion_executed:
                raise UserError(_('تم تنفيذ الإنهاء مسبقًا ولا يمكن تكراره.'))
            if rec.termination_type_id.can_close_contract and rec.contract_id:
                vals = {'date_end': rec.approved_last_work_date or rec.requested_last_work_date}
                if 'state' in rec.contract_id._fields:
                    vals['state'] = 'close'
                rec.contract_id.write(vals)
            emp_vals = {}
            if 'dm_employment_status' in rec.employee_id._fields:
                emp_vals['dm_employment_status'] = 'terminated'
            if rec.archive_employee or rec.termination_type_id.allow_archive_employee:
                emp_vals['active'] = False
            if emp_vals:
                rec.employee_id.write(emp_vals)
            if not rec.exit_interview_id:
                rec.exit_interview_id = self.env['dm.hr.exit.interview'].create({
                    'offboarding_id': rec.id,
                    'employee_id': rec.employee_id.id,
                    'company_id': rec.company_id.id,
                }).id
            rec.write({'completion_executed': True, 'employee_status': 'terminated'})

    def action_reopen_admin(self):
        if not self.env.user.has_group('dm_hr_offboarding.group_dm_hr_offboarding_admin'):
            raise AccessError(_('إعادة فتح طلب منتهي متاحة لمدير النظام فقط.'))
        self.write({'state': 'final_approval', 'completion_executed': False})


class DmHrOffboardingApprovalItem(models.Model):
    _name = 'dm.hr.offboarding.approval.item'
    _description = 'خطوة اعتماد إنهاء الخدمة'
    _order = 'offboarding_id, sequence, id'

    offboarding_id = fields.Many2one('dm.hr.offboarding', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='offboarding_id.company_id', store=True, readonly=True)
    policy_step_id = fields.Many2one('dm.hr.approval.policy.step', readonly=True)
    sequence = fields.Integer(readonly=True)
    name = fields.Char(string='الخطوة', readonly=True)
    approver_user_id = fields.Many2one('res.users', string='المعتمد المحدد', readonly=True)
    approver_group_id = fields.Many2one('res.groups', string='مجموعة الاعتماد', readonly=True)
    require_comment = fields.Boolean(readonly=True)
    delegate_user_id = fields.Many2one('res.users', readonly=True)
    instructions = fields.Text(readonly=True)
    state = fields.Selection([('pending', 'بانتظار'), ('approved', 'معتمد'), ('rejected', 'مرفوض'), ('cancelled', 'ملغي')], default='pending', readonly=True)
    action_by_id = fields.Many2one('res.users', readonly=True)
    action_date = fields.Datetime(readonly=True)
    comment = fields.Text(readonly=True)

    def action_approve(self):
        self.write({'state': 'approved', 'action_by_id': self.env.user.id, 'action_date': fields.Datetime.now()})

    def action_reject(self):
        self.write({'state': 'rejected', 'action_by_id': self.env.user.id, 'action_date': fields.Datetime.now()})


class DmHrOffboardingClearanceDepartment(models.Model):
    _name = 'dm.hr.offboarding.clearance.department'
    _description = 'قسم إخلاء طرف إنهاء الخدمة'
    _order = 'company_id, sequence, name'

    name = fields.Char(string='القسم', required=True, translate=True)
    code = fields.Char(string='الكود', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة')
    responsible_user_id = fields.Many2one('res.users', string='المسؤول الافتراضي')
    mandatory = fields.Boolean(string='إلزامي', default=True)
    default_description = fields.Text(string='وصف افتراضي')


class DmHrOffboardingClearanceLine(models.Model):
    _name = 'dm.hr.offboarding.clearance.line'
    _description = 'بند إخلاء طرف إنهاء الخدمة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'offboarding_id, sequence, id'

    sequence = fields.Integer(default=10)
    offboarding_id = fields.Many2one('dm.hr.offboarding', string='طلب إنهاء الخدمة', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='offboarding_id.company_id', store=True, readonly=True)
    employee_id = fields.Many2one(related='offboarding_id.employee_id', store=True, readonly=True)
    department_id = fields.Many2one('dm.hr.offboarding.clearance.department', string='جهة الإخلاء')
    responsible_user_id = fields.Many2one('res.users', string='المسؤول')
    description = fields.Text(string='الوصف', required=True)
    mandatory = fields.Boolean(string='إلزامي', default=True)
    due_date = fields.Date(string='تاريخ الاستحقاق')
    has_custody = fields.Boolean(string='مرتبط بعهدة')
    custody_id = fields.Many2one('dm.hr.custody', string='العهدة')
    custody_value = fields.Monetary(string='قيمة العهدة/الحسم')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    received = fields.Boolean(string='تم الاستلام')
    custody_condition = fields.Selection(
        [('not_applicable', 'لا ينطبق'), ('good', 'سليمة'), ('damaged', 'تالفة'), ('lost', 'مفقودة')],
        default='not_applicable',
        string='حالة العهدة',
    )
    deduction_amount = fields.Monetary(string='مبلغ الحسم')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    notes = fields.Text(string='ملاحظات')
    override_reason = fields.Text(string='سبب الاستثناء')
    approved_by_id = fields.Many2one('res.users', string='اعتمد بواسطة', readonly=True)
    approved_date = fields.Datetime(string='تاريخ الاعتماد', readonly=True)
    state = fields.Selection([('pending', 'بانتظار'), ('approved', 'معتمد'), ('rejected', 'مرفوض'), ('waived', 'مستثنى')], default='pending', tracking=True)

    def action_approve(self):
        for rec in self:
            vals = {'state': 'approved', 'approved_by_id': self.env.user.id, 'approved_date': fields.Datetime.now()}
            if rec.custody_id and rec.received:
                rec.custody_id.action_return()
            elif rec.custody_id and rec.deduction_amount:
                rec.custody_id.action_lost()
            rec.write(vals)

    def action_waive(self):
        for rec in self:
            if rec.mandatory and not rec.override_reason:
                raise UserError(_(
                    'لا يمكن استثناء بند إلزامي بدون سبب واضح.\n\n'
                    'اكتب سبب الاستثناء في حقل "سبب الاستثناء"، ثم اضغط استثناء مرة أخرى.'
                ))
            rec.write({'state': 'waived', 'approved_by_id': self.env.user.id, 'approved_date': fields.Datetime.now()})

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrOffboardingSettlement(models.Model):
    _name = 'dm.hr.offboarding.settlement'
    _description = 'التسوية النهائية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(string='رقم التسوية', default='جديد', copy=False, readonly=True, tracking=True)
    offboarding_id = fields.Many2one('dm.hr.offboarding', string='طلب إنهاء الخدمة', required=True, ondelete='restrict')
    employee_id = fields.Many2one(related='offboarding_id.employee_id', store=True, readonly=True)
    company_id = fields.Many2one(related='offboarding_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='offboarding_id.currency_id', store=True, readonly=True)
    settlement_date = fields.Date(string='تاريخ التسوية', default=fields.Date.context_today, required=True)
    line_ids = fields.One2many('dm.hr.offboarding.settlement.line', 'settlement_id', string='بنود التسوية')
    earnings_total = fields.Monetary(string='إجمالي المستحقات', compute='_compute_totals', store=True)
    deductions_total = fields.Monetary(string='إجمالي الحسميات', compute='_compute_totals', store=True)
    net_amount = fields.Monetary(string='الصافي', compute='_compute_totals', store=True)
    eos_explanation = fields.Text(string='شرح مكافأة نهاية الخدمة', readonly=True)
    state = fields.Selection([('draft', 'مسودة'), ('ready', 'جاهزة'), ('approved', 'معتمدة'), ('paid', 'مدفوعة'), ('cancelled', 'ملغية')], default='draft', tracking=True)

    _sql_constraints = [('offboarding_uniq', 'unique(offboarding_id)', 'لا يمكن إنشاء أكثر من تسوية لنفس طلب إنهاء الخدمة.')]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.offboarding.settlement') or 'جديد'
        return super().create(vals_list)

    @api.depends('line_ids.amount', 'line_ids.line_type')
    def _compute_totals(self):
        for rec in self:
            rec.earnings_total = sum(rec.line_ids.filtered(lambda l: l.line_type == 'earning').mapped('amount'))
            rec.deductions_total = sum(rec.line_ids.filtered(lambda l: l.line_type == 'deduction').mapped('amount'))
            rec.net_amount = rec.earnings_total - rec.deductions_total

    def action_compute_lines(self):
        for rec in self:
            if rec.state not in ('draft', 'ready'):
                raise UserError(_('لا يمكن إعادة احتساب تسوية معتمدة.'))
            rec.line_ids.unlink()
            off = rec.offboarding_id
            lines = []
            eos_amount, explanation = off._compute_eos_amount_details()
            rec.eos_explanation = explanation
            if eos_amount:
                lines.append((0, 0, {'line_type': 'earning', 'source': 'eos', 'description': _('مكافأة نهاية الخدمة'), 'quantity': 1, 'price_unit': eos_amount}))
            wage = off.contract_id.wage or 0.0
            if wage and (off.approved_last_work_date or off.requested_last_work_date):
                last = off.approved_last_work_date or off.requested_last_work_date
                qty = last.day
                lines.append((0, 0, {'line_type': 'earning', 'source': 'salary', 'description': _('راتب حتى آخر يوم عمل'), 'quantity': qty, 'price_unit': wage / 30.0, 'payroll_postable': True}))
            leave_amount = rec._get_leave_balance_amount()
            if leave_amount:
                lines.append((0, 0, {'line_type': 'earning', 'source': 'leave_balance', 'description': _('رصيد إجازات مستحق'), 'quantity': 1, 'price_unit': leave_amount}))
            for line in off.clearance_line_ids.filtered(lambda l: l.deduction_amount):
                lines.append((0, 0, {'line_type': 'deduction', 'source': 'custody', 'description': line.description, 'quantity': 1, 'price_unit': line.deduction_amount}))
            if 'dm.hr.employee.financial.installment' in self.env:
                installment_model = self.env['dm.hr.employee.financial.installment']
                installments = installment_model.search([
                    ('employee_id', '=', off.employee_id.id),
                    ('state', 'in', ['not_due', 'due']),
                ])
                balance = sum(installments.mapped('amount'))
                if balance:
                    lines.append((0, 0, {'line_type': 'deduction', 'source': 'advance_loan', 'description': _('رصيد سلف/قروض قائم'), 'quantity': 1, 'price_unit': balance}))
            if off.notice_difference_days < 0 and wage:
                lines.append((0, 0, {'line_type': 'deduction', 'source': 'notice', 'description': _('حسم نقص مدة الإشعار'), 'quantity': abs(off.notice_difference_days), 'price_unit': wage / 30.0}))
            rec.write({'line_ids': lines, 'state': 'ready'})

    def _get_leave_balance_amount(self):
        self.ensure_one()
        wage = self.offboarding_id.contract_id.wage or 0.0
        if not wage:
            return 0.0
        balance = 0.0
        for leave_type in self.env['hr.leave.type'].search([('requires_allocation', '!=', 'no')]):
            balance += leave_type.with_context(employee_id=self.employee_id.id).virtual_remaining_leaves or 0.0
        return max(balance, 0.0) * wage / 30.0

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class DmHrOffboardingSettlementLine(models.Model):
    _name = 'dm.hr.offboarding.settlement.line'
    _description = 'بند التسوية النهائية'
    _order = 'settlement_id, sequence, id'

    settlement_id = fields.Many2one('dm.hr.offboarding.settlement', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(related='settlement_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='settlement_id.currency_id', store=True, readonly=True)
    line_type = fields.Selection([('earning', 'استحقاق'), ('deduction', 'حسم')], required=True, default='earning')
    source = fields.Selection([
        ('salary', 'راتب'), ('eos', 'مكافأة نهاية الخدمة'), ('leave_balance', 'رصيد إجازات'),
        ('overtime', 'عمل إضافي'), ('commission', 'عمولات'), ('bonus', 'مكافآت'),
        ('allowance', 'بدلات/مطالبات'), ('advance_loan', 'سلف/قروض'), ('custody', 'عهد'),
        ('notice', 'إشعار'), ('absence', 'غياب/تأخير'), ('other', 'أخرى'),
    ], required=True, default='other')
    description = fields.Char(string='الوصف', required=True)
    quantity = fields.Float(string='الكمية', default=1.0)
    price_unit = fields.Monetary(string='السعر')
    amount = fields.Monetary(string='الإجمالي', compute='_compute_amount', store=True)
    payroll_postable = fields.Boolean(string='قابل للترحيل للرواتب')
    posted_to_payroll = fields.Boolean(string='مرحل للرواتب', readonly=True)

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.quantity or 0.0) * (rec.price_unit or 0.0)


class DmHrExitInterview(models.Model):
    _name = 'dm.hr.exit.interview'
    _description = 'مقابلة الخروج'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='المرجع', default='جديد', copy=False, readonly=True)
    offboarding_id = fields.Many2one('dm.hr.offboarding', string='طلب إنهاء الخدمة', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True)
    company_id = fields.Many2one('res.company', string='الشركة', required=True, default=lambda self: self.env.company)
    interview_date = fields.Date(string='تاريخ المقابلة', default=fields.Date.context_today)
    satisfaction = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string='مستوى الرضا')
    reason_summary = fields.Text(string='ملخص الأسباب')
    recommendations = fields.Text(string='توصيات HR')
    can_return = fields.Boolean(string='يمكن إعادة التوظيف مستقبلًا')
    confidential_notes = fields.Text(string='ملاحظات سرية')
    state = fields.Selection([('draft', 'مسودة'), ('submitted', 'معتمدة')], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.exit.interview') or 'جديد'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})
