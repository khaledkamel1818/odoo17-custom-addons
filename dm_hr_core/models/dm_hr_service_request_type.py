# -*- coding: utf-8 -*-
from odoo import fields, models

REQUEST_TYPES = [
    ('permission', 'استئذان'),
    ('remote_work', 'عمل عن بعد'),
    ('salary_certificate', 'خطاب تعريف بالراتب'),
    ('salary_transfer_certificate', 'خطاب تثبيت/تحويل راتب للبنك'),
    ('experience_certificate', 'شهادة خبرة'),
    ('document_update', 'تحديث بيانات أو مستندات'),
    ('overtime', 'طلب ساعات إضافية'),
    ('business_trip', 'انتداب / مهمة عمل'),
    ('equipment', 'أدوات أو عهدة'),
    ('other', 'طلب آخر'),
]


class DmHrServiceRequestType(models.Model):
    _name = 'dm.hr.service.request.type'
    _description = 'إعداد نوع طلب خدمة الموظفين'
    _order = 'sequence, name'
    _check_company_auto = True

    name = fields.Char(string='اسم النوع', required=True, translate=True)
    code = fields.Selection(REQUEST_TYPES, string='كود النوع', required=True, index=True)
    sequence = fields.Integer(string='الترتيب', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
    monthly_limit_hours = fields.Float(string='حد الاستئذان الشهري بالساعات')
    yearly_limit_hours = fields.Float(string='حد الاستئذان السنوي بالساعات')
    require_attachment = fields.Boolean(string='المرفق إلزامي')
    report_action_xmlid = fields.Char(
        string='قالب PDF',
        help='مثال: dm_hr_core.action_report_dm_hr_salary_certificate',
    )
    requires_dates = fields.Boolean(
        string='يتطلب تاريخ بداية ونهاية',
        default=False,
        help='إذا كان مفعلاً، يطلب النظام تاريخ بداية ونهاية لهذا النوع من الطلبات.',
    )
    requires_permission_validation = fields.Boolean(
        string='يتطلب تحقق الاستئذان (التداخل والحدود)',
        default=False,
        help='يفعّل فحص التداخل والحدود الشهرية/السنوية لهذا النوع.',
    )
    requires_bank_details = fields.Boolean(
        string='يتطلب بيانات بنكية',
        default=False,
        help='إذا كان مفعلاً، يطلب النظام اسم البنك ورقم IBAN.',
    )
    requires_trip_details = fields.Boolean(
        string='يتطلب بيانات الانتداب',
        default=False,
        help='إذا كان مفعلاً، يطلب النظام نوع الانتداب والوجهة ووصف المهمة.',
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'لا يمكن تكرار نوع الطلب داخل نفس الشركة.'),
    ]
