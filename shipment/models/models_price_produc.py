# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions 
import requests
import json
import logging
from  odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta 
import base64
import time
import re
_logger = logging.getLogger(__name__)
class PriceProduct(models.Model):
    _inherit  = 'sale.order'
    #CAMPOS PARA REALIZAR LAS COTIZACIONES
    province_id = fields.Char()
    postal_code = fields.Char(string="Codigo postal")
    shipping_address = fields.Char(string="Dirección de envió")
    #Campos para la creacion del pedido
    id_exter = fields.Char(string="Id del externo")
    name_order = fields.Many2one("res.partner",string="Selecciona al cliente")
    name_order_client=fields.Char(string="Nombre del cliente")
    last_name = fields.Char(string="Apellidos",)
    email_order = fields.Char(string="Correo electronico")
    phone = fields.Char(string="Telefono fijo")
    cell_phone = fields.Char(string="Telefono celular")
    amount = fields.Integer(string="Monto") 
    pay_product = fields.Boolean(string="Pagado", default=True)
    location = fields.Char(string="Localidad o Provincia")
    neighborhood = fields.Char(string="Colonia o Barrio")
    #campos para el paquete
    package_height = fields.Integer(string="Alto del paquete")
    package_width = fields.Integer(string="Ancho del paquete")
    package_length = fields.Integer(string="Largo del paquete")
    package_weight = fields.Float()
    #Campos para la creacion del envio
    observations = fields.Char(string="Observaciones")
    confirmed = fields.Boolean(string="Esta confirmado", default=True)
    service = fields.Selection([('N','Servicio estándar'),('P','Servicio prioritario'),('X','Servicio express'),('R','Servicio de devoluciones')], default='N', string="Tipo de servicio")
    modality = fields.Selection([('D','Envio a domicilio'),('S','Envio a sucursal')], default='D', string="Modo de envio")
    company_mail = fields.Char(string="Empresa de correo")
    price_mail = fields.Integer(string="Precio del envio")
    street = fields.Char(string="Calle")
    num_street = fields.Integer(string="Numero de calle",)
    floor = fields.Integer(string="Numero de piso")
    departament = fields.Char(string="Nombre del departamento")
    selec_status = fields.Selection([('B','Borrador'),('C','Por confirmar'), ('E','En proceso'), ('P','Proceso')],  default='C', string="Estado del Envio")
    #Lista de cotizaciones
    quotestre = fields.Many2one("shipment.quotes_report",string="Seleccion de Cotizacion", domain="[('sale_order_id', '=', id)]")
    list_quote= fields.One2many("shipment.quotes_report", "sale_order_id")
    #CAMPOS PARA EL ACCESS TOKEN
    api_key = fields.Char(string="Api key")
    secret_api = fields.Char(string="Secret api")
    access_token_enviopack = fields.Char(compute="_camp_access_automatic")
    #CAMPO PARA LA VALIDACION SI YA SE REGISTRO EL ENVIO Y SE GENERO LA ETIQUETA
    validation_camps = fields.Boolean(default = False)

    def generate_access_token(self):
        url = 'https://api-mx.enviopack.com/auth'
        data = {
            'api-key': self.api_key,
            'secret-key': self.secret_api
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        try:
            query = requests.post(url, data=data, headers=headers)
            data_access = query.json()
            access = data_access["token"]
            return access
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al obtener datos de la API: {e}")

    @api.onchange("name_order")
    def editable_automatic_data(self):
            # for camp_auto in self:
                self.id_exter= self.name
                self.amount = self.amount_total
                self.name_order_client= self.name_order.name
                self.postal_code = self.name_order.zip
                self.email_order = self.name_order.email
                self.phone = self.name_order.phone
                self.cell_phone = self.name_order.mobile
                self.neighborhood = self.name_order.street2
                self.street = self.name_order.street
                
    @api.onchange("list_quote")
    def _select_list_quote(self):
        selected_quote = None
        # Encuentra la cotización seleccionada
        for quote in self.list_quote:
            if quote.select_quote:
                if selected_quote:
                    quote.select_quote = False  # Si ya se ha seleccionado una cotización, desmarca la actual
                else:
                    selected_quote = quote  # Si no se ha seleccionado ninguna cotización, marca la actual como seleccionada

        # Si se encontró una cotización seleccionada, actualiza los valores
        if selected_quote:
            self.quotestre = selected_quote.id
            self.company_mail = selected_quote.id_mail
            self.price_mail = selected_quote.shipping_cost

    @api.constrains("email_order")
    def validations_camps(self):
        for val in self:
            if val.email_order and not re.match(r"[^@]+@[^@]+\.[^@]+", val.email_order):
                raise exceptions.ValidationError("El correo electrónico no es válido.")
 
    @api.onchange("postal_code")
    def obtener_provincia(self):
        if self.postal_code:
            url = 'https://api-mx.enviopack.com/provincias/obtener/por-codigo-postal'
            params = {
                'access_token': self.access_token_enviopack,
                'codigo_postal': self.postal_code,
            }
            _logger.info(f"DATOS DE LA CONSULTA DE LA PROVINCIA: {params}")
            try:
                query = requests.get(url, params=params)
                if query.status_code == 401:
                    self.access_token_enviopack = self.generate_access_token()
                    params["access_token"] = self.access_token_enviopack
                    query = requests.get(url, params=params)
                    data = query.json() 
                elif query.status_code == 200:
                    data = query.json()
                    _logger.info(f"CONSULTA DE LA PROVINCIA: {data}")
                if 'provincias' in data:
                    for provincia_key, provincia_data in data['provincias'].items():
                        if 'nombre' in provincia_data and 'id' in provincia_data:
                            self.location = provincia_data['nombre']
                            self.province_id = provincia_data['id']
                            break
                else:
                    _logger.error(f"La respuesta de la API no contiene 'nombre' o 'id'. Respuesta: {data}")
            except requests.exceptions.RequestException as e:
                _logger.error(f"Error al obtener datos de la API: {e}")

    @api.model
    def _camp_access_automatic(self):
        _logger.info('')
        Param = self.env['ir.config_parameter']
        api_key = Param.get_param('Apikey_Enviopack', default="")
        secret_api = Param.get_param('SecretApi_Enviopack', default="")
        self.api_key = api_key
        _logger.info(f'EL API KEY: {self.api_key}')
        self.secret_api = secret_api
        _logger.info(f'EL SECRET API: {self.secret_api}')

        if self.env['shipment.quotes_report'].search_count([]) > 0: 
            search = self.env['shipment.quotes_report'].browse(1)
            self.access_token_enviopack = search.access_token	
            if search.api_key != Param.get_param('Apikey_Enviopack', default="") or search.secret_api != Param.get_param('SecretApi_Enviopack', default=""):
                self.access_token_enviopack = self.generate_access_token()
                search.api_key = self.api_key
                _logger.info(f'SE ACTUALIZO EL API KEY: {self.api_key}')
                search.secret_api = self.secret_api
                _logger.info(f'SE ACTUALIZO EL SECRET API: {self.secret_api}')
                search.access_token = self.access_token_enviopack
                _logger.info(f'SE ACTUALIZO EL ACCESS TOKEN DE LA API: {self.access_token_enviopack}') 
        else:
            access_token = f"{self.generate_access_token()}"
            self.env['shipment.quotes_report'].create({'api_key': self.api_key, 'secret_api': self.secret_api,'access_token': access_token})
            self.access_token_enviopack = access_token

    #FUNCIÓN PARA GENERERAR LAS COTIZACIONES
    def create_quotes(self):
        url = 'https://api-mx.enviopack.com/cotizar/costo'
        for data in self:
            params = {
                "access_token": data.access_token_enviopack,
                "provincia": data.province_id,
                "codigo_postal":data.postal_code,
                "peso": data.package_weight,
                "paquetes": f"{data.package_height}x{data.package_width}x{data.package_length}",
                "direccion_envio": data.shipping_address
            }
            _logger.info(f"DATOS DE LA COTIZACION: {params}")
            try:
                query = requests.get(url, params=params)
                if query.status_code == 401:#Si da este error se actualiza el access token y se reinicia la consulta
                    _logger.info("El access token a expirado")
                    data.access_token_enviopack = self.generate_access_token()
                    params["access_token"] = data.access_token_enviopack
                    query = requests.get(url, params=params)
                    quote_list = query.json()
                    _logger.info(F"HUBO UN ERROR: {query}")
                elif query.status_code == 200:
                    quote_list = query.json()
                    _logger.info(f"Se registro la cotizacion: {quote_list}")
                name_quotes = self.name #Guardo el name de la orden de ventas 
                temp_quotes = {}# Diccionario para almacenar las cotizaciones temporalmente
                for quote_data in quote_list:
                    carrier_id_data = quote_data['correo']['id']
                    carrier_name_data = quote_data['correo']['nombre']
                    shipping_cost_data = quote_data['costo_envio']
                    date_estimated_data = datetime.strptime(quote_data['fecha_estimada'], "%d/%m/%Y").strftime("%Y-%m-%d")
                    date_preparation_data = datetime.strptime(quote_data['fecha_preparacion'], "%d/%m/%Y").strftime("%Y-%m-%d")
                    delivery_time_data = quote_data['horas_entrega']
                    _logger.info(f"Se registro la cotizacion: {quote_data}")
                    # Esta condicion es para que si el ID ya existe en el diccionario y el costo es mayor, se ignora
                    if carrier_id_data in temp_quotes and temp_quotes[carrier_id_data]['shipping_cost'] <= shipping_cost_data:
                        continue
                    # Se actualiza el diccionario con la nueva cotización
                    temp_quotes[carrier_id_data] = {
                        'name_quotes': name_quotes,
                        'id_mail': carrier_id_data,
                        'name': carrier_name_data,
                        'shipping_cost': shipping_cost_data,
                        'delivery_time': delivery_time_data,
                        'date_estimated': date_estimated_data,
                        'date_preparation': date_preparation_data,
                        'sale_order_id': self.id
                    }
                # Se guardan las cotizaciones
                for quote_data in temp_quotes.values():
                    new_quote = self.env['shipment.quotes_report'].create(quote_data)
                    self.quotestre = new_quote.id
                    _logger.info(f"Se creó el registro: {quote_data['name']}")  
                    mensaje = f"Se ha realizado la cotización con {quote_data['name']}"
                    self.message_post(body=mensaje)
            except requests.exceptions.RequestException as e:
                _logger.error(f"Error al obtener datos de la API: {e}")

    #FUNCIÓN PARA REGISTRAR LOS PEDIDOS
    def create_orders_enviopack(self):
        url = 'https://api-mx.enviopack.com/pedidos'
        for data in self:
            access_token = data.access_token_enviopack
            order_data = {
                "id_externo": data.id_exter, 
                "nombre": data.name_order_client,
                "apellido": data.last_name,
                "email": data.email_order,
                "telefono": data.phone,
                "celular": data.cell_phone,
                "fecha_alta": f"{datetime.now()}",
                "monto": data.amount,
                "pagado": data.pay_product,
                "provincia": data.province_id,
                "localidad": data.location
            }
            _logger.info(f"LISTA DE DATOS DEL PEDIDO: {order_data}")
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            try:
                    register = requests.post(url, json=order_data, headers=headers)
                    if register.status_code == 401:
                        new_access_token = self.generate_access_token()
                        if new_access_token:
                            self.access_token_enviopack = new_access_token
                            headers['Authorization'] = f'Bearer {new_access_token}'
                            register = requests.post(url, json=order_data, headers=headers)
                            orders = register.json()
                    elif register.status_code == 200:
                        _logger.critical(f"{register.json() = }")
                        orders = register.json()
                    orders_id = orders.get("id")
                    _logger.info(f"Se ha creado el pedido: {orders}")
                    mensaje = f"Se ha registrado el pedido en Enviópack y su id es: {orders_id}"
                    self.message_post(body=mensaje)
                    return orders_id   
            except requests.exceptions.RequestException as e:
                _logger.error(f"Error al enviar los datos de la API: {e}")

    #FUNCIÓN PARA REGISTRAR LOS ENVIOS
    def create_shipment_enviopack(self):
        #Obtengo el id del pedido que se genero en la funcion create_orders_enviopack
        id_orders_api = self.create_orders_enviopack()
        _logger.info(f"ID DEL PEDIDO: {id_orders_api}")
        if id_orders_api is None:
            _logger.error(f"Error al traer el id del pedido")
            return
        url = 'https://api-mx.enviopack.com/envios'
        access_token = self.access_token_enviopack
        data_headers = {
            'pedido': id_orders_api,
            'direccion_envio': self.shipping_address,
            'destinatario': self.name_order_client,
            'observaciones': self.observations,
            'modalidad': self.modality,
            'servicio': self.service,
            'correo': self.company_mail,
            'confirmado': self.confirmed,
            'paquetes': [{"alto": self.package_height,"ancho": self.package_width,"largo": self.package_length,"peso": self.package_weight}],
            'calle': self.street,
            'numero':self.num_street,
            'piso': self.floor,
            'depto':self.departament,
            'codigo_postal': self.postal_code,
            'provincia':self.province_id,
            'localidad': self.location,
            'barrio': self.neighborhood
        }
        _logger.info(f"DATOS DEL ENVIO: {data_headers}")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        try:
            query = requests.post(url, json=data_headers, headers=headers)
            if query.status_code == 401:
                new_access_token = self.generate_access_token()
                if new_access_token:
                    self.access_token_enviopack = new_access_token
                    headers['Authorization'] = f'Bearer {new_access_token}'
                    query = requests.post(url, json=data_headers, headers=headers)
                    shipment = query.json()
                    _logger.info(f"SE HA CREADO EL ENVIO DESPUES DE ACTUALIZAR EL ACCESS TOKEN: {shipment}")
            if query.status_code == 200:
                _logger.critical(f"{query = }")
                shipment = query.json()
            id_shipment= shipment.get("id")
            _logger.info(f"Se ha creado el envio: {shipment}")
            mensaje = f"Se ha registrado el envió en Enviópack y su id es: {id_shipment}"
            self.message_post(body=mensaje)
            return id_shipment 
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al enviar los datos de la API: {e}")
    
    def create_labels_shipments(self,shipment='False'):
        url = f'https://api-mx.enviopack.com/envios/{shipment}/etiqueta?access_token={self.access_token_enviopack}&formato=pdf'
        _logger.info(f"DATOS PARA LA CONSULTA DE LA ETIQUETA : {url}")
        try:
            query_labels = requests.get(url)
            # _logger.critical(f"{data_labels = }")
            if query_labels.status_code == 401:
                self.access_token_enviopack = self.generate_access_token()
                query_labels = requests.get(url)
            elif query_labels.status_code == 200:
                _logger.info(f"Se imprimio la etiqueta{query_labels.content}")
                return query_labels.content
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al enviar para la consulta de la etiquetalos datos de la API: {e}")

    def report_pdf_labels_shipments(self):
        #Primero, necesitas tener un envío válido para generar las etiquetas
        shipment = self.create_shipment_enviopack()
        # # OBTENGO LA INFORMACION DEVUELTA POR LA FUNCION
        time.sleep(60) 
        labels_pdf = self.create_labels_shipments(shipment)
        name_pdf_file = self.id_exter+'_Enviopack.pdf'
        pdf_view =self.env['shipment.pdf_view'].create({
        'recup_pdf': base64.b64encode(labels_pdf),
        'file_name': name_pdf_file,
        'sale_order_id': self.id,
        })

        # Creo un registro ir.attachment con el archivo PDF
        attachment = self.env['ir.attachment'].create({
            'name': pdf_view.file_name,
            'datas': pdf_view.recup_pdf,
            'res_model': self._name,
            'res_id': self.id,
        })

        # Creo el mensaje en el chatter con el archivo PDF adjunto
        self.message_post(
            body="Se ha creado la guia del envio:",
            attachment_ids=[attachment.id]
        )

        self.validation_camps = True