# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    dm_asset_profile = fields.Selection(
        selection=[
            ('vehicle', 'Vehicle'),
            ('equipment', 'Equipment'),
            ('building', 'Building'),
            ('it', 'IT Asset'),
            ('furniture', 'Furniture'),
            ('other', 'Other'),
        ],
        string='Asset Profile',
        default='other',
        tracking=True,
    )
    dm_branch_id = fields.Many2one('dm.finance.branch', string='Branch', tracking=True)
    dm_location = fields.Char(string='Asset Location', tracking=True)
    dm_maintenance_notes = fields.Text(string='Maintenance Notes')
    dm_revaluation_value = fields.Monetary(string='Last Revaluation Value', currency_field='currency_id')
    dm_last_revaluation_date = fields.Date(string='Last Revaluation Date')

