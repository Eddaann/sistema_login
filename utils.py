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
    - nombre, apellido_paterno, apellido_materno, email, telefono, tipo_profesor, carrera_codigo (opcional)
    """
    resultados = {
        'exitosos': [],
        'errores': [],
        'total_procesados': 0
    }
    
    try:
        # Leer archivo según extensión
        if archivo.filename.endswith('.csv'):
            # Intentar leer con diferentes codificaciones
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                try:
                    df = pd.read_csv(archivo, encoding='latin-1')
                except:
                    archivo.seek(0)
                    df = pd.read_csv(archivo, encoding='iso-8859-1')
        else:  # Excel
            df = pd.read_excel(archivo)
        
        # Limpiar nombres de columnas (eliminar espacios y convertir a minúsculas)
        df.columns = df.columns.str.strip().str.lower()
        
        # Validar columnas requeridas
        columnas_requeridas = ['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'tipo_profesor']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            columnas_encontradas = ', '.join(df.columns.tolist())
            resultados['errores'].append(f"Columnas faltantes: {', '.join(columnas_faltantes)}. Columnas encontradas: {columnas_encontradas}")
            return resultados
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                resultados['total_procesados'] += 1
                
                # Validar datos básicos
                if pd.isna(row['nombre']) or pd.isna(row['apellido_paterno']) or pd.isna(row['apellido_materno']) or pd.isna(row['email']):
                    resultados['errores'].append(f"Fila {index + 2}: Datos básicos incompletos (nombre, apellido_paterno, apellido_materno o email vacío)")
                    continue
                
                # Validar tipo de profesor
                tipo_profesor = str(row['tipo_profesor']).lower().strip()
                if tipo_profesor not in ['profesor_completo', 'profesor_asignatura', 'tiempo completo', 'asignatura']:
                    resultados['errores'].append(f"Fila {index + 2}: Tipo de profesor inválido (debe ser: profesor_completo, profesor_asignatura, tiempo completo o asignatura)")
                    continue
                
                # Normalizar tipo de profesor
                if tipo_profesor in ['tiempo completo']:
                    tipo_profesor = 'profesor_completo'
                elif tipo_profesor in ['asignatura']:
                    tipo_profesor = 'profesor_asignatura'
                
                # Determinar carrera(s)
                carreras = []
                if 'carrera_codigo' in df.columns and not pd.isna(row['carrera_codigo']):
                    # Puede tener múltiples carreras separadas por coma
                    codigos_carrera = str(row['carrera_codigo']).split(',')
                    for codigo in codigos_carrera:
                        carrera = Carrera.query.filter_by(codigo=codigo.upper().strip()).first()
                        if carrera:
                            carreras.append(carrera)
                        else:
                            resultados['errores'].append(f"Fila {index + 2}: Carrera con código '{codigo.strip()}' no encontrada")
                elif carrera_defecto_id:
                    carrera = Carrera.query.get(carrera_defecto_id)
                    if carrera:
                        carreras.append(carrera)
                
                if not carreras:
                    resultados['errores'].append(f"Fila {index + 2}: No se pudo determinar la carrera (especifica carrera_codigo o selecciona carrera por defecto)")
                    continue
                
                # Construir apellido completo
                apellido_paterno = str(row['apellido_paterno']).strip().title()
                apellido_materno = str(row['apellido_materno']).strip().title()
                apellido_completo = f"{apellido_paterno} {apellido_materno}"
                
                # Generar username único
                nombre_base = str(row['nombre']).lower().strip()
                apellido_base = apellido_paterno.lower()
                username_base = f"{nombre_base}.{apellido_base}".replace(' ', '')
                username = username_base
                contador = 1
                
                while User.query.filter_by(username=username).first():
                    username = f"{username_base}{contador}"
                    contador += 1
                
                # Verificar si el email ya existe
                if User.query.filter_by(email=str(row['email']).strip()).first():
                    resultados['errores'].append(f"Fila {index + 2}: Email {row['email']} ya existe en el sistema")
                    continue
                
                # Crear usuario
                usuario = User(
                    username=username,
                    email=str(row['email']).strip(),
                    password='profesor123',  # Contraseña temporal
                    nombre=str(row['nombre']).strip().title(),
                    apellido=apellido_completo,
                    rol=tipo_profesor,
                    telefono=str(row['telefono']).strip() if 'telefono' in df.columns and not pd.isna(row['telefono']) else None,
                    carreras=carreras  # Asignar carreras (relación many-to-many)
                )
                
                db.session.add(usuario)
                resultados['exitosos'].append({
                    'nombre': usuario.get_nombre_completo(),
                    'username': username,
                    'email': usuario.email,
                    'tipo': usuario.get_rol_display(),
                    'carreras': ', '.join([c.nombre for c in carreras])
                })
                
            except Exception as e:
                resultados['errores'].append(f"Fila {index + 2}: Error al procesar - {str(e)}")
        
        # Guardar todos los cambios
        if resultados['exitosos']:
            db.session.commit()
        
    except pd.errors.EmptyDataError:
        resultados['errores'].append('El archivo está vacío o no tiene datos válidos')
    except pd.errors.ParserError:
        resultados['errores'].append('Error al leer el archivo. Verifica que sea un CSV válido')
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
    """Generar archivo CSV de plantilla para importar profesores (solo encabezados)"""
    # Solo crear encabezados sin datos de ejemplo
    contenido_csv = "nombre,apellido_paterno,apellido_materno,email,telefono,tipo_profesor,carrera_codigo\n"
    
    # Crear response
    response = make_response(contenido_csv)
    response.headers["Content-Disposition"] = "attachment; filename=plantilla_profesores.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return response

def procesar_archivo_materias(archivo, carrera_defecto_id=None):
    """
    Procesar archivo CSV/Excel con datos de materias
    
    Formato esperado del archivo:
    - nombre, codigo, cuatrimestre, carrera_codigo (opcional), creditos, horas_teoricas, horas_practicas, descripcion
    """
    resultado = {
        'exito': False,
        'mensaje': '',
        'procesados': 0,
        'creados': 0,
        'actualizados': 0,
        'errores': []
    }
    
    try:
        # Leer archivo según extensión
        if archivo.filename.endswith('.csv'):
            # Intentar leer con diferentes codificaciones
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)  # Volver al inicio del archivo
                try:
                    df = pd.read_csv(archivo, encoding='latin-1')
                except:
                    archivo.seek(0)
                    df = pd.read_csv(archivo, encoding='iso-8859-1')
        else:  # Excel
            df = pd.read_excel(archivo)
        
        # Limpiar nombres de columnas (eliminar espacios y convertir a minúsculas)
        df.columns = df.columns.str.strip().str.lower()
        
        # Validar columnas requeridas
        columnas_requeridas = ['nombre', 'codigo', 'cuatrimestre']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            # Mostrar las columnas que se encontraron para ayudar al usuario
            columnas_encontradas = ', '.join(df.columns.tolist())
            resultado['mensaje'] = f"Formato del archivo: El archivo debe contener las siguientes columnas obligatorias: {', '.join(columnas_requeridas)}. Las columnas opcionales son: carrera_codigo, creditos, horas_teoricas, horas_practicas, descripcion. Columnas encontradas en el archivo: {columnas_encontradas}"
            return resultado
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                resultado['procesados'] += 1
                
                # Validar datos básicos
                if pd.isna(row['nombre']) or pd.isna(row['codigo']) or pd.isna(row['cuatrimestre']):
                    resultado['errores'].append(f"Fila {index + 2}: Datos básicos incompletos (nombre, código o cuatrimestre vacío)")
                    continue
                
                # Validar cuatrimestre
                try:
                    cuatrimestre = int(row['cuatrimestre'])
                    if cuatrimestre < 0 or cuatrimestre > 10:
                        resultado['errores'].append(f"Fila {index + 2}: Cuatrimestre debe estar entre 0 y 10")
                        continue
                except:
                    resultado['errores'].append(f"Fila {index + 2}: Cuatrimestre inválido (debe ser un número)")
                    continue
                
                # Determinar carrera
                carrera_id = carrera_defecto_id
                if 'carrera_codigo' in df.columns and not pd.isna(row['carrera_codigo']):
                    carrera = Carrera.query.filter_by(codigo=str(row['carrera_codigo']).upper().strip()).first()
                    if carrera:
                        carrera_id = carrera.id
                    else:
                        resultado['errores'].append(f"Fila {index + 2}: Carrera con código '{row['carrera_codigo']}' no encontrada en el sistema")
                        continue
                
                if not carrera_id:
                    resultado['errores'].append(f"Fila {index + 2}: No se pudo determinar la carrera (especifica carrera_codigo o selecciona carrera por defecto)")
                    continue
                
                # Verificar si la materia ya existe (por código)
                codigo = str(row['codigo']).upper().strip()
                materia_existente = Materia.query.filter_by(codigo=codigo, carrera_id=carrera_id, activa=True).first()
                
                # Obtener valores opcionales
                creditos = int(row['creditos']) if 'creditos' in df.columns and not pd.isna(row['creditos']) else 3
                horas_teoricas = int(row['horas_teoricas']) if 'horas_teoricas' in df.columns and not pd.isna(row['horas_teoricas']) else 3
                horas_practicas = int(row['horas_practicas']) if 'horas_practicas' in df.columns and not pd.isna(row['horas_practicas']) else 0
                descripcion = str(row['descripcion']).strip() if 'descripcion' in df.columns and not pd.isna(row['descripcion']) and str(row['descripcion']).upper() != 'NULL' else None
                
                if materia_existente:
                    # Actualizar materia existente
                    materia_existente.nombre = str(row['nombre']).strip()
                    materia_existente.cuatrimestre = cuatrimestre
                    materia_existente.creditos = creditos
                    materia_existente.horas_teoricas = horas_teoricas
                    materia_existente.horas_practicas = horas_practicas
                    materia_existente.descripcion = descripcion
                    resultado['actualizados'] += 1
                else:
                    # Crear nueva materia
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
                    resultado['creados'] += 1
                
            except Exception as e:
                resultado['errores'].append(f"Fila {index + 2}: Error al procesar - {str(e)}")
        
        # Guardar todos los cambios
        if resultado['creados'] > 0 or resultado['actualizados'] > 0:
            db.session.commit()
            resultado['exito'] = True
            resultado['mensaje'] = 'Importación completada exitosamente'
        elif len(resultado['errores']) > 0:
            resultado['mensaje'] = 'No se pudo importar ninguna materia debido a errores'
        else:
            resultado['mensaje'] = 'No se encontraron registros para procesar'
        
    except pd.errors.EmptyDataError:
        resultado['mensaje'] = 'El archivo está vacío o no tiene datos válidos'
    except pd.errors.ParserError:
        resultado['mensaje'] = 'Error al leer el archivo. Verifica que sea un CSV válido'
    except Exception as e:
        db.session.rollback()
        resultado['mensaje'] = f"Error al leer el archivo: {str(e)}"
    
    return resultado

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