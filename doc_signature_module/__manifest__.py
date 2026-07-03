{
    'name': 'Custom Document Signature',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'Place signature on document and generate PDF',
    'description': '''
        Module to create documents with movable signature positioning.
        - Upload signature image
        - Set position in millimeters (Left/Top)
        - Generate PDF with signature at exact coordinates
        - Track changes via Chatter
    ''',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'reports/report.xml',
        'reports/template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}