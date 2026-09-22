# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    them_apps_background_preset = fields.Selection(
        selection=[
            ('midnight', 'ليلي داكن'),
            ('ocean', 'أزرق بحري'),
            ('violet', 'بنفسجي'),
            ('emerald', 'أخضر هادئ'),
            ('graphite', 'رمادي احترافي'),
            ('image', 'صورة'),
            ('custom', 'مخصص'),
        ],
        string='خلفية قائمة التطبيقات',
        default='midnight',
        config_parameter='them.apps_menu_background_preset',
    )
    them_apps_background_custom = fields.Char(
        string='قيمة CSS مخصصة للخلفية',
        config_parameter='them.apps_menu_background_custom',
        help=(
            "اكتب لوناً مثل #10202a أو تدرجاً مثل "
            "linear-gradient(135deg, #0f172a 0%, #164e63 100%)."
        ),
    )
    them_apps_background_image = fields.Binary(
        string='صورة خلفية قائمة التطبيقات',
        help='ارفع صورة لاستخدامها كخلفية لشاشة أيقونات التطبيقات.',
    )
    them_apps_background_image_filename = fields.Char(
        string='اسم ملف صورة الخلفية',
        config_parameter='them.apps_menu_background_image_filename',
    )

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            them_apps_background_image=params.get_param('them.apps_menu_background_image') or False,
            them_apps_background_image_filename=params.get_param('them.apps_menu_background_image_filename') or False,
        )
        return res

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        image = self.them_apps_background_image or ''
        if isinstance(image, bytes):
            image = image.decode('ascii')
        params.set_param('them.apps_menu_background_image', image)
        params.set_param('them.apps_menu_background_image_filename', self.them_apps_background_image_filename or '')
