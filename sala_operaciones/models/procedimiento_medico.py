from odoo import models, fields, api
from odoo.exceptions import ValidationError

# Definimos un nuevo modelo llamado "Procedimiento médico"
class ProcedimientoMedico(models.Model):
    _name = 'medical.procedure'
    _description = 'Procedimiento médico'
    _rec_name = 'nombre'

    # Campos del modelo
    nombre = fields.Char(string='Nombre del procedimiento', required=True)
    codigo = fields.Char(string='Código del procedimiento')
    descripcion = fields.Text(string='Descripción del procedimiento')
    categoria = fields.Selection([
        ('cirugia', 'Cirugía'),
        ('endoscopia', 'Endoscopia'),
        ('diagnostico', 'Diagnóstico'),
        ('tratamiento', 'Tratamiento')
    ], string='Categoría del procedimiento')
    activo = fields.Boolean(string='Activo', default=True)

    # Función para convertir a mayúsculas y eliminar espacios en blanco
    @api.onchange('nombre', 'codigo', 'descripcion')
    def _convertir_mayusculas(self):
        for record in self:
            if isinstance(record.nombre, str):  # Verificar si es una cadena de texto
                record.nombre = record.nombre.upper().strip()
            if isinstance(record.codigo, str):  # Verificar si es una cadena de texto
                record.codigo = record.codigo.upper().strip()
            if isinstance(record.descripcion, str):  # Verificar si es una cadena de texto
                record.descripcion = record.descripcion.upper().strip()
    # Función de constraint para evitar datos repetidos
    @api.constrains('nombre', 'codigo')
    def _check_unique(self):
        for record in self:
            if self.search([('nombre', '=', record.nombre), ('id', '!=', record.id)]):
                raise ValidationError('Nombre del procedimiento repetido. Por favor, ingrese un nombre diferente.')
            if self.search([('codigo', '=', record.codigo), ('id', '!=', record.id)]):
                raise ValidationError('Código del procedimiento repetido. Por favor, ingrese un código diferente.')