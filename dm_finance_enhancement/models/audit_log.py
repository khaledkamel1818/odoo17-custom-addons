# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DmFinanceAuditLog(models.Model):
    _name = 'dm.finance.audit.log'
    _description = 'Finance Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'
    _check_company_auto = True

    name = fields.Char(string='Reference', required=True, tracking=True)
    event_type = fields.Selection(
        selection=[
            ('tax_report', 'Tax Report'),
            ('annual_closing', 'Annual Closing'),
            ('bank_reconciliation', 'Bank Reconciliation'),
            ('asset_depreciation', 'Asset Depreciation'),
            ('journal_posting', 'Journal Posting'),
            ('report_export', 'Report Export'),
            ('configuration', 'Configuration'),
        ],
        string='Event Type',
        required=True,
        index=True,
        tracking=True,
    )
    event_date = fields.Datetime(string='Event Date', default=fields.Datetime.now, required=True, index=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    model_name = fields.Char(string='Model')
    record_res_id = fields.Integer(string='Record ID')
    description = fields.Text(string='Description')
    payload = fields.Text(string='Payload')

    @api.model
    def log_event(self, event_type, name, record=None, description=None, payload=None, company=None):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'dm_finance_enhancement.enable_audit_trail', 'True'
        )
        if str(enabled).lower() not in ('true', '1', 'yes'):
            return self.browse()
        vals = {
            'event_type': event_type,
            'name': name,
            'description': description,
            'payload': payload,
            'company_id': (company or self.env.company).id,
        }
        if record:
            vals.update({
                'model_name': record._name,
                'record_res_id': record.id,
            })
        return self.sudo().create(vals)

