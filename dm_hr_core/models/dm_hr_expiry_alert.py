# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import fields, models


class DmHrExpiryAlert(models.Model):
    """Weekly cron that raises expiry reminders for employee documents.

    Alerts are created as mail activities on the employee (HR team). The
    reminder window is configurable per company via the company setting
    ``dm_expiry_alert_days`` (default 30 days).
    """

    _name = 'dm.hr.expiry.alert'
    _description = 'Expiry Alert Runner'

    def _cron_run(self):
        """Create mail activities for expiring documents / contracts."""
        alert_days = self.env['ir.config_parameter'].sudo().get_param(
            'dm_hr_core.expiry_alert_days', default='30')
        try:
            alert_days = int(alert_days)
        except ValueError:
            alert_days = 30
        horizon = date.today() + timedelta(days=alert_days)

        activity_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return

        # Expiring iqama / national IDs
        employees = self.env['hr.employee'].sudo().search([
            ('iqama_expiry_date', '<=', horizon),
            ('iqama_expiry_date', '>=', date.today()),
        ])
        for employee in employees:
            self._create_alert(employee, activity_type, 'Iqama / National ID',
                               employee.iqama_expiry_date)

        # Expiring contracts
        contracts = self.env['hr.contract'].sudo().search([
            ('date_end', '!=', False),
            ('date_end', '<=', horizon),
            ('date_end', '>=', date.today()),
        ])
        for contract in contracts:
            self._create_alert(contract.employee_id, activity_type, 'Contract',
                                                               contract.date_end)

    @staticmethod
    def _create_alert(employee, activity_type, label, expiry_date):
        """Schedule an expiry reminder activity, but never create duplicates."""
        if not employee or not expiry_date:
            return
        summary = '%s expires soon' % label
        already_scheduled = employee.activity_ids.filtered(
            lambda a: a.summary == summary
            and a.activity_type_id == activity_type
        )
        if already_scheduled:
            return
        employee.activity_schedule(
            activity_type_id=activity_type.id,
            date_deadline=expiry_date,
            summary=summary,
            note='The %s of %s expires on %s.' % (
                label, employee.name, expiry_date),
        )