# -*- coding: utf-8 -*-
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    dm_is_saudi_annual_leave = fields.Boolean(
        string='إجازة سنوية سعودية',
        help='يستخدمها النظام لمنح الرصيد السنوي تلقائياً: 21 يوم قبل خمس سنوات خدمة و30 يوم بعدها.',
    )


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    dm_allocation_origin = fields.Selection(
        [
            ('manual_hr', 'إضافة يدوية من الموارد البشرية'),
            ('saudi_annual_auto', 'استحقاق سنوي سعودي تلقائي'),
        ],
        string='مصدر الرصيد',
        readonly=True,
        copy=False,
    )
    dm_auto_annual_year = fields.Integer(
        string='سنة الاستحقاق السنوي',
        readonly=True,
        copy=False,
        index=True,
    )


class DmHrLeaveBalanceWizard(models.TransientModel):
    _name = 'dm.hr.leave.balance.wizard'
    _description = 'إضافة رصيد إجازات للموظفين'

    employee_ids = fields.Many2many(
        'hr.employee',
        string='الموظفون',
        required=True,
        domain="[('company_id', 'in', allowed_company_ids), ('active', '=', True)]",
    )
    holiday_status_id = fields.Many2one(
        'hr.leave.type',
        string='نوع الإجازة',
        required=True,
        domain="[('requires_allocation', '=', 'yes'), ('active', '=', True)]",
    )
    number_of_days = fields.Float(string='عدد الأيام', required=True, default=1.0)
    date_from = fields.Date(
        string='بداية الصلاحية',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_to = fields.Date(string='نهاية الصلاحية')
    reason = fields.Text(
        string='السبب',
        default='إضافة رصيد يدوي بواسطة الموارد البشرية',
    )
    validate_now = fields.Boolean(string='اعتماد الرصيد مباشرة', default=True)

    def _check_leave_officer(self):
        if not (
            self.env.user.has_group('dm_hr_core.group_dm_hr_officer')
            or self.env.user.has_group('dm_hr_core.group_dm_hr_manager')
            or self.env.user.has_group('dm_hr_core.group_dm_hr_admin')
            or self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        ):
            raise AccessError(_('إضافة أرصدة الإجازات متاحة لمسؤول الموارد البشرية فقط.'))

    @api.constrains('number_of_days', 'date_from', 'date_to')
    def _check_values(self):
        for wizard in self:
            if wizard.number_of_days <= 0:
                raise ValidationError(_('رصيد الإجازة يجب أن يكون أكبر من صفر.'))
            if wizard.date_to and wizard.date_to < wizard.date_from:
                raise ValidationError(_('نهاية صلاحية الرصيد يجب أن تكون بعد بداية الصلاحية.'))

    def action_create_allocations(self):
        self.ensure_one()
        self._check_leave_officer()
        Allocation = self.env['hr.leave.allocation'].sudo()
        allocations = self.env['hr.leave.allocation']
        for employee in self.employee_ids:
            allocation = Allocation.create({
                'private_name': _('إضافة رصيد يدوي - %s') % employee.name,
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'employee_ids': [(6, 0, [employee.id])],
                'holiday_status_id': self.holiday_status_id.id,
                'number_of_days': self.number_of_days,
                'number_of_days_display': self.number_of_days,
                'allocation_type': 'regular',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'notes': self.reason,
                'dm_allocation_origin': 'manual_hr',
            })
            allocations |= allocation
        if self.validate_now and allocations:
            allocations.action_validate()
        return {
            'name': _('أرصدة الإجازات المضافة'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.allocation',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', allocations.ids)],
            'target': 'current',
        }


class DmHrLeaveAnnualAllocationWizard(models.TransientModel):
    _name = 'dm.hr.leave.annual.allocation.wizard'
    _description = 'توليد رصيد الإجازة السنوية السعودية'

    year = fields.Integer(
        string='السنة',
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
    )
    holiday_status_id = fields.Many2one(
        'hr.leave.type',
        string='نوع الإجازة السنوية',
        required=True,
        domain="[('requires_allocation', '=', 'yes'), ('active', '=', True)]",
        default=lambda self: self.env['hr.leave.type'].search([
            ('dm_is_saudi_annual_leave', '=', True),
            ('company_id', 'in', [False, self.env.company.id]),
        ], limit=1),
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='الموظفون',
        domain="[('company_id', 'in', allowed_company_ids), ('active', '=', True), ('join_date', '!=', False)]",
        help='اتركها فارغة لتوليد الرصيد لكل الموظفين النشطين الذين لديهم تاريخ التحاق.',
    )

    def action_generate(self):
        self.ensure_one()
        return self.env['dm.hr.leave.hub'].generate_saudi_annual_allocations(
            year=self.year,
            holiday_status_id=self.holiday_status_id.id,
            employee_ids=self.employee_ids.ids,
        )


