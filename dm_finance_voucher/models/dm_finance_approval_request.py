# -*- coding: utf-8 -*-

from odoo import models


class DmFinanceApprovalRequest(models.Model):
    _inherit = 'dm.finance.approval.request'

    def action_approve(self, comment=False):
        result = super().action_approve(comment=comment)
        for request in self:
            if request.res_model == 'dm.finance.voucher' and request.state == 'approved':
                self.env['dm.finance.voucher'].browse(request.res_id).sudo()._approval_approved()
        return result

    def action_reject(self, reason):
        result = super().action_reject(reason)
        for request in self:
            if request.res_model == 'dm.finance.voucher' and request.state == 'rejected':
                self.env['dm.finance.voucher'].browse(request.res_id).sudo()._approval_rejected()
        return result
