# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class DmFinanceVoucherTest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Voucher = cls.env['dm.finance.voucher']
        cls.Flow = cls.env['dm.finance.approval.flow']
        cls.model = cls.env['ir.model']._get('dm.finance.voucher')
        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', 'in', ('bank', 'cash')),
        ], limit=1)
        cls.account = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('deprecated', '=', False),
        ], limit=1)
        if not cls.journal or not cls.account:
            raise UserError('The test database needs at least one bank/cash journal and one active account.')

    def _create_flow(self, allow_self_approval=True):
        return self.Flow.create({
            'name': 'Voucher Approval Flow',
            'company_id': self.company.id,
            'model_id': self.model.id,
            'document_type': 'voucher',
            'allow_self_approval': allow_self_approval,
            'line_ids': [(0, 0, {
                'name': 'Finance Manager',
                'sequence': 10,
                'approver_type': 'user',
                'user_id': self.env.user.id,
            })],
        })

    def _create_voucher(self):
        return self.Voucher.create({
            'voucher_type': 'payment',
            'company_id': self.company.id,
            'currency_id': self.company.currency_id.id,
            'journal_id': self.journal.id,
            'line_ids': [(0, 0, {
                'name': 'Test line',
                'account_id': self.account.id,
                'amount': 100.0,
            })],
        })

    def test_01_voucher_amount_computed(self):
        voucher = self._create_voucher()
        self.assertEqual(voucher.amount_total, 100.0)
        self.assertNotEqual(voucher.name, '/')

    def test_02_negative_line_amount_blocked(self):
        with self.assertRaises(ValidationError):
            self.Voucher.create({
                'voucher_type': 'payment',
                'company_id': self.company.id,
                'currency_id': self.company.currency_id.id,
                'journal_id': self.journal.id,
                'line_ids': [(0, 0, {
                    'name': 'Bad line',
                    'account_id': self.account.id,
                    'amount': -1.0,
                })],
            })

    def test_03_submit_requires_approval_flow(self):
        voucher = self._create_voucher()
        with self.assertRaises(UserError):
            voucher.action_submit()

    def test_04_submit_and_approve_voucher(self):
        self._create_flow()
        voucher = self._create_voucher()
        voucher.action_submit()
        self.assertEqual(voucher.state, 'under_approval')
        self.assertTrue(voucher.approval_request_id)
        voucher.approval_request_id.action_approve()
        self.assertEqual(voucher.state, 'approved')

    def test_05_posting_boundary_is_protected(self):
        voucher = self._create_voucher()
        with self.assertRaises(UserError):
            voucher.action_post()
