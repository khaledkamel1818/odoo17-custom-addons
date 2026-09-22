# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDmHrOffboarding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Offboarding Employee',
            'join_date': fields.Date.today() - relativedelta(years=6),
        })
        cls.contract = cls.env['hr.contract'].create({
            'name': 'Offboarding Contract',
            'employee_id': cls.employee.id,
            'wage': 6000,
            'date_start': fields.Date.today() - relativedelta(years=6),
            'state': 'open',
        })
        cls.type_resignation = cls.env.ref('dm_hr_offboarding.offboarding_type_resignation')

    def test_offboarding_workflow_and_settlement(self):
        request = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'اختبار سير العمل',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=35),
        })
        request.action_submit()
        self.assertEqual(request.state, 'manager_approval')
        request.action_approve()
        request.action_approve()
        request.action_approve()
        request.action_generate_clearance()
        request.clearance_line_ids.write({'state': 'approved'})
        request.action_approve()
        self.assertEqual(request.state, 'finance_settlement')
        self.assertTrue(request.settlement_id)
        request.settlement_id.action_approve()
        request.action_approve()
        request.action_approve()
        self.assertEqual(request.state, 'done')
        self.assertTrue(request.completion_executed)
        self.assertEqual(self.employee.dm_employment_status, 'terminated')
