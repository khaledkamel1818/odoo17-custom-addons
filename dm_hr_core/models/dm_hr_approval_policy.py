# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


REQUEST_TYPES = [
    ('all', 'جميع الطلبات'), ('permission', 'استئذان'),
    ('remote_work', 'عمل عن بعد'), ('salary_certificate', 'خطاب تعريف بالراتب'),
    ('salary_transfer_certificate', 'خطاب تثبيت راتب'),
    ('experience_certificate', 'شهادة خبرة'), ('document_update', 'تحديث بيانات أو مستندات'),
    ('overtime', 'طلب ساعات إضافية'), ('business_trip', 'انتداب / مهمة عمل'),
    ('equipment', 'أدوات أو عهدة'), ('other', 'طلب آخر'),
]


class DmHrApprovalPolicy(models.Model):
    _name = 'dm.hr.approval.policy'
    _description = 'سياسة موافقات الموارد البشرية'
    _order = 'company_id, sequence, id'
    _check_company_auto = True

    name = fields.Char(string='اسم السياسة', required=True, translate=True)
    sequence = fields.Integer(string='الأولوية', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', required=True,
                                 default=lambda self: self.env.company, index=True)
    request_type = fields.Selection(REQUEST_TYPES, string='نوع الطلب', required=True, default='all')
    branch_id = fields.Many2one(
        'dm.hr.branch',
        string='فرع محدد',
        help='اتركه فارغاً لتطبيق السياسة على كل الفروع.',
    )
    sector_id = fields.Many2one(
        'hr.department',
        string='قطاع محدد',
        domain="[('dm_org_level', '=', 'sector')]",
        help='اتركه فارغاً إذا كانت السياسة لا ترتبط بقطاع.',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='إدارة محددة',
        domain="[('dm_org_level', '=', 'department')]",
        help='اتركها فارغة لتطبيق السياسة على كل الإدارات. عند تحديدها تطبق على الإدارة وفروعها.',
    )
    section_id = fields.Many2one(
        'hr.department',
        string='قسم محدد',
        domain="[('dm_org_level', '=', 'section')]",
    )
    unit_id = fields.Many2one(
        'hr.department',
        string='وحدة محددة',
        domain="[('dm_org_level', '=', 'unit')]",
    )
    apply_on_child_levels = fields.Boolean(
        string='تطبيق السياسة على المستويات التابعة',
        default=True,
        help='إذا كانت مفعلة، يمكن لسياسة القطاع أن تطبق على الإدارات والأقسام والوحدات والموظفين التابعين له.',
    )
    job_id = fields.Many2one(
        'hr.job',
        string='وظيفة محددة',
        help='اتركها فارغة لتطبيق السياسة على كل الوظائف.',
    )
    priority_filter = fields.Selection(
        [('0', 'عادي'), ('1', 'مهم'), ('2', 'عاجل')],
        string='أولوية محددة',
        help='اتركها فارغة إذا كانت السياسة لا تعتمد على أولوية الطلب.',
    )
    min_duration_hours = fields.Float(string='أقل مدة بالساعات')
    max_duration_hours = fields.Float(string='أعلى مدة بالساعات')
    min_service_years = fields.Float(string='أقل سنوات خدمة')
    allow_self_approval = fields.Boolean(string='السماح بالاعتماد الذاتي')
    step_ids = fields.One2many('dm.hr.approval.policy.step', 'policy_id', string='خطوات الاعتماد', copy=True)
    sla_hours = fields.Float(
        string='مهلة السياسة بالساعات',
        help='قيمة إرشادية عامة؛ يمكن تحديد مهلة أدق على كل خطوة.',
    )
    escalation_user_id = fields.Many2one(
        'res.users',
        string='مسؤول التصعيد العام',
        domain=[('share', '=', False)],
        help='يستخدم كمسؤول تصعيد افتراضي للخطوات التي لا تحتوي مسؤول تصعيد.',
    )
    note = fields.Text(string='ملاحظات')

    @api.constrains('active', 'step_ids')
    def _check_steps(self):
        for policy in self:
            if policy.active and not policy.step_ids:
                raise ValidationError(_('السياسة الفعالة يجب أن تحتوي على خطوة اعتماد واحدة على الأقل.'))

    @api.constrains('min_duration_hours', 'max_duration_hours', 'min_service_years', 'sla_hours')
    def _check_policy_limits(self):
        for policy in self:
            if policy.min_duration_hours < 0 or policy.max_duration_hours < 0 or policy.min_service_years < 0 or policy.sla_hours < 0:
                raise ValidationError(_('قيم المدد وسنوات الخدمة يجب ألا تكون سالبة.'))
            if policy.max_duration_hours and policy.min_duration_hours > policy.max_duration_hours:
                raise ValidationError(_('أعلى مدة يجب أن تكون أكبر من أو تساوي أقل مدة.'))

    def init(self):
        """Allow multiple scoped policies per request type.

        Older releases had a unique constraint on company/request type. The
        deeper workflow needs several policies for the same request type based
        on department, job, duration, priority, or service years.
        """
        self.env.cr.execute("""
            ALTER TABLE dm_hr_approval_policy
            DROP CONSTRAINT IF EXISTS dm_hr_approval_policy_policy_type_company_uniq
        """)
        self.env.cr.execute("""
            ALTER TABLE dm_hr_approval_policy
            DROP CONSTRAINT IF EXISTS policy_type_company_uniq
        """)


