# -*- coding: utf-8 -*-
{
    'name': 'مركز الإجازات الذكي',
    'version': '17.0.1.0.1',
    'category': 'Human Resources/Time Off',
    'summary': 'واجهة عربية موحدة للإجازات والأرصدة والاعتمادات',
    'license': 'LGPL-3',
    'author': 'DM',
    'depends': ['dm_hr_workspace', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/holiday_status_data.xml',
        'data/cron_data.xml',
        'views/hr_leave_allocation_views.xml',
        'views/hr_leave_hub_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dm_hr_leave_hub/static/src/js/leave_hub.js',
            'dm_hr_leave_hub/static/src/xml/leave_hub.xml',
            'dm_hr_leave_hub/static/src/scss/leave_hub.scss',
        ],
    },
    'application': False,
    'installable': True,
}
