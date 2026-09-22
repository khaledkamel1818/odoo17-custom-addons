# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class DmHrLeaveHubTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Leave Hub Employee',
            'user_id': cls.env.user.id,
            'company_id': cls.env.company.id,
        })
        cls.hub = cls.env['dm.hr.leave.hub']

    def test_dashboard_contract(self):
        data = self.hub.get_data()
        self.assertEqual(data['employee']['id'], self.employee.id)
        self.assertIn('metrics', data)
        self.assertIn('balances', data)
        self.assertIn('recent', data)
        self.assertIn('role', data)

    def test_employee_actions_are_web_safe(self):
        for key in ('new', 'mine', 'calendar', 'allocations'):
            action = self.hub.open_action(key)
            self.assertEqual(action['type'], 'ir.actions.act_window')
            self.assertTrue(action['views'])

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(UserError):
            self.hub.open_action('unknown')

    def test_workspace_leave_link_opens_new_hub(self):
        action = self.env['dm.hr.workspace.dashboard'].open_action('my_leaves')
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'dm_hr_leave_hub.dashboard')
