# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DmHrAttendanceLocation(models.Model):
    _name = 'dm.hr.attendance.location'
    _description = 'موقع بصمة الحضور GPS'
    _order = 'company_id, sequence, name'
    _check_company_auto = True

    name = fields.Char(string='اسم الموقع', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', required=True,
                                 default=lambda self: self.env.company, index=True)
    latitude = fields.Float(string='خط العرض', digits=(10, 7), required=True)
    longitude = fields.Float(string='خط الطول', digits=(10, 7), required=True)
    radius_meters = fields.Float(string='نطاق السماح (متر)', default=150.0, required=True)
    address = fields.Char(string='العنوان')
    employee_ids = fields.Many2many(
        'hr.employee', 'dm_hr_attendance_location_employee_rel',
        'location_id', 'employee_id', string='الموظفون المخصصون',
        help='إذا تُركت فارغة يصبح الموقع متاحًا لجميع موظفي الشركة.',
    )
    map_url = fields.Char(compute='_compute_map_url', string='رابط الخريطة')

    @api.depends('latitude', 'longitude')
    def _compute_map_url(self):
        for location in self:
            location.map_url = (
                'https://www.google.com/maps?q=%s,%s' % (location.latitude, location.longitude)
                if location.latitude or location.longitude else False
            )

    @api.constrains('latitude', 'longitude', 'radius_meters')
    def _check_coordinates(self):
        from odoo.exceptions import ValidationError
        for location in self:
            if not -90 <= location.latitude <= 90 or not -180 <= location.longitude <= 180:
                raise ValidationError('إحداثيات موقع الحضور غير صحيحة.')
            if location.radius_meters <= 0:
                raise ValidationError('نطاق السماح يجب أن يكون أكبر من صفر متر.')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dm_attendance_location_ids = fields.Many2many(
        'dm.hr.attendance.location', 'dm_hr_attendance_location_employee_rel',
        'employee_id', 'location_id', string='مواقع الحضور المسموحة',
        domain="[('company_id', '=', company_id)]",
        help='إذا تُركت فارغة يستطيع الموظف التسجيل من أي موقع حضور نشط للشركة.',
    )


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    dm_attendance_source = fields.Selection(
        [
            ('gps_geofence', 'GPS داخل موقع معتمد'),
            ('gps_only', 'GPS بدون نطاق'),
            ('manual', 'يدوي / بدون GPS'),
        ],
        string='مصدر البصمة',
        readonly=True,
        copy=False,
    )
    dm_gps_compliance = fields.Selection(
        [
            ('verified', 'مطابق'),
            ('gps_only', 'موثق GPS فقط'),
            ('missing', 'غير موثق GPS'),
        ],
        string='مطابقة GPS',
        readonly=True,
        copy=False,
    )
    in_dm_location_id = fields.Many2one(
        'dm.hr.attendance.location', string='موقع الحضور المعتمد', readonly=True,
    )
    out_dm_location_id = fields.Many2one(
        'dm.hr.attendance.location', string='موقع الانصراف المعتمد', readonly=True,
    )
