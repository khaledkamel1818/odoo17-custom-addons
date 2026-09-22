# -*- coding: utf-8 -*-
from odoo import fields, models


class DmHrInsuranceProvider(models.Model):
    _name = 'dm.hr.insurance.provider'
    _description = 'مزود التأمين'
    _order = 'name'

    name = fields.Char(string='الاسم', required=True)
    provider_type = fields.Selection(
        [
            ('medical', 'طبي'),
            ('social', 'التأمينات الاجتماعية'),
            ('other', 'أخرى'),
        ],
        string='نوع المزود',
        default='medical',
        required=True,
    )
    partner_id = fields.Many2one('res.partner', string='جهة الاتصال المرتبطة')
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        required=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(string='نشط', default=True)
    note = fields.Text(string='ملاحظات')

    _sql_constraints = [
        (
            'name_company_uniq',
            'UNIQUE(name, company_id)',
            'يجب أن يكون اسم مزود التأمين فريداً لكل شركة.',
        ),
    ]
