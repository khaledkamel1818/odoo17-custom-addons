# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class DmHrWorkspaceDashboardTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard = cls.env['dm.hr.workspace.dashboard']
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Workspace Employee',
            'user_id': cls.env.user.id,
        })

    def test_dashboard_payload_contains_core_sections(self):
        data = self.dashboard.get_dashboard_data()
        self.assertIn('employee', data)
        self.assertIn('attendance', data)
        self.assertIn('metrics', data)
        self.assertIn('quick_actions', data)
        self.assertIn('recent_requests', data)
        self.assertIn('pending_approvals', data)
        self.assertIn('recent_leaves', data)
        self.assertIn('leave_balances', data)
        self.assertIn('attendance_timeline', data)
        self.assertIn('compliance', data)
        self.assertIn('request_pipeline', data)
        self.assertIn('hr_command', data)
        self.assertTrue(data['employee']['id'])
        self.assertGreaterEqual(len(data['metrics']), 4)
        self.assertGreaterEqual(len(data['compliance']), 4)

    def test_open_quick_request_action(self):
        action = self.dashboard.open_action('new_permission')
        self.assertEqual(action['res_model'], 'dm.hr.service.request')
        self.assertEqual(action['context']['default_request_type'], 'permission')
        self.assertEqual(action['views'], [(False, 'form')])

    def test_all_dashboard_actions_are_web_safe(self):
        for key in [
            'my_requests', 'my_leaves', 'attendance', 'my_attendance',
            'approvals', 'documents', 'employees', 'new_leave',
            'new_permission', 'new_letter', 'new_salary_transfer', 'new_other', 'my_profile',
        ]:
            action = self.dashboard.open_action(key)
            if action and action.get('type') == 'ir.actions.act_window':
                self.assertTrue(action.get('views'), key)

    def test_gps_attendance_is_recorded(self):
        self.env.company.write({
            'hr_workspace_attendance_enabled': True,
            'hr_workspace_gps_required': True,
            'hr_workspace_gps_max_accuracy': 100.0,
            'hr_workspace_geofence_required': False,
        })
        data = self.dashboard.toggle_attendance({
            'latitude': 24.7136, 'longitude': 46.6753, 'gps_accuracy': 12.0,
        })
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id),
        ], order='id desc', limit=1)
        self.assertAlmostEqual(attendance.in_latitude, 24.7136)
        self.assertAlmostEqual(attendance.in_longitude, 46.6753)
        self.assertEqual(attendance.in_gps_accuracy, 12.0)
        self.assertEqual(attendance.dm_attendance_source, 'gps_only')
        self.assertEqual(attendance.dm_gps_compliance, 'gps_only')
        self.assertEqual(data['attendance']['state'], 'checked_in')

    def test_gps_is_required_when_enabled(self):
        self.env.company.hr_workspace_gps_required = True
        self.env.company.hr_workspace_geofence_required = False
        with self.assertRaises(Exception):
            self.dashboard.toggle_attendance({})

    def test_geofence_accepts_inside_and_rejects_outside(self):
        self.env.company.write({
            'hr_workspace_attendance_enabled': True,
            'hr_workspace_gps_required': True,
            'hr_workspace_geofence_required': True,
            'hr_workspace_gps_max_accuracy': 100.0,
        })
        location = self.env['dm.hr.attendance.location'].create({
            'name': 'Riyadh Office', 'company_id': self.env.company.id,
            'latitude': 24.7136, 'longitude': 46.6753, 'radius_meters': 100,
        })
        self.dashboard.toggle_attendance({
            'latitude': 24.71361, 'longitude': 46.67531, 'gps_accuracy': 10.0,
        })
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id),
        ], order='id desc', limit=1)
        self.assertEqual(attendance.in_dm_location_id, location)
        self.assertEqual(attendance.dm_attendance_source, 'gps_geofence')
        self.assertEqual(attendance.dm_gps_compliance, 'verified')
        self.dashboard.toggle_attendance({
            'latitude': 24.71361, 'longitude': 46.67531, 'gps_accuracy': 10.0,
        })
        with self.assertRaises(Exception):
            self.dashboard.toggle_attendance({
                'latitude': 21.4858, 'longitude': 39.1925, 'gps_accuracy': 10.0,
            })
