# -*- coding: utf-8 -*-
{
    'name': 'لوحة الحسابات الاحترافية',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'داشبورد عربي احترافي للحسابات والتحصيل والمدفوعات والسندات',
    'description': """
لوحة حسابات احترافية
====================

مركز قيادة مالي عربي لعرض مؤشرات الحسابات، الذمم، السيولة، السندات،
الفواتير الحديثة، والتنبيهات التنفيذية في Odoo 17 Community.
    """,
    'author': 'DM',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_payment',
        'dm_finance_core',
        'dm_finance_voucher',
        'web',
    ],
    'data': [
        'views/dm_finance_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_web': [
            'dm_finance_dashboard/static/src/js/finance_dashboard.js',
            'dm_finance_dashboard/static/src/xml/finance_dashboard.xml',
            'dm_finance_dashboard/static/src/scss/finance_dashboard.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
