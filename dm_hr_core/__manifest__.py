# -*- coding: utf-8 -*-
{
    'name': 'الموارد البشرية الأساسية',
    'version': '17.0.4.0.0',
    'category': 'Human Resources',
    'summary': 'بيانات الموارد البشرية الأساسية: الموظفون، العقود، البدلات، التأمين، المرافقون، المستندات وإعدادات الشركة',
    'description': """
حزمة الموارد البشرية الأساسية لنظام DM على Odoo 17 Community.

* ملف موظف شامل مناسب للسوق السعودي: الهوية، الإقامة، التأمينات، المرافقون، المستندات.
* خدمات الموظف الذاتية: طلبات الإجازة، الاستئذانات، الخطابات، العهد، الانتداب والطلبات الأخرى.
* دورة اعتماد عملية للطلبات: مسودة، اعتماد المدير، اعتماد الموارد البشرية، اعتماد نهائي أو رفض.
* حضور وانصراف وتقارير تشغيلية مرتبطة بملف الموظف.
* بدلات مرنة على العقد والموظف بدون تثبيت نسب أو مبالغ داخل الكود.
* إعدادات ونسب التأمينات الاجتماعية وساند قابلة للتهيئة حسب الشركة والفترة.
* تأمين طبي ومزودون ووثائق تأمين للموظفين.
* صلاحيات وقواعد وصول متعددة الشركات مع عرض عربي كامل للقوائم والواجهات.
* اختبارات آلية للتحقق من القيود، دورة الطلبات، العدادات وسلوك تعدد الشركات.
""",
    'license': 'LGPL-3',
    'author': 'DM',
    'depends': [
        'base_setup',
        'hr',
        'hr_contract',
        'hr_holidays',
        'hr_attendance',
        'project',
        'mail',
        'dm_hr_leave_hub',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/default_data.xml',
        'data/sequence_data.xml',
        'data/leave_type_data.xml',
        'data/service_request_type_data.xml',
        'data/cron_data.xml',
        'data/saudi_hr_reference_data.xml',
        'views/dm_hr_service_request_views.xml',
        'views/dm_hr_service_request_type_views.xml',
        'views/dm_hr_approval_policy_views.xml',
        'views/dm_hr_phase2_views.xml',
        'views/dm_hr_phase3_views.xml',
        'views/dm_hr_shift_views.xml',
        'views/dm_hr_leave_finance_views.xml',
        'views/dm_hr_attendance_views.xml',
        'views/dm_hr_allowance_views.xml',
        'views/dm_hr_insurance_views.xml',
        'views/dm_hr_dependent_document_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_contract_history_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'views/hr_org_structure_views.xml',
        'reports/dm_hr_service_request_reports.xml',
        'reports/dm_hr_wage_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dm_hr_core/static/src/js/org_chart.js',
            'dm_hr_core/static/src/xml/org_chart.xml',
            'dm_hr_core/static/src/js/service_center.js',
            'dm_hr_core/static/src/xml/service_center.xml',
            'dm_hr_core/static/src/scss/dm_hr_core_backend.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
