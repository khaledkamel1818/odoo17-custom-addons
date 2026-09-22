# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrCustody(models.Model):
    _inherit = 'dm.hr.custody'

    asset_id = fields.Many2one(
        'account.asset.asset',
        string='الأصل المحاسبي',
        index=True,
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help='يربط العهدة غير المالية بسجل الأصل الثابت في المالية دون تكرار بيانات الأصل.',
    )
    asset_category_id = fields.Many2one(
        'account.asset.category',
        string='تصنيف الأصل',
        related='asset_id.category_id',
        store=True,
        readonly=True,
    )
    asset_state = fields.Selection(
        related='asset_id.state',
        string='حالة الأصل',
        store=True,
        readonly=True,
    )
    asset_value = fields.Monetary(
        string='قيمة الأصل',
        related='asset_id.value',
        currency_field='asset_currency_id',
        store=True,
        readonly=True,
    )
    asset_residual_value = fields.Monetary(
        string='القيمة الدفترية المتبقية',
        related='asset_id.value_residual',
        currency_field='asset_currency_id',
        readonly=True,
    )
    asset_currency_id = fields.Many2one(
        'res.currency',
        string='عملة الأصل',
        related='asset_id.currency_id',
        readonly=True,
    )

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        for rec in self:
            if rec.asset_id:
                if not rec.code:
                    rec.code = rec.asset_id.code or rec.asset_id.name
                if not rec.company_id and rec.employee_id:
                    rec.company_id = rec.employee_id.company_id

    @api.constrains('asset_id', 'company_id')
    def _check_asset_company(self):
        for rec in self:
            if rec.asset_id and rec.company_id and rec.asset_id.company_id != rec.company_id:
                raise ValidationError(_(
                    'لا يمكن ربط العهدة بهذا الأصل لأن الشركة مختلفة.\n\n'
                    'شركة العهدة: %(custody_company)s\n'
                    'شركة الأصل: %(asset_company)s\n\n'
                    'اختر أصلًا تابعًا لنفس الشركة أو عدّل شركة العهدة قبل الحفظ.'
                ) % {
                    'custody_company': rec.company_id.display_name,
                    'asset_company': rec.asset_id.company_id.display_name,
                })

    def action_open_asset(self):
        self.ensure_one()
        if not self.asset_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('الأصل المحاسبي'),
            'res_model': 'account.asset.asset',
            'view_mode': 'form',
            'res_id': self.asset_id.id,
        }


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    custody_ids = fields.One2many('dm.hr.custody', 'asset_id', string='عهد الموظفين')
    custody_count = fields.Integer(string='عدد العهد', compute='_compute_custody_info')
    current_custody_employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف المستلم حاليًا',
        compute='_compute_custody_info',
        store=False,
    )

    def _compute_custody_info(self):
        for asset in self:
            asset.custody_count = len(asset.custody_ids)
            delivered = asset.custody_ids.filtered(lambda c: c.state == 'delivered')[:1]
            asset.current_custody_employee_id = delivered.employee_id

    def action_view_hr_custodies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('عهد الموظفين'),
            'res_model': 'dm.hr.custody',
            'view_mode': 'tree,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }


class DmHrOffboardingClearanceLine(models.Model):
    _inherit = 'dm.hr.offboarding.clearance.line'

    asset_id = fields.Many2one(
        'account.asset.asset',
        string='الأصل المرتبط',
        related='custody_id.asset_id',
        readonly=True,
    )
    asset_residual_value = fields.Monetary(
        string='القيمة الدفترية',
        related='custody_id.asset_residual_value',
        currency_field='currency_id',
        readonly=True,
    )

    @api.onchange('custody_id')
    def _onchange_custody_id_asset(self):
        for rec in self:
            if rec.custody_id and rec.custody_id.asset_id:
                rec.custody_value = rec.custody_id.asset_residual_value or rec.custody_id.asset_value
