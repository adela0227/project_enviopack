from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class quotes_report(models.Model):
    _name ="shipment.quotes_report"
    
    name= fields.Char(string="Empresa de Correo")
    mail_package = fields.Char(default="Enviópack", string="Nombre de la api")
    id_mail = fields.Char(string="ID")
    name_quotes= fields.Char(string="Orden de venta")
    shipping_cost = fields.Float(string='Precio del envio')
    delivery_time = fields.Integer(string='Horas para la entrega')
    date_estimated = fields.Date(string="Fecha de entrega estimada")
    date_preparation = fields.Date(string="Fecha de preparación")
    sale_order_id = fields.Many2one('sale.order')
    select_quote = fields.Boolean(string="Seleccionar cotización")
    access_token = fields.Char()
    api_key = fields.Char()
    secret_api = fields.Char()
    