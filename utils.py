import pandas as pd
import io
from flask import make_response
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime
from models import User, Carrera, db, Materia

def procesar_archivo_profesores(archivo, carrera_defecto_id=None):
    """
    Procesar archivo CSV/Excel con datos de profesores
    
    Formato esperado del archivo:
    - nombre, apellido, email, telefono, tipo_profesor, carrera_codigo (opcional)
    """
    resultados = {
        'exitosos': [],
        'errores': [],
        'total_procesados': 0
    }
    
    try:
        # Leer archivo según extensión
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:  # Excel
            df = pd.read_excel(archivo)
        
        # Validar columnas requeridas
        columnas_requeridas = ['nombre', 'apellido', 'email', 'tipo_profesor']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            resultados['errores'].append(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
            return resultados
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                resultados['total_procesados'] += 1
                
                # Validar datos básicos
                if pd.isna(row['nombre']) or pd.isna(row['apellido']) or pd.isna(row['email']):
                    resultados['errores'].append(f"Fila {index + 2}: Datos básicos incompletos")
                    continue
                
                # Validar tipo de profesor
                tipo_profesor = str(row['tipo_profesor']).lower().strip()
                if tipo_profesor not in ['profesor_completo', 'profesor_asignatura', 'tiempo completo', 'asignatura']:
                    resultados['errores'].append(f"Fila {index + 2}: Tipo de profesor inválido")
                    continue
                
                # Normalizar tipo de profesor
                if tipo_profesor in ['tiempo completo']:
                    tipo_profesor = 'profesor_completo'
                elif tipo_profesor in ['asignatura']:
                    tipo_profesor = 'profesor_asignatura'
                
                # Determinar carrera
                carrera_id = carrera_defecto_id
                if 'carrera_codigo' in df.columns and not pd.isna(row['carrera_codigo']):
                    carrera = Carrera.query.filter_by(codigo=str(row['carrera_codigo']).upper().strip()).first()
                    if carrera:
                        carrera_id = carrera.id
                
                # Generar username único
                nombre_base = str(row['nombre']).lower().strip()
                apellido_base = str(row['apellido']).lower().strip()
                username_base = f"{nombre_base}.{apellido_base}".replace(' ', '')
                username = username_base
                contador = 1
                
                while User.query.filter_by(username=username).first():
                    username = f"{username_base}{contador}"
                    contador += 1
                
                # Verificar si el email ya existe
                if User.query.filter_by(email=str(row['email']).strip()).first():
                    resultados['errores'].append(f"Fila {index + 2}: Email {row['email']} ya existe")
                    continue
                
                # Crear usuario
                usuario = User(
                    username=username,
                    email=str(row['email']).strip(),
                    password='profesor123',  # Contraseña temporal
                    nombre=str(row['nombre']).strip().title(),
                    apellido=str(row['apellido']).strip().title(),
                    rol=tipo_profesor,
                    telefono=str(row['telefono']).strip() if 'telefono' in df.columns and not pd.isna(row['telefono']) else None,
                    carrera_id=carrera_id
                )
                
                db.session.add(usuario)
                resultados['exitosos'].append({
                    'nombre': usuario.get_nombre_completo(),
                    'username': username,
                    'email': usuario.email,
                    'tipo': usuario.get_rol_display(),
                    'carrera': usuario.get_carrera_nombre()
                })
                
            except Exception as e:
                resultados['errores'].append(f"Fila {index + 2}: Error al procesar - {str(e)}")
        
        # Guardar todos los cambios
        if resultados['exitosos']:
            db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        resultados['errores'].append(f"Error al leer archivo: {str(e)}")
    
    return resultados

def generar_pdf_profesores(carrera_id=None, incluir_contacto=True):
    """
    Generar PDF con lista de profesores
    """
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Contenido del PDF
    elements = []
    
    # Título
    if carrera_id:
        carrera = Carrera.query.get(carrera_id)
        titulo = f"Lista de Profesores - {carrera.nombre}"
    else:
        titulo = "Lista de Profesores - Todas las Carreras"
    
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 12))
    
    # Información del reporte
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Fecha de generación: {fecha_reporte}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Obtener profesores
    query = User.query.filter(
        User.rol.in_(['profesor_completo', 'profesor_asignatura']),
        User.activo == True
    )
    
    if carrera_id:
        query = query.filter(User.carrera_id == carrera_id)
    
    profesores = query.order_by(User.apellido, User.nombre).all()
    
    if not profesores:
        elements.append(Paragraph("No se encontraron profesores con los criterios especificados.", styles['Normal']))
    else:
        # Agrupar por carrera si se muestran todas
        if not carrera_id:
            profesores_por_carrera = {}
            for profesor in profesores:
                carrera_nombre = profesor.get_carrera_nombre()
                if carrera_nombre not in profesores_por_carrera:
                    profesores_por_carrera[carrera_nombre] = []
                profesores_por_carrera[carrera_nombre].append(profesor)
            
            # Generar tabla para cada carrera
            for carrera_nombre, lista_profesores in profesores_por_carrera.items():
                elements.append(Paragraph(carrera_nombre, heading_style))
                elements.append(Spacer(1, 6))
                
                # Crear tabla
                data = crear_tabla_profesores(lista_profesores, incluir_contacto)
                table = Table(data)
                table.setStyle(get_table_style())
                
                elements.append(table)
                elements.append(Spacer(1, 20))
        else:
            # Crear tabla única
            data = crear_tabla_profesores(profesores, incluir_contacto)
            table = Table(data)
            table.setStyle(get_table_style())
            
            elements.append(table)
    
    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Sistema de Gestión Académica", styles['Normal']))
    
    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def crear_tabla_profesores(profesores, incluir_contacto):
    """Crear datos de tabla para profesores"""
    if incluir_contacto:
        headers = ['Nombre', 'Tipo', 'Email', 'Teléfono', 'Fecha Registro']
        data = [headers]
        
        for profesor in profesores:
            data.append([
                profesor.get_nombre_completo(),
                'T.C.' if profesor.is_profesor_completo() else 'Asig.',
                profesor.email,
                profesor.telefono or 'N/A',
                profesor.fecha_registro.strftime('%d/%m/%Y')
            ])
    else:
        headers = ['Nombre', 'Tipo', 'Fecha Registro']
        data = [headers]
        
        for profesor in profesores:
            data.append([
                profesor.get_nombre_completo(),
                'Tiempo Completo' if profesor.is_profesor_completo() else 'Por Asignatura',
                profesor.fecha_registro.strftime('%d/%m/%Y')
            ])
    
    return data

