# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class DmHrShiftWorkflowTest(TransactionCase):
    def test_shift_creates_calendar_and_assigns_employee(self):
        shift = self.env['dm.hr.shift'].create({
            'name': 'Morning Shift', 'time_from': 8.0, 'time_to': 16.0,
            'company_id': self.env.company.id,
        })
        self.assertTrue(shift.calendar_id)
        self.assertEqual(len(shift.calendar_id.attendance_ids), 5)
        employee = self.env['hr.employee'].create({
            'name': 'Shift Employee', 'dm_shift_id': shift.id,
        })
        self.assertEqual(employee.resource_calendar_id, shift.calendar_id)
        shift.write({'time_to': 17.0})
        self.assertEqual(set(shift.calendar_id.attendance_ids.mapped('hour_to')), {17.0})

    def test_invalid_shift_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['dm.hr.shift'].create({
                'name': 'Invalid Shift', 'time_from': 18.0, 'time_to': 8.0,
            })
