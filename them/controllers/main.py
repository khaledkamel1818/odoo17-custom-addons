# -*- coding: utf-8 -*-

import base64

from odoo import http
from odoo.http import request


class ThemAppsMenuBackgroundController(http.Controller):

    @http.route('/them/apps_menu_background_image', type='http', auth='user')
    def apps_menu_background_image(self, **kwargs):
        params = request.env['ir.config_parameter'].sudo()
        image = (params.get_param('them.apps_menu_background_image') or '').strip()
        filename = (params.get_param('them.apps_menu_background_image_filename') or '').strip()

        if not image:
            return request.not_found()

        try:
            content = base64.b64decode(image)
        except Exception:
            return request.not_found()

        return request.make_response(
            content,
            headers=[
                ('Content-Type', self._guess_mimetype(image, filename)),
                ('Cache-Control', 'no-store'),
            ],
        )

    def _guess_mimetype(self, image, filename=''):
        filename = filename.lower()
        if filename.endswith('.svg') or image.startswith('PHN2Zy'):
            return 'image/svg+xml'
        if filename.endswith(('.jpg', '.jpeg')) or image.startswith('/9j/'):
            return 'image/jpeg'
        if filename.endswith('.gif') or image.startswith('R0lGOD'):
            return 'image/gif'
        if filename.endswith('.webp') or image.startswith('UklGR'):
            return 'image/webp'
        return 'image/png'
