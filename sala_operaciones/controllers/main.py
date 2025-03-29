import logging
from odoo import http
from odoo.http import request
import json

_logger = logging.getLogger(__name__)

class SalaOperacionesController(http.Controller):
    
    @http.route('/sala_operaciones/get_salas', type='json', auth='user')
    def get_salas(self):
        try:
            salas = request.env['operating.room'].search_read([], ['id', 'nombre', 'color'])
            return {
                'status': 'success',
                'data': [
                    {'id': s['id'], 'nombre': s['nombre'], 'color': s['color']}
                    for s in salas
                ]
            }
        except Exception as e:
            _logger.error("Error: %s", str(e))
            return {'status': 'error', 'message': str(e)}