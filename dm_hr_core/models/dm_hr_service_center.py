# -*- coding: utf-8 -*-
from odoo import _, api, models


class DmHrServiceCenter(models.AbstractModel):
    _name = 'dm.hr.service.center'
    _description = 'مركز خدمات الموظفين'

    @api.model
    def get_dashboard_data(self):
        Request = self.env['dm.hr.service.request']
        user = self.env.user
        employee = user.employee_id or self.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        my_domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        approval_domain = [
            ('state', 'in', ['submitted', 'manager_approved']),
            '|',
            ('manager_user_id', '=', user.id),
            '|',
            ('approval_item_ids.approver_user_id', '=', user.id),
            ('approval_item_ids.delegate_user_id', '=', user.id),
        ]
        cards = [
            {
                'key': 'new_permission',
                'title': _('استئذان'),
                'description': _('طلب خروج أو تأخير أو انصراف مبكر.'),
                'icon': 'fa-clock-o',
            },
            {
                'key': 'new_salary_certificate',
                'title': _('تعريف الراتب'),
                'description': _('إصدار خطاب تعريف راتب للجهات الخارجية.'),
                'icon': 'fa-file-text-o',
            },
            {
                'key': 'new_salary_transfer',
                'title': _('تثبيت/تحويل الراتب للبنك'),
                'description': _('خطاب تثبيت راتب مرتبط بالبنك وIBAN.'),
                'icon': 'fa-bank',
            },
            {
                'key': 'new_business_trip',
                'title': _('انتداب'),
                'description': _('طلب مهمة عمل أو انتداب مع مدة واضحة.'),
                'icon': 'fa-briefcase',
            },
        ]
        return {
            'employee': employee.name if employee else _('غير مرتبط بموظف'),
            'counts': {
                'my_draft': Request.search_count(my_domain + [('state', '=', 'draft')]),
                'my_pending': Request.search_count(my_domain + [('state', 'in', ['submitted', 'manager_approved'])]),
                'my_approved': Request.search_count(my_domain + [('state', '=', 'approved')]),
                'to_approve': Request.search_count(approval_domain),
            },
            'cards': cards,
        }

    @api.model
    def open_action(self, key):
        action_xml = {
            'my_requests': 'dm_hr_core.dm_hr_service_request_action_my',
            'to_approve': 'dm_hr_core.dm_hr_service_request_action_to_approve',
            'new_request': 'dm_hr_core.dm_hr_service_request_action_new',
            'new_permission': 'dm_hr_core.dm_hr_service_request_action_new',
            'new_salary_certificate': 'dm_hr_core.dm_hr_service_request_action_new',
            'new_salary_transfer': 'dm_hr_core.dm_hr_service_request_action_new',
            'new_business_trip': 'dm_hr_core.dm_hr_service_request_action_new',
        }.get(key)
        if not action_xml:
            return False
        action = self.env.ref(action_xml).sudo().read()[0]
        defaults = {
            'new_permission': {'default_request_type': 'permission', 'default_subject': _('طلب استئذان')},
            'new_salary_certificate': {'default_request_type': 'salary_certificate', 'default_subject': _('طلب تعريف راتب')},
            'new_salary_transfer': {'default_request_type': 'salary_transfer_certificate', 'default_subject': _('طلب تثبيت/تحويل راتب للبنك')},
            'new_business_trip': {'default_request_type': 'business_trip', 'default_subject': _('طلب انتداب')},
        }.get(key, {})
        context = action.get('context') if isinstance(action.get('context'), dict) else {}
        context.update(defaults)
        action['context'] = context
        if key.startswith('new_'):
            action['views'] = [(False, 'form')]
        return action
