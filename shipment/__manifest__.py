# -*- coding: utf-8 -*-
{
    'name': "shipment",
    'description': """
        Module shipment-full
    """,
    'author': "adela",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'auto_installable': False,
    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','contacts','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views_price_produc.xml',
    ],
}

