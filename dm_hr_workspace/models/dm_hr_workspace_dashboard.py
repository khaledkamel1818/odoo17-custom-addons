# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
from math import asin, cos, radians, sin, sqrt

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DmHrWorkspaceDashboard(models.AbstractModel):
    _name = 'dm.hr.workspace.dashboard'
    _description = 'لوحة منصة الموارد البشرية'

    @api.model
    def _get_user_employee(self):
        employee = self.env.user.employee_id
        if employee:
            return employee
        return self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', 'in', self.env.companies.ids),
        ], limit=1)

    @api.model
    def _is_hr_user(self):
        user = self.env.user
        return any([
            user.has_group('dm_hr_core.group_dm_hr_officer'),
            user.has_group('dm_hr_core.group_dm_hr_manager'),
            user.has_group('dm_hr_core.group_dm_hr_admin'),
        ])

    @api.model
    def _today_utc_range(self):
        tz_name = self.env.user.tz or self.env.company.resource_calendar_id.tz or 'Asia/Riyadh'
        timezone = pytz.timezone(tz_name)
        today = fields.Date.context_today(self)
        local_start = timezone.localize(datetime.combine(today, time.min))
        local_end = timezone.localize(datetime.combine(today, time.max))
        return (
            local_start.astimezone(pytz.UTC).replace(tzinfo=None),
            local_end.astimezone(pytz.UTC).replace(tzinfo=None),
        )

    @api.model
    def _count(self, model, domain):
        return self.env[model].sudo().search_count(domain)

    @api.model
    def _format_dt(self, value):
        if not value:
            return ''
        return fields.Datetime.context_timestamp(self, value).strftime('%Y-%m-%d %H:%M')

    @api.model
    def _format_date(self, value):
        if not value:
            return ''
        return fields.Date.to_string(value)

    @api.model
    def _employee_image_url(self, employee):
        """Avoid broken /web/image calls when an old attachment is missing."""
        if not employee:
            return ''
        try:
            if employee.sudo().image_128:
                return '/web/image/hr.employee/%s/image_128' % employee.id
        except FileNotFoundError:
            return ''
        return ''

    @api.model
    def _selection_label(self, model_name, field_name, value):
        if not value:
            return ''
        field = self.env[model_name]._fields[field_name]
        return dict(field._description_selection(self.env)).get(value, value)

    @api.model
    def _state_tone(self, state):
        if state in ('approved', 'validate'):
            return 'success'
        if state in ('submitted', 'confirm', 'manager_approved', 'validate1'):
            return 'warning'
        if state in ('rejected', 'refuse'):
            return 'danger'
        if state in ('cancelled',):
            return 'muted'
        return 'info'

    @api.model
    def _normalize_act_window(self, action):
        """Return an Odoo web-safe action dictionary.

        Client actions created dynamically must include ``views``.  Without it,
        the web client tries to run ``action.views.map`` and crashes.
        """
        if not action:
            return action
        if action.get('type') == 'ir.actions.act_window' and not action.get('views'):
            view_modes = (action.get('view_mode') or 'tree,form').split(',')
            action['views'] = [(False, mode.strip()) for mode in view_modes if mode.strip()]
        action.setdefault('context', {})
        action.setdefault('target', 'current')
        return action

    @api.model
    def _action_from_xmlid(self, xmlid):
        action = self.env['ir.actions.actions'].sudo()._for_xml_id(xmlid)
        return self._normalize_act_window(action)

    @api.model
    def get_dashboard_data(self):
        employee = self._get_user_employee()
        today_start, today_end = self._today_utc_range()
        is_hr = self._is_hr_user()
        user = self.env.user
        employee_domain = [('company_id', 'in', self.env.companies.ids)]
        active_employee_domain = employee_domain + [('active', '=', True)]
        team_domain = [('parent_id.user_id', '=', user.id), ('company_id', 'in', self.env.companies.ids)]
        has_team = bool(self.env['hr.employee'].sudo().search_count(team_domain))
        company = self.env.company

        attendance_domain_today = [
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
            ('employee_id.company_id', 'in', self.env.companies.ids),
        ]
        open_attendance_domain = [
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
            ('check_out', '=', False),
            ('employee_id.company_id', 'in', self.env.companies.ids),
        ]
        my_request_domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        my_leave_domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        visible_employee_domain = employee_domain if is_hr else (team_domain if has_team else [('id', '=', employee.id if employee else 0)])
        visible_attendance_domain = [
            ('employee_id', 'in', self.env['hr.employee'].sudo().search(visible_employee_domain).ids),
        ]
        approvals_domain = [
            ('state', 'in', ['submitted', 'manager_approved']),
            ('company_id', 'in', self.env.companies.ids),
        ]
        if not is_hr:
            approvals_domain += ['|', ('manager_user_id', '=', user.id), ('employee_id.leave_manager_id', '=', user.id)]

        expiring_date = fields.Date.context_today(self) + timedelta(days=30)
        document_expiry_domain = [
            ('expiry_date', '!=', False),
            ('expiry_date', '<=', expiring_date),
            ('company_id', 'in', self.env.companies.ids),
        ]
        iqama_expiry_domain = [
            ('iqama_expiry_date', '!=', False),
            ('iqama_expiry_date', '<=', expiring_date),
            ('company_id', 'in', self.env.companies.ids),
        ]

        last_attendance = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id if employee else 0)
        ], order='check_in desc', limit=1)
        attendance_state = 'checked_out'
        if employee:
            attendance_state = employee.sudo().attendance_state or 'checked_out'

        pending_leave_domain = my_leave_domain + [('state', 'in', ['confirm', 'validate1'])]
        approved_leave_domain = my_leave_domain + [('state', '=', 'validate')]
        pending_request_domain = my_request_domain + [('state', 'in', ['submitted', 'manager_approved'])]
        approved_request_domain = my_request_domain + [('state', '=', 'approved')]

        documents_metric_domain = document_expiry_domain if is_hr else document_expiry_domain + [
            ('employee_id', '=', employee.id if employee else 0),
        ]
        iqama_metric_domain = iqama_expiry_domain if is_hr else iqama_expiry_domain + [
            ('id', '=', employee.id if employee else 0),
        ]
        attendance_metric_domain = attendance_domain_today if is_hr else attendance_domain_today + visible_attendance_domain

        dashboard = {
            'config': {
                'name': company.hr_workspace_name or _('منصة الموارد البشرية'),
                'attendance_enabled': company.hr_workspace_attendance_enabled,
                'gps_required': company.hr_workspace_gps_required,
                'gps_max_accuracy': company.hr_workspace_gps_max_accuracy,
                'geofence_required': company.hr_workspace_geofence_required,
                'self_service_enabled': company.hr_workspace_self_service_enabled,
                'compliance_enabled': company.hr_workspace_compliance_enabled,
                'show_hr_command': is_hr,
            },
            'user': {
                'name': user.name,
                'is_hr': is_hr,
                'is_manager': has_team,
            },
            'employee': {
                'id': employee.id if employee else False,
                'name': employee.name if employee else _('لا يوجد موظف مرتبط بالمستخدم'),
                'employee_number': employee.employee_number if employee else '',
                'job': employee.job_id.name if employee and employee.job_id else '',
                'department': employee.department_id.name if employee and employee.department_id else '',
                'manager': employee.parent_id.name if employee and employee.parent_id else '',
                'status': employee.dm_employment_status if employee else '',
                'image_url': self._employee_image_url(employee),
            },
            'attendance': {
                'state': attendance_state,
                'state_label': _('داخل الدوام') if attendance_state == 'checked_in' else _('خارج الدوام'),
                'button_label': _('تسجيل انصراف') if attendance_state == 'checked_in' else _('تسجيل حضور'),
                'last_check_in': self._format_dt(last_attendance.check_in),
                'last_check_out': self._format_dt(last_attendance.check_out),
                'hours_today': round(employee.sudo().hours_today or 0.0, 2) if employee else 0.0,
                'present_today': self._count('hr.attendance', open_attendance_domain if is_hr else open_attendance_domain + visible_attendance_domain),
                'attendance_records_today': self._count('hr.attendance', attendance_metric_domain),
            },
            'metrics': [
                {
                    'key': 'employees',
                    'label': _('الموظفون النشطون'),
                    'value': self._count('hr.employee', active_employee_domain) if is_hr else self._count('hr.employee', team_domain),
                    'icon': 'fa-users',
                    'tone': 'teal',
                    'action': 'employees',
                },
                {
                    'key': 'leaves_pending',
                    'label': _('إجازاتي المعلقة'),
                    'value': self._count('hr.leave', pending_leave_domain),
                    'icon': 'fa-calendar-check-o',
                    'tone': 'amber',
                    'action': 'my_leaves',
                },
                {
                    'key': 'requests_pending',
                    'label': _('طلباتي المعلقة'),
                    'value': self._count('dm.hr.service.request', pending_request_domain),
                    'icon': 'fa-inbox',
                    'tone': 'violet',
                    'action': 'my_requests',
                },
                {
                    'key': 'approvals',
                    'label': _('موافقات بانتظارك'),
                    'value': self._count('dm.hr.service.request', approvals_domain),
                    'icon': 'fa-check-square-o',
                    'tone': 'blue',
                    'action': 'approvals',
                },
                {
                    'key': 'expiring_documents',
                    'label': _('مستندات تنتهي قريبًا'),
                    'value': self._count('dm.hr.document', documents_metric_domain) + self._count('hr.employee', iqama_metric_domain),
                    'icon': 'fa-exclamation-triangle',
                    'tone': 'red',
                    'action': 'documents' if is_hr else 'my_profile',
                },
                {
                    'key': 'attendance_today',
                    'label': _('سجلات حضور اليوم'),
                    'value': self._count('hr.attendance', attendance_metric_domain),
                    'icon': 'fa-clock-o',
                    'tone': 'green',
                    'action': 'attendance' if (is_hr or has_team) else 'my_attendance',
                },
            ],
            'quick_actions': [
                {'key': 'new_leave', 'label': _('طلب إجازة'), 'icon': 'fa-calendar-plus-o', 'description': _('إنشاء طلب إجازة ومتابعة الاعتماد')},
                {'key': 'new_permission', 'label': _('استئذان'), 'icon': 'fa-sign-out', 'description': _('طلب خروج مؤقت أو استئذان')},
                {'key': 'new_letter', 'label': _('خطاب تعريف'), 'icon': 'fa-file-text-o', 'description': _('طلب خطاب تعريف بالراتب')},
                {'key': 'new_salary_transfer', 'label': _('تثبيت راتب'), 'icon': 'fa-bank', 'description': _('خطاب تثبيت الراتب للبنك أو جهة التمويل')},
                {'key': 'new_other', 'label': _('طلب آخر'), 'icon': 'fa-plus-circle', 'description': _('عهدة، انتداب، تحديث بيانات أو طلب عام')},
            ],
            'service_sections': self._get_service_sections(
                is_hr,
                has_team,
                company.hr_workspace_attendance_enabled,
                company.hr_workspace_self_service_enabled,
            ),
            'workforce': {
                'team_count': self._count('hr.employee', team_domain),
                'active_count': self._count('hr.employee', active_employee_domain if is_hr else visible_employee_domain),
                'present_now': self._count('hr.attendance', open_attendance_domain if is_hr else open_attendance_domain + visible_attendance_domain),
                'approved_leaves': self._count('hr.leave', approved_leave_domain),
                'approved_requests': self._count('dm.hr.service.request', approved_request_domain),
            },
            'alerts': self._get_alerts(employee, expiring_date, is_hr),
            'recent_requests': self._get_recent_requests(my_request_domain),
            'pending_approvals': self._get_pending_approvals(approvals_domain),
            'recent_leaves': self._get_recent_leaves(my_leave_domain),
            'leave_balances': self._get_leave_balances(employee),
            'attendance_timeline': self._get_attendance_timeline(employee),
            'compliance': self._get_compliance(employee, expiring_date),
            'request_pipeline': self._get_request_pipeline(employee_domain) if is_hr else [],
            'hr_command': self._get_hr_command_center(employee_domain, expiring_date) if is_hr else {},
        }
        return dashboard

    @api.model
    def _get_service_sections(self, is_hr, has_team, attendance_enabled, self_service_enabled):
        my_items = [{'key': 'my_profile', 'label': _('ملفي الوظيفي'), 'icon': 'fa-id-card-o'}]
        if self_service_enabled:
            my_items += [
                {'key': 'my_requests', 'label': _('طلباتي'), 'icon': 'fa-inbox'},
                {'key': 'my_leaves', 'label': _('إجازاتي'), 'icon': 'fa-calendar-check-o'},
            ]
        if attendance_enabled:
            my_items.append({'key': 'my_attendance', 'label': _('حضوري وانصرافي'), 'icon': 'fa-clock-o'})
        sections = [{
            'key': 'self_service',
            'title': _('خدماتي'),
            'description': _('طلباتك وملفك وحضورك في مكان واحد'),
            'items': my_items,
        }]
        if has_team or is_hr:
            sections.append({
                'key': 'management',
                'title': _('إدارة الفريق والموافقات'),
                'description': _('متابعة الموظفين والطلبات التي تحتاج إجراء'),
                'items': [
                    {'key': 'employees', 'label': _('الموظفون'), 'icon': 'fa-users'},
                    {'key': 'approvals', 'label': _('الموافقات'), 'icon': 'fa-check-square-o'},
                    {'key': 'attendance', 'label': _('حضور الفريق'), 'icon': 'fa-calendar'},
                ],
            })
        if is_hr:
            operation_items = [
                {'key': 'new_employee', 'label': _('تعيين موظف جديد'), 'icon': 'fa-user-plus'},
                {'key': 'new_contract', 'label': _('إنشاء عقد جديد'), 'icon': 'fa-file-text-o'},
                {'key': 'contracts', 'label': _('العقود'), 'icon': 'fa-file-text'},
                {'key': 'shifts', 'label': _('ورديات العمل'), 'icon': 'fa-calendar-times-o'},
                {'key': 'documents', 'label': _('المستندات'), 'icon': 'fa-files-o'},
                {'key': 'insurance', 'label': _('التأمين الطبي'), 'icon': 'fa-shield'},
                {'key': 'allowances', 'label': _('البدلات'), 'icon': 'fa-money'},
                {'key': 'reports', 'label': _('التقارير والتحليل'), 'icon': 'fa-bar-chart'},
            ]
            if (self.env.user.has_group('dm_hr_core.group_dm_hr_manager')
                    or self.env.user.has_group('dm_hr_core.group_dm_hr_admin')):
                operation_items += [
                    {'key': 'approval_policies', 'label': _('موافقات طلبات الخدمات'), 'icon': 'fa-random'},
                    {'key': 'leave_approvals', 'label': _('موافقات الإجازات'), 'icon': 'fa-calendar-check-o'},
                    {'key': 'settings', 'label': _('الإعدادات المرنة'), 'icon': 'fa-sliders'},
                ]
            sections.append({
                'key': 'hr_operations',
                'title': _('عمليات الموارد البشرية'),
                'description': _('العقود والمستندات والتأمين والبدلات والتقارير'),
                'items': operation_items,
            })
        return sections

    @api.model
    def _get_recent_requests(self, domain):
        requests = self.env['dm.hr.service.request'].sudo().search(domain, order='create_date desc', limit=6)
        return [{
            'id': request.id,
            'number': request.name,
            'subject': request.subject,
            'type': request.request_type,
            'type_label': self._selection_label('dm.hr.service.request', 'request_type', request.request_type),
            'state': request.state,
            'state_label': self._selection_label('dm.hr.service.request', 'state', request.state),
            'tone': self._state_tone(request.state),
            'date': self._format_dt(request.create_date),
        } for request in requests]

    @api.model
    def _get_pending_approvals(self, domain):
        requests = self.env['dm.hr.service.request'].sudo().search(domain, order='create_date desc', limit=6)
        return [{
            'id': request.id,
            'number': request.name,
            'subject': request.subject,
            'employee': request.employee_id.name,
            'type_label': self._selection_label('dm.hr.service.request', 'request_type', request.request_type),
            'state_label': self._selection_label('dm.hr.service.request', 'state', request.state),
            'tone': self._state_tone(request.state),
            'date': self._format_dt(request.submitted_on or request.create_date),
        } for request in requests]

    @api.model
    def _get_recent_leaves(self, domain):
        leaves = self.env['hr.leave'].sudo().search(domain, order='create_date desc', limit=5)
        return [{
            'id': leave.id,
            'name': leave.holiday_status_id.name or leave.name or _('إجازة'),
            'date_from': self._format_date(leave.request_date_from),
            'date_to': self._format_date(leave.request_date_to),
            'duration': leave.duration_display or ('%s يوم' % (leave.number_of_days_display or 0)),
            'state': leave.state,
            'state_label': self._selection_label('hr.leave', 'state', leave.state),
            'tone': self._state_tone(leave.state),
        } for leave in leaves]

    @api.model
    def _get_leave_balances(self, employee):
        if not employee:
            return []
        leave_types = self.env['hr.leave.type'].sudo().with_context(
            employee_id=employee.id,
            default_employee_id=employee.id,
            from_dashboard=True,
        ).search([
            ('active', '=', True),
            ('company_id', 'in', [False] + self.env.companies.ids),
        ], order='sequence, id', limit=6)
        balances = []
        for leave_type in leave_types:
            maximum = round(leave_type.max_leaves or 0.0, 2)
            remaining = round(leave_type.virtual_remaining_leaves or 0.0, 2)
            taken = round(leave_type.leaves_taken or 0.0, 2)
            if leave_type.requires_allocation == 'yes' and not any([maximum, remaining, taken]):
                continue
            percentage = 0
            if maximum > 0:
                percentage = max(0, min(100, round((remaining / maximum) * 100)))
            balances.append({
                'id': leave_type.id,
                'name': leave_type.name,
                'remaining': remaining,
                'taken': taken,
                'maximum': maximum,
                'percentage': percentage,
                'unit': _('ساعة') if leave_type.request_unit == 'hour' else _('يوم'),
                'unlimited': leave_type.requires_allocation == 'no',
            })
        return balances[:5]

    @api.model
    def _get_attendance_timeline(self, employee):
        if not employee:
            return []
        attendances = self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', employee.id)],
            order='check_in desc',
            limit=6,
        )
        return [{
            'id': attendance.id,
            'check_in': self._format_dt(attendance.check_in),
            'check_out': self._format_dt(attendance.check_out) or _('لم يسجل انصراف'),
            'hours': round(attendance.worked_hours or 0.0, 2),
            'open': not bool(attendance.check_out),
        } for attendance in attendances]

    @api.model
    def _get_compliance(self, employee, expiring_date):
        if not employee:
            return []
        active_contract = self.env['hr.contract'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['open', 'draft']),
        ], limit=1)
        bank_contract = self.env['hr.contract'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['open', 'draft']),
            ('dm_payment_method', '=', 'bank_transfer'),
        ], limit=1)
        active_insurance = self.env['dm.hr.insurance.policy'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'active'),
        ], limit=1)
        documents = self.env['dm.hr.document'].sudo().search_count([
            ('employee_id', '=', employee.id),
        ], limit=1)
        return [
            {
                'label': _('ربط المستخدم بالموظف'),
                'done': bool(employee.user_id),
                'detail': _('مكتمل') if employee.user_id else _('اربط المستخدم بملف الموظف'),
            },
            {
                'label': _('هوية / إقامة'),
                'done': bool(employee.iqama_no and employee.iqama_expiry_date and employee.iqama_expiry_date > expiring_date),
                'detail': _('صالحة') if employee.iqama_expiry_date and employee.iqama_expiry_date > expiring_date else _('ناقصة أو تنتهي قريبًا'),
            },
            {
                'label': _('التأمينات الاجتماعية'),
                'done': bool(employee.gosi_employee_category and employee.social_security_no),
                'detail': _('مكتملة') if employee.gosi_employee_category and employee.social_security_no else _('تحتاج فئة ورقم اشتراك'),
            },
            {
                'label': _('العقد الوظيفي'),
                'done': bool(active_contract),
                'detail': _('يوجد عقد نشط/مسودة') if active_contract else _('لا يوجد عقد نشط'),
            },
            {
                'label': _('حماية الأجور'),
                'done': bool(employee.dm_bank_name and employee.dm_iban and bank_contract),
                'detail': _('بيانات بنكية وتحويل راتب مكتملة') if employee.dm_bank_name and employee.dm_iban and bank_contract else _('تحتاج بنك/IBAN وعقد بتحويل بنكي'),
            },
            {
                'label': _('التأمين الطبي'),
                'done': bool(active_insurance),
                'detail': _('وثيقة نشطة') if active_insurance else _('لا توجد وثيقة نشطة'),
            },
            {
                'label': _('مستندات الموظف'),
                'done': bool(documents),
                'detail': _('يوجد مستندات') if documents else _('أضف المستندات الأساسية'),
            },
        ]

    @api.model
    def _get_request_pipeline(self, employee_domain):
        Request = self.env['dm.hr.service.request'].sudo()
        base = [('company_id', 'in', self.env.companies.ids)]
        states = ['draft', 'submitted', 'manager_approved', 'approved', 'rejected']
        return [{
            'state': state,
            'label': self._selection_label('dm.hr.service.request', 'state', state),
            'count': Request.search_count(base + [('state', '=', state)]),
            'tone': self._state_tone(state),
        } for state in states]

    @api.model
    def _get_hr_command_center(self, employee_domain, expiring_date):
        Employee = self.env['hr.employee'].sudo()
        return {
            'missing_gosi': Employee.search_count(employee_domain + [
                ('active', '=', True),
                '|',
                ('gosi_employee_category', '=', False),
                ('social_security_no', '=', False),
            ]),
            'iqama_expiring': Employee.search_count(employee_domain + [
                ('active', '=', True),
                ('iqama_expiry_date', '!=', False),
                ('iqama_expiry_date', '<=', expiring_date),
            ]),
            'without_manager': Employee.search_count(employee_domain + [
                ('active', '=', True),
                ('parent_id', '=', False),
            ]),
            'without_contract': Employee.search_count(employee_domain + [
                ('active', '=', True),
                ('contract_ids', '=', False),
            ]),
            'missing_bank': Employee.search_count(employee_domain + [
                ('active', '=', True),
                '|',
                ('dm_bank_name', '=', False),
                ('dm_iban', '=', False),
            ]),
        }

    @api.model
    def _get_alerts(self, employee, expiring_date, is_hr):
        alerts = []
        if not employee:
            alerts.append({
                'level': 'danger',
                'title': _('لا يوجد موظف مرتبط'),
                'message': _('اربط المستخدم بموظف حتى تظهر خدمات الموظف الذاتية والحضور والإجازات.'),
                'action': 'employees',
            })
            return alerts
        if employee.iqama_expiry_date and employee.iqama_expiry_date <= expiring_date:
            alerts.append({
                'level': 'danger',
                'title': _('تنبيه هوية / إقامة'),
                'message': _('هوية أو إقامة الموظف تنتهي خلال 30 يومًا.'),
                'action': 'my_profile',
            })
        if not employee.gosi_employee_category:
            alerts.append({
                'level': 'warning',
                'title': _('بيانات التأمينات ناقصة'),
                'message': _('لم يتم تحديد فئة الموظف في التأمينات الاجتماعية.'),
                'action': 'my_profile',
            })
        pending = self._count('dm.hr.service.request', [
            ('employee_id', '=', employee.id),
            ('state', 'in', ['submitted', 'manager_approved']),
        ])
        if pending:
            alerts.append({
                'level': 'info',
                'title': _('طلبات قيد الاعتماد'),
                'message': _('لديك %s طلب/طلبات بانتظار الاعتماد.') % pending,
                'action': 'my_requests',
            })
        if is_hr:
            missing_gosi = self._count('hr.employee', [
                ('active', '=', True),
                ('gosi_employee_category', '=', False),
                ('company_id', 'in', self.env.companies.ids),
            ])
            if missing_gosi:
                alerts.append({
                    'level': 'warning',
                    'title': _('امتثال التأمينات'),
                    'message': _('%s موظف/موظفين بدون فئة تأمينات اجتماعية.') % missing_gosi,
                    'action': 'employees',
                })
        return alerts[:6]

    @api.model
    def open_action(self, action_key):
        employee = self._get_user_employee()
        action_map = {
            'workspace': 'dm_hr_workspace.action_dm_hr_workspace',
            'my_requests': 'dm_hr_core.dm_hr_service_request_action_my',
            'my_leaves': 'dm_hr_core.dm_hr_leave_action_my',
            'attendance': 'dm_hr_core.dm_hr_attendance_action_all',
            'my_attendance': 'dm_hr_core.dm_hr_attendance_action_my',
            'approvals': 'dm_hr_core.dm_hr_service_request_action_all',
            'documents': 'dm_hr_core.dm_hr_document_action',
            'employees': 'hr.open_view_employee_list_my',
            'new_leave': 'hr_holidays.hr_leave_action_my_request',
            'contracts': 'hr_contract.action_hr_contract',
            'insurance': 'dm_hr_core.dm_hr_insurance_policy_action',
            'allowances': 'dm_hr_core.dm_hr_employee_allowance_action',
            'reports': 'dm_hr_core.dm_hr_attendance_report_action',
            'settings': 'dm_hr_workspace.action_dm_hr_workspace_settings',
            'approval_policies': 'dm_hr_core.dm_hr_approval_policy_action',
            'leave_approvals': 'hr_holidays.open_view_holiday_status',
            'shifts': 'dm_hr_core.dm_hr_shift_action',
        }
        hr_only_actions = {
            'contracts', 'insurance', 'allowances', 'reports', 'settings',
            'documents', 'approval_policies', 'leave_approvals', 'shifts',
            'new_employee', 'new_contract',
        }
        if action_key in hr_only_actions and not self._is_hr_user():
            raise UserError(_('ليس لديك صلاحية لفتح هذا القسم.'))
        if action_key in {'approval_policies', 'leave_approvals', 'settings'} and not (
            self.env.user.has_group('dm_hr_core.group_dm_hr_manager')
            or self.env.user.has_group('dm_hr_core.group_dm_hr_admin')
        ):
            raise UserError(_('إعدادات الموافقات متاحة لمدير الموارد البشرية فقط.'))
        if action_key == 'new_employee':
            return {
                'name': _('تعيين موظف جديد'), 'type': 'ir.actions.act_window',
                'res_model': 'hr.employee', 'view_mode': 'form',
                'views': [(False, 'form')], 'target': 'current',
                'context': {'default_company_id': self.env.company.id},
            }
        if action_key == 'new_contract':
            return {
                'name': _('إنشاء عقد جديد'), 'type': 'ir.actions.act_window',
                'res_model': 'hr.contract', 'view_mode': 'form',
                'views': [(False, 'form')], 'target': 'current',
                'context': {'default_company_id': self.env.company.id},
            }
        if action_key == 'new_leave' and not self.env.company.hr_workspace_self_service_enabled:
            raise UserError(_('الخدمة الذاتية غير مفعلة لهذه الجهة.'))
        if action_key in action_map:
            result = self._action_from_xmlid(action_map[action_key])
            if action_key == 'approvals' and result:
                result['domain'] = [('state', 'in', ['submitted', 'manager_approved'])]
            return result
        request_defaults = {
            'new_permission': ('permission', _('استئذان')),
            'new_letter': ('salary_certificate', _('خطاب تعريف بالراتب')),
            'new_salary_transfer': ('salary_transfer_certificate', _('خطاب تثبيت راتب')),
            'new_other': ('other', _('طلب آخر')),
        }
        if action_key in request_defaults and not self.env.company.hr_workspace_self_service_enabled:
            raise UserError(_('الخدمة الذاتية غير مفعلة لهذه الجهة.'))
        if action_key in request_defaults:
            request_type, subject = request_defaults[action_key]
            return {
                'name': subject,
                'type': 'ir.actions.act_window',
                'res_model': 'dm.hr.service.request',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'target': 'current',
                'context': {
                    'default_employee_id': employee.id if employee else False,
                    'default_request_type': request_type,
                    'default_subject': subject,
                },
            }
        if action_key == 'my_profile' and employee:
            return {
                'name': _('ملفي الوظيفي'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.employee',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_id': employee.id,
            }
        return False

    @api.model
    def toggle_attendance(self, geo_information=None):
        employee = self._get_user_employee()
        if not employee:
            raise UserError(_('لا يوجد موظف مرتبط بالمستخدم الحالي.'))
        if not self.env.company.hr_workspace_attendance_enabled:
            raise UserError(_('تسجيل الحضور من المنصة غير مفعل لهذه الجهة.'))
        geo_information = geo_information or {}
        if self.env.company.hr_workspace_gps_required:
            latitude = geo_information.get('latitude')
            longitude = geo_information.get('longitude')
            accuracy = geo_information.get('gps_accuracy')
            if latitude is None or longitude is None:
                raise UserError(_('يجب السماح بالوصول إلى الموقع لتسجيل الحضور أو الانصراف.'))
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise UserError(_('إحداثيات الموقع غير صحيحة.'))
            max_accuracy = self.env.company.hr_workspace_gps_max_accuracy
            if max_accuracy and (accuracy is None or accuracy > max_accuracy):
                raise UserError(_(
                    'دقة الموقع الحالية (%s متر) أقل من الدقة المطلوبة (%s متر). حاول في مكان مفتوح.'
                ) % (round(accuracy or 0), round(max_accuracy)))
        allowed_geo = {
            'mode': 'manual',
            'latitude': geo_information.get('latitude', 0.0),
            'longitude': geo_information.get('longitude', 0.0),
            'gps_accuracy': geo_information.get('gps_accuracy', 0.0),
        }
        if self.env.company.hr_workspace_geofence_required:
            location, distance = self._get_attendance_location(
                employee, allowed_geo['latitude'], allowed_geo['longitude']
            )
            if not location:
                raise UserError(_(
                    'رفض تسجيل الحضور: موقعك الحالي خارج نطاق مواقع البصمة المعتمدة أو لا يوجد موقع مخصص لك. راجع إعدادات مواقع GPS أو اقترب من نقطة البصمة.'
                ))
            allowed_geo['dm_location_id'] = location.id
        before_attendance = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
        ], order='id desc', limit=1)
        employee.sudo()._attendance_action_change(allowed_geo)
        attendance = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
        ], order='id desc', limit=1)
        if attendance:
            source = 'manual'
            compliance = 'missing'
            if self.env.company.hr_workspace_geofence_required and allowed_geo.get('dm_location_id'):
                source = 'gps_geofence'
                compliance = 'verified'
            elif self.env.company.hr_workspace_gps_required:
                source = 'gps_only'
                compliance = 'gps_only'
            if attendance != before_attendance or not attendance.check_out:
                attendance.write({
                    'dm_attendance_source': source,
                    'dm_gps_compliance': compliance,
                })
        return self.get_dashboard_data()

    @api.model
    def _get_attendance_location(self, employee, latitude, longitude):
        locations = self.env['dm.hr.attendance.location'].sudo().search([
            ('active', '=', True),
            ('company_id', '=', employee.company_id.id),
            '|', ('employee_ids', '=', False), ('employee_ids', 'in', employee.id),
        ])
        nearest = self.env['dm.hr.attendance.location']
        nearest_distance = False
        for location in locations:
            lat_delta = radians(location.latitude - latitude)
            lon_delta = radians(location.longitude - longitude)
            value = sin(lat_delta / 2) ** 2 + cos(radians(latitude)) * \
                cos(radians(location.latitude)) * sin(lon_delta / 2) ** 2
            distance = 6371000 * 2 * asin(sqrt(value))
            if distance <= location.radius_meters and (
                    nearest_distance is False or distance < nearest_distance):
                nearest, nearest_distance = location, distance
        return nearest, nearest_distance
