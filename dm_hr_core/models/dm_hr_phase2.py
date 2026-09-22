# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrProbationExtension(models.Model):
    _name = 'dm.hr.probation.extension'
    _description = 'طلب تمديد فترة التجربة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _check_company_auto = True

    name = fields.Char(default='/', copy=False, readonly=True, string='رقم الطلب')
    employee_id = fields.Many2one('hr.employee', required=True, string='الموظف', tracking=True)
    contract_id = fields.Many2one('hr.contract', required=True, string='العقد', tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, readonly=True)
    current_start_date = fields.Date(related='contract_id.date_start', store=True, readonly=True, string='بداية العقد')
    current_probation_end = fields.Date(related='contract_id.probation_end', store=True, readonly=True, string='نهاية التجربة الحالية')
    used_days = fields.Integer(string='المدة المستخدمة/يوم', compute='_compute_dates', store=True)
    extension_days = fields.Integer(string='مدة التمديد/يوم', required=True, tracking=True)
    new_probation_end = fields.Date(string='تاريخ الانتهاء الجديد', compute='_compute_dates', store=True)
    reason = fields.Text(string='سبب التمديد', required=True)
    manager_evaluation = fields.Text(string='تقييم المدير')
    manager_recommendation = fields.Selection([('extend', 'تمديد'), ('confirm', 'تثبيت'), ('terminate', 'إنهاء')], string='توصية المدير')
    employee_written_approval = fields.Boolean(string='موافقة الموظف الكتابية')
    extension_file = fields.Binary(string='مستند التمديد', attachment=True)
    document_id = fields.Many2one('dm.hr.document', string='مستند محفوظ', readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'), ('manager', 'المدير المباشر'), ('department', 'مدير الإدارة'),
        ('hr', 'الموارد البشرية'), ('employee', 'موافقة الموظف'), ('approved', 'معتمد'),
        ('rejected', 'مرفوض'), ('cancelled', 'ملغي'),
    ], default='draft', tracking=True)

    @api.depends('current_start_date', 'current_probation_end', 'extension_days')
    def _compute_dates(self):
        for rec in self:
            if rec.current_start_date and rec.current_probation_end:
                rec.used_days = max((rec.current_probation_end - rec.current_start_date).days, 0)
                rec.new_probation_end = rec.current_probation_end + timedelta(days=rec.extension_days or 0)
            else:
                rec.used_days = 0
                rec.new_probation_end = False

    @api.constrains('used_days', 'extension_days')
    def _check_180_days(self):
        for rec in self:
            if rec.used_days + rec.extension_days > 180:
                raise ValidationError(_('لا يمكن تجاوز إجمالي فترة التجربة 180 يوماً.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.probation.extension') or '/'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve_next(self):
        flow = {'manager': 'department', 'department': 'hr', 'hr': 'employee', 'employee': 'approved'}
        for rec in self:
            next_state = flow.get(rec.state)
            if next_state == 'approved':
                if not rec.employee_written_approval:
                    raise ValidationError(_('يجب تسجيل موافقة الموظف الكتابية قبل الاعتماد النهائي.'))
                rec.contract_id.probation_end = rec.new_probation_end
                if rec.extension_file:
                    rec.document_id = self.env['dm.hr.document'].create({
                        'employee_id': rec.employee_id.id,
                        'document_type': 'probation_extension',
                        'name': rec.name,
                        'issue_date': fields.Date.today(),
                        'expiry_date': rec.new_probation_end,
                        'document_file': rec.extension_file,
                    })
            if next_state:
                rec.state = next_state

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrDocumentRenewal(models.Model):
    _name = 'dm.hr.document.renewal'
    _description = 'طلب تجديد الهوية والوثائق'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(default='/', copy=False, readonly=True, string='رقم الطلب')
    employee_id = fields.Many2one('hr.employee', required=True, string='الموظف', tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, readonly=True)
    document_type = fields.Selection([
        ('national_id', 'الهوية الوطنية'), ('iqama', 'الإقامة'),
        ('passport', 'جواز السفر'), ('driving_license', 'رخصة القيادة'),
    ], required=True, string='نوع الوثيقة')
    current_expiry_date = fields.Date(string='تاريخ الانتهاء الحالي')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    fees = fields.Monetary(string='الرسوم')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    responsible_id = fields.Many2one('res.users', string='المسؤول')
    transaction_state = fields.Selection([
        ('new', 'جديد'), ('submitted', 'مقدم'), ('in_progress', 'تحت الإجراء'),
        ('done', 'منجز'), ('blocked', 'متعثر'),
    ], default='new', string='حالة المعاملة')
    new_document_id = fields.Many2one('dm.hr.document', string='الوثيقة الجديدة')
    state = fields.Selection([
        ('draft', 'مسودة'), ('manager', 'المدير عند الحاجة'), ('hr', 'الموارد البشرية'),
        ('gov_relations', 'العلاقات الحكومية'), ('approved', 'معتمد'), ('rejected', 'مرفوض'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.document.renewal') or '/'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve_next(self):
        flow = {'manager': 'hr', 'hr': 'gov_relations', 'gov_relations': 'approved'}
        for rec in self:
            rec.state = flow.get(rec.state, rec.state)


class DmHrManpowerRequest(models.Model):
    _name = 'dm.hr.manpower.request'
    _description = 'طلب احتياج وظيفي'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(default='/', copy=False, readonly=True, string='رقم الطلب')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع')
    sector_id = fields.Many2one('hr.department', string='القطاع', domain="[('dm_org_level','=','sector')]")
    department_id = fields.Many2one('hr.department', string='الإدارة', domain="[('dm_org_level','=','department')]")
    section_id = fields.Many2one('hr.department', string='القسم', domain="[('dm_org_level','=','section')]")
    job_id = fields.Many2one('hr.job', string='الوظيفة', required=True)
    requested_count = fields.Integer(string='العدد', default=1, required=True)
    need_type = fields.Selection([('new', 'احتياج جديد'), ('replacement', 'بديل')], required=True, default='new')
    reason = fields.Text(string='السبب', required=True)
    qualifications = fields.Text(string='المؤهلات')
    budget_amount = fields.Monetary(string='الميزانية')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    cost_center = fields.Char(string='مركز التكلفة')
    required_join_date = fields.Date(string='تاريخ الانضمام المطلوب')
    vacancy_job_id = fields.Many2one('hr.job', string='وظيفة شاغرة مرتبطة', readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'), ('section_manager', 'مدير القسم'), ('department_manager', 'مدير الإدارة'),
        ('sector_manager', 'مدير القطاع'), ('hr', 'الموارد البشرية'), ('finance', 'المالية'),
        ('executive', 'الإدارة العليا'), ('approved', 'معتمد'), ('rejected', 'مرفوض'),
    ], default='draft', tracking=True)

    @api.constrains('requested_count')
    def _check_count(self):
        for rec in self:
            if rec.requested_count <= 0:
                raise ValidationError(_('عدد الوظائف المطلوب يجب أن يكون أكبر من صفر.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.manpower.request') or '/'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'section_manager'})

    def action_approve_next(self):
        flow = {'section_manager': 'department_manager', 'department_manager': 'sector_manager', 'sector_manager': 'hr', 'hr': 'finance', 'finance': 'executive', 'executive': 'approved'}
        self.write({'state': flow.get(self.state, self.state)})

    def action_create_vacancy(self):
        for rec in self:
            rec.vacancy_job_id = rec.job_id.copy({'name': '%s - %s' % (rec.job_id.name, rec.name)})


class DmHrAnnouncement(models.Model):
    _name = 'dm.hr.announcement'
    _description = 'الأخبار والإعلانات والتعاميم'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'publish_date desc, id desc'

    name = fields.Char(required=True, string='العنوان', translate=True)
    announcement_type = fields.Selection([('news', 'خبر/إعلان'), ('circular', 'تعميم رسمي')], default='news', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع')
    sector_id = fields.Many2one('hr.department', string='القطاع')
    department_id = fields.Many2one('hr.department', string='الإدارة')
    section_id = fields.Many2one('hr.department', string='القسم')
    job_id = fields.Many2one('hr.job', string='الوظيفة')
    publish_date = fields.Date(default=fields.Date.today, string='تاريخ النشر')
    effective_date = fields.Date(string='تاريخ السريان')
    expiry_date = fields.Date(string='تاريخ الانتهاء')
    priority = fields.Selection([('0', 'عادي'), ('1', 'مهم'), ('2', 'عاجل')], default='0')
    body = fields.Html(string='المحتوى')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    acknowledgement_required = fields.Boolean(string='يتطلب تأكيد اطلاع')
    acknowledgement_ids = fields.One2many('dm.hr.announcement.ack', 'announcement_id', string='تأكيدات الاطلاع')
    state = fields.Selection([('draft', 'مسودة'), ('published', 'منشور'), ('expired', 'منتهي')], default='draft', tracking=True)

    def action_publish(self):
        Ack = self.env['dm.hr.announcement.ack']
        Employee = self.env['hr.employee'].sudo()
        for rec in self:
            rec.state = 'published'
            if rec.acknowledgement_required:
                domain = [('company_id', '=', rec.company_id.id)]
                if rec.branch_id:
                    domain.append(('dm_branch_id', '=', rec.branch_id.id))
                if rec.department_id:
                    domain.append(('department_id', 'child_of', rec.department_id.id))
                if rec.job_id:
                    domain.append(('job_id', '=', rec.job_id.id))
                for employee in Employee.search(domain):
                    if not Ack.search_count([('announcement_id', '=', rec.id), ('employee_id', '=', employee.id)]):
                        Ack.create({'announcement_id': rec.id, 'employee_id': employee.id})


class DmHrAnnouncementAck(models.Model):
    _name = 'dm.hr.announcement.ack'
    _description = 'تأكيد اطلاع الموظف'
    _order = 'announcement_id, employee_id'

    announcement_id = fields.Many2one('dm.hr.announcement', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', required=True)
    acknowledged = fields.Boolean(string='تم الاطلاع')
    acknowledged_on = fields.Datetime(string='تاريخ الاطلاع')
    company_id = fields.Many2one(related='announcement_id.company_id', store=True)

    def action_acknowledge(self):
        self.write({'acknowledged': True, 'acknowledged_on': fields.Datetime.now()})


class DmHrCompanyDocument(models.Model):
    _name = 'dm.hr.company.document'
    _description = 'مستندات الشركة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char(required=True, translate=True, string='اسم المستند')
    category = fields.Selection([
        ('policy', 'سياسة'), ('procedure', 'إجراء'), ('regulation', 'لائحة'),
        ('form', 'نموذج'), ('guide', 'دليل'), ('template', 'قالب'), ('decision', 'قرار رسمي'),
    ], required=True, default='policy')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    version = fields.Char(string='الإصدار', default='1.0')
    effective_date = fields.Date(string='تاريخ السريان')
    is_confidential = fields.Boolean(string='سري')
    file = fields.Binary(string='الملف', attachment=True)
    approved_by_id = fields.Many2one('res.users', string='اعتمد بواسطة')
    acknowledgement_required = fields.Boolean(string='يتطلب تأكيد اطلاع')
    state = fields.Selection([('draft', 'مسودة'), ('approved', 'معتمد'), ('archived', 'مؤرشف')], default='draft', tracking=True)

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by_id': self.env.user.id})
