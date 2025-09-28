from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, SelectMultipleField, SubmitField, IntegerField, TimeField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from models import User, Horario, Carrera, Materia

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    """Formulario de registro de usuario"""
    username = StringField('Usuario', validators=[
        DataRequired(), 
        Length(min=4, max=20, message='El usuario debe tener entre 4 y 20 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Ingrese un email válido')
    ])
    
    nombre = StringField('Nombre', validators=[
        DataRequired(), 
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    
    apellido = StringField('Apellido', validators=[
        DataRequired(), 
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    
    telefono = StringField('Teléfono', validators=[
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(), 
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    
    rol = SelectField('Rol', choices=[
        ('', 'Seleccione un rol'),
        ('admin', 'Administrador'),
        ('jefe_carrera', 'Jefe de Carrera'),
        ('profesor', 'Profesor')
    ], validators=[DataRequired(message='Debe seleccionar un rol')])
    
    tipo_profesor = SelectField('Tipo de Profesor', choices=[
        ('', 'Seleccione tipo de profesor'),
        ('profesor_completo', 'Profesor de Tiempo Completo'),
        ('profesor_asignatura', 'Profesor por Asignatura')
    ])
    
    carrera = SelectMultipleField('Carrera', validators=[Optional()])
    
    otra_carrera = BooleanField('¿Estás inscrito en otra carrera además de la que seleccionaste?', validators=[Optional()])
    
    submit = SubmitField('Registrarse')
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Seleccione una carrera')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]
    
    def validate_username(self, username):
        """Validar que el usuario no exista"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Elija uno diferente.')
    
    def validate_email(self, email):
        """Validar que el email no exista"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado. Elija uno diferente.')
    
    def validate_tipo_profesor(self, tipo_profesor):
        """Validar tipo de profesor si se seleccionó profesor como rol"""
        if self.rol.data == 'profesor' and not tipo_profesor.data:
            raise ValidationError('Debe seleccionar el tipo de profesor.')
    
    def validate_carrera(self, carrera):
        """Validar carrera si se seleccionó profesor o jefe de carrera como rol"""
        if self.rol.data in ['profesor', 'jefe_carrera'] and (not carrera.data or len(carrera.data) == 0):
            if self.rol.data == 'profesor':
                raise ValidationError('Los profesores deben seleccionar al menos una carrera.')
            elif self.rol.data == 'jefe_carrera':
                raise ValidationError('Los jefes de carrera deben seleccionar al menos una carrera.')
        
        # Validar que no haya otro jefe de carrera para las carreras seleccionadas
        if self.rol.data == 'jefe_carrera' and carrera.data:
            for carrera_id in carrera.data:
                existing_jefe = User.query.filter(
                    User.rol == 'jefe_carrera',
                    User.carreras.any(id=int(carrera_id)),
                    User.activo == True
                ).first()
                if existing_jefe:
                    carrera_obj = Carrera.query.get(int(carrera_id))
                    raise ValidationError(f'Ya existe un jefe de carrera para {carrera_obj.nombre if carrera_obj else "esta carrera"}. Contacte al administrador.')
    
    def get_final_rol(self):
        """Obtener el rol final basado en la selección"""
        if self.rol.data == 'profesor':
            return self.tipo_profesor.data
        return self.rol.data

class HorarioForm(FlaskForm):
    """Formulario para crear/editar horarios"""
    nombre = StringField('Nombre del Período', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    turno = SelectField('Turno', choices=[
        ('', 'Seleccione un turno'),
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino')
    ], validators=[DataRequired(message='Debe seleccionar un turno')])
    
    hora_inicio = TimeField('Hora de Inicio', validators=[
        DataRequired(message='La hora de inicio es obligatoria')
    ])
    
    hora_fin = TimeField('Hora de Fin', validators=[
        DataRequired(message='La hora de fin es obligatoria')
    ])
    
    orden = IntegerField('Orden', validators=[
        DataRequired(message='El orden es obligatorio'),
        NumberRange(min=1, max=20, message='El orden debe estar entre 1 y 20')
    ])
    
    submit = SubmitField('Guardar Horario')
    
    def validate_hora_fin(self, hora_fin):
        """Validar que la hora de fin sea posterior a la de inicio"""
        if self.hora_inicio.data and hora_fin.data:
            if hora_fin.data <= self.hora_inicio.data:
                raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
    
    def validate_orden(self, orden):
        """Validar que el orden no esté duplicado en el mismo turno"""
        if self.turno.data and orden.data:
            # En caso de edición, excluir el horario actual de la validación
            query = Horario.query.filter_by(turno=self.turno.data, orden=orden.data, activo=True)
            
            # Si estamos editando, excluir el horario actual
            if hasattr(self, '_horario_id') and self._horario_id:
                query = query.filter(Horario.id != self._horario_id)
            
            if query.first():
                raise ValidationError(f'Ya existe un período con orden {orden.data} en el turno {self.turno.data}.')

class EliminarHorarioForm(FlaskForm):
    """Formulario para confirmar eliminación de horario"""
    submit = SubmitField('Confirmar Eliminación')

class CarreraForm(FlaskForm):
    """Formulario para crear/editar carreras"""
    nombre = StringField('Nombre de la Carrera', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=5, max=150, message='El nombre debe tener entre 5 y 150 caracteres')
    ])
    
    codigo = StringField('Código', validators=[
        DataRequired(message='El código es obligatorio'),
        Length(min=2, max=10, message='El código debe tener entre 2 y 10 caracteres')
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    
    facultad = StringField('Facultad', validators=[
        Optional(),
        Length(max=100, message='La facultad no puede exceder 100 caracteres')
    ])
    
    jefe_carrera_id = SelectField('Jefe de Carrera', 
                                 choices=[('', 'Sin asignar')],
                                 validators=[Optional()],
                                 coerce=lambda x: int(x) if x and x.isdigit() else None)
    
    submit = SubmitField('Guardar Carrera')
    
    def __init__(self, *args, **kwargs):
        super(CarreraForm, self).__init__(*args, **kwargs)
        # Cargar los usuarios que pueden ser jefes de carrera (profesores y jefes de carrera)
        try:
            jefes_disponibles = User.query.filter(
                User.rol.in_(['profesor', 'jefe_carrera']),
                User.activo == True
            ).order_by(User.nombre, User.apellido).all()
            
            self.jefe_carrera_id.choices = [('', 'Sin asignar')] + [
                (str(user.id), f"{user.nombre} {user.apellido} - {user.email}")
                for user in jefes_disponibles
            ]
        except Exception as e:
            print(f"Error cargando opciones de jefe de carrera: {e}")
            self.jefe_carrera_id.choices = [('', 'Sin asignar')]
    
    def validate_codigo(self, codigo):
        """Validar que el código no esté duplicado"""
        # En caso de edición, excluir la carrera actual de la validación
        query = Carrera.query.filter_by(codigo=codigo.data.upper(), activa=True)
        
        if hasattr(self, '_carrera_id') and self._carrera_id:
            query = query.filter(Carrera.id != self._carrera_id)
        
        if query.first():
            raise ValidationError(f'Ya existe una carrera con código {codigo.data.upper()}.')
    
    def validate_nombre(self, nombre):
        """Validar que el nombre no esté duplicado"""
        query = Carrera.query.filter_by(nombre=nombre.data, activa=True)
        
        if hasattr(self, '_carrera_id') and self._carrera_id:
            query = query.filter(Carrera.id != self._carrera_id)
        
        if query.first():
            raise ValidationError('Ya existe una carrera con este nombre.')

class ImportarProfesoresForm(FlaskForm):
    """Formulario para importar profesores desde archivo CSV/Excel"""
    archivo = FileField('Archivo CSV/Excel', validators=[
        DataRequired(message='Debe seleccionar un archivo'),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Solo se permiten archivos CSV o Excel')
    ])
    
    carrera_defecto = SelectField('Carrera por Defecto', validators=[
        Optional()
    ])
    
    submit = SubmitField('Importar Profesores')
    
    def __init__(self, *args, **kwargs):
        super(ImportarProfesoresForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera_defecto.choices = [('', 'Sin carrera por defecto')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

class FiltrarProfesoresForm(FlaskForm):
    """Formulario para filtrar profesores"""
    carrera = SelectField('Filtrar por Carrera', validators=[Optional()])
    tipo_profesor = SelectField('Tipo de Profesor', choices=[
        ('', 'Todos los tipos'),
        ('profesor_completo', 'Tiempo Completo'),
        ('profesor_asignatura', 'Por Asignatura')
    ], validators=[Optional()])
    
    submit = SubmitField('Filtrar')
    
    def __init__(self, *args, **kwargs):
        super(FiltrarProfesoresForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Todas las carreras')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

class ExportarProfesoresForm(FlaskForm):
    """Formulario para exportar profesores a PDF"""
    carrera = SelectField('Carrera a Exportar', validators=[Optional()])
    incluir_contacto = SelectField('Incluir Información de Contacto', choices=[
        ('si', 'Sí'),
        ('no', 'No')
    ], default='si')
    
    submit = SubmitField('Exportar a PDF')
    
    def __init__(self, *args, **kwargs):
        super(ExportarProfesoresForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Todas las carreras')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

class EliminarCarreraForm(FlaskForm):
    """Formulario para confirmar eliminación de carrera"""
    submit = SubmitField('Confirmar Eliminación')

class MateriaForm(FlaskForm):
    """Formulario para crear/editar materias"""
    nombre = StringField('Nombre de la Materia', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=200, message='El nombre debe tener entre 3 y 200 caracteres')
    ])
    
    codigo = StringField('Código', validators=[
        DataRequired(message='El código es obligatorio'),
        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres')
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    
    cuatrimestre = IntegerField('Cuatrimestre', validators=[
        DataRequired(message='El cuatrimestre es obligatorio'),
        NumberRange(min=1, max=12, message='El cuatrimestre debe estar entre 1 y 12')
    ])
    
    creditos = IntegerField('Créditos', validators=[
        DataRequired(message='Los créditos son obligatorios'),
        NumberRange(min=1, max=10, message='Los créditos deben estar entre 1 y 10')
    ], default=3)
    
    horas_teoricas = IntegerField('Horas Teóricas', validators=[
        DataRequired(message='Las horas teóricas son obligatorias'),
        NumberRange(min=0, max=10, message='Las horas teóricas deben estar entre 0 y 10')
    ], default=3)
    
    horas_practicas = IntegerField('Horas Prácticas', validators=[
        DataRequired(message='Las horas prácticas son obligatorias'),
        NumberRange(min=0, max=10, message='Las horas prácticas deben estar entre 0 y 10')
    ], default=0)
    
    carrera = SelectField('Carrera', validators=[DataRequired(message='Debe seleccionar una carrera')])
    
    submit = SubmitField('Guardar Materia')
    
    def __init__(self, *args, **kwargs):
        super(MateriaForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]
    
    def validate_codigo(self, codigo):
        """Validar que el código no esté duplicado"""
        # En caso de edición, excluir la materia actual de la validación
        query = Materia.query.filter_by(codigo=codigo.data.upper(), activa=True)
        
        if hasattr(self, '_materia_id') and self._materia_id:
            query = query.filter(Materia.id != self._materia_id)
        
        if query.first():
            raise ValidationError(f'Ya existe una materia con código {codigo.data.upper()}.')

class ImportarMateriasForm(FlaskForm):
    """Formulario para importar materias desde archivo CSV/Excel"""
    archivo = FileField('Archivo CSV/Excel', validators=[
        DataRequired(message='Debe seleccionar un archivo'),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Solo se permiten archivos CSV o Excel')
    ])
    
    carrera_defecto = SelectField('Carrera por Defecto', validators=[
        Optional()
    ])
    
    submit = SubmitField('Importar Materias')
    
    def __init__(self, *args, **kwargs):
        super(ImportarMateriasForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera_defecto.choices = [('', 'Sin carrera por defecto')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

class FiltrarMateriasForm(FlaskForm):
    """Formulario para filtrar materias"""
    carrera = SelectField('Filtrar por Carrera', validators=[Optional()])
    cuatrimestre = SelectField('Filtrar por Cuatrimestre', choices=[
        ('', 'Todos los cuatrimestres'),
        ('1', 'Cuatrimestre 1'),
        ('2', 'Cuatrimestre 2'),
        ('3', 'Cuatrimestre 3'),
        ('4', 'Cuatrimestre 4'),
        ('5', 'Cuatrimestre 5'),
        ('6', 'Cuatrimestre 6'),
        ('7', 'Cuatrimestre 7'),
        ('8', 'Cuatrimestre 8'),
        ('9', 'Cuatrimestre 9'),
        ('10', 'Cuatrimestre 10'),
        ('11', 'Cuatrimestre 11'),
        ('12', 'Cuatrimestre 12')
    ], validators=[Optional()])
    
    submit = SubmitField('Filtrar')
    
    def __init__(self, *args, **kwargs):
        super(FiltrarMateriasForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Todas las carreras')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

class ExportarMateriasForm(FlaskForm):
    """Formulario para exportar materias a PDF"""
    carrera = SelectField('Carrera a Exportar', validators=[Optional()])
    cuatrimestre = SelectField('Cuatrimestre a Exportar', choices=[
        ('', 'Todos los cuatrimestres'),
        ('1', 'Cuatrimestre 1'),
        ('2', 'Cuatrimestre 2'),
        ('3', 'Cuatrimestre 3'),
        ('4', 'Cuatrimestre 4'),
        ('5', 'Cuatrimestre 5'),
        ('6', 'Cuatrimestre 6'),
        ('7', 'Cuatrimestre 7'),
        ('8', 'Cuatrimestre 8'),
        ('9', 'Cuatrimestre 9'),
        ('10', 'Cuatrimestre 10'),
        ('11', 'Cuatrimestre 11'),
        ('12', 'Cuatrimestre 12')
    ], validators=[Optional()])
    
    submit = SubmitField('Exportar a PDF')

class GenerarHorariosForm(FlaskForm):
    """Formulario para generar horarios académicos automáticamente"""
    
    carrera = SelectField('Carrera', choices=[], validators=[DataRequired()])
    
    cuatrimestre = SelectField('Cuatrimestre', choices=[
        ('', 'Seleccione cuatrimestre'),
        ('1', 'Cuatrimestre 1'),
        ('2', 'Cuatrimestre 2'),
        ('3', 'Cuatrimestre 3'),
        ('4', 'Cuatrimestre 4'),
        ('5', 'Cuatrimestre 5'),
        ('6', 'Cuatrimestre 6'),
        ('7', 'Cuatrimestre 7'),
        ('8', 'Cuatrimestre 8'),
        ('9', 'Cuatrimestre 9'),
        ('10', 'Cuatrimestre 10'),
        ('11', 'Cuatrimestre 11'),
        ('12', 'Cuatrimestre 12')
    ], validators=[DataRequired()])
    
    turno = SelectField('Turno', choices=[
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('ambos', 'Ambos turnos')
    ], validators=[DataRequired()])
    
    dias_semana = SelectField('Días de la semana', choices=[
        ('lunes_viernes', 'Lunes a Viernes'),
        ('lunes_sabado', 'Lunes a Sábado'),
        ('personalizado', 'Personalizado')
    ], default='lunes_viernes', validators=[DataRequired()])
    
    # Campos para selección personalizada de días
    lunes = SelectField('Lunes', choices=[('si', 'Sí'), ('no', 'No')], default='si')
    martes = SelectField('Martes', choices=[('si', 'Sí'), ('no', 'No')], default='si')
    miercoles = SelectField('Miércoles', choices=[('si', 'Sí'), ('no', 'No')], default='si')
    jueves = SelectField('Jueves', choices=[('si', 'Sí'), ('no', 'No')], default='si')
    viernes = SelectField('Viernes', choices=[('si', 'Sí'), ('no', 'No')], default='si')
    sabado = SelectField('Sábado', choices=[('si', 'Sí'), ('no', 'No')], default='no')
    
    periodo_academico = StringField('Período Académico', 
                                   default='2025-1', 
                                   validators=[DataRequired(), 
                                             Length(max=20, message='Máximo 20 caracteres')])
    
    submit = SubmitField('Generar Horarios')

class EditarHorarioAcademicoForm(FlaskForm):
    """Formulario para editar un horario académico"""
    
    profesor_id = SelectField('Profesor', choices=[], validators=[DataRequired()])
    horario_id = SelectField('Horario', choices=[], validators=[DataRequired()])
    dia_semana = SelectField('Día', choices=[
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado')
    ], validators=[DataRequired()])
    
    aula = StringField('Aula', validators=[Length(max=20, message='Máximo 20 caracteres')])
    periodo_academico = StringField('Período Académico', validators=[DataRequired(), Length(max=20)])
    
    submit = SubmitField('Guardar Cambios')

class EliminarHorarioAcademicoForm(FlaskForm):
    """Formulario para confirmar eliminación de horario académico"""
    
    confirmacion = StringField('Escriba "ELIMINAR" para confirmar', 
                              validators=[DataRequired(), 
                                        Length(min=8, max=8, message='Debe escribir exactamente "ELIMINAR"')])
    
    submit = SubmitField('Eliminar Horario')

class DisponibilidadProfesorForm(FlaskForm):
    """Formulario para gestionar disponibilidad de profesores"""
    
    profesor_id = SelectField('Profesor', validators=[DataRequired()], choices=[])
    dia_semana = SelectField('Día de la semana', validators=[DataRequired()], choices=[
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado')
    ])
    
    submit = SubmitField('Guardar Disponibilidad')

class EditarDisponibilidadProfesorForm(FlaskForm):
    """Formulario para editar disponibilidad de un profesor específico"""
    
    horario_id = SelectField('Horario', validators=[DataRequired()], choices=[])
    disponible = SelectField('Disponibilidad', validators=[DataRequired()], choices=[
        ('True', 'Disponible'),
        ('False', 'No disponible')
    ])
    
    submit = SubmitField('Actualizar')

class AgregarProfesorForm(FlaskForm):
    """Formulario para que administradores agreguen profesores manualmente"""
    
    username = StringField('Nombre de Usuario', validators=[
        DataRequired(message='El nombre de usuario es obligatorio'),
        Length(min=4, max=20, message='El usuario debe tener entre 4 y 20 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='Ingrese un email válido')
    ])
    
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    
    apellido = StringField('Apellido', validators=[
        DataRequired(message='El apellido es obligatorio'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    
    telefono = StringField('Teléfono', validators=[
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='La confirmación de contraseña es obligatoria'),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    
    tipo_profesor = SelectField('Tipo de Profesor', validators=[DataRequired(message='Debe seleccionar el tipo de profesor')], choices=[
        ('', 'Seleccione tipo de profesor'),
        ('profesor_completo', 'Profesor de Tiempo Completo'),
        ('profesor_asignatura', 'Profesor por Asignatura')
    ])
    
    carrera = SelectField('Carrera', validators=[DataRequired(message='Debe seleccionar una carrera')])
    
    submit = SubmitField('Crear Profesor')
    
    def __init__(self, *args, **kwargs):
        super(AgregarProfesorForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        from models import Carrera
        self.carrera.choices = [
            (str(c.id), f"{c.codigo} - {c.nombre}") 
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]
    
    def get_disponibilidades_data(self):
        """Obtener los datos de disponibilidad del formulario"""
        disponibilidades = []
        
        # Procesar todos los campos que empiecen con 'disp_'
        for field_name, field in self._fields.items():
            if field_name.startswith('disp_') and field.data:
                parts = field_name.split('_')
                if len(parts) >= 3:
                    horario_id = parts[1]
                    dia_semana = parts[2]
                    disponible = field.data
                    
                    disponibilidades.append({
                        'horario_id': int(horario_id),
                        'dia_semana': dia_semana,
                        'disponible': disponible
                    })
        
        return disponibilidades
    
    def validate_username(self, username):
        """Validar que el usuario no exista"""
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Elija uno diferente.')
    
    def validate_email(self, email):
        """Validar que el email no exista"""
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado. Elija uno diferente.')

# Formularios para Gestión de Usuarios (solo administradores)

class AgregarUsuarioForm(FlaskForm):
    """Formulario para agregar nuevo usuario"""
    username = StringField('Usuario', validators=[
        DataRequired(),
        Length(min=4, max=20, message='El usuario debe tener entre 4 y 20 caracteres')
    ])

    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Ingrese un email válido')
    ])

    nombre = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])

    apellido = StringField('Apellido', validators=[
        DataRequired(),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])

    telefono = StringField('Teléfono', validators=[
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])

    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])

    rol = SelectField('Rol', choices=[
        ('', 'Seleccione un rol'),
        ('admin', 'Administrador'),
        ('jefe_carrera', 'Jefe de Carrera'),
        ('profesor_completo', 'Profesor de Tiempo Completo'),
        ('profesor_asignatura', 'Profesor por Asignatura')
    ], validators=[DataRequired(message='Debe seleccionar un rol')])

    carrera = SelectField('Carrera', validators=[Optional()])

    activo = BooleanField('Usuario Activo', default=True)

    submit = SubmitField('Crear Usuario')

    def __init__(self, *args, **kwargs):
        super(AgregarUsuarioForm, self).__init__(*args, **kwargs)
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Seleccione una carrera')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}")
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

    def validate_username(self, username):
        """Validar que el usuario no exista"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Elija uno diferente.')

    def validate_email(self, email):
        """Validar que el email no exista"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado. Elija uno diferente.')

    def validate_carrera(self, carrera):
        """Validar carrera si se seleccionó profesor como rol"""
        if self.rol.data in ['profesor_completo', 'profesor_asignatura'] and not carrera.data:
            raise ValidationError('Los profesores deben seleccionar una carrera.')

class EditarUsuarioForm(FlaskForm):
    """Formulario para editar usuario existente"""
    username = StringField('Usuario', validators=[
        DataRequired(),
        Length(min=4, max=20, message='El usuario debe tener entre 4 y 20 caracteres')
    ])

    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Ingrese un email válido')
    ])

    nombre = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])

    apellido = StringField('Apellido', validators=[
        DataRequired(),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])

    telefono = StringField('Teléfono', validators=[
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])

    rol = SelectField('Rol', choices=[
        ('', 'Seleccione un rol'),
        ('admin', 'Administrador'),
        ('jefe_carrera', 'Jefe de Carrera'),
        ('profesor_completo', 'Profesor de Tiempo Completo'),
        ('profesor_asignatura', 'Profesor por Asignatura')
    ], validators=[DataRequired(message='Debe seleccionar un rol')])

    carrera = SelectField('Carrera', validators=[Optional()])

    activo = BooleanField('Usuario Activo')

    submit = SubmitField('Actualizar Usuario')

    def __init__(self, user=None, *args, **kwargs):
        super(EditarUsuarioForm, self).__init__(*args, **kwargs)
        self.user = user
        # Llenar opciones de carreras
        self.carrera.choices = [('', 'Seleccione una carrera')] + [
            (str(c.id), f"{c.codigo} - {c.nombre}")
            for c in Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
        ]

    def validate_username(self, username):
        """Validar que el usuario no exista (excepto el actual)"""
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.user.id:
            raise ValidationError('Este nombre de usuario ya está en uso. Elija uno diferente.')

    def validate_email(self, email):
        """Validar que el email no exista (excepto el actual)"""
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.user.email:
            raise ValidationError('Este email ya está registrado. Elija uno diferente.')

    def validate_carrera(self, carrera):
        """Validar carrera si se seleccionó profesor o jefe de carrera como rol"""
        if self.rol.data in ['profesor_completo', 'profesor_asignatura', 'jefe_carrera'] and not carrera.data:
            if self.rol.data == 'jefe_carrera':
                raise ValidationError('Los jefes de carrera deben seleccionar una carrera.')
            else:
                raise ValidationError('Los profesores deben seleccionar una carrera.')
        
        # Validar que no haya otro jefe de carrera para la misma carrera (excepto el usuario actual)
        if self.rol.data == 'jefe_carrera' and carrera.data:
            existing_jefe = User.query.filter(
                User.rol == 'jefe_carrera',
                User.carrera_id == int(carrera.data),
                User.activo == True
            ).first()
            if existing_jefe and existing_jefe.id != self.user.id:
                carrera_obj = Carrera.query.get(int(carrera.data))
                raise ValidationError(f'Ya existe un jefe de carrera para {carrera_obj.nombre if carrera_obj else "esta carrera"}.')

class EliminarUsuarioForm(FlaskForm):
    """Formulario para confirmar eliminación de usuario"""
    confirmacion = StringField('Escriba "ELIMINAR" para confirmar', validators=[
        DataRequired(),
        Length(min=8, max=8, message='Debe escribir exactamente "ELIMINAR"')
    ])

    submit = SubmitField('Eliminar Usuario')

    def validate_confirmacion(self, confirmacion):
        """Validar que se haya escrito exactamente "ELIMINAR" """
        if confirmacion.data != 'ELIMINAR':
            raise ValidationError('Debe escribir exactamente "ELIMINAR" para confirmar la eliminación.')