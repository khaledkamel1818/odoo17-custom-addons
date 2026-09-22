# -*- coding: utf-8 -*-

{
    'name': 'DM Finance Enhancement',
    'summary': 'Professional finance layer for Saudi and Egyptian accounting requirements',
    'description': """
DM Finance Enhancement
======================

Professional finance enhancement layer for Odoo 17 Community.

It adds:
* Executive finance dashboard.
* Advanced chart of accounts hierarchy and balances.
* Dynamic financial report wizard with PDF/XLSX exports.
* VAT, Zakat, withholding and localization configuration.
* Bank reconciliation workspace with CSV/XLSX import and suggested matching.
* Annual closing workflow with audit trail.
* Fixed asset enhancement over the existing asset module.
    """,
    'version': '17.0.1.0.1',
    'category': 'Accounting/Accounting',
    'author': 'DM',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_payment',
        'analytic',
        'mail',
        'web',
        'dm_finance_core',
        'dm_finance_dashboard',
        'dm_finance_voucher',
        'accounting_pdf_reports',
        'om_account_asset',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/sequence_data.xml',
        'views/res_config_settings_views.xml',
        'views/account_account_views.xml',
        'views/bank_reconciliation_views.xml',
        'views/annual_closing_views.xml',
        'views/asset_views.xml',
        'wizard/finance_report_wizard_views.xml',
        'report/finance_report_templates.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
        'views/menu_unification_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dm_finance_enhancement/static/src/js/finance_dashboard.js',
            'dm_finance_enhancement/static/src/xml/finance_dashboard.xml',
            'dm_finance_enhancement/static/src/scss/finance_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