class DmHrApprovalPolicyStep(models.Model):
    _name = 'dm.hr.approval.policy.step'
    _description = 'خطوة سياسة موافقات الموارد البشرية'
    _order = 'policy_id, sequence, id'

    policy_id = fields.Many2one('dm.hr.approval.policy', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='policy_id.company_id', store=True, readonly=True)
    sequence = fields.Integer(string='الترتيب', default=10, required=True)
    name = fields.Char(string='اسم الخطوة', required=True, translate=True)
    approver_type = fields.Selection([
        ('manager', 'المدير المباشر'), ('hr_officer', 'مسؤول الموارد البشرية'),
        ('hr_manager', 'مدير الموارد البشرية'), ('user', 'مستخدم محدد'),
        ('group', 'مجموعة صلاحيات'), ('department_manager', 'مسؤول موافقات الإدارة'),
        ('parent_department_manager', 'مسؤول موافقات الإدارة الأعلى'),
        ('job_role', 'حسب دور الوظيفة'),
    ], string='جهة الاعتماد', default='manager', required=True)
    user_id = fields.Many2one('res.users', string='المستخدم', domain=[('share', '=', False)])
    group_id = fields.Many2one('res.groups', string='المجموعة')
    job_approval_role = fields.Selection(
        [
            ('department_manager', 'مدير إدارة'),
            ('section_manager', 'مدير قسم'),
            ('hr_reviewer', 'مراجع موارد بشرية'),
            ('executive', 'اعتماد تنفيذي'),
        ],
        string='دور الوظيفة المطلوب',
    )
    require_comment = fields.Boolean(string='اشتراط تعليق عند الاعتماد')
    sla_hours = fields.Float(string='مهلة الخطوة بالساعات')
    delegate_user_id = fields.Many2one(
        'res.users',
        string='مفوّض بديل',
        domain=[('share', '=', False)],
        help='يمكنه اعتماد هذه الخطوة عند الحاجة بدون تغيير المعتمد الأساسي.',
    )
    escalation_user_id = fields.Many2one(
        'res.users',
        string='يصعد إلى',
        domain=[('share', '=', False)],
        help='يتم تنبيهه آليًا إذا تجاوزت الخطوة مهلة الاعتماد.',
    )
    instructions = fields.Text(
        string='تعليمات الخطوة',
        help='تظهر داخل الطلب لتوضيح المطلوب من المعتمد قبل الاعتماد.',
    )

    @api.constrains('approver_type', 'user_id', 'group_id')
    def _check_target(self):
        for step in self:
            if step.approver_type == 'user' and not step.user_id:
                raise ValidationError(_('يجب تحديد المستخدم لهذه الخطوة.'))
            if step.approver_type == 'group' and not step.group_id:
                raise ValidationError(_('يجب تحديد مجموعة الصلاحيات لهذه الخطوة.'))
            if step.approver_type == 'job_role' and not step.job_approval_role:
                raise ValidationError(_('يجب تحديد دور الوظيفة لهذه الخطوة.'))


class DmHrServiceApprovalItem(models.Model):
    _name = 'dm.hr.service.approval.item'
    _description = 'سجل اعتماد طلب خدمة موظف'
    _order = 'request_id, sequence, id'

    request_id = fields.Many2one('dm.hr.service.request', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True, readonly=True)
    policy_step_id = fields.Many2one('dm.hr.approval.policy.step', ondelete='restrict', readonly=True)
    sequence = fields.Integer(readonly=True)
    name = fields.Char(string='الخطوة', readonly=True)
    approver_type = fields.Selection(related='policy_step_id.approver_type', readonly=True)
    approver_user_id = fields.Many2one('res.users', string='المعتمد المحدد', readonly=True)
    approver_group_id = fields.Many2one('res.groups', string='مجموعة الاعتماد', readonly=True)
    require_comment = fields.Boolean(related='policy_step_id.require_comment', readonly=True)
    deadline = fields.Datetime(string='المهلة النهائية', readonly=True)
    delegate_user_id = fields.Many2one('res.users', string='المفوّض البديل', readonly=True)
    escalation_user_id = fields.Many2one('res.users', string='مسؤول التصعيد', readonly=True)
    escalated = fields.Boolean(string='تم التصعيد', readonly=True)
    escalated_on = fields.Datetime(string='تاريخ التصعيد', readonly=True)
    instructions = fields.Text(string='تعليمات الاعتماد', readonly=True)
    state = fields.Selection([
        ('pending', 'بانتظار الاعتماد'), ('approved', 'معتمد'),
        ('rejected', 'مرفوض'), ('cancelled', 'ملغي'),
    ], default='pending', required=True, readonly=True)
    action_by_id = fields.Many2one('res.users', string='نفذ بواسطة', readonly=True)
    action_date = fields.Datetime(string='تاريخ الإجراء', readonly=True)
    comment = fields.Text(string='التعليق', readonly=True)
