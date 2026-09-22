# -*- coding: utf-8 -*-
{
    'name': 'DM HR Offboarding',
    'summary': 'Resignation, termination, clearance, EOS and final settlement',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'author': 'DM',
    'license': 'LGPL-3',
    'depends': ['hr', 'hr_contract', 'hr_holidays', 'hr_attendance', 'mail', 'dm_hr_core'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/sequence_data.xml',
        'data/offboarding_type_data.xml',
        'views/dm_hr_offboarding_views.xml',
        'reports/dm_hr_offboarding_reports.xml',
        'views/menus.xml',
    ],
    'application': False,
    'installable': True,
}
