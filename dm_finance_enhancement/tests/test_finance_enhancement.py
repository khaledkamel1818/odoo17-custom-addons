# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestDmFinanceEnhancement(TransactionCase):

    def test_dashboard_payload_shape(self):
        payload = self.env['dm.finance.enhancement.dashboard'].get_dashboard_data({})
        self.assertIn('cards', payload)
        self.assertIn('bank_cards', payload)
        self.assertIn('recent_moves', payload)

    def test_report_wizard_creation(self):
        wizard = self.env['dm.finance.report.wizard'].create({
            'report_type': 'trial_balance',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'company_id': self.env.company.id,
        })
        self.assertEqual(wizard.report_type, 'trial_balance')

