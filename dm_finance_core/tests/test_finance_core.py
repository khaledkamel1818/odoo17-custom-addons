# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class DmFinanceCoreTest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Branch = cls.env['dm.finance.branch']
        cls.Flow = cls.env['dm.finance.approval.flow']
        cls.Request = cls.env['dm.finance.approval.request']
        cls.aml_model = cls.env['ir.model']._get('account.move')

    def test_01_branch_code_required(self):
        with self.assertRaises(ValidationError):
            self.Branch.create({
                'name': 'No Code',
                'code': ' ',
                'company_id': self.company.id,
            })

    def test_02_active_approval_flow_requires_step(self):
        with self.assertRaises(ValidationError):
            self.Flow.create({
                'name': 'No Steps',
                'company_id': self.company.id,
                'model_id': self.aml_model.id,
                'document_type': 'voucher',
            })

    def _flow_with_user_step(self):
        return self.Flow.create({
            'name': 'Voucher Flow',
            'company_id': self.company.id,
            'model_id': self.aml_model.id,
            'document_type': 'voucher',
            'line_ids': [(0, 0, {
                'name': 'Finance Manager',
                'sequence': 10,
                'approver_type': 'user',
                'user_id': self.env.user.id,
            })],
        })

    def test_03_self_approval_blocked_by_default(self):
        flow = self._flow_with_user_step()
        request = self.Request.create({
            'request_name': 'Test approval',
            'res_model': 'account.move',
            'res_id': 999999,
            'company_id': self.company.id,
            'flow_id': flow.id,
        })
        request.action_submit()
        with self.assertRaises(UserError):
            request.action_approve()

    def test_04_self_approval_allowed_when_configured(self):
        flow = self._flow_with_user_step()
        flow.allow_self_approval = True
        request = self.Request.create({
            'request_name': 'Test approval allowed',
            'res_model': 'account.move',
            'res_id': 1000000,
            'company_id': self.company.id,
            'flow_id': flow.id,
        })
        request.action_submit()
        request.action_approve()
        self.assertEqual(request.state, 'approved')
