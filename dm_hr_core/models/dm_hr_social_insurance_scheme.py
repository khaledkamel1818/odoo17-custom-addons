# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrSocialInsuranceScheme(models.Model):
    _name = 'dm.hr.social.insurance.scheme'
    _description = 'نظام التأمينات الاجتماعية'
    _order = 'sequence, code'

    name = fields.Char(string='الاسم', required=True)
    code = fields.Char(string='الرمز', required=True)
    sequence = fields.Integer(string='التسلسل', default=10)
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda self: self.env.company,
        help='اتركه فارغاً لتعريف قالب عام متاح لكل الشركات.',
    )
    rate_ids = fields.One2many(
        'dm.hr.social.insurance.rate', 'scheme_id', string='النسب')
    active = fields.Boolean(string='نشط', default=True)
    note = fields.Text(string='ملاحظات')

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_("رمز النظام مطلوب."))

    def init(self):
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS dm_hr_social_insurance_scheme_code_global_uniq
            ON dm_hr_social_insurance_scheme (code) WHERE company_id IS NULL
        """)
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS dm_hr_social_insurance_scheme_code_company_uniq
            ON dm_hr_social_insurance_scheme (code, company_id)
            WHERE company_id IS NOT NULL
        """)
