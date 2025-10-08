from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Horario, Carrera, Materia, HorarioAcademico, DisponibilidadProfesor, init_db, init_upload_dirs
from forms import (LoginForm, RegistrationForm, HorarioForm, EliminarHorarioForm, 
                   CarreraForm, ImportarProfesoresForm, FiltrarProfesoresForm, ExportarProfesoresForm,
                   MateriaForm, ImportarMateriasForm, FiltrarMateriasForm, ExportarMateriasForm,
                   GenerarHorariosForm, EditarHorarioAcademicoForm, EliminarHorarioAcademicoForm,
                   DisponibilidadProfesorForm, EditarDisponibilidadProfesorForm, AgregarProfesorForm,
                   EditarUsuarioForm)
from utils import procesar_archivo_profesores, generar_pdf_profesores, procesar_archivo_materias, generar_pdf_materias, generar_plantilla_csv
from datetime import time, datetime
import os
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import csv

app = Flask(__name__)

# Configuración de la aplicación
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui_cambiala_en_produccion'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_academico.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario por ID para Flask-Login"""
    return User.query.get(int(user_id))

# Rutas principales
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if user.activo:
                login_user(user)
                flash(f'¡Bienvenido, {user.get_nombre_completo()}!', 'success')
                
                # Redirigir a la página solicitada o al dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Obtener el rol final (considerando tipo de profesor)
            rol_final = form.get_final_rol()
            
            # Para profesores y jefes de carrera, obtener las carreras seleccionadas
            carreras = []
            carrera_id = None
            if rol_final in ['profesor_completo', 'profesor_asignatura', 'jefe_carrera'] and form.carrera.data:
                carreras = Carrera.query.filter(Carrera.id.in_(form.carrera.data)).all()
                if rol_final == 'jefe_carrera' and carreras:
                    carrera_id = carreras[0].id
            
            # Crear nuevo usuario
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                rol=rol_final,
                telefono=form.telefono.data if form.telefono.data else None,
                carreras=carreras,
                carrera_id=carrera_id
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'¡Registro exitoso! Bienvenido, {user.get_nombre_completo()}.', 'success')
            
            # Iniciar sesión automáticamente después del registro
            login_user(user)
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta. Inténtalo de nuevo.', 'error')
            print(f"Error en registro: {e}")
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal para usuarios autenticados"""
    # Obtener estadísticas para mostrar en el dashboard
    user_count = User.query.count()
    admin_count = User.query.filter_by(rol='admin').count()
    jefe_count = User.query.filter_by(rol='jefe_carrera').count()
    profesor_completo_count = User.query.filter_by(rol='profesor_completo').count()
    profesor_asignatura_count = User.query.filter_by(rol='profesor_asignatura').count()
    profesor_count = profesor_completo_count + profesor_asignatura_count
    
    return render_template('dashboard.html',
                         user_count=user_count,
                         admin_count=admin_count,
                         jefe_count=jefe_count,
                         profesor_count=profesor_count)

@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    name = current_user.get_nombre_completo()
    logout_user()
    flash(f'¡Hasta luego, {name}!', 'info')
    return redirect(url_for('index'))

# Rutas para diferentes roles (ejemplos básicos)
@app.route('/admin')
@login_required
def admin_panel():
    """Panel de administración - solo para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin/panel.html', users=users)

# @app.route('/jefe-carrera')
# @login_required
# def jefe_carrera_panel():
#     """Panel para jefes de carrera"""
#     if not current_user.is_jefe_carrera():
#         flash('No tienes permisos para acceder a esta página.', 'error')
#         return redirect(url_for('dashboard'))
#     
#     # Verificar que el jefe tenga una carrera asignada
#     if not current_user.carrera_id:
#         flash('No tienes una carrera asignada. Contacta al administrador.', 'warning')
#         return redirect(url_for('dashboard'))
#     
#     # Obtener datos específicos de la carrera del jefe
#     profesores = current_user.get_profesores_carrera()
#     materias = current_user.get_materias_carrera()
#     horarios_academicos = current_user.get_horarios_academicos_carrera()
#     
#     return render_template('jefe/panel.html', 
#                          profesores=profesores, 
#                          materias=materias,
#                          horarios_academicos=horarios_academicos,
#                          carrera=current_user.carrera)

# ==========================================
# GESTIÓN DE PROFESORES PARA JEFES DE CARRERA
# ==========================================

