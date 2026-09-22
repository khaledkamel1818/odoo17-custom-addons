# -*- coding: utf-8 -*-
from odoo import fields, models


class DmHrEmployeeDependent(models.Model):
    _name = 'dm.hr.employee.dependent'
    _description = 'مرافق الموظف'
    _order = 'employee_id, name'

    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='الاسم', required=True)
    relationship = fields.Selection(
        [
            ('spouse', 'زوج/زوجة'),
            ('child', 'ابن/ابنة'),
            ('father', 'الأب'),
            ('mother', 'الأم'),
            ('other', 'أخرى'),
        ],
        string='صلة القرابة',
        default='child',
        required=True,
    )
    birthdate = fields.Date(string='تاريخ الميلاد')
    included_in_gos = fields.Boolean(
        string='مشمول في التأمينات الاجتماعية',
        help='هل هذا المرافق مشمول ضمن مساهمات التأمينات الاجتماعية العائلية.',
    )
    active = fields.Boolean(string='نشط', default=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        related='employee_id.company_id', readonly=True, store=True)
