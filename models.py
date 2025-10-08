from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time
import os

db = SQLAlchemy()

# Tabla intermedia para relación many-to-many entre usuarios y carreras
user_carreras = db.Table('user_carreras',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('carrera_id', db.Integer, db.ForeignKey('carrera.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """Modelo de usuario con diferentes roles"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    # Información personal
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    imagen_perfil = db.Column(db.String(200))  # Ruta de la imagen de perfil
    
    # Rol del usuario
    rol = db.Column(db.String(20), nullable=False)
    # Para profesores: especifica si es de tiempo completo o por asignatura
    tipo_profesor = db.Column(db.String(20))
    
    # Relación many-to-many con carreras (para profesores y jefes de carrera)
    carreras = db.relationship('Carrera', secondary=user_carreras, backref=db.backref('usuarios', lazy=True))
    
    # Campo específico para jefes de carrera (una carrera asignada)
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'))
    carrera = db.relationship('Carrera', foreign_keys=[carrera_id], backref=db.backref('jefe_carrera', uselist=False))
    
    # Campos adicionales
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    def __init__(self, username, email, password, nombre, apellido, rol, telefono=None, tipo_profesor=None, carreras=None, imagen_perfil=None, carrera_id=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.nombre = nombre
        self.apellido = apellido
        self.rol = rol
        self.telefono = telefono
        self.tipo_profesor = tipo_profesor
        if carreras:
            self.carreras = carreras
        self.imagen_perfil = imagen_perfil
        self.carrera_id = carrera_id
    
    def set_password(self, password):
        """Establecer contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def get_nombre_completo(self):
        """Obtener nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"
    
    def is_admin(self):
        """Verificar si es administrador"""
        return self.rol == 'admin'
    
    def is_jefe_carrera(self):
        """Verificar si es jefe de carrera"""
        return self.rol == 'jefe_carrera'
    
    def is_profesor(self):
        """Verificar si es profesor (cualquier tipo)"""
        return self.rol in ['profesor_completo', 'profesor_asignatura']
    
    def is_profesor_completo(self):
        """Verificar si es profesor de tiempo completo"""
        return self.rol == 'profesor_completo'
    
    def is_profesor_asignatura(self):
        """Verificar si es profesor por asignatura"""
        return self.rol == 'profesor_asignatura'
    
    def get_rol_display(self):
        """Obtener nombre del rol para mostrar"""
        roles = {
            'admin': 'Administrador',
            'jefe_carrera': 'Jefe de Carrera',
            'profesor_completo': 'Profesor de Tiempo Completo',
            'profesor_asignatura': 'Profesor por Asignatura'
        }
        return roles.get(self.rol, self.rol)
    
    def get_imagen_perfil_url(self):
        """Obtener URL de la imagen de perfil o ícono por defecto"""
        if self.imagen_perfil and os.path.exists(os.path.join('static', 'uploads', 'perfiles', self.imagen_perfil)):
            return f'/static/uploads/perfiles/{self.imagen_perfil}'
        return None  # Retornar None para usar ícono por defecto
    
    def get_carrera_nombre(self):
        """Obtener nombre de la(s) carrera(s)"""
        if not self.carreras:
            return 'Sin carrera asignada'
        if len(self.carreras) == 1:
            return self.carreras[0].nombre
        else:
            return ', '.join([c.nombre for c in self.carreras])
    
    def get_carrera_codigo(self):
        """Obtener código de la(s) carrera(s)"""
        if not self.carreras:
            return 'N/A'
        if len(self.carreras) == 1:
            return self.carreras[0].codigo
        else:
            return ', '.join([c.codigo for c in self.carreras])
    
    def get_info_completa(self):
        """Obtener información completa del profesor"""
        info = {
            'nombre_completo': self.get_nombre_completo(),
            'rol': self.get_rol_display(),
            'carrera': self.get_carrera_nombre(),
            'codigo_carrera': self.get_carrera_codigo(),
            'email': self.email,
            'telefono': self.telefono or 'No especificado',
            'fecha_registro': self.fecha_registro.strftime('%d/%m/%Y')
        }
        return info
    
    def puede_acceder_carrera(self, carrera_id):
        """Verificar si el jefe de carrera puede acceder a una carrera específica"""
        if self.is_admin():
            return True
        if self.is_jefe_carrera():
            return self.carrera_id == carrera_id
        return False
    
    def get_profesores_carrera(self):
        """Obtener profesores de la carrera del jefe (solo para jefes de carrera)"""
        if not self.is_jefe_carrera() or not self.carrera_id:
            return []
        # Incluir tanto profesores asignados a la carrera como jefes de carrera
        profesores = User.query.filter(
            User.carreras.any(id=self.carrera_id),
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).all()
        
        jefes = User.query.filter(
            User.carrera_id == self.carrera_id,
            User.rol == 'jefe_carrera',
            User.activo == True
        ).all()
        
        return profesores + jefes
    
    def get_materias_carrera(self):
        """Obtener materias de la carrera del jefe (solo para jefes de carrera)"""
        if not self.is_jefe_carrera() or not self.carrera_id:
            return []
        from models import Materia
        return Materia.query.filter(
            Materia.carrera_id == self.carrera_id,
            Materia.activa == True
        ).all()
    
    def get_horarios_academicos_carrera(self):
        """Obtener horarios académicos de la carrera del jefe (solo para jefes de carrera)"""
        if not self.is_jefe_carrera() or not self.carrera_id:
            return []
        from models import HorarioAcademico
        # Para profesores: usar relación many-to-many
        return HorarioAcademico.query.join(User, HorarioAcademico.profesor_id == User.id).filter(
            User.carreras.any(id=self.carrera_id),
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).all()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Horario(db.Model):
    """Modelo para gestionar horarios de la escuela"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Información del horario
    nombre = db.Column(db.String(100), nullable=False)  # Ej: "1ra Hora", "Receso", etc.
    turno = db.Column(db.String(20), nullable=False)    # 'matutino' o 'vespertino'
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    orden = db.Column(db.Integer, nullable=False)       # Para ordenar los horarios
    
    # Metadatos
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relación con el usuario que lo creó
    creador = db.relationship('User', backref=db.backref('horarios_creados', lazy=True))
    
    def __init__(self, nombre, turno, hora_inicio, hora_fin, orden, creado_por):
        self.nombre = nombre
        self.turno = turno
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.orden = orden
        self.creado_por = creado_por
    
    def get_hora_inicio_str(self):
        """Obtener hora de inicio como string formateado"""
        return self.hora_inicio.strftime('%H:%M')
    
    def get_hora_fin_str(self):
        """Obtener hora de fin como string formateado"""
        return self.hora_fin.strftime('%H:%M')
    
    def get_duracion_minutos(self):
        """Calcular duración en minutos"""
        inicio = datetime.combine(datetime.today(), self.hora_inicio)
        fin = datetime.combine(datetime.today(), self.hora_fin)
        return int((fin - inicio).total_seconds() / 60)
    
    def get_turno_display(self):
        """Obtener nombre del turno para mostrar"""
        return 'Matutino' if self.turno == 'matutino' else 'Vespertino'
    
    def __repr__(self):
        return f'<Horario {self.nombre} - {self.turno}>'

class Carrera(db.Model):
    """Modelo para gestionar carreras universitarias"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Información de la carrera
    nombre = db.Column(db.String(150), nullable=False, unique=True)
    codigo = db.Column(db.String(10), nullable=False, unique=True)  # Ej: "ING-SIS", "MED", etc.
    descripcion = db.Column(db.Text)
    facultad = db.Column(db.String(100))
    
    # Metadatos
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creada_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relaciones
    creador = db.relationship('User', foreign_keys=[creada_por], backref=db.backref('carreras_creadas', lazy=True))
    
    def __init__(self, nombre, codigo, descripcion=None, facultad=None, creada_por=None):
        self.nombre = nombre
        self.codigo = codigo
        self.descripcion = descripcion
        self.facultad = facultad
        self.creada_por = creada_por
    
    def get_profesores_count(self):
        """Obtener cantidad de profesores en esta carrera"""
        # Para profesores: usar relación many-to-many
        profesores_many_to_many = User.query.filter(
            User.carreras.any(id=self.id),
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).count()
        
        # Para jefes de carrera asignados a esta carrera: usar carrera_id
        jefes_carrera = User.query.filter(
            User.carrera_id == self.id,
            User.rol == 'jefe_carrera',
            User.activo == True
        ).count()
        
        return profesores_many_to_many + jefes_carrera
    
    def get_profesores_completos_count(self):
        """Obtener cantidad de profesores de tiempo completo"""
        return User.query.filter(
            User.carreras.any(id=self.id),
            User.rol == 'profesor_completo',
            User.activo == True
        ).count()
    
    def get_profesores_asignatura_count(self):
        """Obtener cantidad de profesores por asignatura"""
        return User.query.filter(
            User.carreras.any(id=self.id),
            User.rol == 'profesor_asignatura',
            User.activo == True
        ).count()
    
    def get_jefe_carrera(self):
        """Obtener el jefe de carrera asignado a esta carrera"""
        return User.query.filter(
            User.carrera_id == self.id,
            User.rol == 'jefe_carrera',
            User.activo == True
        ).first()
    
    def tiene_jefe_carrera(self):
        """Verificar si la carrera tiene un jefe asignado"""
        return self.get_jefe_carrera() is not None
    
    def get_jefe_carrera_nombre(self):
        """Obtener el nombre del jefe de carrera"""
        jefe = self.get_jefe_carrera()
        return jefe.get_nombre_completo() if jefe else 'Sin asignar'
    
    def __repr__(self):
        return f'<Carrera {self.codigo} - {self.nombre}>'

def init_db():
    """Inicializar la base de datos y crear un usuario admin por defecto"""
    db.create_all()
    
    # Crear usuario admin por defecto si no existe
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@sistema.com',
            password='admin123',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuario administrador creado: admin/admin123")
    
    # Crear horarios por defecto si no existen
    if Horario.query.count() == 0:
        horarios_matutino = [
            Horario('1ra Hora', 'matutino', time(7, 0), time(7, 50), 1, admin.id),
            Horario('2da Hora', 'matutino', time(7, 50), time(8, 40), 2, admin.id),
            Horario('Receso', 'matutino', time(8, 40), time(9, 0), 3, admin.id),
            Horario('3ra Hora', 'matutino', time(9, 0), time(9, 50), 4, admin.id),
            Horario('4ta Hora', 'matutino', time(9, 50), time(10, 40), 5, admin.id),
            Horario('5ta Hora', 'matutino', time(10, 40), time(11, 30), 6, admin.id),
            Horario('6ta Hora', 'matutino', time(11, 30), time(12, 20), 7, admin.id),
        ]
        
        horarios_vespertino = [
            Horario('1ra Hora', 'vespertino', time(13, 0), time(13, 50), 1, admin.id),
            Horario('2da Hora', 'vespertino', time(13, 50), time(14, 40), 2, admin.id),
            Horario('Receso', 'vespertino', time(14, 40), time(15, 0), 3, admin.id),
            Horario('3ra Hora', 'vespertino', time(15, 0), time(15, 50), 4, admin.id),
            Horario('4ta Hora', 'vespertino', time(15, 50), time(16, 40), 5, admin.id),
            Horario('5ta Hora', 'vespertino', time(16, 40), time(17, 30), 6, admin.id),
            Horario('6ta Hora', 'vespertino', time(17, 30), time(18, 20), 7, admin.id),
        ]
        
        for horario in horarios_matutino + horarios_vespertino:
            db.session.add(horario)
        
        db.session.commit()
        print("Horarios por defecto creados")
    
    # Crear carreras por defecto si no existen
    if Carrera.query.count() == 0:
        carreras_defecto = [
            Carrera('Ingeniería en Sistemas', 'ING-SIS', 'Carrera de ingeniería en sistemas computacionales', 'Facultad de Ingeniería', admin.id),
            Carrera('Medicina', 'MED', 'Carrera de medicina general', 'Facultad de Medicina', admin.id),
            Carrera('Derecho', 'DER', 'Carrera de ciencias jurídicas', 'Facultad de Derecho', admin.id),
            Carrera('Administración de Empresas', 'ADM', 'Carrera de administración y gestión empresarial', 'Facultad de Ciencias Económicas', admin.id),
            Carrera('Psicología', 'PSI', 'Carrera de psicología clínica y educativa', 'Facultad de Humanidades', admin.id),
            Carrera('Arquitectura', 'ARQ', 'Carrera de diseño arquitectónico', 'Facultad de Arquitectura', admin.id),
            Carrera('Enfermería', 'ENF', 'Carrera de enfermería profesional', 'Facultad de Ciencias de la Salud', admin.id),
            Carrera('Contaduría Pública', 'CPN', 'Carrera de contaduría y auditoría', 'Facultad de Ciencias Económicas', admin.id),
        ]
        
        for carrera in carreras_defecto:
            db.session.add(carrera)
        
        db.session.commit()
        print("Carreras por defecto creadas")
    
    # Crear materias por defecto si no existen
    if Materia.query.count() == 0:
        # Obtener IDs de carreras para crear materias
        ing_sis = Carrera.query.filter_by(codigo='ING-SIS').first()
        med = Carrera.query.filter_by(codigo='MED').first()
        
        if ing_sis:
            materias_ingenieria = [
                Materia('Introducción a la Programación', 'ISI-101', 1, ing_sis.id, 4, 3, 2, 'Fundamentos de programación', admin.id),
                Materia('Matemáticas Discretas', 'MAT-101', 1, ing_sis.id, 3, 3, 0, 'Lógica y matemáticas básicas', admin.id),
                Materia('Estructuras de Datos', 'ISI-201', 2, ing_sis.id, 4, 3, 2, 'Algoritmos y estructuras de datos', admin.id),
                Materia('Base de Datos', 'ISI-301', 3, ing_sis.id, 4, 3, 2, 'Sistemas de gestión de bases de datos', admin.id),
                Materia('Ingeniería de Software', 'ISI-401', 4, ing_sis.id, 4, 3, 2, 'Metodologías de desarrollo de software', admin.id),
            ]
            
            for materia in materias_ingenieria:
                db.session.add(materia)
        
        if med:
            materias_medicina = [
                Materia('Anatomía Humana', 'MED-101', 1, med.id, 5, 4, 2, 'Estudio del cuerpo humano', admin.id),
                Materia('Bioquímica', 'MED-102', 1, med.id, 4, 3, 2, 'Química de los procesos biológicos', admin.id),
                Materia('Fisiología', 'MED-201', 2, med.id, 5, 4, 2, 'Funcionamiento de los sistemas del cuerpo', admin.id),
                Materia('Patología General', 'MED-301', 3, med.id, 4, 3, 1, 'Estudio de las enfermedades', admin.id),
            ]
            
            for materia in materias_medicina:
                db.session.add(materia)
        
        db.session.commit()
        print("Materias por defecto creadas")

class Materia(db.Model):
    """Modelo para gestionar materias académicas"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Información básica de la materia
    nombre = db.Column(db.String(200), nullable=False)
    codigo = db.Column(db.String(20), nullable=False, unique=True)  # Ej: "ISI-101", "MAT-201"
    descripcion = db.Column(db.Text)
    
    # Información académica
    cuatrimestre = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    creditos = db.Column(db.Integer, nullable=False, default=3)
    horas_teoricas = db.Column(db.Integer, nullable=False, default=0)
    horas_practicas = db.Column(db.Integer, nullable=False, default=0)
    
    # Relaciones
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'), nullable=False)
    carrera = db.relationship('Carrera', backref=db.backref('materias', lazy=True))
    
    # Metadatos
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relación con el usuario que la creó
    creador = db.relationship('User', backref=db.backref('materias_creadas', lazy=True))
    
    def __init__(self, nombre, codigo, cuatrimestre, carrera_id, creditos=3, 
                 horas_teoricas=0, horas_practicas=0, descripcion=None, creado_por=None):
        self.nombre = nombre
        self.codigo = codigo.upper()
        self.cuatrimestre = cuatrimestre
        self.carrera_id = carrera_id
        self.creditos = creditos
        self.horas_teoricas = horas_teoricas
        self.horas_practicas = horas_practicas
        self.descripcion = descripcion
        self.creado_por = creado_por
    
    def get_horas_totales(self):
        """Obtener total de horas (teóricas + prácticas)"""
        return self.horas_teoricas + self.horas_practicas
    
    def get_cuatrimestre_display(self):
        """Obtener nombre del cuatrimestre para mostrar"""
        return f"Cuatrimestre {self.cuatrimestre}"
    
    def get_carrera_nombre(self):
        """Obtener nombre de la carrera"""
        return self.carrera.nombre if self.carrera else 'Carrera no encontrada'
    
    def get_carrera_codigo(self):
        """Obtener código de la carrera"""
        return self.carrera.codigo if self.carrera else 'N/A'
    
    def __repr__(self):
        return f'<Materia {self.codigo} - {self.nombre}>'

class HorarioAcademico(db.Model):
    """Modelo para gestionar horarios académicos generados (asignaciones profesor-materia-horario)"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones principales
    profesor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)
    
    # Información adicional
    dia_semana = db.Column(db.String(10), nullable=False)  # 'lunes', 'martes', etc.
    aula = db.Column(db.String(20))  # Ej: "A101", "Lab1", etc.
    periodo_academico = db.Column(db.String(20), default='2025-1')  # Ej: "2025-1", "2025-2"
    
    # Metadatos
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relaciones
    profesor = db.relationship('User', foreign_keys=[profesor_id], backref=db.backref('horarios_academicos', lazy=True))
    materia = db.relationship('Materia', backref=db.backref('horarios_academicos', lazy=True))
    horario = db.relationship('Horario', backref=db.backref('horarios_academicos', lazy=True))
    creador = db.relationship('User', foreign_keys=[creado_por], backref=db.backref('horarios_creados_academicos', lazy=True))
    
    def __init__(self, profesor_id, materia_id, horario_id, dia_semana, aula=None, 
                 periodo_academico='2025-1', creado_por=None):
        self.profesor_id = profesor_id
        self.materia_id = materia_id
        self.horario_id = horario_id
        self.dia_semana = dia_semana.lower()
        self.aula = aula
        self.periodo_academico = periodo_academico
        self.creado_por = creado_por
    
    def get_dia_display(self):
        """Obtener nombre del día para mostrar"""
        dias = {
            'lunes': 'Lunes',
            'martes': 'Martes',
            'miercoles': 'Miércoles',
            'jueves': 'Jueves',
            'viernes': 'Viernes',
            'sabado': 'Sábado',
            'domingo': 'Domingo'
        }
        return dias.get(self.dia_semana, self.dia_semana.title())
    
    def get_hora_inicio_str(self):
        """Obtener hora de inicio del horario"""
        return self.horario.get_hora_inicio_str() if self.horario else 'N/A'
    
    def get_hora_fin_str(self):
        """Obtener hora de fin del horario"""
        return self.horario.get_hora_fin_str() if self.horario else 'N/A'
    
    def get_profesor_nombre(self):
        """Obtener nombre completo del profesor"""
        return self.profesor.get_nombre_completo() if self.profesor else 'Profesor no asignado'
    
    def get_materia_nombre(self):
        """Obtener nombre de la materia"""
        return self.materia.nombre if self.materia else 'Materia no asignada'
    
    def get_materia_codigo(self):
        """Obtener código de la materia"""
        return self.materia.codigo if self.materia else 'N/A'
    
    def get_turno_display(self):
        """Obtener turno del horario"""
        return self.horario.get_turno_display() if self.horario else 'N/A'
    
    def __repr__(self):
        return f'<HorarioAcademico {self.get_materia_codigo()} - {self.get_profesor_nombre()} - {self.get_dia_display()} {self.get_hora_inicio_str()}>'

class DisponibilidadProfesor(db.Model):
    """Modelo para gestionar la disponibilidad de profesores"""
    id = db.Column(db.Integer, primary_key=True)

    # Relaciones
    profesor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)

    # Información de disponibilidad
    dia_semana = db.Column(db.String(10), nullable=False)  # 'lunes', 'martes', etc.
    disponible = db.Column(db.Boolean, default=True)

    # Metadatos
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relaciones
    profesor = db.relationship('User', foreign_keys=[profesor_id], backref=db.backref('disponibilidades', lazy=True))
    horario = db.relationship('Horario', backref=db.backref('disponibilidades_profesores', lazy=True))
    creador = db.relationship('User', foreign_keys=[creado_por], backref=db.backref('disponibilidades_creadas', lazy=True))

    def __init__(self, profesor_id, horario_id, dia_semana, disponible=True, creado_por=None):
        self.profesor_id = profesor_id
        self.horario_id = horario_id
        self.dia_semana = dia_semana.lower()
        self.disponible = disponible
        self.creado_por = creado_por

    def get_dia_display(self):
        """Obtener nombre del día para mostrar"""
        dias = {
            'lunes': 'Lunes',
            'martes': 'Martes',
            'miercoles': 'Miércoles',
            'jueves': 'Jueves',
            'viernes': 'Viernes',
            'sabado': 'Sábado',
            'domingo': 'Domingo'
        }
        return dias.get(self.dia_semana, self.dia_semana.title())

    def get_profesor_nombre(self):
        """Obtener nombre completo del profesor"""
        return self.profesor.get_nombre_completo() if self.profesor else 'Profesor no encontrado'

    def get_hora_inicio_str(self):
        """Obtener hora de inicio del horario"""
        return self.horario.get_hora_inicio_str() if self.horario else 'N/A'

    def get_hora_fin_str(self):
        """Obtener hora de fin del horario"""
        return self.horario.get_hora_fin_str() if self.horario else 'N/A'

    def __repr__(self):
        return f'<DisponibilidadProfesor {self.get_profesor_nombre()} - {self.get_dia_display()} {self.get_hora_inicio_str()} - {"Disponible" if self.disponible else "No disponible"}>'


def init_upload_dirs():
    """Inicializar directorios para subir archivos"""
    dirs = [
        'static/uploads',
        'static/uploads/perfiles'
    ]

    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Directorio creado: {dir_path}")


class ConfiguracionSistema(db.Model):
    """Modelo para almacenar configuraciones del sistema"""
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'string', 'int', 'bool', 'json'
    descripcion = db.Column(db.String(255))
    categoria = db.Column(db.String(50), nullable=False)  # 'database', 'backup', 'general', 'security'
    editable = db.Column(db.Boolean, default=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, clave, valor, tipo='string', descripcion='', categoria='general', editable=True):
        self.clave = clave
        self.valor = valor
        self.tipo = tipo
        self.descripcion = descripcion
        self.categoria = categoria
        self.editable = editable

    @staticmethod
    def get_config(clave, default=None):
        """Obtener valor de configuración"""
        config = ConfiguracionSistema.query.filter_by(clave=clave).first()
        if config:
            if config.tipo == 'int':
                return int(config.valor) if config.valor else default
            elif config.tipo == 'bool':
                return config.valor.lower() == 'true' if config.valor else default
            elif config.tipo == 'json':
                import json
                return json.loads(config.valor) if config.valor else default
            else:
                return config.valor
        return default

    @staticmethod
    def set_config(clave, valor, tipo='string', descripcion='', categoria='general', editable=True):
        """Establecer valor de configuración"""
        config = ConfiguracionSistema.query.filter_by(clave=clave).first()
        if not config:
            config = ConfiguracionSistema(clave, str(valor), tipo, descripcion, categoria, editable)
            db.session.add(config)
        else:
            config.valor = str(valor)
            config.tipo = tipo
            config.descripcion = descripcion
            config.categoria = categoria
            config.editable = editable
        db.session.commit()
        return config

    @staticmethod
    def get_configs_by_category(categoria):
        """Obtener todas las configuraciones de una categoría"""
        return ConfiguracionSistema.query.filter_by(categoria=categoria).all()


class BackupHistory(db.Model):
    """Modelo para almacenar historial de backups"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'manual', 'automatico'
    tamano = db.Column(db.Integer)  # Tamaño en bytes
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='completado')  # 'completado', 'error', 'en_progreso'
    ruta_archivo = db.Column(db.String(500))
    checksum = db.Column(db.String(64))  # Hash SHA256 del archivo
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    usuario = db.relationship('User', backref=db.backref('backups', lazy=True))

    def __init__(self, filename, tipo='manual', tamano=None, ruta_archivo=None, usuario_id=None):
        self.filename = filename
        self.tipo = tipo
        self.tamano = tamano
        self.ruta_archivo = ruta_archivo
        self.usuario_id = usuario_id

    def get_tamano_formateado(self):
        """Obtener tamaño formateado en MB/KB"""
        if not self.tamano:
            return 'N/A'
        if self.tamano > 1024 * 1024:
            return '.1f'
        elif self.tamano > 1024:
            return '.1f'
        else:
            return f"{self.tamano} B"

    def get_fecha_formateada(self):
        """Obtener fecha formateada"""
        return self.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if self.fecha_creacion else 'N/A'