def get_table_style():
    """Obtener estilo para las tablas"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

def generar_plantilla_csv():
    """Generar archivo CSV de plantilla para importar profesores"""
    data = {
        'nombre': ['Juan', 'María', 'Carlos'],
        'apellido': ['Pérez', 'González', 'Rodríguez'],
        'email': ['juan.perez@universidad.edu', 'maria.gonzalez@universidad.edu', 'carlos.rodriguez@universidad.edu'],
        'telefono': ['555-1234', '555-5678', '555-9012'],
        'tipo_profesor': ['profesor_completo', 'profesor_asignatura', 'profesor_completo'],
        'carrera_codigo': ['ING-SIS', 'MED', 'DER']
    }
    
    df = pd.DataFrame(data)
    
    # Crear response
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=plantilla_profesores.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

def procesar_archivo_materias(archivo, carrera_defecto_id=None):
    """
    Procesar archivo CSV/Excel con datos de materias
    
    Formato esperado del archivo:
    - nombre, codigo, cuatrimestre, carrera_codigo (opcional), creditos, horas_teoricas, horas_practicas, descripcion
    """
    resultados = {
        'exitosos': [],
        'errores': [],
        'total_procesados': 0
    }
    
    try:
        # Leer archivo según extensión
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:  # Excel
            df = pd.read_excel(archivo)
        
        # Validar columnas requeridas
        columnas_requeridas = ['nombre', 'codigo', 'cuatrimestre']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            resultados['errores'].append(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
            return resultados
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                resultados['total_procesados'] += 1
                
                # Validar datos básicos
                if pd.isna(row['nombre']) or pd.isna(row['codigo']) or pd.isna(row['cuatrimestre']):
                    resultados['errores'].append(f"Fila {index + 2}: Datos básicos incompletos")
                    continue
                
                # Validar cuatrimestre
                try:
                    cuatrimestre = int(row['cuatrimestre'])
                    if cuatrimestre < 1 or cuatrimestre > 12:
                        resultados['errores'].append(f"Fila {index + 2}: Cuatrimestre debe estar entre 1 y 12")
                        continue
                except:
                    resultados['errores'].append(f"Fila {index + 2}: Cuatrimestre inválido")
                    continue
                
                # Determinar carrera
                carrera_id = carrera_defecto_id
                if 'carrera_codigo' in df.columns and not pd.isna(row['carrera_codigo']):
                    carrera = Carrera.query.filter_by(codigo=str(row['carrera_codigo']).upper().strip()).first()
                    if carrera:
                        carrera_id = carrera.id
                    else:
                        resultados['errores'].append(f"Fila {index + 2}: Carrera con código {row['carrera_codigo']} no encontrada")
                        continue
                
                if not carrera_id:
                    resultados['errores'].append(f"Fila {index + 2}: No se pudo determinar la carrera")
                    continue
                
                # Verificar si el código ya existe
                codigo = str(row['codigo']).upper().strip()
                if Materia.query.filter_by(codigo=codigo, activa=True).first():
                    resultados['errores'].append(f"Fila {index + 2}: Código {codigo} ya existe")
                    continue
                
                # Obtener valores opcionales
                creditos = int(row['creditos']) if 'creditos' in df.columns and not pd.isna(row['creditos']) else 3
                horas_teoricas = int(row['horas_teoricas']) if 'horas_teoricas' in df.columns and not pd.isna(row['horas_teoricas']) else 3
                horas_practicas = int(row['horas_practicas']) if 'horas_practicas' in df.columns and not pd.isna(row['horas_practicas']) else 0
                descripcion = str(row['descripcion']) if 'descripcion' in df.columns and not pd.isna(row['descripcion']) else None
                
                # Crear materia
                materia = Materia(
                    nombre=str(row['nombre']).strip(),
                    codigo=codigo,
                    cuatrimestre=cuatrimestre,
                    carrera_id=carrera_id,
                    creditos=creditos,
                    horas_teoricas=horas_teoricas,
                    horas_practicas=horas_practicas,
                    descripcion=descripcion,
                    creado_por=1  # Admin por defecto
                )
                
                db.session.add(materia)
                resultados['exitosos'].append({
                    'nombre': materia.nombre,
                    'codigo': codigo,
                    'cuatrimestre': cuatrimestre,
                    'carrera': materia.get_carrera_nombre()
                })
                
            except Exception as e:
                resultados['errores'].append(f"Fila {index + 2}: Error al procesar - {str(e)}")
        
        # Guardar todos los cambios
        if resultados['exitosos']:
            db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        resultados['errores'].append(f"Error al leer archivo: {str(e)}")
    
    return resultados

def generar_pdf_materias(materias, nombre_carrera=None, cuatrimestre=None):
    """
    Generar PDF con lista de materias
    """
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Contenido del PDF
    elements = []
    
    # Título
    if nombre_carrera and cuatrimestre:
        titulo = f"Materias - {nombre_carrera} - Cuatrimestre {cuatrimestre}"
    elif nombre_carrera:
        titulo = f"Materias - {nombre_carrera}"
    elif cuatrimestre:
        titulo = f"Materias - Cuatrimestre {cuatrimestre}"
    else:
        titulo = "Materias - Todas las Carreras"
    
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 12))
    
    # Información del reporte
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Fecha de generación: {fecha_reporte}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if not materias:
        elements.append(Paragraph("No se encontraron materias con los criterios especificados.", styles['Normal']))
    else:
        # Crear tabla
        data = crear_tabla_materias(materias)
        table = Table(data)
        table.setStyle(get_table_style())
        
        elements.append(table)
    
    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Sistema de Gestión Académica", styles['Normal']))
    
    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def crear_tabla_materias(materias):
    """Crear datos de tabla para materias"""
    headers = ['Código', 'Nombre', 'Carrera', 'Cuatrimestre', 'Créditos', 'Horas Totales']
    data = [headers]
    
    for materia in materias:
        data.append([
            materia.codigo,
            materia.nombre,
            materia.get_carrera_codigo(),
            f"Cuatrimestre {materia.cuatrimestre}",
            str(materia.creditos),
            str(materia.get_horas_totales())
        ])
    
    return data