class DmHrLeaveHub(models.AbstractModel):
    _inherit = 'dm.hr.leave.hub'

    @api.model
    def _annual_days_for_employee(self, employee, target_year):
        if not employee.join_date:
            return 0.0
        month = employee.join_date.month
        day = employee.join_date.day
        try:
            anniversary = date(target_year, month, day)
        except ValueError:
            anniversary = date(target_year, month, 28)
        service_delta = relativedelta(anniversary, employee.join_date)
        service_years = service_delta.years + service_delta.months / 12.0 + service_delta.days / 365.0
        return 30.0 if service_years >= 5 else 21.0

    @api.model
    def generate_saudi_annual_allocations(self, year=None, holiday_status_id=None, employee_ids=None):
        if not (
            self.env.user.has_group('dm_hr_core.group_dm_hr_officer')
            or self.env.user.has_group('dm_hr_core.group_dm_hr_manager')
            or self.env.user.has_group('dm_hr_core.group_dm_hr_admin')
            or self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        ):
            raise AccessError(_('توليد الرصيد السنوي متاح لمسؤول الموارد البشرية فقط.'))
        year = year or fields.Date.context_today(self).year
        LeaveType = self.env['hr.leave.type'].sudo()
        leave_type = LeaveType.browse(holiday_status_id) if holiday_status_id else LeaveType.search([
            ('dm_is_saudi_annual_leave', '=', True),
            ('company_id', 'in', [False] + self.env.companies.ids),
        ], limit=1)
        if not leave_type:
            raise UserError(_('حدد نوع إجازة عليه علامة "إجازة سنوية سعودية" أولاً.'))
        Employee = self.env['hr.employee'].sudo()
        domain = [
            ('active', '=', True),
            ('join_date', '!=', False),
            ('company_id', 'in', self.env.companies.ids),
        ]
        if employee_ids:
            domain.append(('id', 'in', employee_ids))
        employees = Employee.search(domain)
        Allocation = self.env['hr.leave.allocation'].sudo()
        created = self.env['hr.leave.allocation']
        date_from = date(year, 1, 1)
        date_to = date(year, 12, 31)
        for employee in employees:
            days = self._annual_days_for_employee(employee, year)
            if not days:
                continue
            existing = Allocation.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('dm_auto_annual_year', '=', year),
                ('dm_allocation_origin', '=', 'saudi_annual_auto'),
                ('state', '!=', 'refuse'),
            ])
            if existing:
                continue
            allocation = Allocation.create({
                'private_name': _('الرصيد السنوي السعودي %s - %s') % (year, employee.name),
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'employee_ids': [(6, 0, [employee.id])],
                'holiday_status_id': leave_type.id,
                'number_of_days': days,
                'number_of_days_display': days,
                'allocation_type': 'regular',
                'date_from': date_from,
                'date_to': date_to,
                'notes': _('توليد تلقائي حسب نظام الإجازة السنوية السعودي: 21 يوم قبل خمس سنوات خدمة و30 يوم بعدها.'),
                'dm_allocation_origin': 'saudi_annual_auto',
                'dm_auto_annual_year': year,
            })
            allocation.action_validate()
            created |= allocation
        return {
            'name': _('الأرصدة السنوية المولدة'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.allocation',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created.ids)],
            'target': 'current',
        }

    @api.model
    def cron_generate_saudi_annual_allocations(self):
        """Cron entry point: skip companies that are not configured yet.

        A cron must never raise: if the Saudi annual leave type is not
        configured (or not usable) for a company, we log a warning and skip
        it instead of failing the whole job.
        """
        LeaveType = self.env['hr.leave.type'].sudo()
        for company in self.env['res.company'].sudo().search([]):
            leave_type = LeaveType.search([
                ('dm_is_saudi_annual_leave', '=', True),
                ('company_id', 'in', [False, company.id]),
            ], limit=1)
            if not leave_type:
                _logger.warning(
                    'توليد رصيد الإجازة السنوية السعودية: تخطي الشركة %s '
                    'لعدم وجود نوع إجازة معلَّم بـ"إجازة سنوية سعودية".',
                    company.name,
                )
                continue
            self.with_company(company).generate_saudi_annual_allocations(
                year=fields.Date.context_today(self.with_company(company)).year
            )
