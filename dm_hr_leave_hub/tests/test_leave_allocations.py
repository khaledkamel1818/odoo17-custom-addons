# -*- coding: utf-8 -*-
from datetime import date

from odoo import fields
from odoo.tests import TransactionCase


class DmHrLeaveAllocationTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Annual Saudi Leave',
            'requires_allocation': 'yes',
            'allocation_validation_type': 'hr',
            'dm_is_saudi_annual_leave': True,
        })
        cls.employee_new = cls.env['hr.employee'].create({
            'name': 'New Joiner',
            'join_date': date(fields.Date.context_today(cls.env['hr.employee']).year - 1, 1, 1),
        })
        cls.employee_senior = cls.env['hr.employee'].create({
            'name': 'Senior Employee',
            'join_date': date(fields.Date.context_today(cls.env['hr.employee']).year - 6, 1, 1),
        })

    def test_manual_balance_wizard_creates_validated_allocation(self):
        wizard = self.env['dm.hr.leave.balance.wizard'].create({
            'employee_ids': [(6, 0, [self.employee_new.id])],
            'holiday_status_id': self.leave_type.id,
            'number_of_days': 5,
        })
        action = wizard.action_create_allocations()
        allocations = self.env['hr.leave.allocation'].search(action['domain'])
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations.number_of_days, 5)
        self.assertEqual(allocations.state, 'validate')
        self.assertEqual(allocations.dm_allocation_origin, 'manual_hr')

    def test_saudi_annual_allocation_generates_21_and_30_days(self):
        year = fields.Date.context_today(self.env['dm.hr.leave.hub']).year
        action = self.env['dm.hr.leave.hub'].generate_saudi_annual_allocations(
            year=year,
            holiday_status_id=self.leave_type.id,
            employee_ids=[self.employee_new.id, self.employee_senior.id],
        )
        allocations = self.env['hr.leave.allocation'].search(action['domain']).sorted('number_of_days')
        self.assertEqual(allocations.mapped('number_of_days'), [21.0, 30.0])
        self.assertEqual(set(allocations.mapped('state')), {'validate'})
        self.assertEqual(set(allocations.mapped('dm_auto_annual_year')), {year})
