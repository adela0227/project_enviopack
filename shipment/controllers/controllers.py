# -*- coding: utf-8 -*-
# from odoo import http


# class Shipment(http.Controller):
#     @http.route('/shipment/shipment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/shipment/shipment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('shipment.listing', {
#             'root': '/shipment/shipment',
#             'objects': http.request.env['shipment.shipment'].search([]),
#         })

#     @http.route('/shipment/shipment/objects/<model("shipment.shipment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('shipment.object', {
#             'object': obj
#         })

