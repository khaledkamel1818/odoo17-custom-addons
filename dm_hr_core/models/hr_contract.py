# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    contract_class = fields.Selection(
        [
            ('permanent', 'دائم'),
            ('fixed', 'محدد المدة'),
            ('part_time', 'دوام جزئي'),
            ('training', 'تدريب'),
        ],
        string='فئة العقد',
        default='permanent',
        tracking=True,
    )
    gosi_insured = fields.Boolean(string='مشترك في التأمينات', tracking=True)
    medical_insurance_policy_id = fields.Many2one(
        'dm.hr.insurance.policy',
        string='وثيقة التأمين الطبي',
        ondelete='restrict',
    )
    allowance_ids = fields.One2many(
        'dm.hr.contract.allowance', 'contract_id', string='البدلات')
    probation_end = fields.Date(string='تاريخ انتهاء التجربة')
    notice_period_days = fields.Integer(string='مدة الإشعار (أيام)')

    # ---- DM HR additions -----------------------------------------------
    dm_payment_method = fields.Selection(
        [
            ('bank_transfer', 'تحويل بنكي'),
            ('cash', 'نقداً'),
            ('cheque', 'شيك'),
        ],
        string='طريقة الدفع',
        default='bank_transfer',
        tracking=True,
    )
    dm_salary_payment_day = fields.Integer(
        string='يوم صرف الراتب',
        default=27,
        tracking=True,
        help='اليوم الشهري المستهدف لصرف الراتب ومطابقته داخلياً مع حماية الأجور.',
    )
    dm_wps_required = fields.Boolean(
        string='خاضع لحماية الأجور',
        default=True,
        tracking=True,
    )
    dm_work_days_per_week = fields.Float(
        string='أيام العمل أسبوعياً',
        default=5.0,
        tracking=True,
    )
    dm_auto_renew = fields.Boolean(
        string='تجديد تلقائي',
        default=False,
        help='عند التفعيل، يتم تجديد العقد تلقائياً عند انتهائه.',
    )
    dm_contract_state = fields.Selection(
        [
            ('draft', 'مسودة'),
            ('running', 'ساري'),
            ('expired', 'منتهي'),
            ('cancelled', 'ملغى'),
            ('closed', 'مغلق'),
        ],
        string='حالة العقد',
        default='running',
        tracking=True,
    )
    dm_termination_reason = fields.Char(
        string='سبب الإنهاء',
        tracking=True,
    )

    @api.constrains('probation_end', 'date_start')
    def _check_probation_end_date(self):
        for contract in self:
            if (
                contract.probation_end
                and contract.date_start
                and contract.probation_end < contract.date_start
            ):
                raise ValidationError(_(
                    "يجب ألا يكون تاريخ انتهاء فترة التجربة قبل تاريخ بداية العقد."))

    @api.constrains('dm_salary_payment_day', 'dm_payment_method', 'dm_wps_required')
    def _check_saudi_payroll_controls(self):
        for contract in self:
            if contract.dm_salary_payment_day and not 1 <= contract.dm_salary_payment_day <= 31:
                raise ValidationError(_('يوم صرف الراتب يجب أن يكون بين 1 و31.'))
            if contract.dm_wps_required and contract.dm_payment_method != 'bank_transfer':
                raise ValidationError(_('العقود الخاضعة لحماية الأجور يجب أن تكون بطريقة دفع تحويل بنكي.'))
