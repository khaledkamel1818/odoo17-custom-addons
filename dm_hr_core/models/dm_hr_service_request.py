# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class DmHrServiceRequest(models.Model):
    _name = 'dm.hr.service.request'
    _description = 'طلب خدمة موظف'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='رقم الطلب',
        default='/',
        copy=False,
        readonly=True,
        tracking=True,
    )
    subject = fields.Char(string='موضوع الطلب', required=True, tracking=True)
    request_type_id = fields.Many2one(
        'dm.hr.service.request.type',
        string='نوع الطلب',
        required=True,
        tracking=True,
        default=lambda self: self._default_request_type_id(),
    )
    request_type = fields.Selection(
        selection='_selection_request_type',
        string='كود نوع الطلب',
        compute='_compute_request_type',
        store=True,
        readonly=True,
        index=True,
    )
    request_type_config_id = fields.Many2one(
        'dm.hr.service.request.type',
        string='إعداد نوع الطلب',
        related='request_type_id',
        store=True,
        readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف',
        default=lambda self: self._default_employee_id(),
        required=True,
        tracking=True,
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='المستخدم',
        related='employee_id.user_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='الإدارة',
        related='employee_id.department_id',
        store=True,
        readonly=True,
    )
    branch_id = fields.Many2one(
        'dm.hr.branch',
        string='الفرع',
        related='employee_id.dm_branch_id',
        store=True,
        readonly=True,
    )
    sector_id = fields.Many2one(
        'hr.department',
        string='القطاع',
        related='employee_id.dm_sector_id',
        store=True,
        readonly=True,
    )
    department_level_id = fields.Many2one(
        'hr.department',
        string='الإدارة (الهيكل)',
        related='employee_id.dm_department_level_id',
        store=True,
        readonly=True,
    )
    section_id = fields.Many2one(
        'hr.department',
        string='القسم',
        related='employee_id.dm_section_id',
        store=True,
        readonly=True,
    )
    unit_id = fields.Many2one(
        'hr.department',
        string='الوحدة',
        related='employee_id.dm_unit_id',
        store=True,
        readonly=True,
    )
    job_id = fields.Many2one(
        'hr.job',
        string='المسمى الوظيفي',
        related='employee_id.job_id',
        store=True,
        readonly=True,
    )
    manager_user_id = fields.Many2one(
        'res.users',
        string='المدير المباشر',
        compute='_compute_manager_user_id',
        store=True,
        readonly=True,
    )
    date_from = fields.Datetime(string='من تاريخ')
    date_to = fields.Datetime(string='إلى تاريخ')
    duration_hours = fields.Float(
        string='المدة بالساعات',
        compute='_compute_duration_hours',
        store=True,
    )
    priority = fields.Selection(
        [('0', 'عادي'), ('1', 'مهم'), ('2', 'عاجل')],
        string='الأولوية',
        default='0',
        tracking=True,
    )
    description = fields.Text(string='تفاصيل الطلب')
    permission_kind = fields.Selection(
        [('late_arrival', 'تأخير'), ('early_leave', 'انصراف مبكر'), ('personal', 'شخصي'), ('medical', 'طبي'), ('other', 'أخرى')],
        string='نوع الاستئذان',
    )
    permission_reason = fields.Text(string='سبب الاستئذان')
    letter_language = fields.Selection([('ar', 'العربية'), ('en', 'English')], string='لغة الخطاب', default='ar')
    letter_reference = fields.Char(string='الرقم المرجعي للخطاب', readonly=True, copy=False)
    letter_recipient = fields.Char(
        string='موجه إلى',
        help='الجهة المطلوب توجيه الخطاب لها، مثل بنك أو سفارة أو جهة حكومية.',
    )
    letter_purpose = fields.Selection(
        [
            ('bank', 'بنك / تمويل'),
            ('embassy', 'سفارة / تأشيرة'),
            ('government', 'جهة حكومية'),
            ('landlord', 'مالك عقار'),
            ('other', 'أخرى'),
        ],
        string='غرض الخطاب',
    )
    bank_name = fields.Char(string='اسم البنك')
    iban = fields.Char(string='IBAN')
    include_allowances = fields.Boolean(
        string='إظهار البدلات في الخطاب',
        default=True,
    )
    trip_type = fields.Selection([('internal', 'داخلي'), ('external', 'خارجي')], string='نوع الانتداب')
    trip_location = fields.Char(string='مكان الانتداب')
    trip_mission = fields.Text(string='المهمة')
    project_name = fields.Char(string='المشروع')
    cost_center = fields.Char(string='مركز التكلفة')
    need_ticket = fields.Boolean(string='يتطلب تذاكر')
    need_accommodation = fields.Boolean(string='يتطلب سكن')
    allowance_amount = fields.Monetary(string='بدل الانتداب')
    advance_amount = fields.Monetary(string='السلفة')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    salary_compliance_note = fields.Text(
        string='فحص امتثال الراتب',
        compute='_compute_salary_compliance_note',
    )
    hr_notes = fields.Text(string='ملاحظات الموارد البشرية')
    rejection_reason = fields.Text(string='سبب الرفض')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'dm_hr_service_request_attachment_rel',
        'request_id',
        'attachment_id',
        string='المرفقات',
    )
    attachment_count = fields.Integer(
        string='عدد المرفقات',
        compute='_compute_attachment_count',
    )
    submitted_on = fields.Datetime(string='تاريخ الإرسال', readonly=True)
    approved_on = fields.Datetime(string='تاريخ الاعتماد', readonly=True)
    rejected_on = fields.Datetime(string='تاريخ الرفض', readonly=True)
    approver_user_id = fields.Many2one(
        'res.users',
        string='آخر معتمد',
        readonly=True,
        tracking=True,
    )
    approval_policy_id = fields.Many2one(
        'dm.hr.approval.policy', string='سياسة الموافقات', readonly=True, copy=False,
        tracking=True, check_company=True,
    )
    approval_policy_preview_id = fields.Many2one(
        'dm.hr.approval.policy',
        string='السياسة المتوقعة',
        compute='_compute_approval_preview',
        readonly=True,
    )
    approval_route_preview = fields.Text(
        string='مسار الموافقة المتوقع',
        compute='_compute_approval_preview',
        readonly=True,
    )
    submitted_org_snapshot = fields.Text(
        string='لقطة الهيكل وقت التقديم',
        readonly=True,
        copy=False,
        help='تُحفظ عند إرسال الطلب حتى لا تتغير بيانات الطلب التاريخية إذا تغير هيكل الموظف لاحقاً.',
    )
    approval_item_ids = fields.One2many(
        'dm.hr.service.approval.item', 'request_id', string='سجل الموافقات',
        readonly=True, copy=False,
    )
    current_approval_item_id = fields.Many2one(
        'dm.hr.service.approval.item', string='خطوة الاعتماد الحالية',
        compute='_compute_current_approval', readonly=True,
    )
    current_approval_label = fields.Char(
        string='بانتظار', compute='_compute_current_approval', readonly=True,
    )
    approval_comment = fields.Text(
        string='تعليق الاعتماد', copy=False,
        help='يُحفظ في سجل الخطوة الحالية عند الاعتماد.',
    )
    state = fields.Selection(
        [
            ('draft', 'مسودة'),
            ('submitted', 'بانتظار المدير'),
            ('manager_approved', 'بانتظار الموارد البشرية'),
            ('approved', 'معتمد'),
            ('rejected', 'مرفوض'),
            ('cancelled', 'ملغي'),
        ],
        string='الحالة',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )
    saudi_policy_note = fields.Text(
        string='مرجع سعودي مختصر',
        compute='_compute_saudi_policy_note',
    )

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if employee:
            return employee.id
        return self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id),
             ('company_id', 'in', self.env.companies.ids)],
            limit=1,
        ).id

    @api.model
    def _default_request_type_id(self):
        return self.env['dm.hr.service.request.type'].search([
            ('code', '=', 'permission'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

    @api.model
    def _selection_request_type(self):
        return self.env['dm.hr.service.request.type'].sudo().search([]).mapped(
            lambda r: (r.code, r.name)
        )

    @api.depends('request_type_id', 'request_type_id.code')
    def _compute_request_type(self):
        for request in self:
            request.request_type = request.request_type_id.code or False

    @api.depends('employee_id.parent_id.user_id')
    def _compute_manager_user_id(self):
        for request in self:
            request.manager_user_id = request.employee_id.parent_id.user_id

    @api.depends('date_from', 'date_to')
    def _compute_duration_hours(self):
        for request in self:
            if request.date_from and request.date_to:
                delta = request.date_to - request.date_from
                request.duration_hours = max(delta.total_seconds() / 3600.0, 0.0)
            else:
                request.duration_hours = 0.0

    def _compute_attachment_count(self):
        for request in self:
            request.attachment_count = len(request.attachment_ids)

    @api.depends('approval_item_ids.state', 'approval_item_ids.sequence')
    def _compute_current_approval(self):
        for request in self:
            item = request.approval_item_ids.filtered(
                lambda line: line.state == 'pending'
            ).sorted(lambda line: (line.sequence, line.id))[:1]
            request.current_approval_item_id = item
            request.current_approval_label = item.name if item else False

    @api.depends(
        'request_type', 'employee_id', 'branch_id', 'sector_id',
        'department_level_id', 'section_id', 'unit_id', 'department_id',
        'job_id', 'priority',
        'date_from', 'date_to', 'duration_hours', 'company_id',
    )
    def _compute_approval_preview(self):
        for request in self:
            policy = request._find_approval_policy()
            request.approval_policy_preview_id = policy
            request.approval_route_preview = request._build_approval_route_preview(policy)

    @api.depends('request_type')
    def _compute_saudi_policy_note(self):
        notes = {
            'permission': _(
                'مرجع تشغيلي: الاستئذان الداخلي يراجع حسب سياسة الشركة، مع مراعاة ألا تؤدي الجداول إلى مخالفة حدود ساعات العمل والراحة.'),
            'overtime': _(
                'مرجع سعودي: ساعات العمل الإضافية تحتاج موافقة، ويحتسب أجرها وفق نظام العمل وسياسة الشركة المعتمدة.'),
            'business_trip': _(
                'مرجع تشغيلي: الانتداب أو مهمة العمل يجب أن يوضح المدة والوجهة والتكلفة والمسؤول المباشر.'),
            'salary_certificate': _(
                'مرجع تشغيلي: خطاب التعريف بالراتب يصدر بعد تحقق الموارد البشرية من بيانات العقد والراتب والهوية.'),
            'salary_transfer_certificate': _(
                'مرجع سعودي: تثبيت الراتب يرتبط عادة بحساب بنكي معتمد، ويتوافق تشغيليًا مع متطلبات حماية الأجور والتحويل عبر البنوك المرخصة.'),
            'experience_certificate': _(
                'مرجع تشغيلي: شهادة الخبرة تصدر بناءً على بيانات الخدمة الفعلية وسجل العقد.'),
        }
        default_note = _(
            'مرجع تشغيلي: راجع الطلب وفق سياسة الشركة ونظام العمل السعودي والبيانات المعتمدة في ملف الموظف.')
        for request in self:
            request.saudi_policy_note = notes.get(request.request_type, default_note)

    @api.depends('request_type', 'employee_id', 'bank_name', 'iban')
    def _compute_salary_compliance_note(self):
        Contract = self.env['hr.contract'].sudo()
        for request in self:
            if request.request_type not in ('salary_certificate', 'salary_transfer_certificate'):
                request.salary_compliance_note = False
                continue
            contract = Contract.search([
                ('employee_id', '=', request.employee_id.id),
                ('state', 'in', ['open', 'draft']),
            ], order='date_start desc, id desc', limit=1)
            checks = []
            checks.append(_('العقد: %s') % (_('موجود') if contract else _('لا يوجد عقد نشط/مسودة')))
            if contract:
                checks.append(_('طريقة الدفع: %s') % dict(contract._fields['dm_payment_method']._description_selection(self.env)).get(contract.dm_payment_method, contract.dm_payment_method))
                checks.append(_('الأجر الأساسي: %s') % (contract.wage or 0.0))
            checks.append(_('البنك/IBAN: %s') % (_('مكتمل') if (request.bank_name and request.iban) else _('غير مكتمل')))
            request.salary_compliance_note = '\n'.join(checks)

    @api.constrains('date_from', 'date_to', 'request_type')
    def _check_dates(self):
        timed_types = {'permission', 'remote_work', 'overtime', 'business_trip'}
        for request in self:
            if request.date_from and request.date_to and request.date_to < request.date_from:
                raise ValidationError(_('تاريخ نهاية الطلب يجب أن يكون بعد تاريخ البداية.'))
            if request.request_type in timed_types and (not request.date_from or not request.date_to):
                raise ValidationError(_('هذا النوع من الطلبات يحتاج تاريخ بداية ونهاية.'))
            if request.request_type == 'salary_transfer_certificate':
                if not request.bank_name or not request.iban:
                    raise ValidationError(_('طلب تثبيت الراتب يحتاج اسم البنك ورقم IBAN.'))
                if request.iban and not request.iban.replace(' ', '').upper().startswith('SA'):
                    raise ValidationError(_('رقم IBAN السعودي يجب أن يبدأ بـ SA.'))
            if request.request_type == 'permission':
                request._check_permission_controls()
            if request.request_type == 'business_trip' and (not request.trip_type or not request.trip_location or not request.trip_mission):
                raise ValidationError(_('طلب الانتداب يحتاج نوع الانتداب والمكان ووصف المهمة.'))

    def _check_permission_controls(self):
        self.ensure_one()
        if not self.date_from or not self.date_to:
            return
        overlap = self.search_count([
            ('id', '!=', self.id),
            ('employee_id', '=', self.employee_id.id),
            ('request_type', '=', 'permission'),
            ('state', 'not in', ['cancelled', 'rejected']),
            ('date_from', '<', self.date_to),
            ('date_to', '>', self.date_from),
        ])
        if overlap:
            raise ValidationError(_('يوجد استئذان آخر متداخل مع نفس الفترة.'))
        config = self.request_type_config_id
        if not config:
            return
        month_start = self.date_from.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = self.date_from.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        same_requests = self.search([
            ('id', '!=', self.id),
            ('employee_id', '=', self.employee_id.id),
            ('request_type', '=', 'permission'),
            ('state', 'not in', ['cancelled', 'rejected']),
            ('date_from', '>=', year_start),
        ])
        yearly = sum(same_requests.mapped('duration_hours')) + self.duration_hours
        monthly = sum(same_requests.filtered(lambda req: req.date_from >= month_start).mapped('duration_hours')) + self.duration_hours
        if config.monthly_limit_hours and monthly > config.monthly_limit_hours:
            raise ValidationError(_('تجاوزت حد الاستئذان الشهري المسموح: %s ساعة.') % config.monthly_limit_hours)
        if config.yearly_limit_hours and yearly > config.yearly_limit_hours:
            raise ValidationError(_('تجاوزت حد الاستئذان السنوي المسموح: %s ساعة.') % config.yearly_limit_hours)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code(
                    'dm.hr.service.request') or '/'
            request_type_id = vals.get('request_type_id')
            if request_type_id:
                type_rec = self.env['dm.hr.service.request.type'].sudo().browse(request_type_id)
                if not vals.get('letter_reference') and type_rec.code in ('salary_certificate', 'salary_transfer_certificate'):
                    vals['letter_reference'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.service.letter') or '/'
        requests = super().create(vals_list)
        requests._check_employee_scope()
        return requests

    def write(self, vals):
        if self.env.context.get('dm_hr_approval_engine'):
            return super().write(vals)
        self._check_employee_scope(vals)
        if 'employee_id' in vals and not self._is_hr_user():
            raise AccessError(_('لا يمكنك نقل الطلب إلى موظف آخر.'))
        return super().write(vals)

    def _is_hr_user(self):
        return any([
            self.env.user.has_group('dm_hr_core.group_dm_hr_officer'),
            self.env.user.has_group('dm_hr_core.group_dm_hr_manager'),
            self.env.user.has_group('dm_hr_core.group_dm_hr_admin'),
        ])

    def _check_employee_scope(self, vals=None):
        if self._is_hr_user():
            return
        employee_id = vals.get('employee_id') if vals else False
        records = self
        if employee_id:
            records = self.browse()
            employee = self.env['hr.employee'].sudo().browse(employee_id)
            if employee.user_id != self.env.user:
                raise AccessError(_('يمكنك إنشاء طلباتك الشخصية فقط.'))
        for request in records:
            if request.user_id != self.env.user:
                raise AccessError(_('يمكنك التعامل مع طلباتك الشخصية فقط.'))

    def _can_manager_approve(self):
        self.ensure_one()
        return (
            self._is_hr_user()
            or self.manager_user_id == self.env.user
            or self.employee_id.leave_manager_id == self.env.user
        )

    def _find_approval_policy(self):
        self.ensure_one()
        Policy = self.env['dm.hr.approval.policy'].sudo()
        base = [
            ('active', '=', True),
            ('company_id', '=', self.company_id.id),
            '|', ('apply_to_all_types', '=', True), ('request_type_id', '=', self.request_type_id.id),
        ]
        candidates = Policy.search(base)
        matched = candidates.filtered(lambda policy: self._policy_matches_request(policy))
        return matched.sorted(lambda policy: (-self._policy_specificity(policy), policy.sequence, policy.id))[:1]

    def _policy_matches_request(self, policy):
        self.ensure_one()
        if policy.branch_id and self.branch_id != policy.branch_id:
            return False
        if policy.sector_id and not self._policy_department_matches(policy, policy.sector_id):
            return False
        if policy.department_id and not self._policy_department_matches(policy, policy.department_id):
            return False
        if policy.section_id and not self._policy_department_matches(policy, policy.section_id):
            return False
        if policy.unit_id and not self._policy_department_matches(policy, policy.unit_id):
            return False
        if policy.job_id and self.job_id != policy.job_id:
            return False
        if policy.priority_filter and self.priority != policy.priority_filter:
            return False
        if policy.min_duration_hours and self.duration_hours < policy.min_duration_hours:
            return False
        if policy.max_duration_hours and self.duration_hours > policy.max_duration_hours:
            return False
        if policy.min_service_years and self._employee_service_years() < policy.min_service_years:
            return False
        return True

    def _policy_department_matches(self, policy, policy_department):
        self.ensure_one()
        employee_departments = (
            self.sector_id | self.department_level_id |
            self.section_id | self.unit_id | self.department_id
        )
        if not policy_department or not employee_departments:
            return False
        if policy_department in employee_departments:
            return True
        if policy.apply_on_child_levels:
            child_departments = policy_department.search([('id', 'child_of', policy_department.id)])
            return bool(employee_departments & child_departments)
        return False

    def _policy_specificity(self, policy):
        score = 0
        if policy.request_type_id:
            score += 64 if policy.request_type_id.code == self.request_type else 0
        elif policy.request_type == 'all':
            score += 32
        elif policy.request_type == 'offboarding' and self.request_type == 'offboarding':
            score += 64
        score += 48 if policy.branch_id else 0
        score += 12 if policy.sector_id else 0
        score += 24 if policy.department_id else 0
        score += 36 if policy.section_id else 0
        score += 44 if policy.unit_id else 0
        score += 16 if policy.job_id else 0
        score += 8 if policy.priority_filter else 0
        score += 4 if policy.min_duration_hours or policy.max_duration_hours else 0
        score += 2 if policy.min_service_years else 0
        return score

    def _employee_service_years(self):
        self.ensure_one()
        join_date = self.employee_id.join_date
        if not join_date:
            return 0.0
        return max((fields.Date.today() - join_date).days / 365.0, 0.0)

    def _resolve_step_approver(self, step):
        self.ensure_one()
        assigned_user = step.user_id
        if step.approver_type == 'manager':
            assigned_user = self.manager_user_id or self.employee_id.leave_manager_id
        elif step.approver_type == 'department_manager':
            assigned_user = self._get_department_approval_user()
        elif step.approver_type == 'parent_department_manager':
            assigned_user = self._get_parent_department_approval_user()
        elif step.approver_type == 'job_role':
            assigned_user = self._get_job_role_approval_user(step.job_approval_role)
        return assigned_user

    def _build_approval_route_preview(self, policy):
        self.ensure_one()
        if not policy:
            return _('لا توجد سياسة موافقات مطابقة. سيستخدم النظام المسار الافتراضي: المدير المباشر ثم الموارد البشرية.')
        lines = [_('السياسة: %s') % policy.name]
        for index, step in enumerate(policy.step_ids.sorted(lambda line: (line.sequence, line.id)), start=1):
            assigned_user = self._resolve_step_approver(step)
            target = assigned_user.name or step.group_id.display_name or _('غير محدد')
            details = [_('%s. %s → %s') % (index, step.name, target)]
            if step.sla_hours:
                details.append(_('مهلة: %s ساعة') % step.sla_hours)
            if step.delegate_user_id:
                details.append(_('مفوّض: %s') % step.delegate_user_id.name)
            if step.escalation_user_id or policy.escalation_user_id:
                details.append(_('تصعيد: %s') % ((step.escalation_user_id or policy.escalation_user_id).name))
            if step.instructions:
                details.append(_('تعليمات: %s') % step.instructions)
            lines.append(' | '.join(details))
        return '\n'.join(lines)

    def _build_org_snapshot(self):
        self.ensure_one()
        lines = [
            _('الشركة: %s') % (self.company_id.name or ''),
            _('الفرع: %s') % (self.branch_id.name or ''),
            _('القطاع: %s') % (self.sector_id.name or ''),
            _('الإدارة: %s') % (self.department_level_id.name or ''),
            _('القسم: %s') % (self.section_id.name or ''),
            _('الوحدة: %s') % (self.unit_id.name or ''),
            _('المنصب: %s') % (self.job_id.name or ''),
            _('المدير المباشر: %s') % (self.manager_user_id.name or ''),
        ]
        return '\n'.join(lines)

    def _create_policy_approval_items(self):
        Item = self.env['dm.hr.service.approval.item'].sudo()
        for request in self:
            if not request.approval_policy_id or request.approval_item_ids:
                continue
            values = []
            steps = request.approval_policy_id.sudo().step_ids.sorted(
                lambda line: (line.sequence, line.id)
            )
            for step in steps:
                assigned_user = request._resolve_step_approver(step)
                if step.approver_type in (
                    'manager', 'user', 'department_manager',
                    'parent_department_manager', 'job_role',
                ) and not assigned_user:
                    raise UserError(_(
                        'لا يوجد معتمد محدد لخطوة "%s". راجع الهيكل والموافقات للموظف %s.'
                    ) % (step.name, request.employee_id.name))
                values.append({
                    'request_id': request.id,
                    'policy_step_id': step.id,
                    'sequence': step.sequence,
                    'name': step.name,
                        'approver_user_id': assigned_user.id,
                        'approver_group_id': step.group_id.id,
                        'deadline': fields.Datetime.add(fields.Datetime.now(), hours=step.sla_hours) if step.sla_hours else False,
                        'delegate_user_id': step.delegate_user_id.id,
                        'escalation_user_id': (step.escalation_user_id or request.approval_policy_id.escalation_user_id).id,
                        'instructions': step.instructions,
                    })
            Item.create(values)

    def _employee_user(self, employee):
        return employee.user_id if employee and employee.user_id else self.env['res.users']

    def _get_department_approval_user(self):
        self.ensure_one()
        department = self.employee_id.department_id
        approver = department.dm_approval_manager_id or department.manager_id
        return self._employee_user(approver)

    def _get_parent_department_approval_user(self):
        self.ensure_one()
        department = self.employee_id.department_id.parent_id
        while department:
            approver = department.dm_approval_manager_id or department.manager_id
            user = self._employee_user(approver)
            if user:
                return user
            department = department.parent_id
        return self.env['res.users']

    def _get_job_role_approval_user(self, role):
        self.ensure_one()
        if not role:
            return self.env['res.users']
        domain = [
            ('active', '=', True),
            ('job_id.dm_approval_role', '=', role),
            ('company_id', '=', self.company_id.id),
            ('user_id', '!=', False),
        ]
        if self.employee_id.department_id:
            scoped = self.env['hr.employee'].sudo().search(
                domain + [('department_id', 'child_of', self.employee_id.department_id.id)],
                limit=1,
            )
            if scoped:
                return scoped.user_id
        employee = self.env['hr.employee'].sudo().search(domain, limit=1)
        return employee.user_id if employee else self.env['res.users']

    def _current_policy_item(self):
        self.ensure_one()
        return self.approval_item_ids.filtered(
            lambda item: item.state == 'pending'
        ).sorted(lambda item: (item.sequence, item.id))[:1]

    def _check_can_approve_item(self, item):
        self.ensure_one()
        policy = self.approval_policy_id.sudo()
        if not policy.allow_self_approval and self.user_id == self.env.user:
            raise AccessError(_('لا يمكن لصاحب الطلب اعتماد طلبه بنفسه وفق السياسة الحالية.'))
        if item.delegate_user_id == self.env.user:
            if item.require_comment and not self.approval_comment:
                raise UserError(_('هذه الخطوة تشترط كتابة تعليق الاعتماد.'))
            return
        if item.approver_user_id and item.approver_user_id != self.env.user:
            raise AccessError(_('هذه الخطوة مخصصة لمستخدم آخر.'))
        approver_type = item.approver_type
        allowed = (
            (approver_type == 'manager' and self._can_manager_approve())
            or (approver_type == 'hr_officer' and self._is_hr_user())
            or (approver_type == 'hr_manager' and (
                self.env.user.has_group('dm_hr_core.group_dm_hr_manager')
                or self.env.user.has_group('dm_hr_core.group_dm_hr_admin')
            ))
            or (approver_type == 'user' and item.approver_user_id == self.env.user)
            or (approver_type == 'group' and item.approver_group_id in self.env.user.groups_id)
            or (approver_type in ('department_manager', 'parent_department_manager', 'job_role')
                and item.approver_user_id == self.env.user)
        )
        if not allowed:
            raise AccessError(_('لا تملك صلاحية تنفيذ خطوة الاعتماد الحالية.'))
        if item.require_comment and not self.approval_comment:
            raise UserError(_('هذه الخطوة تشترط كتابة تعليق الاعتماد.'))

    def _schedule_approval_activity(self, item, is_next=False):
        self.ensure_one()
        if not item:
            return
        note_parts = [
            _('الطلب بانتظار خطوة الاعتماد: %s') % item.name if is_next else
            _('طلب جديد بانتظار خطوة الاعتماد: %s') % item.name
        ]
        if item.deadline:
            note_parts.append(_('المهلة النهائية: %s') % fields.Datetime.to_string(item.deadline))
        if item.instructions:
            note_parts.append(_('تعليمات الخطوة: %s') % item.instructions)
        for user in (item.approver_user_id | item.delegate_user_id):
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_('اعتماد طلب موظف'),
                note='\n'.join(note_parts),
            )

    @api.model
    def cron_escalate_overdue_approvals(self):
        overdue_items = self.env['dm.hr.service.approval.item'].sudo().search([
            ('state', '=', 'pending'),
            ('deadline', '!=', False),
            ('deadline', '<', fields.Datetime.now()),
            ('escalated', '=', False),
            ('escalation_user_id', '!=', False),
        ])
        for item in overdue_items:
            item.request_id.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=item.escalation_user_id.id,
                summary=_('تصعيد موافقة متأخرة'),
                note=_('تجاوزت خطوة "%s" مهلة الاعتماد في الطلب %s.') % (item.name, item.request_id.display_name),
            )
            item.write({'escalated': True, 'escalated_on': fields.Datetime.now()})

    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                continue
            if not request.subject:
                raise UserError(_('يرجى كتابة موضوع الطلب قبل الإرسال.'))
            if request.request_type_config_id.require_attachment and not request.attachment_ids:
                raise UserError(_('هذا النوع من الطلبات يتطلب مرفقاً.'))
            policy = request._find_approval_policy()
            request.write({
                'state': 'submitted',
                'submitted_on': fields.Datetime.now(),
                'rejection_reason': False,
                'approval_policy_id': policy.id,
                'submitted_org_snapshot': request._build_org_snapshot(),
            })
            if policy:
                request._create_policy_approval_items()
            if policy:
                request._schedule_approval_activity(request._current_policy_item())
            elif request.manager_user_id:
                request.sudo().activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=request.manager_user_id.id,
                    summary=_('اعتماد طلب موظف'),
                    note=_('طلب جديد بانتظار المدير المباشر'),
                )

    def action_approve(self):
        for request in self:
            if not request.approval_policy_id:
                return request.action_manager_approve()
            if request.state not in ('submitted', 'manager_approved'):
                continue
            item = request._current_policy_item()
            if not item:
                continue
            request._check_can_approve_item(item)
            item.sudo().write({
                'state': 'approved', 'action_by_id': self.env.user.id,
                'action_date': fields.Datetime.now(),
                'comment': request.approval_comment or False,
            })
            request.with_context(dm_hr_approval_engine=True).write({
                'approver_user_id': self.env.user.id, 'approval_comment': False,
            })
            request.activity_feedback(['mail.mail_activity_data_todo'])
            next_item = request._current_policy_item()
            if next_item:
                request.with_context(dm_hr_approval_engine=True).write({'state': 'manager_approved'})
                request._schedule_approval_activity(next_item, is_next=True)
            else:
                request.with_context(dm_hr_approval_engine=True).write({
                    'state': 'approved', 'approved_on': fields.Datetime.now(),
                })

    def action_manager_approve(self):
        for request in self:
            if request.approval_policy_id:
                request.action_approve()
                continue
            if request.state != 'submitted':
                continue
            if not request._can_manager_approve():
                raise AccessError(_('هذا الطلب يحتاج اعتماد المدير المباشر أو الموارد البشرية.'))
            request.with_context(dm_hr_approval_engine=True).write({
                'state': 'manager_approved',
                'approver_user_id': self.env.user.id,
            })
            request.activity_feedback(['mail.mail_activity_data_todo'])

    def action_hr_approve(self):
        if not self._is_hr_user():
            raise AccessError(_('الاعتماد النهائي متاح للموارد البشرية فقط.'))
        for request in self:
            if request.approval_policy_id:
                request.action_approve()
                continue
            if request.state not in ('submitted', 'manager_approved'):
                continue
            request.with_context(dm_hr_approval_engine=True).write({
                'state': 'approved',
                'approved_on': fields.Datetime.now(),
                'approver_user_id': self.env.user.id,
            })
            request.activity_feedback(['mail.mail_activity_data_todo'])

    def action_reject(self):
        for request in self:
            if request.state not in ('submitted', 'manager_approved'):
                continue
            if request.approval_policy_id:
                item = request._current_policy_item()
                request._check_can_approve_item(item)
            elif not (request._can_manager_approve() or request._is_hr_user()):
                raise AccessError(_('لا تملك صلاحية رفض هذا الطلب.'))
            if not request.rejection_reason:
                raise UserError(_('يرجى كتابة سبب الرفض قبل تنفيذ الإجراء.'))
            if request.approval_policy_id:
                item.sudo().write({
                    'state': 'rejected', 'action_by_id': self.env.user.id,
                    'action_date': fields.Datetime.now(), 'comment': request.rejection_reason,
                })
            request.with_context(dm_hr_approval_engine=True).write({
                'state': 'rejected',
                'rejected_on': fields.Datetime.now(),
                'approver_user_id': self.env.user.id,
                'approval_comment': False,
            })
            request.activity_feedback(['mail.mail_activity_data_todo'])

    def action_cancel(self):
        for request in self:
            if request.state in ('approved', 'rejected'):
                raise UserError(_('لا يمكن إلغاء طلب معتمد أو مرفوض.'))
            if request.user_id != self.env.user and not request._is_hr_user():
                raise AccessError(_('يمكن إلغاء الطلب بواسطة صاحبه أو الموارد البشرية فقط.'))
            request.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        for request in self:
            if request.state not in ('rejected', 'cancelled'):
                continue
            if request.user_id != self.env.user and not request._is_hr_user():
                raise AccessError(_('يمكن إعادة الطلب بواسطة صاحبه أو الموارد البشرية فقط.'))
            request.write({
                'state': 'draft',
                'rejection_reason': False,
                'approved_on': False,
                'rejected_on': False,
                'approval_policy_id': False,
                'approval_comment': False,
            })
            request.approval_item_ids.sudo().unlink()

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('المرفقات'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }

    def action_print_request_pdf(self):
        self.ensure_one()
        xmlid = self.request_type_config_id.report_action_xmlid
        if not xmlid:
            if self.request_type == 'salary_transfer_certificate':
                xmlid = 'dm_hr_core.action_report_dm_hr_salary_transfer'
            elif self.request_type == 'salary_certificate':
                xmlid = 'dm_hr_core.action_report_dm_hr_salary_certificate'
            else:
                xmlid = 'dm_hr_core.action_report_dm_hr_service_request'
        return self.env.ref(xmlid).report_action(self)
