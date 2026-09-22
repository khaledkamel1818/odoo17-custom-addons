# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dm_finance_localization_mode = fields.Selection(
        selection=[
            ('generic', 'Generic'),
            ('saudi', 'Saudi Arabia'),
            ('egypt', 'Egypt'),
            ('multi', 'Saudi Arabia and Egypt'),
        ],
        string='Finance Localization Mode',
        default='generic',
        config_parameter='dm_finance_enhancement.localization_mode',
    )
    dm_finance_sa_vat_rate = fields.Float(
        string='Saudi VAT Rate (%)',
        default=15.0,
        config_parameter='dm_finance_enhancement.sa_vat_rate',
        help='Configurable default only. Tax calculations should rely on Odoo tax records whenever possible.',
    )
    dm_finance_eg_vat_rate = fields.Float(
        string='Egypt VAT Rate (%)',
        default=14.0,
        config_parameter='dm_finance_enhancement.eg_vat_rate',
        help='Configurable default only. Keep it aligned with current tax configuration.',
    )
    dm_finance_withholding_rate = fields.Float(
        string='Withholding Tax Rate (%)',
        default=0.0,
        config_parameter='dm_finance_enhancement.withholding_rate',
    )
    dm_finance_zakat_rate = fields.Float(
        string='Zakat Rate (%)',
        default=2.5,
        config_parameter='dm_finance_enhancement.zakat_rate',
        help='Configurable planning/reporting rate. Do not treat it as legal advice.',
    )
    dm_finance_default_retained_earnings_account_id = fields.Many2one(
        'account.account',
        string='Default Retained Earnings Account',
        config_parameter='dm_finance_enhancement.default_retained_earnings_account_id',
        domain="[('company_id', '=', company_id), ('account_type', 'in', ('equity', 'equity_unaffected'))]",
    )
    dm_finance_default_closing_journal_id = fields.Many2one(
        'account.journal',
        string='Default Closing Journal',
        config_parameter='dm_finance_enhancement.default_closing_journal_id',
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
    )
    dm_finance_enable_audit_trail = fields.Boolean(
        string='Enable Finance Audit Trail',
        default=True,
        config_parameter='dm_finance_enhancement.enable_audit_trail',
    )
    dm_finance_enable_advanced_dashboard = fields.Boolean(
        string='Enable Advanced Finance Dashboard',
        default=True,
        config_parameter='dm_finance_enhancement.enable_advanced_dashboard',
    )

