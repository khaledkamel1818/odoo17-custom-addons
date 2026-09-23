# -*- coding: utf-8 -*-
from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DmHrAttendanceReason(models.Model):
    _name = 'dm.hr.attendance.reason'
    _description = 'أسباب الحضور والانصراف'
    _order = 'sequence, name'

    name = fields.Char(string='السبب', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    reason_type = fields.Selection([
        ('late', 'تأخير'),
        ('early_leave', 'خروج مبكر'),
        ('absence', 'غياب'),
        ('missed_check_in', 'نسيان حضور'),
        ('missed_check_out', 'نسيان خروج'),
        ('adjustment', 'تعديل حضور/انصراف'),
        ('other', 'أخرى'),
    ], string='نوع السبب', default='other', required=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    dm_branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    dm_sector_id = fields.Many2one('hr.department', string='القطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    dm_department_level_id = fields.Many2one('hr.department', string='الإدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    dm_section_id = fields.Many2one('hr.department', string='القسم', related='employee_id.dm_section_id', store=True, readonly=True)
    dm_manager_id = fields.Many2one('hr.employee', string='المدير المباشر', related='employee_id.parent_id', store=True, readonly=True)
    dm_attendance_state = fields.Selection([
        ('normal', 'طبيعي'),
        ('late', 'تأخير'),
        ('early_leave', 'خروج مبكر'),
        ('absence_related', 'مرتبط بغياب'),
        ('corrected', 'تم التصحيح'),
    ], string='حالة السجل', default='normal', tracking=True)
    dm_correction_id = fields.Many2one('dm.hr.attendance.correction', string='آخر تصحيح معتمد', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._dm_check_attendance_on_leave()
        return records

    def _dm_check_attendance_on_leave(self):
        Leave = self.env['hr.leave'].sudo()
        for attendance in self:
            company = attendance.employee_id.company_id or self.env.company
            if not company.dm_attendance_block_on_approved_leave or not attendance.check_in:
                continue
            check_date = fields.Datetime.context_timestamp(attendance, attendance.check_in).date()
            leave = Leave.search([
                ('employee_id', '=', attendance.employee_id.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', check_date),
                ('request_date_to', '>=', check_date),
            ], limit=1)
            if leave:
                raise ValidationError(_('لا يمكن تسجيل حضور في يوم إجازة معتمدة للموظف: %s') % attendance.employee_id.name)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _attendance_action_change(self, geo_information=None):
        for employee in self:
            company = employee.company_id or self.env.company
            if company.dm_attendance_block_on_approved_leave:
                today = fields.Date.context_today(employee)
                leave = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', today),
                    ('request_date_to', '>=', today),
                ], limit=1)
                if leave:
                    raise UserError(_('لا يمكن تسجيل حضور أو انصراف أثناء إجازة معتمدة.'))
        return super()._attendance_action_change(geo_information=geo_information)


class DmHrAttendanceCorrection(models.Model):
    _name = 'dm.hr.attendance.correction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'طلبات وتصحيحات الحضور'
    _order = 'id desc'

    name = fields.Char(string='رقم الطلب', default='جديد', copy=False, readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    request_date = fields.Date(string='التاريخ', required=True, default=fields.Date.context_today, tracking=True)
    request_type = fields.Selection([
        ('late_justification', 'تبرير التأخير'),
        ('early_leave_justification', 'تبرير الخروج المبكر'),
        ('absence_justification', 'تبرير الغياب'),
        ('attendance_adjustment', 'طلب تعديل حضور أو انصراف'),
        ('missed_check_in', 'نسيان تسجيل حضور'),
        ('missed_check_out', 'نسيان تسجيل خروج'),
    ], string='نوع الطلب', required=True, default='attendance_adjustment', tracking=True)
    attendance_id = fields.Many2one('hr.attendance', string='سجل الحضور المرتبط')
    original_check_in = fields.Datetime(string='وقت الحضور الأصلي', readonly=True)
    original_check_out = fields.Datetime(string='وقت الانصراف الأصلي', readonly=True)
    requested_check_in = fields.Datetime(string='وقت الحضور المطلوب')
    requested_check_out = fields.Datetime(string='وقت الانصراف المطلوب')
    reason_id = fields.Many2one('dm.hr.attendance.reason', string='السبب المحدد')
    reason = fields.Text(string='السبب التفصيلي', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات')
    company_id = fields.Many2one('res.company', string='الشركة', related='employee_id.company_id', store=True, readonly=True)
    branch_id = fields.Many2one('dm.hr.branch', string='الفرع', related='employee_id.dm_branch_id', store=True, readonly=True)
    sector_id = fields.Many2one('hr.department', string='القطاع', related='employee_id.dm_sector_id', store=True, readonly=True)
    department_level_id = fields.Many2one('hr.department', string='الإدارة', related='employee_id.dm_department_level_id', store=True, readonly=True)
    section_id = fields.Many2one('hr.department', string='القسم', related='employee_id.dm_section_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', string='المدير المباشر', related='employee_id.parent_id', store=True, readonly=True)
    manager_user_id = fields.Many2one('res.users', string='مستخدم المدير', related='manager_id.user_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('manager', 'اعتماد المدير'),
        ('hr', 'اعتماد الموارد البشرية'),
        ('approved', 'معتمد ومنفذ'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'جديد':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('dm.hr.attendance.correction') or 'جديد'
        return super().create(vals_list)

    @api.onchange('attendance_id')
    def _onchange_attendance_id(self):
        if self.attendance_id:
            self.employee_id = self.attendance_id.employee_id
            self.original_check_in = self.attendance_id.check_in
            self.original_check_out = self.attendance_id.check_out

    @api.constrains('requested_check_in', 'requested_check_out')
    def _check_requested_times(self):
        for rec in self:
            if rec.requested_check_in and rec.requested_check_out and rec.requested_check_out <= rec.requested_check_in:
                raise ValidationError(_('وقت الانصراف المطلوب يجب أن يكون بعد وقت الحضور المطلوب.'))

    def action_submit(self):
        self.write({'state': 'manager'})
        self._schedule_manager_activity()

    def _schedule_manager_activity(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        for rec in self:
            if activity_type and rec.manager_user_id:
                rec.activity_schedule(activity_type_id=activity_type.id, user_id=rec.manager_user_id.id, summary=_('اعتماد تصحيح حضور'))

    def action_approve(self):
        for rec in self:
            if rec.state == 'manager':
                rec.state = 'hr'
            elif rec.state == 'hr':
                rec._apply_correction()
                rec.state = 'approved'
            else:
                raise UserError(_('لا يمكن اعتماد الطلب في هذه المرحلة.'))
            rec.message_post(body=_('تم اعتماد المرحلة الحالية.'))

    def _apply_correction(self):
        Attendance = self.env['hr.attendance'].sudo()
        for rec in self:
            attendance = rec.attendance_id.sudo()
            if not attendance:
                base_dt = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, datetime.combine(rec.request_date, time(hour=8))))
                attendance = Attendance.create({
                    'employee_id': rec.employee_id.id,
                    'check_in': rec.requested_check_in or base_dt,
                })
                rec.attendance_id = attendance
            vals = {'dm_attendance_state': 'corrected', 'dm_correction_id': rec.id}
            if rec.requested_check_in:
                vals['check_in'] = rec.requested_check_in
            if rec.requested_check_out:
                vals['check_out'] = rec.requested_check_out
            attendance.write(vals)

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
