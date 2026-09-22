# -*- coding: utf-8 -*-
{
    'name': 'المالية الأساسية',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'أساس المالية: الفروع، الأبعاد، الموافقات، الصلاحيات، والإعدادات',
    'description': """
DM Finance Core
===============
Phase 1 foundation for the Saudi Finance Suite on Odoo 17 Community.

This module introduces shared finance configuration, branch/dimension
foundations, approval-route metadata, audit foundations, menus, security
groups, and bilingual UI terms. It does not post accounting entries.
""",
    'license': 'LGPL-3',
    'author': 'DM',
    'depends': [
        'account',
        'analytic',
        'base_setup',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/dm_finance_branch_views.xml',
        'views/dm_finance_approval_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