@app.route('/jefe-carrera/profesores')
@login_required
def gestionar_profesores_jefe():
    """Gestión de profesores para jefes de carrera (solo su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    if not current_user.carrera_id:
        flash('No tienes una carrera asignada. Contacta al administrador.', 'warning')
        return redirect(url_for('dashboard'))
    
    profesores = current_user.get_profesores_carrera()
    return render_template('jefe/profesores.html', profesores=profesores, carrera=current_user.carrera)

@app.route('/jefe-carrera/profesor/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_profesor_jefe(id):
    """Editar profesor para jefes de carrera (solo de su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    profesor = User.query.get_or_404(id)
    
    # Verificar que el profesor pertenezca a la carrera del jefe
    # Para profesores: verificar si está asignado a la carrera del jefe
    if profesor.is_profesor():
        if not any(carrera.id == current_user.carrera_id for carrera in profesor.carreras):
            flash('No tienes permisos para editar este profesor.', 'error')
            return redirect(url_for('gestionar_profesores_jefe'))
    # Para jefes de carrera: verificar que sea de la misma carrera
    elif profesor.is_jefe_carrera():
        if profesor.carrera_id != current_user.carrera_id:
            flash('No tienes permisos para editar este jefe de carrera.', 'error')
            return redirect(url_for('gestionar_profesores_jefe'))
    
    form = EditarUsuarioForm()
    if form.validate_on_submit():
        profesor.nombre = form.nombre.data
        profesor.apellido = form.apellido.data
        profesor.email = form.email.data
        profesor.telefono = form.telefono.data
        profesor.rol = form.rol.data
        profesor.tipo_profesor = form.tipo_profesor.data if form.rol.data in ['profesor_completo', 'profesor_asignatura'] else None
        
        db.session.commit()
        flash('Profesor actualizado exitosamente.', 'success')
        return redirect(url_for('gestionar_profesores_jefe'))
    
    # Pre-llenar el formulario
    form.nombre.data = profesor.nombre
    form.apellido.data = profesor.apellido
    form.email.data = profesor.email
    form.telefono.data = profesor.telefono
    form.rol.data = profesor.rol
    form.tipo_profesor.data = profesor.tipo_profesor
    
    return render_template('jefe/editar_profesor.html', form=form, profesor=profesor)

@app.route('/jefe-carrera/profesor/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_profesor_jefe(id):
    """Eliminar profesor para jefes de carrera (solo de su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    profesor = User.query.get_or_404(id)
    
    # Verificar que el profesor pertenezca a la carrera del jefe
    # Para profesores: verificar si está asignado a la carrera del jefe
    if profesor.is_profesor():
        if not any(carrera.id == current_user.carrera_id for carrera in profesor.carreras):
            flash('No tienes permisos para eliminar este profesor.', 'error')
            return redirect(url_for('gestionar_profesores_jefe'))
    # Para jefes de carrera: verificar que sea de la misma carrera
    elif profesor.is_jefe_carrera():
        if profesor.carrera_id != current_user.carrera_id:
            flash('No tienes permisos para eliminar este jefe de carrera.', 'error')
            return redirect(url_for('gestionar_profesores_jefe'))
    
    # Desactivar en lugar de eliminar
    profesor.activo = False
    db.session.commit()
    
    flash('Profesor eliminado exitosamente.', 'success')
    return redirect(url_for('gestionar_profesores_jefe'))

# ==========================================
# GESTIÓN DE MATERIAS PARA JEFES DE CARRERA
# ==========================================

@app.route('/jefe-carrera/materias')
@login_required
def gestionar_materias_jefe():
    """Gestión de materias para jefes de carrera (solo su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    if not current_user.carrera_id:
        flash('No tienes una carrera asignada. Contacta al administrador.', 'warning')
        return redirect(url_for('dashboard'))
    
    materias = current_user.get_materias_carrera()
    return render_template('jefe/materias.html', materias=materias, carrera=current_user.carrera)

@app.route('/jefe-carrera/materia/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_materia_jefe(id):
    """Editar materia para jefes de carrera (solo de su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    materia = Materia.query.get_or_404(id)
    
    # Verificar que la materia pertenezca a la carrera del jefe
    if not current_user.puede_acceder_carrera(materia.carrera_id):
        flash('No tienes permisos para editar esta materia.', 'error')
        return redirect(url_for('gestionar_materias_jefe'))
    
    form = MateriaForm()
    if form.validate_on_submit():
        materia.nombre = form.nombre.data
        materia.codigo = form.codigo.data.upper()
        materia.descripcion = form.descripcion.data
        materia.cuatrimestre = form.cuatrimestre.data
        materia.creditos = form.creditos.data
        materia.horas_teoricas = form.horas_teoricas.data
        materia.horas_practicas = form.horas_practicas.data
        
        db.session.commit()
        flash('Materia actualizada exitosamente.', 'success')
        return redirect(url_for('gestionar_materias_jefe'))
    
    # Pre-llenar el formulario
    form.nombre.data = materia.nombre
    form.codigo.data = materia.codigo
    form.descripcion.data = materia.descripcion
    form.cuatrimestre.data = materia.cuatrimestre
    form.creditos.data = materia.creditos
    form.horas_teoricas.data = materia.horas_teoricas
    form.horas_practicas.data = materia.horas_practicas
    
    return render_template('jefe/editar_materia.html', form=form, materia=materia)

# ==========================================
# GESTIÓN DE HORARIOS ACADÉMICOS PARA JEFES DE CARRERA
# ==========================================

@app.route('/jefe-carrera/horarios-academicos')
@login_required
def gestionar_horarios_academicos_jefe():
    """Gestión de horarios académicos para jefes de carrera (solo su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    if not current_user.carrera_id:
        flash('No tienes una carrera asignada. Contacta al administrador.', 'warning')
        return redirect(url_for('dashboard'))
    
    horarios_academicos = current_user.get_horarios_academicos_carrera()
    return render_template('jefe/horarios_academicos.html', 
                         horarios_academicos=horarios_academicos, 
                         carrera=current_user.carrera)

@app.route('/jefe-carrera/horario-academico/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_horario_academico_jefe(id):
    """Editar horario académico para jefes de carrera (solo de su carrera)"""
    if not current_user.is_jefe_carrera():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    horario_academico = HorarioAcademico.query.get_or_404(id)
    
    # Verificar que el horario pertenezca a la carrera del jefe
    # Verificar si el profesor del horario está asignado a la carrera del jefe
    profesor = horario_academico.profesor
    if profesor.is_profesor():
        if not any(carrera.id == current_user.carrera_id for carrera in profesor.carreras):
            flash('No tienes permisos para editar este horario académico.', 'error')
            return redirect(url_for('gestionar_horarios_academicos_jefe'))
    elif profesor.is_jefe_carrera():
        if profesor.carrera_id != current_user.carrera_id:
            flash('No tienes permisos para editar este horario académico.', 'error')
            return redirect(url_for('gestionar_horarios_academicos_jefe'))
        flash('No tienes permisos para editar este horario académico.', 'error')
        return redirect(url_for('gestionar_horarios_academicos_jefe'))
    
    form = EditarHorarioAcademicoForm()
    if form.validate_on_submit():
        horario_academico.horario_id = form.horario_id.data
        horario_academico.aula = form.aula.data
        horario_academico.dia_semana = form.dia_semana.data
        
        db.session.commit()
        flash('Horario académico actualizado exitosamente.', 'success')
        return redirect(url_for('gestionar_horarios_academicos_jefe'))
    
    # Pre-llenar el formulario
    form.horario_id.data = horario_academico.horario_id
    form.aula.data = horario_academico.aula
    form.dia_semana.data = horario_academico.dia_semana
    
    return render_template('jefe/editar_horario_academico.html', 
                         form=form, 
                         horario_academico=horario_academico)

@app.route('/profesor')
@login_required
def profesor_panel():
    """Panel para profesores"""
    if not current_user.is_profesor():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('profesor/panel.html')

@app.route('/profesor/horarios')
@login_required
def profesor_horarios():
    """Ver horarios asignados al profesor"""
    if not current_user.is_profesor():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener horarios académicos del profesor actual
    horarios = HorarioAcademico.query.filter_by(
        profesor_id=current_user.id,
        activo=True
    ).join(Horario).order_by(
        Horario.orden,
        HorarioAcademico.dia_semana
    ).all()
    
    # Organizar horarios por día de la semana
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
    horarios_por_dia = {}
    
    for dia in dias_semana:
        horarios_por_dia[dia] = [h for h in horarios if h.dia_semana == dia]
    
    # Estadísticas del profesor
    total_horas = len(horarios)
    materias_unicas = len(set(h.materia_id for h in horarios))
    
    return render_template('profesor/horarios.html', 
                         horarios_por_dia=horarios_por_dia,
                         total_horas=total_horas,
                         materias_unicas=materias_unicas,
                         dias_semana=dias_semana)

# Rutas de gestión de horarios (solo administradores)
@app.route('/admin/horarios')
@login_required
def gestionar_horarios():
    """Gestión de horarios - solo para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener horarios separados por turno y ordenados
    horarios_matutino = Horario.query.filter_by(turno='matutino', activo=True).order_by(Horario.orden).all()
    horarios_vespertino = Horario.query.filter_by(turno='vespertino', activo=True).order_by(Horario.orden).all()
    
    return render_template('admin/horarios.html', 
                         horarios_matutino=horarios_matutino,
                         horarios_vespertino=horarios_vespertino)

@app.route('/admin/horarios/agregar', methods=['GET', 'POST'])
@login_required
def agregar_horario():
    """Agregar nuevo horario - solo para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = HorarioForm()
    
    if form.validate_on_submit():
        try:
            horario = Horario(
                nombre=form.nombre.data,
                turno=form.turno.data,
                hora_inicio=form.hora_inicio.data,
                hora_fin=form.hora_fin.data,
                orden=form.orden.data,
                creado_por=current_user.id
            )
            
            db.session.add(horario)
            db.session.commit()
            
            flash(f'Horario "{horario.nombre}" agregado exitosamente.', 'success')
            return redirect(url_for('gestionar_horarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el horario. Inténtalo de nuevo.', 'error')
            print(f"Error en agregar horario: {e}")
    
    return render_template('admin/horario_form.html', form=form, horario=None)

@app.route('/admin/horarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_horario(id):
    """Editar horario existente - solo para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    horario = Horario.query.get_or_404(id)
    
    if not horario.activo:
        flash('No se puede editar un horario inactivo.', 'error')
        return redirect(url_for('gestionar_horarios'))
    
    form = HorarioForm(obj=horario)
    
    # Agregar ID del horario al formulario para validaciones
    form._horario_id = horario.id
    
    if form.validate_on_submit():
        try:
            horario.nombre = form.nombre.data
            horario.turno = form.turno.data
            horario.hora_inicio = form.hora_inicio.data
            horario.hora_fin = form.hora_fin.data
            horario.orden = form.orden.data
            
            db.session.commit()
            
            flash(f'Horario "{horario.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('gestionar_horarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el horario. Inténtalo de nuevo.', 'error')
            print(f"Error en editar horario: {e}")
    
    return render_template('admin/horario_form.html', form=form, horario=horario)

@app.route('/admin/horarios/eliminar/<int:id>', methods=['GET', 'POST'])
@login_required
def eliminar_horario(id):
    """Eliminar horario - solo para administradores"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    horario = Horario.query.get_or_404(id)
    
    if not horario.activo:
        flash('Este horario ya está eliminado.', 'warning')
        return redirect(url_for('gestionar_horarios'))
    
    form = EliminarHorarioForm()
    
    if form.validate_on_submit():
        try:
            # Marcar como inactivo en lugar de eliminar físicamente
            horario.activo = False
            db.session.commit()
            
            flash(f'Horario "{horario.nombre}" eliminado exitosamente.', 'success')
            return redirect(url_for('gestionar_horarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al eliminar el horario. Inténtalo de nuevo.', 'error')
            print(f"Error en eliminar horario: {e}")
    
    return render_template('admin/eliminar_horario.html', form=form, horario=horario)

# Rutas para gestión de carreras
@app.route('/admin/carreras')
@login_required
def gestionar_carreras():
    """Gestión de carreras (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
    
    # Calcular estadísticas
    total_profesores = sum(carrera.get_profesores_count() for carrera in carreras)
    promedio_profesores = total_profesores / len(carreras) if carreras else 0
    
    # Estadísticas de jefes de carrera
    carreras_con_jefes = sum(1 for carrera in carreras if carrera.tiene_jefe_carrera())
    carreras_sin_jefes = len(carreras) - carreras_con_jefes
    total_jefes_carrera = User.query.filter_by(rol='jefe_carrera', activo=True).count()
    
    # Obtener facultades únicas
    facultades = set(carrera.facultad for carrera in carreras if carrera.facultad)
    
    # Contar carreras con profesores
    carreras_con_profesores = sum(1 for carrera in carreras if carrera.get_profesores_count() > 0)
    
    return render_template('admin/carreras.html', 
                         carreras=carreras,
                         total_profesores=total_profesores,
                         promedio_profesores=promedio_profesores,
                         carreras_con_jefes=carreras_con_jefes,
                         carreras_sin_jefes=carreras_sin_jefes,
                         total_jefes_carrera=total_jefes_carrera,
                         facultades=facultades,
                         carreras_con_profesores=carreras_con_profesores)

@app.route('/admin/carreras/test')
@login_required
def test_carreras():
    """Página de prueba para carreras"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
    return render_template('admin/carreras_test.html', carreras=carreras)

@app.route('/admin/carreras/nueva', methods=['GET', 'POST'])
@login_required
def nueva_carrera():
    """Crear nueva carrera (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = CarreraForm()
    if form.validate_on_submit():
        try:
            carrera = Carrera(
                nombre=form.nombre.data,
                codigo=form.codigo.data.upper(),
                descripcion=form.descripcion.data,
                facultad=form.facultad.data,
                creada_por=current_user.id
            )
            
            db.session.add(carrera)
            db.session.flush()  # Para obtener el ID de la carrera
            
            # Asignar jefe de carrera si se seleccionó uno
            if form.jefe_carrera_id.data:
                jefe = User.query.get(form.jefe_carrera_id.data)
                if jefe:
                    jefe.rol = 'jefe_carrera'
                    jefe.carrera_id = carrera.id
            
            db.session.commit()
            
            mensaje = f'Carrera "{carrera.nombre}" creada exitosamente.'
            if form.jefe_carrera_id.data:
                jefe = User.query.get(form.jefe_carrera_id.data)
                mensaje += f' Jefe de carrera asignado: {jefe.get_nombre_completo()}.'
                
            flash(mensaje, 'success')
            return redirect(url_for('gestionar_carreras'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la carrera. Inténtalo de nuevo.', 'error')
            print(f"Error en nueva carrera: {e}")
    
    return render_template('admin/carrera_form.html', form=form, titulo="Nueva Carrera")

@app.route('/admin/carreras/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_carrera(id):
    """Editar carrera existente (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    carrera = Carrera.query.get_or_404(id)
    if not carrera.activa:
        flash('Esta carrera no está disponible.', 'error')
        return redirect(url_for('gestionar_carreras'))
    
    # Crear formulario sin usar obj=carrera para evitar conflictos
    form = CarreraForm()
    form._carrera_id = carrera.id  # Para validación de código único
    
    # Cargar datos manualmente en GET
    if request.method == 'GET':
        form.nombre.data = carrera.nombre
        form.codigo.data = carrera.codigo
        form.descripcion.data = carrera.descripcion
        form.facultad.data = carrera.facultad
        
        # Cargar el jefe de carrera actual
        jefe_actual = carrera.get_jefe_carrera()
        if jefe_actual:
            form.jefe_carrera_id.data = str(jefe_actual.id)
        else:
            form.jefe_carrera_id.data = ''
    
    if form.validate_on_submit():
        try:
            # Actualizar datos básicos de la carrera
            carrera.nombre = form.nombre.data
            carrera.codigo = form.codigo.data.upper()
            carrera.descripcion = form.descripcion.data
            carrera.facultad = form.facultad.data
            
            # Manejar cambio de jefe de carrera
            nuevo_jefe_id = form.jefe_carrera_id.data
            jefe_anterior = carrera.get_jefe_carrera()
            
            # Remover rol de jefe_carrera del usuario anterior si existe
            if jefe_anterior:
                jefe_anterior.rol = 'profesor'  # Cambiar a profesor regular
                jefe_anterior.carrera_id = carrera.id  # Mantener en la misma carrera
            
            # Asignar nuevo jefe de carrera si se seleccionó uno
            if nuevo_jefe_id:
                nuevo_jefe = User.query.get(nuevo_jefe_id)
                if nuevo_jefe:
                    nuevo_jefe.rol = 'jefe_carrera'
                    nuevo_jefe.carrera_id = carrera.id
            
            db.session.commit()
            
            mensaje = f'Carrera "{carrera.nombre}" actualizada exitosamente.'
            if jefe_anterior and nuevo_jefe_id and str(jefe_anterior.id) != str(nuevo_jefe_id):
                nuevo_jefe = User.query.get(nuevo_jefe_id)
                mensaje += f' Nuevo jefe de carrera: {nuevo_jefe.get_nombre_completo()}.'
            elif nuevo_jefe_id and not jefe_anterior:
                nuevo_jefe = User.query.get(nuevo_jefe_id)
                mensaje += f' Jefe de carrera asignado: {nuevo_jefe.get_nombre_completo()}.'
            elif not nuevo_jefe_id and jefe_anterior:
                mensaje += f' Se removió el jefe de carrera anterior.'
                
            flash(mensaje, 'success')
            return redirect(url_for('gestionar_carreras'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la carrera. Inténtalo de nuevo.', 'error')
            print(f"Error en editar carrera: {e}")
    
    return render_template('admin/carrera_form.html', form=form, carrera=carrera, titulo="Editar Carrera")

@app.route('/admin/carreras/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_carrera(id):
    """Eliminar carrera (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para realizar esta acción.', 'error')
        return redirect(url_for('gestionar_carreras'))
    
    try:
        carrera = Carrera.query.get_or_404(id)
        
        # Verificar si tiene profesores asignados
        profesores_asignados = User.query.filter_by(carrera_id=id).count()
        if profesores_asignados > 0:
            flash(f'No se puede eliminar la carrera "{carrera.nombre}" porque tiene {profesores_asignados} profesores asignados.', 'error')
            return redirect(url_for('gestionar_carreras'))
        
        # Marcar como inactiva
        carrera.activa = False
        db.session.commit()
        
        flash(f'Carrera "{carrera.nombre}" eliminada exitosamente.', 'success')
        return redirect(url_for('gestionar_carreras'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la carrera. Inténtalo de nuevo.', 'error')
        return redirect(url_for('gestionar_carreras'))

# Rutas para gestión de materias
@app.route('/admin/materias')
@login_required
def gestionar_materias():
    """Gestión de materias (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener filtros
    carrera_id_str = request.args.get('carrera', type=str)
    carrera_id = int(carrera_id_str) if carrera_id_str and carrera_id_str != '0' else None
    cuatrimestre_str = request.args.get('cuatrimestre', type=str)
    cuatrimestre = int(cuatrimestre_str) if cuatrimestre_str and cuatrimestre_str != '' else None
    busqueda = request.args.get('busqueda', '').strip()
    
    # Query base para materias
    query = Materia.query.filter_by(activa=True)
    
    # Aplicar filtros
    if carrera_id:
        query = query.filter(Materia.carrera_id == carrera_id)
    
    if cuatrimestre:
        query = query.filter(Materia.cuatrimestre == cuatrimestre)
    
    if busqueda:
        query = query.filter(
            db.or_(
                Materia.nombre.ilike(f'%{busqueda}%'),
                Materia.codigo.ilike(f'%{busqueda}%'),
                Materia.descripcion.ilike(f'%{busqueda}%')
            )
        )
    
    materias = query.order_by(Materia.cuatrimestre, Materia.nombre).all()
    
    # Obtener carreras para el filtro
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
    
    # Calcular estadísticas
    total_materias = len(materias)
    total_carreras = len(carreras)
    cuatrimestres_unicos = len(set(materia.cuatrimestre for materia in materias)) if materias else 0
    
    # Crear formularios
    filtrar_form = FiltrarMateriasForm()
    filtrar_form.carrera.choices = [(0, 'Todas las carreras')] + [(c.id, c.nombre) for c in carreras]
    
    # Configurar valores por defecto del formulario
    if carrera_id is not None:
        filtrar_form.carrera.data = carrera_id
    else:
        filtrar_form.carrera.data = 0  # Todas las carreras por defecto
    
    if cuatrimestre is not None:
        filtrar_form.cuatrimestre.data = str(cuatrimestre)
    
    exportar_form = ExportarMateriasForm()
    exportar_form.carrera.choices = [('', 'Todas las carreras')] + [(str(c.id), c.nombre) for c in carreras]
    
    return render_template('admin/materias.html', 
                         materias=materias, 
                         carreras=carreras,
                         filtrar_form=filtrar_form,
                         exportar_form=exportar_form,
                         total_materias=total_materias,
                         total_carreras=total_carreras,
                         cuatrimestres_unicos=cuatrimestres_unicos,
                         filtros_activos={
                             'carrera': carrera_id,
                             'cuatrimestre': cuatrimestre,
                             'busqueda': busqueda
                         })

@app.route('/admin/materias/nueva', methods=['GET', 'POST'])
@login_required
def nueva_materia():
    """Crear nueva materia (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = MateriaForm()
    if form.validate_on_submit():
        try:
            materia = Materia(
                nombre=form.nombre.data,
                codigo=form.codigo.data,
                cuatrimestre=form.cuatrimestre.data,
                carrera_id=int(form.carrera.data),
                creditos=form.creditos.data,
                horas_teoricas=form.horas_teoricas.data,
                horas_practicas=form.horas_practicas.data,
                descripcion=form.descripcion.data,
                creado_por=current_user.id
            )
            
            db.session.add(materia)
            db.session.commit()
            
            flash(f'Materia "{materia.nombre}" creada exitosamente.', 'success')
            return redirect(url_for('gestionar_materias'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la materia. Inténtalo de nuevo.', 'error')
            print(f"Error en nueva materia: {e}")
    
    return render_template('admin/materia_form.html', form=form, titulo="Nueva Materia")

@app.route('/admin/materias/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_materia(id):
    """Editar materia existente (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    materia = Materia.query.get_or_404(id)
    if not materia.activa:
        flash('Esta materia no está disponible.', 'error')
        return redirect(url_for('gestionar_materias'))
    
    form = MateriaForm(obj=materia)
    form.carrera.data = str(materia.carrera_id)
    
    # Agregar ID de la materia al formulario para validaciones
    form._materia_id = materia.id
    
    if form.validate_on_submit():
        try:
            materia.nombre = form.nombre.data
            materia.codigo = form.codigo.data
            materia.cuatrimestre = form.cuatrimestre.data
            materia.carrera_id = int(form.carrera.data)
            materia.creditos = form.creditos.data
            materia.horas_teoricas = form.horas_teoricas.data
            materia.horas_practicas = form.horas_practicas.data
            materia.descripcion = form.descripcion.data
            
            db.session.commit()
            
            flash(f'Materia "{materia.nombre}" actualizada exitosamente.', 'success')
            return redirect(url_for('gestionar_materias'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la materia. Inténtalo de nuevo.', 'error')
            print(f"Error en editar materia: {e}")
    
    return render_template('admin/materia_form.html', form=form, materia=materia, titulo="Editar Materia")

@app.route('/admin/materias/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_materia(id):
    """Eliminar materia (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para realizar esta acción.', 'error')
        return redirect(url_for('gestionar_materias'))
    
    try:
        materia = Materia.query.get_or_404(id)
        
        # Marcar como inactiva
        materia.activa = False
        db.session.commit()
        
        flash(f'Materia "{materia.nombre}" eliminada exitosamente.', 'success')
        return redirect(url_for('gestionar_materias'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la materia. Inténtalo de nuevo.', 'error')
        return redirect(url_for('gestionar_materias'))

@app.route('/admin/materias/importar', methods=['GET', 'POST'])
@login_required
def importar_materias():
    """Importar materias desde archivo CSV/Excel (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = ImportarMateriasForm()
    
    if form.validate_on_submit():
        try:
            archivo = form.archivo.data
            carrera_defecto_id = int(form.carrera_defecto.data) if form.carrera_defecto.data else None
            
            resultado = procesar_archivo_materias(archivo, carrera_defecto_id)
            
            if resultado['exito']:
                flash(f"Importación exitosa: {resultado['procesados']} materias procesadas, "
                     f"{resultado['creados']} nuevas, {resultado['actualizados']} actualizadas.", 'success')
                
                if resultado['errores']:
                    flash(f"Se encontraron {len(resultado['errores'])} errores durante la importación.", 'warning')
                    return render_template('admin/importar_materias.html', 
                                         form=form, 
                                         resultado=resultado)
            else:
                flash(f"Error en la importación: {resultado['mensaje']}", 'error')
                
        except Exception as e:
            flash('Error al procesar el archivo. Inténtalo de nuevo.', 'error')
            print(f"Error en importar materias: {e}")
    
    return render_template('admin/importar_materias.html', form=form)

@app.route('/admin/materias/exportar')
@login_required
def exportar_materias():
    """Exportar materias a PDF (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Obtener filtros de la URL
        carrera_id = request.args.get('carrera_id', type=int)
        cuatrimestre = request.args.get('cuatrimestre', type=int)
        
        # Query para materias con filtros
        query = Materia.query.filter_by(activa=True)
        
        if carrera_id:
            query = query.filter(Materia.carrera_id == carrera_id)
        
        if cuatrimestre:
            query = query.filter(Materia.cuatrimestre == cuatrimestre)
        
        materias = query.order_by(Materia.cuatrimestre, Materia.nombre).all()
        
        # Generar PDF
        nombre_carrera = None
        if carrera_id:
            carrera = Carrera.query.get(carrera_id)
            nombre_carrera = carrera.nombre if carrera else None
        
        archivo_pdf = generar_pdf_materias(materias, nombre_carrera, cuatrimestre)
        
        return send_file(archivo_pdf, as_attachment=True, download_name=f'materias_{archivo_pdf.split("/")[-1]}')
        
    except Exception as e:
        flash('Error al generar el PDF. Inténtalo de nuevo.', 'error')
        print(f"Error en exportar materias: {e}")
        return redirect(url_for('gestionar_materias'))

@app.route('/admin/materias/plantilla-csv')
@login_required
def descargar_plantilla_csv_materias():
    """Descargar plantilla CSV para importar materias (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Crear contenido CSV con encabezados y ejemplo
        contenido_csv = """nombre,codigo,cuatrimestre,carrera_codigo,creditos,horas_teoricas,horas_practicas,descripcion
Introducción a la Programación,ISI-101,1,ING-SIS,4,3,2,Fundamentos de programación
Matemáticas Discretas,MAT-101,1,ING-SIS,3,3,0,Lógica y matemáticas básicas
Estructuras de Datos,ISI-201,2,ING-SIS,4,3,2,Algoritmos y estructuras de datos
Anatomía Humana,MED-101,1,MED,5,4,2,Estudio del cuerpo humano"""
        
        # Crear respuesta con archivo CSV
        response = make_response(contenido_csv)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=plantilla_materias.csv'
        
        return response
        
    except Exception as e:
        flash('Error al generar la plantilla. Inténtalo de nuevo.', 'error')
        print(f"Error en descargar plantilla CSV: {e}")
        return redirect(url_for('importar_materias'))

# Rutas para gestión de profesores
@app.route('/admin/profesores')
@login_required
def gestionar_profesores():
    """Gestión de profesores (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener filtros
    carrera_id = request.args.get('carrera_id', type=int)
    tipo_profesor = request.args.get('tipo_profesor')
    busqueda = request.args.get('busqueda', '').strip()
    
    # Query base para profesores
    query = User.query.filter(
        User.rol.in_(['profesor_completo', 'profesor_asignatura']),
        User.activo == True
    )
    
    # Aplicar filtros
    if carrera_id:
        query = query.filter(User.carrera_id == carrera_id)
    
    if tipo_profesor:
        query = query.filter(User.rol == tipo_profesor)
    
    if busqueda:
        query = query.filter(
            db.or_(
                User.nombre.ilike(f'%{busqueda}%'),
                User.apellido.ilike(f'%{busqueda}%'),
                User.username.ilike(f'%{busqueda}%'),
                User.email.ilike(f'%{busqueda}%')
            )
        )
    
    profesores = query.order_by(User.apellido, User.nombre).all()
    
    # Obtener carreras para el filtro
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
    
    # Crear formularios
    filtrar_form = FiltrarProfesoresForm()
    filtrar_form.carrera.choices = [(0, 'Todas las carreras')] + [(c.id, c.nombre) for c in carreras]
    
    exportar_form = ExportarProfesoresForm()
    
    return render_template('admin/profesores.html', 
                         profesores=profesores, 
                         carreras=carreras,
                         filtrar_form=filtrar_form,
                         exportar_form=exportar_form,
                         filtros_activos={
                             'carrera': carrera_id,
                             'tipo_profesor': tipo_profesor,
                             'busqueda': busqueda
                         })

@app.route('/admin/profesores/importar', methods=['GET', 'POST'])
@login_required
def importar_profesores():
    """Importar profesores desde archivo CSV/Excel (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = ImportarProfesoresForm()
    
    if form.validate_on_submit():
        try:
            archivo = form.archivo.data
            resultado = procesar_archivo_profesores(archivo)
            
            if resultado['exito']:
                flash(f"Importación exitosa: {resultado['procesados']} profesores procesados, "
                     f"{resultado['creados']} nuevos, {resultado['actualizados']} actualizados.", 'success')
                
                if resultado['errores']:
                    flash(f"Se encontraron {len(resultado['errores'])} errores durante la importación.", 'warning')
                    return render_template('admin/importar_profesores.html', 
                                         form=form, 
                                         resultado=resultado)
            else:
                flash(f"Error en la importación: {resultado['mensaje']}", 'error')
                
        except Exception as e:
            flash('Error al procesar el archivo. Inténtalo de nuevo.', 'error')
            print(f"Error en importar profesores: {e}")
    
    return render_template('admin/importar_profesores.html', form=form)

@app.route('/admin/profesores/plantilla-csv')
@login_required
def descargar_plantilla_csv_profesores():
    """Descargar plantilla CSV para importar profesores (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        return generar_plantilla_csv()
    except Exception as e:
        flash('Error al generar la plantilla CSV. Inténtalo de nuevo.', 'error')
        print(f"Error en descargar plantilla CSV profesores: {e}")
        return redirect(url_for('importar_profesores'))

@app.route('/admin/profesores/exportar')
@login_required
def exportar_profesores():
    """Exportar profesores a PDF (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Obtener filtros de la URL
        carrera_id = request.args.get('carrera_id', type=int)
        tipo_profesor = request.args.get('tipo_profesor')
        
        # Query para profesores con filtros
        query = User.query.filter(
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        )
        
        if carrera_id:
            query = query.filter(User.carrera_id == carrera_id)
        
        if tipo_profesor:
            query = query.filter(User.rol == tipo_profesor)
        
        profesores = query.order_by(User.apellido, User.nombre).all()
        
        # Generar PDF
        nombre_carrera = None
        if carrera_id:
            carrera = Carrera.query.get(carrera_id)
            nombre_carrera = carrera.nombre if carrera else None
        
        archivo_pdf = generar_pdf_profesores(profesores, nombre_carrera, tipo_profesor)
        
        return send_file(archivo_pdf, as_attachment=True, download_name=f'profesores_{archivo_pdf.split("/")[-1]}')
        
    except Exception as e:
        flash('Error al generar el PDF. Inténtalo de nuevo.', 'error')
        print(f"Error en exportar profesores: {e}")
        return redirect(url_for('gestionar_profesores'))

@app.route('/admin/profesores/<int:id>/toggle-estado', methods=['POST'])
@login_required
def toggle_estado_profesor(id):
    """Activar/desactivar profesor (solo admin)"""
    if not current_user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        profesor = User.query.get_or_404(id)
        
        if profesor.rol not in ['profesor_completo', 'profesor_asignatura']:
            return jsonify({'error': 'Usuario no es profesor'}), 400
        
        profesor.activo = not profesor.activo
        db.session.commit()
        
        estado = 'activado' if profesor.activo else 'desactivado'
        return jsonify({
            'message': f'Profesor {profesor.get_nombre_completo()} {estado} exitosamente.',
            'nuevo_estado': profesor.activo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al cambiar estado del profesor.'}), 500

@app.route('/admin/profesores/agregar', methods=['GET', 'POST'])
@login_required
def agregar_profesor():
    """Agregar profesor manualmente (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    form = AgregarProfesorForm()
    
    # Obtener horarios para mostrar en la tabla
    from models import Horario
    horarios = Horario.query.filter_by(activo=True).order_by(Horario.turno, Horario.orden).all()
    
    if form.validate_on_submit():
        try:
            # Crear nuevo profesor
            nuevo_profesor = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                rol=form.tipo_profesor.data,
                telefono=form.telefono.data,
                carrera_id=int(form.carrera.data)
            )
            
            db.session.add(nuevo_profesor)
            db.session.flush()  # Obtener el ID del profesor sin hacer commit
            
            # Guardar disponibilidades
            disponibilidades_data = form.get_disponibilidades_data()
            for disp_data in disponibilidades_data:
                disponibilidad = DisponibilidadProfesor(
                    profesor_id=nuevo_profesor.id,
                    horario_id=disp_data['horario_id'],
                    dia_semana=disp_data['dia_semana'],
                    disponible=disp_data['disponible'],
                    creado_por=current_user.id
                )
                db.session.add(disponibilidad)
            
            db.session.commit()
            
            flash(f'Profesor {nuevo_profesor.get_nombre_completo()} creado exitosamente con su disponibilidad horaria.', 'success')
            return redirect(url_for('gestionar_profesores'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el profesor. Inténtalo de nuevo.', 'error')
            print(f"Error al crear profesor: {e}")
    
    return render_template('admin/profesor_form.html', form=form, titulo="Agregar Profesor", horarios=horarios)

# Manejo de errores
@app.errorhandler(404)
def not_found_error(error):
    """Página de error 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Contexto de plantillas
@app.context_processor
def inject_user_counts():
    """Inyectar conteos de usuarios en todas las plantillas"""
    if current_user.is_authenticated and current_user.is_admin():
        return dict(
            total_users=User.query.count(),
            total_admins=User.query.filter_by(rol='admin').count(),
            total_jefes=User.query.filter_by(rol='jefe_carrera').count(),
            total_profesores=User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()
        )
    return dict()

# Rutas para gestión de horarios académicos
@app.route('/admin/horarios-academicos')
@login_required
def gestionar_horarios_academicos():
    """Gestión de horarios académicos generados"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Obtener filtros
    carrera_id = request.args.get('carrera', type=int)
    periodo_academico = request.args.get('periodo', '2025-1')

    # Query base
    query = HorarioAcademico.query.filter_by(activo=True)

    if carrera_id:
        # Filtrar por carrera a través de la materia
        query = query.join(HorarioAcademico.materia).filter(Materia.carrera_id == carrera_id)

    if periodo_academico:
        query = query.filter(HorarioAcademico.periodo_academico == periodo_academico)

    horarios_academicos = query.order_by(
        HorarioAcademico.dia_semana,
        HorarioAcademico.horario_id
    ).all()

    # Obtener datos para filtros
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()

    # Estadísticas
    total_horarios = len(horarios_academicos)
    profesores_unicos = len(set(h.profesor_id for h in horarios_academicos)) if horarios_academicos else 0
    materias_unicas = len(set(h.materia_id for h in horarios_academicos)) if horarios_academicos else 0

    return render_template('admin/horarios_academicos.html',
                         horarios_academicos=horarios_academicos,
                         carreras=carreras,
                         total_horarios=total_horarios,
                         profesores_unicos=profesores_unicos,
                         materias_unicas=materias_unicas,
                         filtro_carrera=carrera_id,
                         filtro_periodo=periodo_academico)

@app.route('/admin/horarios-academicos/generar', methods=['GET', 'POST'])
@login_required
def generar_horarios_academicos():
    """Generar horarios académicos automáticamente"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    form = GenerarHorariosForm()
    resultado = None

    # Cargar carreras activas
    carreras = Carrera.query.filter_by(activa=True).order_by(Carrera.nombre).all()
    form.carrera.choices = [(str(c.id), c.nombre) for c in carreras]

    if form.validate_on_submit():
        from generador_horarios import generar_horarios_automaticos

        # Preparar días de la semana
        dias_semana = []
        if form.dias_semana.data == 'lunes_viernes':
            dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        elif form.dias_semana.data == 'lunes_sabado':
            dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
        else:  # personalizado
            if form.lunes.data == 'si':
                dias_semana.append('lunes')
            if form.martes.data == 'si':
                dias_semana.append('martes')
            if form.miercoles.data == 'si':
                dias_semana.append('miercoles')
            if form.jueves.data == 'si':
                dias_semana.append('jueves')
            if form.viernes.data == 'si':
                dias_semana.append('viernes')
            if form.sabado.data == 'si':
                dias_semana.append('sabado')

        # Generar horarios
        resultado = generar_horarios_automaticos(
            carrera_id=int(form.carrera.data),
            cuatrimestre=int(form.cuatrimestre.data),
            turno=form.turno.data,
            dias_semana=dias_semana,
            periodo_academico=form.periodo_academico.data,
            creado_por=current_user.id
        )

        if resultado['exito']:
            # No redirigir automáticamente, mostrar resultados en la página
            pass
        else:
            flash(resultado['mensaje'], 'error')

    return render_template('admin/generar_horarios.html', form=form, resultado=resultado)

@app.route('/admin/horarios-academicos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_horario_academico(id):
    """Editar un horario académico"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    horario_academico = HorarioAcademico.query.get_or_404(id)

    form = EditarHorarioAcademicoForm()

    # Cargar opciones para los select
    profesores = User.query.filter(
        User.rol.in_(['profesor_completo', 'profesor_asignatura']),
        User.activo == True
    ).order_by(User.nombre, User.apellido).all()

    horarios = Horario.query.filter_by(activo=True).order_by(Horario.orden).all()

    form.profesor_id.choices = [(str(p.id), p.get_nombre_completo()) for p in profesores]
    form.horario_id.choices = [(str(h.id), f"{h.nombre} ({h.get_hora_inicio_str()}-{h.get_hora_fin_str()})") for h in horarios]

    if form.validate_on_submit():
        horario_academico.profesor_id = int(form.profesor_id.data)
        horario_academico.horario_id = int(form.horario_id.data)
        horario_academico.dia_semana = form.dia_semana.data
        horario_academico.aula = form.aula.data
        horario_academico.periodo_academico = form.periodo_academico.data

        db.session.commit()
        flash('Horario académico actualizado exitosamente.', 'success')
        return redirect(url_for('gestionar_horarios_academicos'))

    # Pre-llenar formulario
    form.profesor_id.data = str(horario_academico.profesor_id)
    form.horario_id.data = str(horario_academico.horario_id)
    form.dia_semana.data = horario_academico.dia_semana
    form.aula.data = horario_academico.aula
    form.periodo_academico.data = horario_academico.periodo_academico

    return render_template('admin/editar_horario_academico.html',
                         form=form,
                         horario_academico=horario_academico)

@app.route('/admin/horarios-academicos/<int:id>/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar_horario_academico(id):
    """Eliminar un horario académico"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    horario_academico = HorarioAcademico.query.get_or_404(id)

    form = EliminarHorarioAcademicoForm()

    if form.validate_on_submit():
        if form.confirmacion.data == 'ELIMINAR':
            horario_academico.activo = False
            db.session.commit()
            flash('Horario académico eliminado exitosamente.', 'success')
            return redirect(url_for('gestionar_horarios_academicos'))
        else:
            flash('Confirmación incorrecta.', 'error')

    return render_template('admin/eliminar_horario_academico.html',
                         form=form,
                         horario_academico=horario_academico)

# ==========================================
# GESTIÓN DE USUARIOS (SOLO ADMINISTRADORES)
# ==========================================

@app.route('/admin/usuarios')
@login_required
def gestionar_usuarios():
    """Gestión de usuarios (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Obtener filtros
    rol_filter = request.args.get('rol', '')
    activo_filter = request.args.get('activo', '')
    busqueda = request.args.get('busqueda', '')

    # Construir consulta base
    query = User.query

    # Aplicar filtros
    if rol_filter:
        if rol_filter == 'profesor':
            query = query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura']))
        else:
            query = query.filter_by(rol=rol_filter)

    if activo_filter:
        if activo_filter == 'activos':
            query = query.filter_by(activo=True)
        elif activo_filter == 'inactivos':
            query = query.filter_by(activo=False)

    if busqueda:
        query = query.filter(
            db.or_(
                User.nombre.contains(busqueda),
                User.apellido.contains(busqueda),
                User.username.contains(busqueda),
                User.email.contains(busqueda)
            )
        )

    usuarios = query.order_by(User.nombre, User.apellido).all()

    # Estadísticas
    total_usuarios = len(usuarios)
    usuarios_activos = sum(1 for u in usuarios if u.activo)
    usuarios_inactivos = total_usuarios - usuarios_activos

    # Conteo por roles
    roles_count = {}
    for usuario in usuarios:
        rol_display = usuario.get_rol_display()
        roles_count[rol_display] = roles_count.get(rol_display, 0) + 1

    return render_template('admin/usuarios.html',
                         usuarios=usuarios,
                         total_usuarios=total_usuarios,
                         usuarios_activos=usuarios_activos,
                         usuarios_inactivos=usuarios_inactivos,
                         roles_count=roles_count,
                         filtros_activos={
                             'rol': rol_filter,
                             'activo': activo_filter,
                             'busqueda': busqueda
                         })

@app.route('/admin/usuario/nuevo', methods=['GET', 'POST'])
@login_required
def agregar_usuario():
    """Agregar nuevo usuario (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    from forms import AgregarUsuarioForm
    form = AgregarUsuarioForm()

    if form.validate_on_submit():
        # Crear nuevo usuario
        nuevo_usuario = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            rol=form.rol.data,
            telefono=form.telefono.data,
            carrera_id=int(form.carrera.data) if form.carrera.data else None,
            activo=form.activo.data
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(f'Usuario {nuevo_usuario.get_nombre_completo()} creado exitosamente.', 'success')
            return redirect(url_for('gestionar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')

    return render_template('admin/usuario_form.html', form=form, titulo="Agregar Usuario", usuario=None)

@app.route('/admin/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    """Editar usuario existente (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    usuario = User.query.get_or_404(id)
    from forms import EditarUsuarioForm
    form = EditarUsuarioForm(user=usuario)

    if form.validate_on_submit():
        # Verificar cambios en el rol y carrera
        rol_anterior = usuario.rol
        carrera_anterior = usuario.carrera_id
        
        # Actualizar usuario
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.nombre = form.nombre.data
        usuario.apellido = form.apellido.data
        usuario.rol = form.rol.data
        usuario.telefono = form.telefono.data
        usuario.carrera_id = int(form.carrera.data) if form.carrera.data else None
        usuario.activo = form.activo.data

        # Si se cambió de jefe de carrera a otro rol, liberar la carrera
        if rol_anterior == 'jefe_carrera' and usuario.rol != 'jefe_carrera' and carrera_anterior:
            # La carrera queda libre para otro jefe
            pass

        # Si se cambió a jefe de carrera desde otro rol, verificar que la carrera esté libre
        if rol_anterior != 'jefe_carrera' and usuario.rol == 'jefe_carrera' and usuario.carrera_id:
            # Verificar que no haya otro jefe activo para esta carrera
            existing_jefe = User.query.filter(
                User.rol == 'jefe_carrera',
                User.carrera_id == usuario.carrera_id,
                User.activo == True,
                User.id != usuario.id
            ).first()
            if existing_jefe:
                flash(f'Error: Ya existe un jefe de carrera activo para esta carrera ({existing_jefe.get_nombre_completo()}).', 'error')
                db.session.rollback()
                return render_template('admin/usuario_form.html', form=form, titulo="Editar Usuario", usuario=usuario)

        try:
            db.session.commit()
            flash(f'Usuario {usuario.get_nombre_completo()} actualizado exitosamente.', 'success')
            return redirect(url_for('gestionar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'error')

    # Llenar formulario con datos actuales
    elif request.method == 'GET':
        form.username.data = usuario.username
        form.email.data = usuario.email
        form.nombre.data = usuario.nombre
        form.apellido.data = usuario.apellido
        form.rol.data = usuario.rol
        form.telefono.data = usuario.telefono
        form.carrera.data = str(usuario.carrera_id) if usuario.carrera_id else ''
        form.activo.data = usuario.activo

    return render_template('admin/usuario_form.html', form=form, titulo="Editar Usuario", usuario=usuario)

@app.route('/admin/usuario/<int:id>/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar_usuario(id):
    """Eliminar usuario (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    usuario = User.query.get_or_404(id)

    # No permitir eliminar al propio usuario
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propio usuario.', 'error')
        return redirect(url_for('gestionar_usuarios'))

    from forms import EliminarUsuarioForm
    form = EliminarUsuarioForm()

    if form.validate_on_submit():
        if form.confirmacion.data == 'ELIMINAR':
            try:
                # Eliminar físicamente el usuario y sus relaciones
                # Primero eliminar las relaciones que podrían causar problemas
                
                # Eliminar horarios académicos donde el usuario es profesor
                from models import HorarioAcademico, DisponibilidadProfesor
                HorarioAcademico.query.filter_by(profesor_id=usuario.id).delete()
                HorarioAcademico.query.filter_by(creado_por=usuario.id).delete()
                
                # Eliminar disponibilidades del profesor
                DisponibilidadProfesor.query.filter_by(profesor_id=usuario.id).delete()
                DisponibilidadProfesor.query.filter_by(creado_por=usuario.id).delete()
                
                # Eliminar el usuario físicamente
                db.session.delete(usuario)
                db.session.commit()
                
                flash(f'Usuario {usuario.get_nombre_completo()} eliminado permanentemente.', 'success')
                return redirect(url_for('gestionar_usuarios'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al eliminar usuario: {str(e)}', 'error')
        else:
            flash('Confirmación incorrecta.', 'error')

    return render_template('admin/eliminar_usuario.html', form=form, usuario=usuario)

@app.route('/admin/usuario/<int:id>/activar', methods=['POST'])
@login_required
def activar_usuario(id):
    """Activar usuario (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    usuario = User.query.get_or_404(id)

    try:
        usuario.activo = True
        db.session.commit()
        flash(f'Usuario {usuario.get_nombre_completo()} activado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar usuario: {str(e)}', 'error')

    return redirect(url_for('gestionar_usuarios'))

@app.route('/admin/usuario/<int:id>/desactivar', methods=['POST'])
@login_required
def desactivar_usuario(id):
    """Desactivar usuario (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    usuario = User.query.get_or_404(id)

    # No permitir desactivar al propio usuario
    if usuario.id == current_user.id:
        flash('No puedes desactivar tu propio usuario.', 'error')
        return redirect(url_for('dashboard'))

    try:
        usuario.activo = False
        db.session.commit()
        flash(f'Usuario {usuario.get_nombre_completo()} desactivado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar usuario: {str(e)}', 'error')

    return redirect(url_for('gestionar_usuarios'))

# Reportes del Sistema
@app.route('/admin/reportes')
@login_required
def reportes_sistema():
    """Página de reportes del sistema"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Estadísticas generales
    total_usuarios = User.query.count()
    total_profesores = User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()
    total_carreras = Carrera.query.filter_by(activa=True).count()
    total_materias = Materia.query.filter_by(activa=True).count()
    total_horarios_academicos = HorarioAcademico.query.filter_by(activo=True).count()

    # Estadísticas por carrera
    carreras_stats = []
    carreras = Carrera.query.filter_by(activa=True).all()
    for carrera in carreras:
        profesores_carrera = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).count()

        materias_carrera = Materia.query.filter(
            Materia.carrera_id == carrera.id,
            Materia.activa == True
        ).count()

        horarios_carrera = HorarioAcademico.query.join(Materia).filter(
            Materia.carrera_id == carrera.id,
            HorarioAcademico.activo == True
        ).count()

        carreras_stats.append({
            'carrera': carrera,
            'profesores': profesores_carrera,
            'materias': materias_carrera,
            'horarios': horarios_carrera
        })

    return render_template('admin/reportes.html',
                         total_usuarios=total_usuarios,
                         total_profesores=total_profesores,
                         total_carreras=total_carreras,
                         total_materias=total_materias,
                         total_horarios_academicos=total_horarios_academicos,
                         carreras_stats=carreras_stats)

# Configuración del Sistema
@app.route('/admin/configuracion')
@login_required
def configuracion_sistema():
    """Página de configuración del sistema"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('admin/configuracion.html')

# API para configuración de base de datos
@app.route('/admin/configuracion/database', methods=['POST'])
@login_required
def guardar_configuracion_database():
    """Guardar configuración de base de datos"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        data = request.get_json()

        # Guardar configuración de base de datos
        from models import ConfiguracionSistema

        # Configuración general
        ConfiguracionSistema.set_config(
            'db_type', data.get('db_type', 'sqlite'),
            tipo='string', descripcion='Tipo de base de datos', categoria='database'
        )

        # Configuración específica por tipo de BD
        if data['db_type'] == 'sqlite':
            ConfiguracionSistema.set_config(
                'sqlite_path', data.get('sqlite_path', 'instance/sistema_academico.db'),
                tipo='string', descripcion='Ruta del archivo SQLite', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'sqlite_backup_freq', data.get('sqlite_backup_freq', 'daily'),
                tipo='string', descripcion='Frecuencia de backup SQLite', categoria='backup'
            )
        elif data['db_type'] == 'postgresql':
            ConfiguracionSistema.set_config(
                'pg_host', data.get('host', 'localhost'),
                tipo='string', descripcion='Host PostgreSQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'pg_port', data.get('port', '5432'),
                tipo='string', descripcion='Puerto PostgreSQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'pg_database', data.get('database', 'sistema_academico'),
                tipo='string', descripcion='Base de datos PostgreSQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'pg_username', data.get('username', 'postgres'),
                tipo='string', descripcion='Usuario PostgreSQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'pg_password', data.get('password', ''),
                tipo='string', descripcion='Contraseña PostgreSQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'pg_ssl', data.get('ssl', 'require'),
                tipo='string', descripcion='SSL PostgreSQL', categoria='database'
            )
        elif data['db_type'] == 'mysql':
            ConfiguracionSistema.set_config(
                'mysql_host', data.get('host', 'localhost'),
                tipo='string', descripcion='Host MySQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mysql_port', data.get('port', '3306'),
                tipo='string', descripcion='Puerto MySQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mysql_database', data.get('database', 'sistema_academico'),
                tipo='string', descripcion='Base de datos MySQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mysql_username', data.get('username', 'root'),
                tipo='string', descripcion='Usuario MySQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mysql_password', data.get('password', ''),
                tipo='string', descripcion='Contraseña MySQL', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mysql_ssl', data.get('ssl', 'true'),
                tipo='string', descripcion='SSL MySQL', categoria='database'
            )
        elif data['db_type'] == 'mariadb':
            ConfiguracionSistema.set_config(
                'mariadb_host', data.get('host', 'localhost'),
                tipo='string', descripcion='Host MariaDB', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mariadb_port', data.get('port', '3306'),
                tipo='string', descripcion='Puerto MariaDB', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mariadb_database', data.get('database', 'sistema_academico'),
                tipo='string', descripcion='Base de datos MariaDB', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mariadb_username', data.get('username', 'root'),
                tipo='string', descripcion='Usuario MariaDB', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mariadb_password', data.get('password', ''),
                tipo='string', descripcion='Contraseña MariaDB', categoria='database'
            )
            ConfiguracionSistema.set_config(
                'mariadb_ssl', data.get('ssl', 'true'),
                tipo='string', descripcion='SSL MariaDB', categoria='database'
            )

        # Configuración de backups
        ConfiguracionSistema.set_config(
            'backup_frequency', data.get('backup_frequency', 'daily'),
            tipo='string', descripcion='Frecuencia de backup automático', categoria='backup'
        )
        ConfiguracionSistema.set_config(
            'backup_retention', data.get('backup_retention', '30'),
            tipo='int', descripcion='Días de retención de backups', categoria='backup'
        )
        ConfiguracionSistema.set_config(
            'backup_location', data.get('backup_location', 'backups/'),
            tipo='string', descripcion='Ubicación de backups', categoria='backup'
        )

        return jsonify({'success': True, 'message': 'Configuración guardada exitosamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al guardar configuración: {str(e)}'}), 500

# API para crear backup
@app.route('/admin/configuracion/backup', methods=['POST'])
@login_required
def crear_backup():
    """Crear backup de la base de datos"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        from models import BackupHistory
        import shutil
        import hashlib
        from datetime import datetime

        # Crear directorio de backups si no existe
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Generar nombre del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.db'
        filepath = os.path.join(backup_dir, filename)

        # Copiar archivo de base de datos
        db_path = 'instance/sistema_academico.db'
        if os.path.exists(db_path):
            shutil.copy2(db_path, filepath)

            # Calcular tamaño y checksum
            file_size = os.path.getsize(filepath)
            with open(filepath, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Registrar en historial
            backup = BackupHistory(
                filename=filename,
                tipo='manual',
                tamano=file_size,
                ruta_archivo=filepath,
                usuario_id=current_user.id
            )
            backup.checksum = checksum
            db.session.add(backup)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Backup creado exitosamente',
                'filename': filename,
                'size': file_size
            })
        else:
            return jsonify({'success': False, 'message': 'Archivo de base de datos no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al crear backup: {str(e)}'}), 500

# API para obtener historial de backups
@app.route('/admin/configuracion/backups', methods=['GET'])
@login_required
def obtener_historial_backups():
    """Obtener historial de backups"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        from models import BackupHistory

        backups = BackupHistory.query.order_by(BackupHistory.fecha_creacion.desc()).limit(10).all()

        backup_list = []
        for backup in backups:
            backup_list.append({
                'id': backup.id,
                'filename': backup.filename,
                'tipo': backup.tipo,
                'tamano': backup.get_tamano_formateado(),
                'fecha': backup.get_fecha_formateada(),
                'estado': backup.estado,
                'usuario': backup.usuario.nombre + ' ' + backup.usuario.apellido if backup.usuario else 'Sistema'
            })

        return jsonify({'success': True, 'backups': backup_list})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al obtener historial: {str(e)}'}), 500

# API para descargar backup
@app.route('/admin/configuracion/backup/<filename>', methods=['GET'])
@login_required
def descargar_backup(filename):
    """Descargar archivo de backup"""
    if not current_user.is_admin():
        flash('No tienes permisos para esta acción.', 'error')
        return redirect(url_for('dashboard'))

    try:
        from models import BackupHistory

        # Verificar que el backup existe en la base de datos
        backup = BackupHistory.query.filter_by(filename=filename).first()
        if not backup:
            flash('Backup no encontrado.', 'error')
            return redirect(url_for('configuracion_sistema'))

        filepath = os.path.join('backups', filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
        else:
            flash('Archivo de backup no encontrado en el servidor.', 'error')
            return redirect(url_for('configuracion_sistema'))

    except Exception as e:
        flash(f'Error al descargar backup: {str(e)}', 'error')
        return redirect(url_for('configuracion_sistema'))

# API para optimizar base de datos
@app.route('/admin/configuracion/optimize', methods=['POST'])
@login_required
def optimizar_base_datos():
    """Optimizar base de datos"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        # Ejecutar comandos de optimización para SQLite
        db.session.execute('VACUUM')
        db.session.execute('ANALYZE')
        db.session.commit()

        return jsonify({'success': True, 'message': 'Base de datos optimizada exitosamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al optimizar base de datos: {str(e)}'}), 500

# API para reiniciar sistema (simulado)
@app.route('/admin/configuracion/restart', methods=['POST'])
@login_required
def reiniciar_sistema():
    """Reiniciar sistema (simulado)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        # En un entorno real, aquí se reiniciaría el servidor
        # Por ahora solo devolvemos éxito
        return jsonify({'success': True, 'message': 'Sistema reiniciado exitosamente'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al reiniciar sistema: {str(e)}'}), 500

# API para probar conexión a base de datos
@app.route('/admin/configuracion/test-connection', methods=['POST'])
@login_required
def probar_conexion():
    """Probar conexión a base de datos"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No tienes permisos para esta acción'}), 403

    try:
        data = request.get_json()
        db_type = data.get('db_type', 'sqlite')

        if db_type == 'sqlite':
            # Para SQLite solo verificar que el archivo existe
            db_path = data.get('sqlite_path', 'instance/sistema_academico.db')
            if os.path.exists(db_path):
                return jsonify({'success': True, 'message': 'Conexión a SQLite exitosa'})
            else:
                return jsonify({'success': False, 'message': 'Archivo de base de datos SQLite no encontrado'})

        elif db_type == 'postgresql':
            # Probar conexión PostgreSQL
            try:
                import psycopg2  # type: ignore[import-untyped]
            except ImportError:
                return jsonify({
                    'success': False, 
                    'message': 'Driver PostgreSQL no instalado. Instale con: pip install psycopg2-binary'
                })
            
            conn = psycopg2.connect(
                host=data.get('host', 'localhost'),
                port=data.get('port', '5432'),
                database=data.get('database', 'sistema_academico'),
                user=data.get('username', 'postgres'),
                password=data.get('password', ''),
                sslmode=data.get('ssl', 'require')
            )
            conn.close()
            return jsonify({'success': True, 'message': 'Conexión a PostgreSQL exitosa'})

        elif db_type in ['mysql', 'mariadb']:
            # Probar conexión MySQL/MariaDB
            try:
                import mysql.connector  # type: ignore[import-untyped]
            except ImportError:
                return jsonify({
                    'success': False, 
                    'message': 'Driver MySQL no instalado. Instale con: pip install mysql-connector-python'
                })
            
            conn = mysql.connector.connect(
                host=data.get('host', 'localhost'),
                port=int(data.get('port', '3306')),
                database=data.get('database', 'sistema_academico'),
                user=data.get('username', 'root'),
                password=data.get('password', ''),
                ssl_disabled=(data.get('ssl', 'true') == 'false')
            )
            conn.close()
            return jsonify({'success': True, 'message': f'Conexión a {db_type.title()} exitosa'})

        else:
            return jsonify({'success': False, 'message': 'Tipo de base de datos no soportado'})

    except ImportError as e:
        return jsonify({'success': False, 'message': f'Driver no instalado: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error de conexión: {str(e)}'})

# Subir imagen de perfil
@app.route('/subir_imagen_perfil', methods=['POST'])
@login_required
def subir_imagen_perfil():
    """Subir imagen de perfil del usuario"""
    if 'imagen_perfil' not in request.files:
        flash('No se encontró el archivo de imagen.', 'error')
        return redirect(url_for('dashboard'))

    file = request.files['imagen_perfil']
    
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('dashboard'))

    if file and allowed_file(file.filename):
        # Generar nombre único para el archivo
        filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        
        # Crear directorio si no existe
        upload_dir = os.path.join('static', 'uploads', 'perfiles')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Actualizar usuario en base de datos
        # Primero eliminar imagen anterior si existe
        if current_user.imagen_perfil:
            old_file_path = os.path.join('static', 'uploads', 'perfiles', current_user.imagen_perfil)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Actualizar con nueva imagen
        current_user.imagen_perfil = filename
        db.session.commit()
        
        flash('Imagen de perfil actualizada exitosamente.', 'success')
    else:
        flash('Tipo de archivo no permitido. Solo se permiten imágenes (PNG, JPG, JPEG, GIF).', 'error')

    return redirect(url_for('dashboard'))

# Eliminar imagen de perfil
@app.route('/eliminar_imagen_perfil', methods=['POST'])
@login_required
def eliminar_imagen_perfil():
    """Eliminar imagen de perfil del usuario"""
    if current_user.imagen_perfil:
        # Eliminar archivo físico
        file_path = os.path.join('static', 'uploads', 'perfiles', current_user.imagen_perfil)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Actualizar base de datos
        current_user.imagen_perfil = None
        db.session.commit()
        
        flash('Imagen de perfil eliminada exitosamente.', 'success')
    else:
        flash('No hay imagen de perfil para eliminar.', 'warning')
    
    return redirect(url_for('dashboard'))

# Función auxiliar para verificar tipos de archivo permitidos
def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Exportar Reportes - PDF
@app.route('/admin/reportes/exportar/pdf')
@login_required
def exportar_reportes_pdf():
    """Exportar reportes del sistema a PDF"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Obtener datos para el reporte
    total_usuarios = User.query.count()
    total_profesores = User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()
    total_carreras = Carrera.query.filter_by(activa=True).count()
    total_materias = Materia.query.filter_by(activa=True).count()
    total_horarios_academicos = HorarioAcademico.query.filter_by(activo=True).count()

    # Datos por carrera
    carreras = Carrera.query.filter_by(activa=True).all()
    carreras_data = []
    for carrera in carreras:
        profesores_carrera = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).count()

        materias_carrera = Materia.query.filter(
            Materia.carrera_id == carrera.id,
            Materia.activa == True
        ).count()

        horarios_carrera = HorarioAcademico.query.join(Materia).filter(
            Materia.carrera_id == carrera.id,
            HorarioAcademico.activo == True
        ).count()

        cobertura = (horarios_carrera / materias_carrera * 100) if materias_carrera > 0 else 0

        carreras_data.append([
            carrera.nombre,
            str(profesores_carrera),
            str(materias_carrera),
            str(horarios_carrera),
            ".1f"
        ])

    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )

    # Título
    title = Paragraph("Reporte del Sistema Académico", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Fecha de generación
    from datetime import datetime
    fecha_style = ParagraphStyle('Fecha', parent=styles['Normal'], fontSize=10, alignment=2)
    fecha = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style)
    elements.append(fecha)
    elements.append(Spacer(1, 20))

    # Estadísticas Generales
    elements.append(Paragraph("Estadísticas Generales", styles['Heading2']))
    elements.append(Spacer(1, 12))

    general_data = [
        ['Métrica', 'Valor'],
        ['Total de Usuarios', str(total_usuarios)],
        ['Total de Profesores', str(total_profesores)],
        ['Carreras Activas', str(total_carreras)],
        ['Materias Activas', str(total_materias)],
        ['Horarios Asignados', str(total_horarios_academicos)],
        ['Promedio Horarios por Profesor', ".1f"]
    ]

    general_table = Table(general_data, colWidths=[3*inch, 2*inch])
    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(general_table)
    elements.append(Spacer(1, 20))

    # Estadísticas por Carrera
    elements.append(Paragraph("Estadísticas por Carrera", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if carreras_data:
        carrera_headers = [['Carrera', 'Profesores', 'Materias', 'Horarios', 'Cobertura (%)']]
        carrera_table_data = carrera_headers + carreras_data

        carrera_table = Table(carrera_table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
        carrera_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(carrera_table)
    else:
        elements.append(Paragraph("No hay datos de carreras disponibles.", styles['Normal']))

    # Generar PDF
    doc.build(elements)

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'reporte_sistema_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
        mimetype='application/pdf'
    )

# Exportar Reportes - Excel
@app.route('/admin/reportes/exportar/excel')
@login_required
def exportar_reportes_excel():
    """Exportar reportes del sistema a Excel"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Crear datos para Excel
    data_general = {
        'Métrica': [
            'Total de Usuarios',
            'Total de Profesores',
            'Carreras Activas',
            'Materias Activas',
            'Horarios Asignados',
            'Promedio Horarios por Profesor'
        ],
        'Valor': [
            User.query.count(),
            User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count(),
            Carrera.query.filter_by(activa=True).count(),
            Materia.query.filter_by(activa=True).count(),
            HorarioAcademico.query.filter_by(activo=True).count(),
            ".1f"
        ]
    }

    # Datos por carrera
    carreras = Carrera.query.filter_by(activa=True).all()
    carreras_data = []
    for carrera in carreras:
        profesores_carrera = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).count()

        materias_carrera = Materia.query.filter(
            Materia.carrera_id == carrera.id,
            Materia.activa == True
        ).count()

        horarios_carrera = HorarioAcademico.query.join(Materia).filter(
            Materia.carrera_id == carrera.id,
            HorarioAcademico.activo == True
        ).count()

        cobertura = (horarios_carrera / materias_carrera * 100) if materias_carrera > 0 else 0

        carreras_data.append({
            'Carrera': carrera.nombre,
            'Profesores': profesores_carrera,
            'Materias': materias_carrera,
            'Horarios': horarios_carrera,
            'Cobertura (%)': round(cobertura, 1)
        })

    # Crear Excel con múltiples hojas
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja de estadísticas generales
        df_general = pd.DataFrame(data_general)
        df_general.to_excel(writer, sheet_name='Estadísticas Generales', index=False)

        # Hoja de estadísticas por carrera
        if carreras_data:
            df_carreras = pd.DataFrame(carreras_data)
            df_carreras.to_excel(writer, sheet_name='Estadísticas por Carrera', index=False)

        # Hoja de resumen
        resumen_data = {
            'Información': [
                'Fecha de Generación',
                'Usuario que generó',
                'Total de Registros Analizados'
            ],
            'Valor': [
                datetime.now().strftime('%d/%m/%Y %H:%M'),
                current_user.get_nombre_completo(),
                len(carreras_data) if carreras_data else 0
            ]
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'reporte_sistema_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Exportar Reportes - CSV
@app.route('/admin/reportes/exportar/csv')
@login_required
def exportar_reportes_csv():
    """Exportar reportes del sistema a CSV"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))

    # Crear datos para CSV
    buffer = BytesIO()

    # Escribir estadísticas generales
    writer = csv.writer(buffer)

    # Encabezado
    writer.writerow(['Reporte del Sistema Académico'])
    writer.writerow(['Generado el', datetime.now().strftime('%d/%m/%Y %H:%M')])
    writer.writerow(['Usuario', current_user.get_nombre_completo()])
    writer.writerow([])

    # Estadísticas Generales
    writer.writerow(['ESTADÍSTICAS GENERALES'])
    writer.writerow(['Métrica', 'Valor'])
    writer.writerow(['Total de Usuarios', User.query.count()])
    writer.writerow(['Total de Profesores', User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()])
    writer.writerow(['Carreras Activas', Carrera.query.filter_by(activa=True).count()])
    writer.writerow(['Materias Activas', Materia.query.filter_by(activa=True).count()])
    writer.writerow(['Horarios Asignados', HorarioAcademico.query.filter_by(activo=True).count()])
    writer.writerow(['Promedio Horarios por Profesor', ".1f"])
    writer.writerow([])

    # Estadísticas por Carrera
    writer.writerow(['ESTADÍSTICAS POR CARRERA'])
    writer.writerow(['Carrera', 'Profesores', 'Materias', 'Horarios', 'Cobertura (%)'])

    carreras = Carrera.query.filter_by(activa=True).all()
    for carrera in carreras:
        profesores_carrera = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).count()

        materias_carrera = Materia.query.filter(
            Materia.carrera_id == carrera.id,
            Materia.activa == True
        ).count()

        horarios_carrera = HorarioAcademico.query.join(Materia).filter(
            Materia.carrera_id == carrera.id,
            HorarioAcademico.activo == True
        ).count()

        cobertura = (horarios_carrera / materias_carrera * 100) if materias_carrera > 0 else 0

        writer.writerow([
            carrera.nombre,
            profesores_carrera,
            materias_carrera,
            horarios_carrera,
            ".1f"
        ])

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'reporte_sistema_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
        mimetype='text/csv'
    )

# Crear base de datos y usuario admin al inicio
with app.app_context():
    init_db()
    init_upload_dirs()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)