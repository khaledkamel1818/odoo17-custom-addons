from odoo import models, fields, api

class SignatureDocument(models.Model):
    _name = 'signature.document'
    _description = 'Document with Movable Signature'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # يفعّل Chatter والتتبع

    name = fields.Char(string='Document Name', required=True, tracking=True)
    content = fields.Html(string='Document Content', default='<p>Paste or write your content here...</p>')
    signature = fields.Binary(string='Signature Image', attachment=True, tracking=True)
    signature_left = fields.Float(string='Left Position (mm)', default=50.0)
    signature_top = fields.Float(string='Top Position (mm)', default=200.0)
    
    state = fields.Selection(
        [('draft', 'Draft'), ('signed', 'Signed'), ('done', 'Done')],
        string='Status',
        default='draft',
        tracking=True
    )

    def action_mark_signed(self):
        self.write({'state': 'signed'})

    def action_mark_done(self):
        self.write({'state': 'done'})
        # في نهاية كلاس SignatureDocument، أضف هذه الدالة:
@api.onchange('signature_left', 'signature_top')
def _onchange_signature_position(self):
    """تقريب الإحداثيات لعدد عشري واحد لتجنب القيم الطويلة"""
    if self.signature_left:
        self.signature_left = round(self.signature_left, 1)
    if self.signature_top:
        self.signature_top = round(self.signature_top, 1)