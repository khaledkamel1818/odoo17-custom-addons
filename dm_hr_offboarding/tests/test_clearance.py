# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDmHrOffboardingClearance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Clearance Test Employee',
            'join_date': fields.Date.today() - relativedelta(years=3),
        })
        cls.contract = cls.env['hr.contract'].create({
            'name': 'Clearance Test Contract',
            'employee_id': cls.employee.id,
            'wage': 5000,
            'date_start': fields.Date.today() - relativedelta(years=3),
            'state': 'open',
        })
        cls.type_resignation = cls.env.ref('dm_hr_offboarding.offboarding_type_resignation')

    def test_clearance_lines_generated(self):
        offboarding = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'Test clearance generation',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=30),
        })
        offboarding.action_submit()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_generate_clearance()
        self.assertTrue(offboarding.clearance_line_ids)
        self.assertGreaterEqual(len(offboarding.clearance_line_ids), 5)

    def test_clearance_department_approval(self):
        offboarding = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'Test department clearance',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=30),
        })
        offboarding.action_submit()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_generate_clearance()
        pending = offboarding.clearance_line_ids.filtered(lambda l: l.state == 'pending')
        self.assertTrue(pending)
        pending.action_approve()
        self.assertEqual(offboarding.clearance_pending_count, 0)

    def test_custody_outstanding_blocks_completion(self):
        custody = self.env['dm.hr.custody'].create({
            'employee_id': self.employee.id,
            'custody_type': 'device',
            'delivery_date': fields.Date.today() - relativedelta(months=6),
            'state': 'delivered',
        })
        offboarding = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'Test custody block',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=30),
        })
        offboarding.action_submit()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_generate_clearance()
        custody_line = offboarding.clearance_line_ids.filtered(lambda l: l.custody_id)
        if custody_line:
            custody_line.write({'received': True})
            custody_line.action_approve()
        non_custody_lines = offboarding.clearance_line_ids.filtered(lambda l: not l.custody_id)
        non_custody_lines.action_approve()
        offboarding.action_approve()
        self.assertEqual(offboarding.state, 'finance_settlement')

    def test_custody_returned_scenario(self):
        custody = self.env['dm.hr.custody'].create({
            'employee_id': self.employee.id,
            'custody_type': 'device',
            'delivery_date': fields.Date.today() - relativedelta(months=6),
            'state': 'delivered',
        })
        offboarding = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'Test custody returned',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=30),
        })
        offboarding.action_submit()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_generate_clearance()
        custody_line = offboarding.clearance_line_ids.filtered(lambda l: l.custody_id)
        if custody_line:
            custody_line.write({
                'received': True,
                'custody_condition': 'good',
            })
            custody_line.action_approve()
            self.assertEqual(custody.state, 'returned')

    def test_complete_clearance_workflow(self):
        custody = self.env['dm.hr.custody'].create({
            'employee_id': self.employee.id,
            'custody_type': 'device',
            'delivery_date': fields.Date.today() - relativedelta(months=6),
            'state': 'delivered',
        })
        offboarding = self.env['dm.hr.offboarding'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'termination_type_id': self.type_resignation.id,
            'reason': 'Test complete clearance',
            'request_date': fields.Date.today(),
            'requested_last_work_date': fields.Date.today() + relativedelta(days=30),
        })
        offboarding.action_submit()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_approve()
        offboarding.action_generate_clearance()
        offboarding.clearance_line_ids.write({'state': 'approved'})
        offboarding.action_approve()
        self.assertEqual(offboarding.state, 'finance_settlement')
        self.assertTrue(offboarding.settlement_id)
