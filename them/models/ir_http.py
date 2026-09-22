# -*- coding: utf-8 -*-

from odoo import models


THEM_BACKGROUND_PRESETS = {
    'midnight': 'linear-gradient(135deg, #0f172a 0%, #10202a 45%, #164e63 100%)',
    'ocean': 'linear-gradient(135deg, #06283d 0%, #1363df 55%, #47b5ff 100%)',
    'violet': 'linear-gradient(135deg, #1e1b4b 0%, #5b21b6 55%, #a855f7 100%)',
    'emerald': 'linear-gradient(135deg, #052e2b 0%, #0f766e 55%, #34d399 100%)',
    'graphite': 'linear-gradient(135deg, #111827 0%, #374151 55%, #6b7280 100%)',
}


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def _them_get_apps_menu_background(self):
        params = self.env['ir.config_parameter'].sudo()
        preset = params.get_param('them.apps_menu_background_preset', 'midnight')

        if preset == 'image':
            image = (params.get_param('them.apps_menu_background_image') or '').strip()
            if image:
                return (
                    "linear-gradient(135deg, rgba(15, 23, 42, 0.60), rgba(16, 32, 42, 0.70)), "
                    "url('/them/apps_menu_background_image') center center / cover no-repeat fixed"
                )

        if preset == 'custom':
            custom_background = (params.get_param('them.apps_menu_background_custom') or '').strip()
            if custom_background:
                return custom_background

        return THEM_BACKGROUND_PRESETS.get(preset, THEM_BACKGROUND_PRESETS['midnight'])

    def session_info(self):
        session_info = super().session_info()
        if self.env.user._is_internal():
            session_info['them_apps_menu_background'] = self._them_get_apps_menu_background()
        return session_info
