# -*- coding: utf-8 -*-
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrInsurancePolicy(models.Model):
    _name = 'dm.hr.insurance.policy'
    _description = 'وثيقة تأمين الموظف'
    _order = 'employee_id, start_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True, ondelete='cascade', index=True)
    provider_id = fields.Many2one(
        'dm.hr.insurance.provider', string='مزود التأمين', required=True)
    policy_no = fields.Char(string='رقم الوثيقة')
    policy_type = fields.Selection(
        [
            ('medical', 'طبي'),
            ('life', 'حياة'),
            ('other', 'أخرى'),
        ],
        string='نوع الوثيقة',
        default='medical',
        required=True,
    )
    start_date = fields.Date(string='تاريخ البداية')
    end_date = fields.Date(string='تاريخ النهاية')
    premium = fields.Monetary(string='القسط الشهري', currency_field='currency_id')
    employee_share_percent = fields.Float(string='حصة الموظف (%)')
    employer_share_percent = fields.Float(string='حصة صاحب العمل (%)')
    active = fields.Boolean(string='نشط', default=True)
    note = fields.Text(string='ملاحظات')
    currency_id = fields.Many2one(
        'res.currency', string='العملة',
        related='employee_id.company_id.currency_id', readonly=True, store=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        related='employee_id.company_id', readonly=True, store=True)
    state = fields.Selection(
        [
            ('scheduled', 'مجدول'),
            ('active', 'نشط'),
            ('expired', 'منتهي'),
        ],
        string='الحالة',
        compute='_compute_state',
        store=True,
    )

    @api.depends('start_date', 'end_date')
    def _compute_state(self):
        today = date.today()
        for record in self:
            if record.start_date and record.start_date > today:
                record.state = 'scheduled'
            elif record.end_date and record.end_date < today:
                record.state = 'expired'
            else:
                record.state = 'active'

    @api.constrains('employee_share_percent', 'employer_share_percent')
    def _check_shares(self):
        for record in self:
            for share in (record.employee_share_percent, record.employer_share_percent):
                if share and not 0 <= share <= 100:
                    raise ValidationError(_(
                        "يجب أن تكون نسب التأمين بين 0 و100."))

    @api.constrains('provider_id', 'start_date', 'end_date')
    def _check_dates_and_overlap(self):
        for record in self:
            if (
                record.start_date
                and record.end_date
                and record.start_date > record.end_date
            ):
                raise ValidationError(_(
                    "يجب ألا يكون تاريخ بداية الوثيقة بعد تاريخ نهايتها."))
            if not record.provider_id:
                continue
            domain = [
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                ('provider_id', '=', record.provider_id.id),
            ]
            for other in self.search(domain):
                if self._periods_overlap(
                    (record.start_date, record.end_date),
                    (other.start_date, other.end_date),
                ):
                    raise ValidationError(_(
                        "لا يمكن تداخل وثيقتين من المزود نفسه للموظف نفسه."))

    @staticmethod
    def _periods_overlap(period_a, period_b):
        start_a, end_a = period_a
        start_b, end_b = period_b
        start_a = start_a or date.min
        end_a = end_a or date.max
        start_b = start_b or date.min
        end_b = end_b or date.max
        return not (end_a < start_b or end_b < start_a)
