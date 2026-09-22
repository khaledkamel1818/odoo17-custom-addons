# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DmHrOrgRequestMixin(models.AbstractModel):
    _name = 'dm.hr.org.request.mixin'
    _description = 'DM HR Organizational Request Mixin'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='الشركة', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', string='القطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', string='الإدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', string='القسم', related='employee_id.dm_section_id', store=True, readonly=True)
    unit_id = fields.Many2one('hr.department', string='الوحدة', related='employee_id.dm_unit_id', store=True, readonly=True)
    job_id = fields.Many2one('hr.job', string='المنصب', related='employee_id.job_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', string='المدير المباشر', related='employee_id.parent_id', store=True, readonly=True)
    manager_user_id = fields.Many2one('res.users', string='مستخدم المدير', related='manager_id.user_id', store=True, readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    rejection_reason = fields.Text(string='سبب الرفض')

    def _set_sequence(self, vals_list, code):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code(code) or 'جديد'
        return vals_list

    def _post_state(self, message):
        for rec in self:
            if hasattr(rec, 'message_post'):
                rec.message_post(body=message)


class DmHrReturnWork(models.Model):
    _name = 'dm.hr.return.work'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'dm.hr.org.request.mixin']
    _description = 'طلب مباشرة العمل'
    _order = 'id desc'

    return_type = fields.Selection([
        ('leave', 'بعد إجازة'),
        ('business_trip', 'بعد انتداب'),
        ('hiring', 'بعد تعيين'),
        ('other', 'أخرى'),
    ], string='نوع المباشرة', required=True, default='leave', tracking=True)
    return_date = fields.Date(string='تاريخ المباشرة', required=True, default=fields.Date.context_today, tracking=True)
    reason = fields.Text(string='السبب / الملاحظات')
    related_leave_id = fields.Many2one('hr.leave', string='الإجازة المرتبطة')
    related_request_id = fields.Many2one('dm.hr.service.request', string='طلب مرتبط')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('manager', 'اعتماد المدير'),
        ('hr', 'اعتماد الموارد البشرية'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(self._set_sequence(vals_list, 'dm.hr.return.work'))

    def action_submit(self):
        self.write({'state': 'manager'})
        self._post_state(_('تم إرسال طلب مباشرة العمل إلى المدير المباشر.'))

    def action_approve(self):
        for rec in self:
            if rec.state == 'manager':
                rec.state = 'hr'
            elif rec.state == 'hr':
                rec.state = 'approved'
            else:
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            rec.message_post(body=_('تمت الموافقة والانتقال للمرحلة التالية.'))

    def action_reject(self):
        self.write({'state': 'rejected'})
        self._post_state(_('تم رفض طلب مباشرة العمل.'))


class DmHrCustody(models.Model):
    _name = 'dm.hr.custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'العهد غير المالية'
    _order = 'id desc'

    name = fields.Char(string='رقم العهدة', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='الشركة', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    custody_type = fields.Selection([
        ('device', 'جهاز'),
        ('card', 'بطاقة'),
        ('car', 'سيارة'),
        ('tool', 'أدوات'),
        ('other', 'أخرى'),
    ], string='نوع العهدة', required=True, default='device', tracking=True)
    code = fields.Char(string='الكود')
    serial_no = fields.Char(string='السيريال')
    delivery_date = fields.Date(string='تاريخ التسليم', tracking=True)
    return_date = fields.Date(string='تاريخ الاسترجاع', tracking=True)
    settlement_notes = fields.Text(string='ملاحظات التسوية')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('delivered', 'مسلمة'),
        ('returned', 'مسترجعة'),
        ('settled', 'مسواة'),
        ('lost', 'مفقودة/تالفة'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.custody') or 'جديد'
        return super().create(vals_list)

    def action_deliver(self):
        self.write({'state': 'delivered', 'delivery_date': fields.Date.context_today(self)})

    def action_return(self):
        self.write({'state': 'returned', 'return_date': fields.Date.context_today(self)})

    def action_settle(self):
        self.write({'state': 'settled'})

    def action_lost(self):
        self.write({'state': 'lost'})


class DmHrClearance(models.Model):
    _name = 'dm.hr.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'dm.hr.org.request.mixin']
    _description = 'إخلاء طرف الموظف'
    _order = 'id desc'

    last_working_date = fields.Date(string='آخر يوم عمل', required=True, default=fields.Date.context_today, tracking=True)
    reason = fields.Text(string='سبب إخلاء الطرف')
    line_ids = fields.One2many('dm.hr.clearance.line', 'clearance_id', string='أقسام الإخلاء')
    custody_ids = fields.Many2many('dm.hr.custody', string='العهد غير المالية')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('in_progress', 'قيد الإخلاء'),
        ('approved', 'مغلق/معتمد'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(self._set_sequence(vals_list, 'dm.hr.clearance'))
        for rec in records:
            rec._ensure_default_lines()
        return records

    def _ensure_default_lines(self):
        departments = [
            ('direct_management', 'الإدارة المباشرة'),
            ('hr', 'الموارد البشرية'),
            ('finance', 'المالية'),
            ('it', 'تقنية المعلومات'),
            ('custody', 'العهد'),
        ]
        for rec in self:
            existing = set(rec.line_ids.mapped('clearance_department'))
            for key, label in departments:
                if key not in existing:
                    self.env['dm.hr.clearance.line'].create({
                        'clearance_id': rec.id,
                        'clearance_department': key,
                        'name': label,
                    })

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.custody_ids = self.env['dm.hr.custody'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'delivered'),
            ])

    def action_submit(self):
        self._ensure_default_lines()
        self.write({'state': 'in_progress'})
        self._post_state(_('بدأت دورة إخلاء الطرف. يجب اعتماد جميع الأقسام قبل الإغلاق.'))

    def action_close_if_ready(self):
        for rec in self:
            if not rec.line_ids:
                rec._ensure_default_lines()
            pending = rec.line_ids.filtered(lambda line: line.state != 'approved')
            if pending:
                raise UserError(_('لا يمكن إغلاق إخلاء الطرف قبل اعتماد جميع الأقسام.'))
            rec.state = 'approved'
            rec.message_post(body=_('تم إغلاق إخلاء الطرف بعد اعتماد جميع الأقسام.'))

    def action_reject(self):
        self.write({'state': 'rejected'})


class DmHrClearanceLine(models.Model):
    _name = 'dm.hr.clearance.line'
    _inherit = ['mail.thread']
    _description = 'بند إخلاء طرف'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    clearance_id = fields.Many2one('dm.hr.clearance', string='طلب إخلاء الطرف', required=True, ondelete='cascade')
    name = fields.Char(string='القسم', required=True)
    clearance_department = fields.Selection([
        ('direct_management', 'الإدارة المباشرة'),
        ('hr', 'الموارد البشرية'),
        ('finance', 'المالية'),
        ('it', 'تقنية المعلومات'),
        ('custody', 'العهد'),
    ], string='جهة الإخلاء', required=True)
    approver_id = fields.Many2one('res.users', string='المعتمد')
    approved_date = fields.Datetime(string='تاريخ الاعتماد')
    notes = fields.Text(string='ملاحظات')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    state = fields.Selection([
        ('pending', 'بانتظار الاعتماد'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='pending', tracking=True)

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })

    def action_reject(self):
        self.write({'state': 'rejected', 'approver_id': self.env.user.id})


class DmHrEmployeeTransfer(models.Model):
    _name = 'dm.hr.employee.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'تنقلات وتغيير وظائف الموظفين'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='الشركة', related='employee_id.company_id', store=True, readonly=True)
    from_branch_id = fields.Many2one('dm.hr.branch', string='من فرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    from_sector_id = fields.Many2one('hr.department', string='من قطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    from_department_id = fields.Many2one('hr.department', string='من إدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    from_section_id = fields.Many2one('hr.department', string='من قسم', related='employee_id.dm_section_id', store=True, readonly=True)
    from_job_id = fields.Many2one('hr.job', string='من وظيفة', related='employee_id.job_id', store=True, readonly=True)
    to_branch_id = fields.Many2one('dm.hr.branch', string='إلى فرع', required=True)
    to_sector_id = fields.Many2one('hr.department', string='إلى قطاع', required=True, domain="[('dm_org_level','=','sector'),('dm_branch_id','=',to_branch_id)]")
    to_department_id = fields.Many2one('hr.department', string='إلى إدارة', required=True, domain="[('dm_org_level','=','department'),('parent_id','=',to_sector_id)]")
    to_section_id = fields.Many2one('hr.department', string='إلى قسم', required=True, domain="[('dm_org_level','=','section'),('parent_id','=',to_department_id)]")
    to_unit_id = fields.Many2one('hr.department', string='إلى وحدة', domain="[('dm_org_level','=','unit'),('parent_id','=',to_section_id)]")
    to_job_id = fields.Many2one('hr.job', string='إلى وظيفة')
    effective_date = fields.Date(string='تاريخ السريان', required=True, default=fields.Date.context_today, tracking=True)
    reason = fields.Text(string='السبب', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('manager', 'المدير المباشر'),
        ('department_manager', 'مدير الإدارة'),
        ('hr', 'الموارد البشرية'),
        ('approved', 'معتمد ومنفذ'),
        ('rejected', 'مرفوض'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.employee.transfer') or 'جديد'
        return super().create(vals_list)

    @api.constrains('to_branch_id', 'to_sector_id', 'to_department_id', 'to_section_id', 'to_unit_id')
    def _check_target_org(self):
        for rec in self:
            if rec.to_sector_id.dm_branch_id != rec.to_branch_id:
                raise ValidationError(_('القطاع الجديد لا يتبع الفرع الجديد.'))
            if rec.to_department_id.parent_id != rec.to_sector_id:
                raise ValidationError(_('الإدارة الجديدة لا تتبع القطاع الجديد.'))
            if rec.to_section_id.parent_id != rec.to_department_id:
                raise ValidationError(_('القسم الجديد لا يتبع الإدارة الجديدة.'))
            if rec.to_unit_id and rec.to_unit_id.parent_id != rec.to_section_id:
                raise ValidationError(_('الوحدة الجديدة لا تتبع القسم الجديد.'))

    def action_submit(self):
        self.write({'state': 'manager'})

    def action_approve(self):
        flow = {
            'manager': 'department_manager',
            'department_manager': 'hr',
            'hr': 'approved',
        }
        for rec in self:
            if rec.state not in flow:
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            rec.state = flow[rec.state]
            if rec.state == 'approved':
                rec._apply_transfer()
            rec.message_post(body=_('تمت الموافقة والانتقال للمرحلة التالية.'))

    def _apply_transfer(self):
        for rec in self:
            rec.employee_id.write({
                'dm_branch_id': rec.to_branch_id.id,
                'dm_sector_id': rec.to_sector_id.id,
                'dm_department_level_id': rec.to_department_id.id,
                'dm_section_id': rec.to_section_id.id,
                'dm_unit_id': rec.to_unit_id.id or False,
                'job_id': rec.to_job_id.id or rec.employee_id.job_id.id,
            })

    def action_reject(self):
        self.write({'state': 'rejected'})


class ProjectTask(models.Model):
    _inherit = 'project.task'

    dm_employee_id = fields.Many2one('hr.employee', string='الموظف المرتبط', index=True)
    dm_service_request_id = fields.Many2one('dm.hr.service.request', string='طلب خدمة مرتبط')
    dm_branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='dm_employee_id.dm_branch_id', store=True, readonly=True)
    dm_department_level_id = fields.Many2one('hr.department', string='الإدارة', related='dm_employee_id.dm_department_level_id', store=True, readonly=True)
