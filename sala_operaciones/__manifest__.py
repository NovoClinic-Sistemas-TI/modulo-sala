{
    'name': 'sala_operaciones',
    'version': '1.0',
    'summary': 'Módulo para gestionar salas de operaciones',
    'description': 'Módulo para gestionar salas de operaciones',
    'author': 'Tu nombre',
    'application': True,
    'sequence': 10,
    'website': 'https://www.tu-website.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'mail', 'calendar'],  #  Dependencia 'web' añadida
    'assets': {
        'web.assets_backend': [
            'sala_operaciones/static/src/js/sala_filter.js',
        ],
        'web.assets_qweb': [
            'sala_operaciones/static/src/xml/sala_filter.xml',
        ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/operating_room.xml',
        'views/procedimiento_medico.xml',
        'views/surgery_reservation_views.xml',
        'views/actions.xml',
    ],

}