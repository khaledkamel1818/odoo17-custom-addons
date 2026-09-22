# -*- coding: utf-8 -*-

{
    'name': 'السندات المالية',
    'summary': 'سندات قبض وصرف وتحويل مع دورة موافقات مالية',
    'description': """
أساس السندات المالية في Odoo 17 Community.

يضيف هذا المديول سندات قبض وصرف وتحويل جاهزة للعمل بالعربية، مع الفروع
المالية، وربط الموافقات، وسجل المتابعة، وحدود ترحيل محاسبي محمية. يبقى
الترحيل المحاسبي خطوة مستقبلية صريحة إلى أن يتم اعتماد مصفوفة قيود السندات.
    """,
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'DM',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'dm_finance_core',
        'account_payment',
        'mail',
    ],
    'data': [
        'data/sequence_data.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/dm_finance_voucher_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
