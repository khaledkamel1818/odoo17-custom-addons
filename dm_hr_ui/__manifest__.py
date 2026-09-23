# -*- coding: utf-8 -*-
{
    'name': 'DM HR UI/UX',
    'summary': 'Unified HR navigation and visual system for DM HR',
    'version': '17.0.1.0.4',
    'category': 'Human Resources',
    'author': 'DM',
    'license': 'LGPL-3',
    'depends': [
        'dm_hr_core',
        'dm_hr_workspace',
        'dm_hr_leave_hub',
        'dm_hr_offboarding',
        'dm_hr_asset_custody',
    ],
    'data': [
        'views/hr_ui_view_inherit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dm_hr_ui/static/src/scss/hr_ui.scss',
            'dm_hr_ui/static/src/js/hr_navbar.js',
        ],
        'web.assets_tests': [
            'dm_hr_ui/static/tests/tours/hr_ui_tours.js',
        ],
    },
    'installable': True,
    'application': False,
}
