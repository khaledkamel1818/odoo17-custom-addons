# -*- coding: utf-8 -*-
{
    'name': 'منصة الموارد البشرية',
    'version': '17.0.5.0.0',
    'category': 'Human Resources',
    'summary': 'واجهة عمل احترافية للموظف والمدير والموارد البشرية بأسلوب منصات HR الحديثة',
    'description': """
منصة موارد بشرية عربية حديثة فوق dm_hr_core:

* لوحة رئيسية حسب الدور: موظف، مدير، موارد بشرية.
* بطاقات ذكية للإجازات، الحضور، الطلبات، التنبيهات والامتثال.
* إجراءات سريعة: طلب إجازة، استئذان، خطاب تعريف، حضور وانصراف.
* متابعة موافقات المدير والموارد البشرية.
* تصميم حديث متجاوب داخل Odoo Backend.
""",
    'license': 'LGPL-3',
    'author': 'DM',
    'depends': [
        'dm_hr_core',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/hr_attendance_location_views.xml',
        'views/res_config_settings_views.xml',
        'views/dm_hr_workspace_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dm_hr_workspace/static/src/js/hr_workspace.js',
            'dm_hr_workspace/static/src/xml/hr_workspace.xml',
            'dm_hr_workspace/static/src/scss/hr_workspace.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
