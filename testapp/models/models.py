# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TestApp(models.Model):
    _name = 'my.app'
    _description = 'first model kh'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float()
    description = fields.Text()
    tureFalse = fields.Boolean()
    html = fields.Html()
    data = fields.Date()
    binary = fields.Binary()
    select = fields.Selection([
          ('1', 'Option 1'),
          ('2', 'Option 2')
], string='Select')

class MyOrders(models.Model):
      _name = 'my.order'
      _description = 'My Orders'

      orderDes = fields.Char()
      data_time = fields.Datetime()
      items_ids = fields.One2many('my.orders.items', 'order_id')

class MyOrdersItems(models.Model):
      _name = 'my.orders.items'
      _description = 'My Order Items'
      itemName = fields.Char()
      itemPrice = fields.Float()
      qty = fields.Integer()
      order_id = fields.Many2one('my.order', string='order')


#    @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

