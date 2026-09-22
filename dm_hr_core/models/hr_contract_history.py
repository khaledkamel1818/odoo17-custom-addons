# -*- coding: utf-8 -*-
from odoo import fields, models


class DmHrContractHistory(models.Model):
    """Audit log of contract / salary changes for an employee.

    Each entry records a snapshot of the contract state at a point in time.
    It is written by the HR Officer/Manager when the contract or wage changes.
    """

    _name = 'dm.hr.contract.history'
    _description = 'سجل العقد والراتب'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True, ondelete='cascade', index=True)
    contract_id = fields.Many2one(
        'hr.contract', string='العقد', ondelete='cascade', index=True)
    date = fields.Date(string='تاريخ السريان', required=True, default=fields.Date.context_today)
    previous_wage = fields.Monetary(string='الراتب السابق', currency_field='currency_id')
    new_wage = fields.Monetary(string='الراتب الجديد', currency_field='currency_id')
    change_type = fields.Selection(
        [
            ('creation', 'إنشاء'),
            ('wage_change', 'تغيير الراتب'),
            ('renewal', 'تجديد'),
            ('termination', 'إنهاء'),
            ('other', 'أخرى'),
        ],
        string='نوع التغيير',
        default='other',
        required=True,
    )
    note = fields.Text(string='ملاحظات')
    currency_id = fields.Many2one(
        'res.currency', string='العملة',
        related='contract_id.currency_id', readonly=True, store=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        related='contract_id.company_id', readonly=True, store=True)
