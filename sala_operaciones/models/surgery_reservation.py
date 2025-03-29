from odoo import models, fields, api
from odoo.exceptions import ValidationError

# Definimos un nuevo modelo llamado "Reserva de sala de operaciones"
class SurgeryReservation(models.Model):
        _name = 'surgery.reservation'
        _inherit = ['mail.thread', 'mail.activity.mixin']
        _description = 'Reserva de sala de operaciones'
        _rec_name = 'sala_y_medico'  # Indica que se mostrará el campo sala_y_medico como nombre de registro
        # Campos del modelo
        fecha = fields.Datetime(string='Fecha de Registro', default=fields.Datetime.now, readonly=True) # Campo para la fecha de la reserva
        medico = fields.Many2one('res.partner', string='Medico Tratante:', required=True, domain=lambda self: [('title', '=', 'Doctor')])  # Campo para el medico (relación con el modelo res.partner)
        paciente = fields.Many2one('res.partner', string='Paciente', domain=lambda self: [('title', '=', 'Paciente')])
        medico_tipo_documento = fields.Many2one('l10n_latam.identification.type', string='Tipo de documento')
        medico_numero_documento = fields.Char(string='Número de documento')
        sala_operaciones_id = fields.Many2one('operating.room', string='Sala de operaciones',required=True)  # Campo para la sala de operaciones (relación con el modelo operating.room)
        hora_inicio = fields.Datetime(string='Hora de inicio')  # Campo para la hora de inicio de la reserva
        hora_fin = fields.Datetime(string='Hora de fin')  # Campo para la hora de fin de la reserva
        procedimiento_id = fields.Many2many('medical.procedure', string='Procedimiento médico')
        color_sala = fields.Char(string='Color de la sala', compute='_compute_color_sala')
        tipo_cirugia = fields.Selection([('AMBULATORIA', 'AMBULATORIA'),('HOSPITALARIA', 'HOSPITALARIA')], string='Tipo de Cirugía', required=True)
        servicio_laboratorio = fields.One2many('surgery.reservation.laboratorio', 'reservation_id', string='Laboratorio')
        precio_servicio_laboratorio = fields.Float(string='Precio del servicio de laboratorio', compute='_compute_precio_servicio_laboratorio')
        estado = fields.Selection([('pendiente', 'Pendiente'),('confirmada', 'Confirmada'),('cancelada', 'Cancelada')], string='Estado', default='pendiente')
        gastos_medico = fields.Float(string='Gastos médico', compute='_compute_gastos_medico')
        gastos_paciente = fields.Float(string='Gastos paciente', compute='_compute_gastos_paciente')
        service_extras = fields.One2many('surgery.service', 'reservation_ids', string='Servicios')
    #    
        @api.depends('servicio_laboratorio')
        def _compute_gastos_medico(self):
            for record in self:
                gastos_medico = sum(producto.precio_producto * producto.cantidad for producto in record.servicio_laboratorio if producto.asume_costo == 'medico')
                record.gastos_medico = gastos_medico

        @api.depends('servicio_laboratorio')
        def _compute_gastos_paciente(self):
            for record in self:
                gastos_paciente = sum(producto.precio_producto * producto.cantidad for producto in record.servicio_laboratorio if producto.asume_costo == 'paciente')
                record.gastos_paciente = gastos_paciente
    #
        @api.model
        def create(self, vals):
            if vals.get('paciente'):
                paciente_id = vals['paciente']
                paciente = self.env['res.partner'].browse(paciente_id)
                if not paciente.title:
                    title_id = self.env['res.partner.title'].search([('name', '=', 'Paciente')]).id
                    paciente.title = title_id
            return super(SurgeryReservation, self).create(vals)
               
        def write(self, vals):
            if 'paciente' in vals and vals['paciente']:
                paciente_id = vals['paciente']
                paciente = self.env['res.partner'].browse(paciente_id)
                if not paciente.title:
                    title_id = self.env['res.partner.title'].search([('name', '=', 'Paciente')]).id
                    paciente.title = title_id
            return super(SurgeryReservation, self).write(vals)
    #                                    
        def confirmar(self):
            # Verificar si ya está confirmado
            if self.estado == 'confirmada':
                raise ValidationError("¡Esta reserva ya está confirmada! 🛑")
            
            # Confirmar y registrar en el Chatter
            self.write({'estado': 'confirmada'})
            
            # Convertir UTC a hora local del usuario
            hora_confirmacion = fields.Datetime.context_timestamp(
                self, 
                fields.Datetime.now()  # Fecha/hora en UTC
            )
            self.message_post(
                body=f"✅ Confirmado por: {self.env.user.name} (Fecha: {hora_confirmacion.strftime('%d/%m/%Y %H:%M:%S')})",
                message_type="comment",
                author_id=self.env.user.partner_id.id,
            )
            return True
    # Campo computado para mostrar el total del costo de servicios de laboratortio  
        @api.depends('servicio_laboratorio.product_id')
        def _compute_precio_servicio_laboratorio(self):
            for record in self:
                precio_total = 0
                if record.servicio_laboratorio:  # Verifica si el campo no está vacío
                    for servicio in record.servicio_laboratorio:
                        precio_total += servicio.product_id.list_price * servicio.cantidad
                record.precio_servicio_laboratorio = precio_total
    # Campo computado para mostrar la sala, el medico, procedimiento
        @api.depends('sala_operaciones_id', 'medico', 'procedimiento_id', 'paciente')
        def _compute_sala_y_medico(self):
            for record in self:
                procedimientos = ', '.join([p.nombre for p in record.procedimiento_id])
                record.sala_y_medico = f"{record.sala_operaciones_id.nombre} - {record.medico.name} - {procedimientos} - {record.paciente.name}"
    # Campo computado para mostrar la sala y el medico           
        sala_y_medico = fields.Char(compute='_compute_sala_y_medico', string='Sala, Médico y Procedimiento')        
    # Campo computado para color de Sala
        @api.depends('sala_operaciones_id')
        def _compute_color_sala(self):
            for record in self:
                record.color_sala = record.sala_operaciones_id.color
        # mostrar campos de otro modelo
        @api.onchange('medico')
        def _onchange_medico(self):
            if self.medico:
                self.medico_tipo_documento = self.medico.l10n_latam_identification_type_id.id
                self.medico_numero_documento = self.medico.vat
       # Validaciones y restricciones
        @api.constrains('hora_inicio', 'hora_fin', 'sala_operaciones_id')
        def _check_room_availability(self):
            for record in self:
                if record.hora_inicio >= record.hora_fin:
                    raise ValidationError('La hora de inicio debe ser anterior a la hora de fin.')

                overlapping_reservations = self.search([
                    ('sala_operaciones_id', '=', record.sala_operaciones_id.id),
                    ('id', '!=', record.id),
                    ('hora_inicio', '<', record.hora_fin),
                    ('hora_fin', '>', record.hora_inicio),
                ])

                if overlapping_reservations:
                    sala_operaciones_nombre = record.sala_operaciones_id.nombre
                    hora_inicio_overlap = overlapping_reservations[0].hora_inicio
                    hora_fin_overlap = overlapping_reservations[0].hora_fin
                    raise ValidationError(f'La sala de operaciones "{sala_operaciones_nombre}" ya está reservada para el horario de {hora_inicio_overlap} a {hora_fin_overlap}.')
