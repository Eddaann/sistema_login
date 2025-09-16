# Sistema de Login y Registro Académico

Sistema web desarrollado en Python con Flask que implementa un sistema de autenticación con diferentes roles de usuario: Administrador, Jefe de Carrera, Profesor de Tiempo Completo y Profesor por Asignatura.

## Características

- **Sistema de autenticación seguro** con encriptación de contraseñas
- **Múltiples roles de usuario**:
  - Administrador: Acceso completo al sistema
  - Jefe de Carrera: Gestión académica y de profesores
  - Profesor de Tiempo Completo: Acceso completo a funciones docentes
  - Profesor por Asignatura: Acceso limitado a materias asignadas
- **Interfaz moderna** con Bootstrap 5
- **Base de datos SQLite** (fácil de configurar)
- **Formularios con validación** automática
- **Dashboard personalizado** según el rol del usuario

## Instalación

### Requisitos previos
- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd sistema_login
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # En macOS/Linux:
   source venv/bin/activate
   
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Abrir en el navegador**
   ```
   http://localhost:5000
   ```

## Uso del Sistema

### Usuario Administrador por Defecto
Al ejecutar la aplicación por primera vez, se crea automáticamente un usuario administrador:
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Rol**: Administrador

### Registro de Nuevos Usuarios

1. Visita `http://localhost:5000/register`
2. Completa el formulario con:
   - Nombre y apellido
   - Usuario único
   - Email válido
   - Teléfono (opcional)
   - Contraseña (mínimo 6 caracteres)
   - Selecciona el rol:
     - **Administrador**: Acceso completo
     - **Jefe de Carrera**: Gestión académica
     - **Profesor**: Selecciona entre tiempo completo o por asignatura

### Funcionalidades por Rol

#### Administrador
- Gestión completa de usuarios
- Configuración del sistema
- Reportes generales
- Administración de seguridad

#### Jefe de Carrera
- Gestión de profesores de la carrera
- Administración del plan de estudios
- Gestión de horarios académicos
- Reportes académicos específicos

#### Profesor de Tiempo Completo
- Gestión de materias asignadas
- Registro de calificaciones
- Control de asistencia
- Acceso a funciones de investigación

#### Profesor por Asignatura
- Gestión de materias específicas asignadas
- Registro de calificaciones
- Control de asistencia
- Acceso limitado (solo materias asignadas)

## Estructura del Proyecto

```
sistema_login/
├── app.py                 # Aplicación principal Flask
├── models.py              # Modelos de base de datos
├── forms.py               # Formularios WTF
├── requirements.txt       # Dependencias de Python
├── README.md             # Este archivo
├── templates/            # Plantillas HTML
│   ├── base.html         # Plantilla base
│   ├── index.html        # Página principal
│   ├── login.html        # Página de login
│   ├── register.html     # Página de registro
│   └── dashboard.html    # Dashboard de usuario
└── static/               # Archivos estáticos
    └── css/
        └── style.css     # Estilos personalizados
```

## Configuración

### Variables de Configuración (app.py)
- `SECRET_KEY`: Cambia esta clave en producción
- `SQLALCHEMY_DATABASE_URI`: Configuración de base de datos
- Debug mode: Desactiva en producción

### Base de Datos
El sistema utiliza SQLite por defecto. La base de datos se crea automáticamente en `sistema_academico.db`.

## Personalización

### Agregar Nuevos Campos
1. Modifica el modelo `User` en `models.py`
2. Actualiza los formularios en `forms.py`
3. Modifica las plantillas HTML correspondientes

### Cambiar Estilos
- Modifica `static/css/style.css` para personalizar la apariencia
- Las plantillas usan Bootstrap 5 para el diseño responsivo

### Agregar Nuevas Rutas
1. Define nuevas rutas en `app.py`
2. Crea las plantillas correspondientes en `templates/`
3. Agrega validaciones de roles si es necesario

## Seguridad

- Las contraseñas se almacenan encriptadas usando Werkzeug
- Validación de formularios en el servidor
- Control de acceso basado en roles
- Protección CSRF con Flask-WTF

## Producción

Para desplegar en producción:

1. Cambia `SECRET_KEY` por una clave segura
2. Configura una base de datos más robusta (PostgreSQL, MySQL)
3. Desactiva el modo debug
4. Usa un servidor WSGI como Gunicorn
5. Configura HTTPS

## Solución de Problemas

### Error de importación de módulos
```bash
pip install -r requirements.txt
```

### Base de datos no se crea
Verifica que tengas permisos de escritura en el directorio del proyecto.

### Puerto en uso
Cambia el puerto en `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

## Contribuir

1. Fork del proyecto
2. Crea una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.