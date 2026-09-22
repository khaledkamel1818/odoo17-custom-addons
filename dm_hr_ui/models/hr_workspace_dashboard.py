# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import UserError


class DmHrWorkspaceDashboard(models.AbstractModel):
    _inherit = 'dm.hr.workspace.dashboard'

    @api.model
    def _is_finance_user(self):
        user = self.env.user
        return any([
            user.has_group('dm_hr_core.group_dm_payroll_officer'),
            user.has_group('dm_hr_core.group_dm_payroll_manager'),
            user.has_group('dm_hr_offboarding.group_dm_hr_offboarding_finance_officer'),
            user.has_group('dm_hr_offboarding.group_dm_hr_offboarding_finance_manager'),
        ])

    @api.model
    def get_dashboard_data(self):
        data = super().get_dashboard_data()
        employee = self._get_user_employee()
        is_hr = self._is_hr_user()
        is_finance = self._is_finance_user()
        user = self.env.user
        has_team = data.get('user', {}).get('is_manager')
        company_domain = [('company_id', 'in', self.env.companies.ids)]
        my_employee_domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        team_employee_ids = self.env['hr.employee'].sudo().search([
            ('parent_id.user_id', '=', user.id),
            ('company_id', 'in', self.env.companies.ids),
        ]).ids

        off_domain = company_domain if is_hr else my_employee_domain
        if has_team and not is_hr:
            off_domain = ['|', ('employee_id', 'in', team_employee_ids)] + my_employee_domain
        open_off_domain = off_domain + [('state', 'not in', ['done', 'rejected', 'cancelled'])]

        data.setdefault('metrics', [])
        data['metrics'].append({
            'key': 'offboarding_open',
            'label': _('إنهاء خدمة مفتوح'),
            'value': self._count('dm.hr.offboarding', open_off_domain),
            'icon': 'fa-sign-out',
            'tone': 'red',
            'action': 'offboarding',
        })
        if is_finance or is_hr:
            data['metrics'].append({
                'key': 'settlements_pending',
                'label': _('تسويات بانتظار المراجعة'),
                'value': self._count('dm.hr.offboarding.settlement', company_domain + [('state', 'in', ['draft', 'ready'])]),
                'icon': 'fa-money',
                'tone': 'amber',
                'action': 'final_settlements',
            })
            data['metrics'].append({
                'key': 'financial_requests_open',
                'label': _('طلبات مالية مفتوحة'),
                'value': self._count('dm.hr.employee.financial.request', company_domain + [('state', 'not in', ['settled', 'rejected', 'cancelled'])]),
                'icon': 'fa-credit-card',
                'tone': 'violet',
                'action': 'financial_requests',
            })
        if is_hr:
            data['metrics'].append({
                'key': 'custodies_delivered',
                'label': _('عهد مسلمة'),
                'value': self._count('dm.hr.custody', company_domain + [('state', '=', 'delivered')]),
                'icon': 'fa-briefcase',
                'tone': 'blue',
                'action': 'custodies',
            })

        data.setdefault('quick_actions', [])
        if employee:
            data['quick_actions'].append({
                'key': 'new_resignation',
                'label': _('تقديم استقالة'),
                'icon': 'fa-sign-out',
                'description': _('بدء طلب إنهاء خدمة مع مسار موافقات وإخلاء طرف'),
            })
            data['quick_actions'].append({
                'key': 'new_advance',
                'label': _('طلب سلفة'),
                'icon': 'fa-credit-card',
                'description': _('طلب مالي بجدولة أقساط بعد الاعتماد'),
            })

        data.setdefault('service_sections', [])
        if is_hr or has_team or employee:
            data['service_sections'].append({
                'key': 'offboarding',
                'title': _('إنهاء الخدمة وإخلاء الطرف'),
                'description': _('الاستقالات، الإخلاء، التسويات النهائية، ومقابلات الخروج'),
                'items': [
                    {'key': 'offboarding', 'label': _('طلبات إنهاء الخدمة'), 'icon': 'fa-sign-out'},
                    {'key': 'custodies', 'label': _('العهد'), 'icon': 'fa-briefcase'},
                    {'key': 'final_settlements', 'label': _('التسويات النهائية'), 'icon': 'fa-money'},
                ],
            })
        if is_finance or is_hr:
            data['service_sections'].append({
                'key': 'finance',
                'title': _('المالية والرواتب'),
                'description': _('السلف، القروض، الأقساط، والتسويات'),
                'items': [
                    {'key': 'financial_requests', 'label': _('السلف والقروض'), 'icon': 'fa-credit-card'},
                    {'key': 'installments', 'label': _('الأقساط والتسويات'), 'icon': 'fa-list-ol'},
                    {'key': 'final_settlements', 'label': _('تسويات إنهاء الخدمة'), 'icon': 'fa-calculator'},
                ],
            })
        return data

    @api.model
    def open_action(self, action_key):
        employee = self._get_user_employee()
        is_hr = self._is_hr_user()
        is_finance = self._is_finance_user()
        has_team = bool(self.env['hr.employee'].sudo().search_count([
            ('parent_id.user_id', '=', self.env.user.id),
            ('company_id', 'in', self.env.companies.ids),
        ]))
        if action_key == 'new_resignation':
            resignation = self.env.ref('dm_hr_offboarding.offboarding_type_resignation', raise_if_not_found=False)
            return {
                'name': _('تقديم استقالة'),
                'type': 'ir.actions.act_window',
                'res_model': 'dm.hr.offboarding',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'target': 'current',
                'context': {
                    'default_employee_id': employee.id if employee else False,
                    'default_termination_type_id': resignation.id if resignation else False,
                },
            }
        if action_key == 'new_advance':
            return self._normalize_act_window({
                'name': _('طلب سلفة'),
                'type': 'ir.actions.act_window',
                'res_model': 'dm.hr.employee.financial.request',
                'view_mode': 'form',
                'context': {
                    'default_employee_id': employee.id if employee else False,
                    'default_request_type': 'advance',
                },
            })
        if action_key == 'offboarding':
            if is_hr:
                return self._action_from_xmlid('dm_hr_offboarding.dm_hr_offboarding_action_all')
            if has_team:
                return self._action_from_xmlid('dm_hr_offboarding.dm_hr_offboarding_action_team')
            return self._action_from_xmlid('dm_hr_offboarding.dm_hr_offboarding_action_my')
        if action_key == 'final_settlements':
            if not (is_finance or is_hr):
                raise UserError(_('التسويات النهائية متاحة للمالية والموارد البشرية المخولة فقط.'))
            return self._action_from_xmlid('dm_hr_offboarding.dm_hr_offboarding_settlement_action')
        if action_key == 'financial_requests':
            if not (is_finance or is_hr):
                raise UserError(_('الطلبات المالية متاحة للمالية والموارد البشرية المخولة فقط.'))
            return self._action_from_xmlid('dm_hr_core.dm_hr_employee_financial_request_report_action')
        if action_key == 'installments':
            if not (is_finance or is_hr):
                raise UserError(_('الأقساط متاحة للمالية والموارد البشرية المخولة فقط.'))
            return self._action_from_xmlid('dm_hr_core.dm_hr_employee_financial_installment_action')
        if action_key == 'custodies':
            if not (is_hr or has_team):
                # Employees still can reach their own custodies through employee file/security if allowed.
                raise UserError(_('العهد متاحة للموارد البشرية أو المدير حسب الصلاحيات.'))
            return self._action_from_xmlid('dm_hr_core.dm_hr_custody_action')
        return super().open_action(action_key)