# Definimos un nuevo modelo para agregar servicios de Laboratorio
class SurgeryReservationProduct(models.Model):
    _name = 'surgery.reservation.laboratorio'
    _description = 'Productos utilizados en la reserva de cirugía'

    reservation_id = fields.Many2one('surgery.reservation', string='Reserva de cirugía')
    product_id = fields.Many2one('product.template', string='Examenes',domain=lambda self: [('detailed_type', '=', 'service'), ('categ_id.name', '=', 'LABORATORIO')])
    cantidad = fields.Integer(string='Cantidad', default=1, required=True)
    precio_producto = fields.Float(string='Precio del producto', compute='_compute_precio_producto')
    asume_costo = fields.Selection([('medico', 'Médico'), ('paciente', 'Paciente')], string='Asume costo', required=True)
    
    @api.depends('product_id')
    def _compute_precio_producto(self):
        for record in self:
            record.precio_producto = record.product_id.list_price
# Definimos un nuevo modelo llamado "Sala de operaciones"
class OperatingRoom(models.Model):
    _name = 'operating.room'
    _description = 'Gestion de Salas'
    _rec_name = 'nombre'
    # Campos del modelo
    nombre = fields.Char(string='Nombre de la sala', required=True)  # Campo para el nombre de la sala
    capacidad = fields.Integer(string='Capacidad de la sala')  # Campo para la capacidad de la sala
    reservations = fields.One2many('surgery.reservation', 'sala_operaciones_id', string='Reservas')
    color = fields.Selection([
        ('#FFE0E0', 'Rojo'),
        ('#00FF00', 'Verde'),
        ('#0000FF', 'Azul'),
        ('#FFFF00', 'Amarillo'),
        ('#FF00FF', 'Magenta'),
    ], string='Color', default='#FFE0E0')  # Campo para el color de la sala

    def update_existing_records(self):
        records = self.env['operating.room'].search([('color', '=', '#FF0000')])
        for record in records:
            record.color = '#FFE0E0'

class SurgeryService(models.Model):
    _name = 'surgery.service'
    _description = 'Servicios de cirugía'

    reservation_ids = fields.Many2one('surgery.reservation', string='Reserva de cirugía')
    service_id = fields.Many2one('product.template', string='Examenes',domain=lambda self: [('detailed_type', '=', 'service'), ('categ_id.name', '=', 'EXTRAS')])
    cantidad = fields.Integer(string='Cantidad', default=1, required=True)
    precio_producto = fields.Float(string='Precio del producto', compute='_compute_precio_producto')
    asume_costo = fields.Selection([('medico', 'Médico'), ('paciente', 'Paciente')], string='Asume costo', required=True)
    
    @api.depends('service_id')
    def _compute_precio_producto(self):
        for record in self:
            record.precio_producto = record.service_id.list_price