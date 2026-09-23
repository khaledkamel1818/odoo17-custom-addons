# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class DmHrLeaveHub(models.AbstractModel):
    _name = 'dm.hr.leave.hub'
    _description = 'مركز الإجازات الذكي'

    @api.model
    def _employee(self):
        return self.env.user.employee_id or self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', 'in', self.env.companies.ids),
        ], limit=1)

    @api.model
    def _is_leave_officer(self):
        return self.env.user.has_group('hr_holidays.group_hr_holidays_user')

    @api.model
    def _is_leave_manager(self):
        return self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

    @api.model
    def _label(self, field_name, value):
        field = self.env['hr.leave']._fields[field_name]
        return dict(field._description_selection(self.env)).get(value, value)

    @api.model
    def _action(self, xmlid):
        action = self.env['ir.actions.actions'].sudo()._for_xml_id(xmlid)
        if action.get('type') == 'ir.actions.act_window' and not action.get('views'):
            action['views'] = [(False, mode.strip()) for mode in
                               (action.get('view_mode') or 'tree,form').split(',')]
        action.setdefault('target', 'current')
        action.setdefault('context', {})
        return action

    @api.model
    def get_data(self):
        employee = self._employee()
        employee_id = employee.id if employee else 0
        Leave = self.env['hr.leave'].sudo()
        my_domain = [('employee_id', '=', employee_id)]
        officer = self._is_leave_officer()
        manager = self._is_leave_manager()
        pending_states = ['confirm', 'validate1']
        pending_approval_domain = [
            ('state', 'in', pending_states),
            ('employee_id.company_id', 'in', self.env.companies.ids),
        ]
        if not officer:
            pending_approval_domain += [('employee_id.leave_manager_id', '=', self.env.user.id)]

        leave_types = self.env['hr.leave.type'].sudo().with_context(
            employee_id=employee_id,
            default_employee_id=employee_id,
            from_dashboard=True,
        ).search([
            ('active', '=', True),
            ('company_id', 'in', [False] + self.env.companies.ids),
        ], order='sequence,id', limit=8) if employee else self.env['hr.leave.type']

        balances = []
        for leave_type in leave_types:
            allocated = round(leave_type.max_leaves or 0.0, 2)
            remaining = round(leave_type.virtual_remaining_leaves or 0.0, 2)
            taken = round(leave_type.leaves_taken or 0.0, 2)
            if leave_type.requires_allocation == 'yes' and not any((allocated, remaining, taken)):
                continue
            balances.append({
                'id': leave_type.id,
                'name': leave_type.name,
                'remaining': remaining,
                'taken': taken,
                'allocated': allocated,
                'unlimited': leave_type.requires_allocation == 'no',
                'unit': _('ساعة') if leave_type.request_unit == 'hour' else _('يوم'),
                'percentage': None if leave_type.requires_allocation == 'no' else max(0, min(100, round(remaining * 100 / allocated))) if allocated > 0 else 0,
            })

        recent = Leave.search(my_domain, order='request_date_from desc, id desc', limit=7)
        return {
            'employee': {
                'id': employee.id if employee else False,
                'name': employee.name if employee else _('لا يوجد موظف مرتبط بالمستخدم'),
                'department': employee.department_id.name if employee and employee.department_id else '',
            },
            'role': {'officer': officer, 'manager': manager},
            'metrics': {
                'pending': Leave.search_count(my_domain + [('state', 'in', pending_states)]),
                'approved': Leave.search_count(my_domain + [('state', '=', 'validate')]),
                'refused': Leave.search_count(my_domain + [('state', '=', 'refuse')]),
                'waiting_approval': Leave.search_count(pending_approval_domain) if officer or employee else 0,
            },
            'balances': balances,
            'recent': [{
                'id': leave.id,
                'type': leave.holiday_status_id.name or _('إجازة'),
                'from': fields.Date.to_string(leave.request_date_from),
                'to': fields.Date.to_string(leave.request_date_to),
                'duration': leave.duration_display,
                'state': leave.state,
                'state_label': self._label('state', leave.state),
            } for leave in recent],
        }

    @api.model
    def open_action(self, key):
        actions = {
            'new': 'hr_holidays.hr_leave_action_my_request',
            'mine': 'dm_hr_core.dm_hr_leave_action_my',
            'calendar': 'hr_holidays.hr_leave_action_new_request',
            'allocations': 'hr_holidays.hr_leave_allocation_action_my',
            'manual_balance': 'dm_hr_leave_hub.dm_hr_leave_balance_wizard_action',
            'annual_balance': 'dm_hr_leave_hub.dm_hr_leave_annual_allocation_wizard_action',
            'approvals': 'hr_holidays.hr_leave_action_action_approve_department',
            'allocation_approvals': 'hr_holidays.hr_leave_allocation_action_approve_department',
            'types': 'hr_holidays.open_view_holiday_status',
            'accruals': 'hr_holidays.open_view_accrual_plans',
            'reports': 'hr_holidays.action_hr_available_holidays_report',
        }
        if key not in actions:
            raise UserError(_('الإجراء المطلوب غير معروف.'))
        if key in {'approvals', 'allocation_approvals', 'manual_balance', 'annual_balance'} and not self._is_leave_officer():
            raise AccessError(_('ليس لديك صلاحية اعتماد الإجازات.'))
        if key in {'types', 'accruals'} and not self._is_leave_manager():
            raise AccessError(_('ليس لديك صلاحية إعداد الإجازات.'))
        return self._action(actions[key])


class DmHrWorkspaceDashboard(models.AbstractModel):
    _inherit = 'dm.hr.workspace.dashboard'

    @api.model
    def open_action(self, action_key):
        if action_key == 'my_leaves':
            return self.env['ir.actions.actions'].sudo()._for_xml_id(
                'dm_hr_leave_hub.action_dm_hr_leave_hub'
            )
        return super().open_action(action_key)
