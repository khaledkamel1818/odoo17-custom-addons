# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrShift(models.Model):
    _name = 'dm.hr.shift'
    _description = 'وردية عمل الموظفين'
    _order = 'company_id, name'
    _check_company_auto = True

    name = fields.Char(string='اسم الوردية', required=True, translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    time_from = fields.Float(string='من الساعة', required=True, default=8.0)
    time_to = fields.Float(string='إلى الساعة', required=True, default=17.0)
    monday = fields.Boolean(string='الاثنين', default=True)
    tuesday = fields.Boolean(string='الثلاثاء', default=True)
    wednesday = fields.Boolean(string='الأربعاء', default=True)
    thursday = fields.Boolean(string='الخميس', default=True)
    friday = fields.Boolean(string='الجمعة')
    saturday = fields.Boolean(string='السبت')
    sunday = fields.Boolean(string='الأحد', default=True)
    calendar_id = fields.Many2one('resource.calendar', string='جدول العمل', readonly=True,
                                  copy=False, ondelete='restrict')
    employee_ids = fields.One2many('hr.employee', 'dm_shift_id', string='الموظفون')
    employee_count = fields.Integer(compute='_compute_employee_count')

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for shift in self:
            shift.employee_count = len(shift.employee_ids)

    @api.constrains('time_from', 'time_to')
    def _check_times(self):
        for shift in self:
            if not 0 <= shift.time_from < 24 or not 0 < shift.time_to <= 24:
                raise ValidationError(_('وقت الوردية يجب أن يكون بين 00:00 و24:00.'))
            if shift.time_to <= shift.time_from:
                raise ValidationError(_('وقت نهاية الوردية يجب أن يكون بعد وقت البداية.'))

    @api.constrains('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    def _check_days(self):
        for shift in self:
            if not any(shift[field] for field in self._day_fields()):
                raise ValidationError(_('يجب اختيار يوم عمل واحد على الأقل.'))

    @api.model
    def _day_fields(self):
        return ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

    def _attendance_values(self):
        self.ensure_one()
        values = []
        for dayofweek, field_name in enumerate(self._day_fields()):
            if self[field_name]:
                values.append((0, 0, {
                    'name': self.name, 'dayofweek': str(dayofweek),
                    'hour_from': self.time_from, 'hour_to': self.time_to,
                    'day_period': 'morning',
                }))
        return values

    def _sync_calendar(self):
        Calendar = self.env['resource.calendar'].sudo()
        for shift in self:
            values = {
                'name': _('وردية: %s') % shift.name,
                'company_id': shift.company_id.id,
                'tz': shift.company_id.resource_calendar_id.tz or 'Asia/Riyadh',
                'attendance_ids': [(5, 0, 0)] + shift._attendance_values(),
            }
            if shift.calendar_id:
                shift.calendar_id.sudo().write(values)
            else:
                shift.calendar_id = Calendar.create(values)
            shift.employee_ids.sudo().write({'resource_calendar_id': shift.calendar_id.id})

    @api.model_create_multi
    def create(self, vals_list):
        shifts = super().create(vals_list)
        shifts._sync_calendar()
        return shifts

    def write(self, vals):
        result = super().write(vals)
        sync_fields = {'name', 'company_id', 'time_from', 'time_to', *self._day_fields()}
        if sync_fields & set(vals):
            self._sync_calendar()
        return result

    def action_open_employees(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('hr.open_view_employee_list_my')
        action['domain'] = [('dm_shift_id', '=', self.id)]
        action['context'] = {'default_dm_shift_id': self.id,
                             'default_resource_calendar_id': self.calendar_id.id}
        return action


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dm_shift_id = fields.Many2one('dm.hr.shift', string='الوردية', check_company=True, tracking=True)

    @api.onchange('dm_shift_id')
    def _onchange_dm_shift_id(self):
        if self.dm_shift_id:
            self.resource_calendar_id = self.dm_shift_id.calendar_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('dm_shift_id') and not vals.get('resource_calendar_id'):
                vals['resource_calendar_id'] = self.env['dm.hr.shift'].browse(vals['dm_shift_id']).calendar_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('dm_shift_id') and 'resource_calendar_id' not in vals:
            vals['resource_calendar_id'] = self.env['dm.hr.shift'].browse(vals['dm_shift_id']).calendar_id.id
        return super().write(vals)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    in_gps_accuracy = fields.Float(string='دقة GPS عند الحضور (متر)', readonly=True)
    out_gps_accuracy = fields.Float(string='دقة GPS عند الانصراف (متر)', readonly=True)
