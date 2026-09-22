# -*- coding: utf-8 -*-
from odoo import fields, models


class DmHrDocument(models.Model):
    _name = 'dm.hr.document'
    _description = 'مستند الموظف'
    _order = 'employee_id, document_type'

    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True, ondelete='cascade', index=True)
    document_type = fields.Selection(
        [
            ('contract', 'العقد'),
            ('national_id', 'الهوية الوطنية'),
            ('iqama', 'الإقامة / الهوية الوطنية'),
            ('passport', 'جواز السفر'),
            ('driving_license', 'رخصة القيادة'),
            ('license', 'رخصة مهنية'),
            ('medical_policy', 'وثيقة التأمين الطبي'),
            ('education', 'الشهادة التعليمية'),
            ('qualification', 'مؤهل'),
            ('insurance', 'تأمين'),
            ('probation_extension', 'مستند تمديد فترة التجربة'),
            ('other', 'أخرى'),
        ],
        string='نوع المستند',
        default='other',
        required=True,
    )
    name = fields.Char(string='الاسم', required=True)
    reference_no = fields.Char(string='رقم المرجع')
    issue_date = fields.Date(string='تاريخ الإصدار')
    expiry_date = fields.Date(string='تاريخ الانتهاء')
    document_file = fields.Binary(string='الملف', attachment=True)
    is_confidential = fields.Boolean(string='سري')
    alert_before_days = fields.Integer(string='تنبيه قبل الانتهاء/يوم', default=30)
    renewal_responsible_id = fields.Many2one('res.users', string='مسؤول المتابعة')
    notes = fields.Text(string='ملاحظات')
    active = fields.Boolean(string='نشط', default=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        related='employee_id.company_id', readonly=True, store=True)
