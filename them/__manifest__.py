# -*- coding: utf-8 -*-
{
    'name': 'them',
    'version': '17.0.1.0.4',
    'category': 'Themes/Backend',
    'summary': 'Enterprise-style backend app icon menu for Odoo Community',
    'description': """
Backend theme that turns the Community apps dropdown into an Enterprise-style
icon grid while keeping the standard Odoo menu behavior.
""",
    'license': 'LGPL-3',
    'author': 'DM',
    'depends': ['web', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'them/static/src/js/navbar_app_icon.js',
            'them/static/src/xml/apps_menu.xml',
            'them/static/src/scss/apps_menu.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
