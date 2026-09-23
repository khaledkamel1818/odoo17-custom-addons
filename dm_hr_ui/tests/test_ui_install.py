# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDmHrUiInstall(TransactionCase):
    def test_core_menus_exist(self):
        for xmlid in [
            'dm_hr_core.menu_dm_hr_employee_portal',
            'dm_hr_core.menu_dm_hr_operations',
            'dm_hr_core.menu_dm_hr_admin',
            'dm_hr_workspace.menu_dm_hr_workspace',
            'dm_hr_core.menu_dm_hr_personnel_affairs',
            'dm_hr_core.menu_dm_hr_attendance_root',
            'dm_hr_core.menu_dm_hr_leaves_root',
            'dm_hr_core.menu_dm_hr_employee_services',
            'dm_hr_offboarding.menu_dm_hr_offboarding_root',
        ]:
            self.assertTrue(self.env.ref(xmlid))

    def test_dashboard_ui_extensions(self):
        dashboard = self.env['dm.hr.workspace.dashboard'].sudo()
        data = dashboard.get_dashboard_data()
        metric_keys = {metric['key'] for metric in data.get('metrics', [])}
        self.assertIn('offboarding_open', metric_keys)
        section_keys = {section['key'] for section in data.get('service_sections', [])}
        self.assertIn('offboarding', section_keys)

    def test_dashboard_actions_exist(self):
        dashboard = self.env['dm.hr.workspace.dashboard'].sudo()
        for key in ['offboarding', 'final_settlements', 'financial_requests', 'installments']:
            action = dashboard.open_action(key)
            self.assertEqual(action.get('type'), 'ir.actions.act_window')

    def test_menu_information_architecture(self):
        """The UI module keeps one clear HR navigation tree and removes old duplicates."""
        expected_sequences = {
            'dm_hr_workspace.menu_dm_hr_workspace': 1,
            'dm_hr_core.menu_dm_hr_personnel_affairs': 5,
            'dm_hr_core.menu_dm_hr_attendance_root': 20,
            'dm_hr_core.menu_dm_hr_leaves_root': 22,
            'dm_hr_core.menu_dm_hr_custody_root': 24,
            'dm_hr_offboarding.menu_dm_hr_offboarding_root': 26,
            'dm_hr_core.menu_dm_hr_employee_finance_root': 28,
            'dm_hr_core.menu_dm_hr_recruitment_needs': 30,
        }
        for xmlid, sequence in expected_sequences.items():
            menu = self.env.ref(xmlid)
            self.assertTrue(menu.active, '%s should be visible' % xmlid)
            self.assertEqual(menu.sequence, sequence, '%s sequence changed' % xmlid)

        removed_menus = [
            'dm_hr_core.menu_dm_hr_operations',
            'dm_hr_core.menu_dm_hr_app_service_requests',
            'dm_hr_core.menu_dm_hr_employees',
            'dm_hr_core.menu_dm_hr_contracts',
            'dm_hr_core.menu_dm_hr_app_leave_requests',
            'dm_hr_core.menu_dm_hr_app_attendance',
            'dm_hr_core.menu_dm_hr_app_special_allowance',
            'dm_hr_core.menu_dm_hr_app_insurance_policy',
            'dm_hr_core.menu_dm_hr_app_document',
            'dm_hr_core.menu_dm_hr_app_dependent',
            'dm_hr_core.menu_dm_hr_app_contract_history',
            'dm_hr_core.menu_dm_hr_leave_request_service',
            'dm_hr_core.menu_dm_hr_allowance_type',
            'dm_hr_core.menu_dm_hr_insurance_provider',
            'dm_hr_core.menu_dm_hr_social_insurance_scheme',
            'dm_hr_core.menu_dm_hr_special_allowance',
            'dm_hr_core.menu_dm_hr_dependent',
            'dm_hr_core.menu_dm_hr_document',
            'dm_hr_core.menu_dm_hr_insurance_policy',
        ]
        for xmlid in removed_menus:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            self.assertFalse(menu, '%s should be removed as duplicate navigation' % xmlid)

    def test_canonical_configuration_menus_are_visible(self):
        for xmlid in [
            'dm_hr_core.menu_dm_hr_app_allowance_type',
            'dm_hr_core.menu_dm_hr_app_insurance_provider',
            'dm_hr_core.menu_dm_hr_app_social_insurance_scheme',
        ]:
            menu = self.env.ref(xmlid)
            self.assertTrue(menu.active, '%s should be visible as canonical configuration menu' % xmlid)

    def test_key_ui_inherited_views_are_valid(self):
        for xmlid in [
            'dm_hr_ui.hr_employee_form_inherit_ui',
            'dm_hr_ui.dm_hr_service_request_form_inherit_ui',
            'dm_hr_ui.dm_hr_attendance_correction_form_inherit_ui',
            'dm_hr_ui.dm_hr_leave_balance_request_form_inherit_ui',
            'dm_hr_ui.dm_hr_leave_purchase_form_inherit_ui',
            'dm_hr_ui.dm_hr_offboarding_form_inherit_ui',
            'dm_hr_ui.dm_hr_custody_form_inherit_ui',
            'dm_hr_ui.dm_hr_employee_financial_request_form_inherit_ui',
        ]:
            view = self.env.ref(xmlid)
            self.assertEqual(view.type, 'form')
            self.assertTrue(view.arch_db)
