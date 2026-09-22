# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase


class DmFinanceDashboardTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard = cls.env['dm.finance.dashboard']

    def test_dashboard_payload_contains_professional_sections(self):
        data = self.dashboard.get_dashboard_data()
        self.assertIn('metrics', data)
        self.assertIn('quick_actions', data)
        self.assertIn('cashflow', data)
        self.assertIn('receivable_health', data)
        self.assertIn('payable_health', data)
        self.assertIn('voucher_pipeline', data)
        self.assertIn('recent_invoices', data)
        self.assertIn('recent_vouchers', data)
        self.assertIn('alerts', data)
        self.assertGreaterEqual(len(data['metrics']), 6)
        self.assertGreaterEqual(len(data['quick_actions']), 4)

    def test_dashboard_actions_are_web_safe(self):
        for key in [
            'customer_invoices', 'vendor_bills', 'journal_entries', 'journals',
            'vouchers', 'vouchers_pending', 'overdue', 'overdue_receivables',
            'overdue_payables', 'new_customer_invoice', 'new_vendor_bill',
            'new_payment_voucher', 'new_receipt_voucher',
        ]:
            action = self.dashboard.open_action(key)
            if action and action.get('type') == 'ir.actions.act_window':
                self.assertTrue(action.get('views'), key)
