# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrAllowanceType(models.Model):
    _name = 'dm.hr.allowance.type'
    _description = 'نوع البدل'
    _order = 'sequence, code'

    name = fields.Char(string='الاسم', required=True, translate=True)
    code = fields.Char(string='الرمز', required=True)
    amount_type = fields.Selection(
        [
            ('fixed', 'مبلغ ثابت'),
            ('percentage_of_basic', 'نسبة من الراتب الأساسي'),
            ('percentage_of_component', 'نسبة من مكون آخر'),
        ],
        string='طريقة الاحتساب',
        default='fixed',
        required=True,
    )
    schedule = fields.Selection(
        [
            ('monthly', 'شهري'),
            ('one_time', 'مرة واحدة'),
        ],
        string='التكرار',
        default='monthly',
        required=True,
    )
    subject_to_gosi = fields.Boolean(
        string='خاضع للتأمينات الاجتماعية',
        help='هل يدخل هذا البدل ضمن الأجر الخاضع للتأمينات الاجتماعية.',
    )
    include_in_net = fields.Boolean(
        string='يدخل في صافي الراتب',
        default=True,
    )
    show_on_payslip = fields.Boolean(string='إظهاره في مسير الراتب', default=True)
    sequence = fields.Integer(string='التسلسل', default=10)
    active = fields.Boolean(string='نشط', default=True)
    note = fields.Text(string='ملاحظات')
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda self: self.env.company,
        help='اتركه فارغاً لتعريف قالب عام متاح لكل الشركات.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        related='company_id.currency_id',
        readonly=True,
        store=True,
    )

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_("رمز نوع البدل مطلوب."))

    def init(self):
        # Partial unique indexes: global templates (no company) share one namespace,
        # company-specific codes are unique per company.
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS dm_hr_allowance_type_code_global_uniq
            ON dm_hr_allowance_type (code) WHERE company_id IS NULL
        """)
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS dm_hr_allowance_type_code_company_uniq
            ON dm_hr_allowance_type (code, company_id) WHERE company_id IS NOT NULL
        """)
