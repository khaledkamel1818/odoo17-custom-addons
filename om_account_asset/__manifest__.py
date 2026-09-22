# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'إدارة الأصول',
    'version': '17.0.1.0.3',
    'author': 'Odoo Mates, Odoo SA',
    'depends': ['account'],
    'description': """إدارة الأصول المملوكة للشركة أو الأشخاص.
        يتابع الإهلاك ويُنشئ قيود اليومية المقابلة.""",
    'summary': 'إدارة الأصول والإهلاك',
    'category': 'Accounting',
    'sequence': 10,
    'website': 'https://www.odoomates.tech',
    'license': 'LGPL-3',
    'images': ['static/description/assets.gif'],
    'data': [
        'data/account_asset_data.xml',
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/asset_modify_views.xml',
        'views/account_asset_views.xml',
        'views/account_move_views.xml',
        'views/account_asset_templates.xml',
        'views/asset_category_views.xml',
        'views/product_views.xml',
        'report/account_asset_report_views.xml',
        'views/app_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'om_account_asset/static/src/scss/account_asset.scss',
        ],
    },
}
