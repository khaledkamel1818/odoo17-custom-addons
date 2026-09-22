# -*- coding: utf-8 -*-
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrSocialInsuranceRate(models.Model):
    _name = 'dm.hr.social.insurance.rate'
    _description = 'نسبة التأمينات الاجتماعية'
    _order = 'scheme_id, employee_category, effective_from desc'

    scheme_id = fields.Many2one(
        'dm.hr.social.insurance.scheme',
        string='النظام',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_category = fields.Selection(
        [
            ('saudi', 'سعودي'),
            ('non_saudi', 'غير سعودي'),
            ('other', 'أخرى'),
        ],
        string='فئة الموظف',
        default='saudi',
        required=True,
    )
    gosi_employee_ratio = fields.Float(
        string='نسبة الموظف في التأمينات (%)',
        help='نسبة مساهمة الموظف في التأمينات الاجتماعية.',
    )
    gosi_employer_ratio = fields.Float(
        string='نسبة صاحب العمل في التأمينات (%)',
        help='نسبة مساهمة صاحب العمل في التأمينات الاجتماعية.',
    )
    gosi_sanad_ratio = fields.Float(
        string='نسبة ساند / النسبة الإضافية (%)',
        help='نسبة مساهمة إضافية قابلة للإعداد مثل ساند، دون قيم ثابتة داخل الكود.',
    )
    min_insurable_wage = fields.Monetary(
        string='الحد الأدنى للأجر الخاضع للتأمين', currency_field='currency_id')
    max_insurable_wage = fields.Monetary(
        string='الحد الأعلى للأجر الخاضع للتأمين', currency_field='currency_id')
    subject_allowance_type_ids = fields.Many2many(
        'dm.hr.allowance.type',
        string='أنواع البدلات الخاضعة للتأمين',
        help='أنواع البدلات التي تدخل ضمن الأجر الخاضع للتأمين لهذه النسبة.',
    )
    effective_from = fields.Date(string='ساري من', required=True)
    effective_to = fields.Date(string='ساري إلى')
    active = fields.Boolean(string='نشط', default=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        related='scheme_id.company_id', readonly=True, store=True)
    currency_id = fields.Many2one(
        'res.currency', string='العملة',
        related='scheme_id.company_id.currency_id', readonly=True, store=True)
    is_active = fields.Boolean(
        string='ساري حالياً',
        compute='_compute_is_active',
        store=True,
    )

    @api.depends('effective_from', 'effective_to')
    def _compute_is_active(self):
        today = date.today()
        for record in self:
            record.is_active = (
                (not record.effective_from or record.effective_from <= today)
                and (not record.effective_to or record.effective_to >= today)
            )

    @api.constrains('gosi_employee_ratio', 'gosi_employer_ratio', 'gosi_sanad_ratio')
    def _check_ratios(self):
        for record in self:
            for ratio in (
                record.gosi_employee_ratio,
                record.gosi_employer_ratio,
                record.gosi_sanad_ratio,
            ):
                if ratio and not 0 <= ratio <= 100:
                    raise ValidationError(_(
                        "يجب أن تكون نسب التأمينات الاجتماعية بين 0 و100."))

    @api.constrains(
        'scheme_id', 'employee_category', 'effective_from', 'effective_to')
    def _check_dates_and_no_overlap(self):
        for record in self:
            if (
                record.effective_from
                and record.effective_to
                and record.effective_from > record.effective_to
            ):
                raise ValidationError(_(
                    "يجب ألا يكون تاريخ بداية السريان بعد تاريخ نهايته."))
            if not record.scheme_id:
                continue
            domain = [
                ('id', '!=', record.id),
                ('scheme_id', '=', record.scheme_id.id),
                ('employee_category', '=', record.employee_category),
            ]
            for other in self.search(domain):
                if self._periods_overlap(
                    (record.effective_from, record.effective_to),
                    (other.effective_from, other.effective_to),
                ):
                    raise ValidationError(_(
                        "لا يمكن تداخل نسب التأمينات للنظام والفئة والشركة نفسها "
                        "في فترات سريان متداخلة."))

    @staticmethod
    def _periods_overlap(period_a, period_b):
        start_a, end_a = period_a
        start_b, end_b = period_b
        start_a = start_a or date.min
        end_a = end_a or date.max
        start_b = start_b or date.min
        end_b = end_b or date.max
        return not (end_a < start_b or end_b < start_a)
