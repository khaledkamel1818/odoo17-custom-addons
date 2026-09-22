# -*- coding: utf-8 -*-
{
    'name': 'DM HR Custody Asset Link',
    'summary': 'Link non-financial employee custody with accounting fixed assets',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'author': 'DM',
    'license': 'LGPL-3',
    'depends': ['dm_hr_core', 'dm_hr_offboarding', 'om_account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/dm_hr_asset_custody_views.xml',
    ],
    'installable': True,
    'application': False,
}
