# -*- coding: utf-8 -*-
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrEmployeeAllowance(models.Model):
    _name = 'dm.hr.employee.allowance'
    _description = 'بدل خاص للموظف'
    _order = 'employee_id, sequence'

    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True, ondelete='cascade', index=True)
    allowance_type_id = fields.Many2one(
        'dm.hr.allowance.type', string='نوع البدل', required=True)
    amount = fields.Monetary(string='المبلغ', currency_field='currency_id')
    percent = fields.Float(string='النسبة (%)')
    percent_of_allowance_type_id = fields.Many2one(
        'dm.hr.allowance.type', string='نسبة من نوع بدل')
    start_date = fields.Date(string='تاريخ البداية')
    end_date = fields.Date(string='تاريخ النهاية')
    active = fields.Boolean(string='نشط', default=True)
    note = fields.Text(string='ملاحظات')
    sequence = fields.Integer(string='التسلسل', default=10)
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

    # NOTE: exceptional allowances require an approval before being effective in
    # payroll. The link to dm.approval.request is introduced by the dm_hr_approval
    # module (later phase). Until then records are created by HR only.

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

    @api.constrains('allowance_type_id', 'start_date', 'end_date')
    def _check_dates_and_overlap(self):
        for record in self:
            if (
                record.start_date
                and record.end_date
                and record.start_date > record.end_date
            ):
                raise ValidationError(_(
                    "يجب ألا يكون تاريخ بداية البدل بعد تاريخ نهايته."))
            if not record.allowance_type_id:
                continue
            domain = [
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                ('allowance_type_id', '=', record.allowance_type_id.id),
            ]
            for other in self.search(domain):
                if self._periods_overlap(
                    (record.start_date, record.end_date),
                    (other.start_date, other.end_date),
                ):
                    raise ValidationError(_(
                        "لا يمكن تداخل بدلَين من نفس النوع للموظف نفسه."))

    @api.constrains(
        'allowance_type_id', 'amount', 'percent', 'percent_of_allowance_type_id')
    def _check_values(self):
        for record in self:
            amount_type = (
                record.allowance_type_id.amount_type
                if record.allowance_type_id else False
            )
            if amount_type == 'fixed' and (record.amount is None or record.amount <= 0):
                raise ValidationError(_(
                    "البدل الثابت يتطلب مبلغاً أكبر من صفر."))
            if amount_type in ('percentage_of_basic', 'percentage_of_component'):
                if not 0 < record.percent <= 100:
                    raise ValidationError(_(
                        "البدلات النسبية تتطلب نسبة أكبر من 0 وأقل أو تساوي 100."))
            if (
                amount_type == 'percentage_of_component'
                and not record.percent_of_allowance_type_id
            ):
                raise ValidationError(_(
                    "البدل المحتسب كنسبة من مكون يتطلب نوع بدل آخر كأساس."))
            if (
                amount_type == 'percentage_of_component'
                and record.percent_of_allowance_type_id == record.allowance_type_id
            ):
                raise ValidationError(_(
                    "لا يمكن أن يكون البدل نسبة من نفس نوعه."))

    @staticmethod
    def _periods_overlap(period_a, period_b):
        start_a, end_a = period_a
        start_b, end_b = period_b
        start_a = start_a or date.min
        end_a = end_a or date.max
        start_b = start_b or date.min
        end_b = end_b or date.max
        return not (end_a < start_b or end_b < start_a)
