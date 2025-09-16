# Sistema de Gestión Académica

## 📋 Descripción General

Sistema web completo desarrollado en Flask para la gestión académica con funcionalidades de autenticación de usuarios, gestión de horarios, profesores y carreras universitarias.

## 🚀 Características Principales

### ✅ Sistema de Autenticación
- **Registro de usuarios** con validación completa
- **Inicio de sesión** seguro con hash de contraseñas
- **Roles de usuario**: Admin, Jefe de Carrera, Profesor de Tiempo Completo, Profesor por Asignatura
- **Protección de rutas** basada en roles
- **Gestión de sesiones** con Flask-Login

### ✅ Gestión de Horarios (Solo Administradores)
- **Creación** de horarios matutinos y vespertinos
- **Edición** y **eliminación** de horarios existentes
- **Validación** de horarios (inicio < fin, no solapamiento)
- **Interface responsiva** con formularios dinámicos

### ✅ Gestión de Carreras (Solo Administradores)
- **CRUD completo** de carreras universitarias
- **Códigos únicos** para cada carrera
- **Conteo automático** de profesores por carrera
- **Estadísticas** de distribución por tipo de profesor

### ✅ Gestión de Profesores (Solo Administradores)
- **Listado completo** de profesores con filtros avanzados
- **Filtrado por carrera** y tipo de profesor
- **Búsqueda por nombre**, apellido, usuario o email
- **Importación masiva** desde archivos CSV/Excel
- **Exportación a PDF** con filtros aplicables
- **Activar/desactivar** profesores
- **Estadísticas en tiempo real**

### ✅ Importación y Exportación
- **Importación CSV/Excel** con validación de datos
- **Plantillas descargables** para importación
- **Reporte de errores** detallado en importación
- **Exportación PDF** personalizable con filtros
- **Manejo de archivos** seguro con validación de tipos

## 📁 Estructura del Proyecto

```
sistema_login/
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── forms.py               # Formularios WTF
├── utils.py               # Utilidades (import/export)
├── requirements.txt       # Dependencias
├── README.md             # Documentación
├── templates/            # Plantillas HTML
│   ├── base.html         # Plantilla base
│   ├── index.html        # Página principal
│   ├── login.html        # Login
│   ├── register.html     # Registro
│   ├── dashboard.html    # Dashboard principal
│   ├── admin/           # Plantillas de administración
│   │   ├── horarios.html
│   │   ├── horario_form.html
│   │   ├── eliminar_horario.html
│   │   ├── carreras.html
│   │   ├── carrera_form.html
│   │   ├── profesores.html
│   │   └── importar_profesores.html
│   └── errors/          # Páginas de error
│       ├── 404.html
│       └── 500.html
├── static/              # Archivos estáticos
│   └── css/
│       └── style.css    # Estilos personalizados
└── instance/            # Base de datos SQLite
    └── sistema_academico.db
```

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask 2.3.3, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, Font Awesome, JavaScript
- **Base de datos**: SQLite
- **Validación**: WTForms, Flask-WTF
- **Archivos**: pandas, openpyxl, reportlab
- **Seguridad**: Werkzeug (hash de contraseñas)

## 📦 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone [repo-url]
cd sistema_login
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python app.py
```

### 4. Acceder al sistema
- **URL**: http://127.0.0.1:5001
- **Usuario admin**: admin
- **Contraseña**: admin123

## 👥 Roles y Permisos

### 🔑 Administrador
- Acceso completo a todas las funcionalidades
- Gestión de usuarios, horarios, carreras y profesores
- Importación y exportación de datos
- Reportes y estadísticas

### 👨‍💼 Jefe de Carrera
- Acceso a dashboard básico
- Funcionalidades específicas por implementar

### 👨‍🏫 Profesor (Tiempo Completo / Por Asignatura)
- Acceso a dashboard básico
- Visualización de información personal
- Funcionalidades específicas por implementar

## 📊 Funcionalidades de Importación

### Formato de Archivo CSV/Excel para Profesores
```csv
username,email,nombre,apellido,telefono,tipo_profesor,carrera_codigo
jperez,juan.perez@universidad.edu,Juan,Pérez,555-1234,profesor_completo,ISI
```

### Validaciones de Importación
- ✅ Usuarios únicos (username y email)
- ✅ Formato de email válido
- ✅ Códigos de carrera existentes
- ✅ Tipos de profesor válidos
- ✅ Campos requeridos completos

## 📈 Funcionalidades de Exportación

### Reportes PDF
- **Filtros aplicables**: Carrera, tipo de profesor
- **Información incluida**: Datos completos del profesor
- **Formato**: Tabular con diseño profesional
- **Descarga automática** con nombre descriptivo

## 🔧 Configuración Avanzada

### Variables de Entorno
```python
SECRET_KEY = 'tu_clave_secreta_aqui_cambiala_en_produccion'
SQLALCHEMY_DATABASE_URI = 'sqlite:///sistema_academico.db'
```

### Configuración de Base de Datos
- **Creación automática** al primer arranque
- **Usuario admin por defecto** (admin/admin123)
- **Horarios predeterminados** (Matutino: 07:00-12:00, Vespertino: 13:00-18:00)
- **Carreras de ejemplo** pre-cargadas

## 🎨 Interfaz de Usuario

### Características del Frontend
- **Diseño responsivo** con Bootstrap 5
- **Iconografía** Font Awesome
- **Validación en tiempo real** con JavaScript
- **Mensajes flash** para feedback del usuario
- **Modales interactivos** para acciones críticas
- **Filtros dinámicos** con AJAX

### Paleta de Colores
- **Primario**: #007bff (Azul Bootstrap)
- **Secundario**: #6c757d (Gris)
- **Éxito**: #28a745 (Verde)
- **Advertencia**: #ffc107 (Amarillo)
- **Peligro**: #dc3545 (Rojo)
- **Purple personalizado**: #6f42c1

## 🔒 Seguridad

### Medidas Implementadas
- **Hash de contraseñas** con Werkzeug
- **Protección CSRF** con Flask-WTF
- **Validación de archivos** por tipo y tamaño
- **Sanitización de datos** en formularios
- **Control de acceso** basado en roles
- **Sesiones seguras** con Flask-Login

## 📝 Modelos de Datos

### Usuario (User)
- **Información personal**: nombre, apellido, email, teléfono
- **Credenciales**: username, password_hash
- **Rol y tipo**: rol, tipo_profesor
- **Relaciones**: carrera_id (para profesores)
- **Metadatos**: fecha_registro, activo

### Carrera
- **Información**: nombre, código, descripción
- **Metadatos**: activa, fecha_creacion, creada_por
- **Métodos**: conteos de profesores por tipo

### Horario
- **Configuración**: nombre, turno, hora_inicio, hora_fin
- **Validación**: horarios no solapados
- **Metadatos**: activo, fecha_creacion

## 🚦 Testing y Validación

### URLs Principales
- `/` - Página principal
- `/login` - Inicio de sesión
- `/register` - Registro
- `/dashboard` - Dashboard principal
- `/admin/horarios` - Gestión de horarios
- `/admin/carreras` - Gestión de carreras
- `/admin/profesores` - Gestión de profesores

### Casos de Prueba Sugeridos
1. **Registro** con diferentes roles
2. **Login/logout** de usuarios
3. **Creación** de horarios con validaciones
4. **Importación** de profesores válidos/inválidos
5. **Exportación** con diferentes filtros
6. **Navegación** entre secciones

## 🚀 Próximas Mejoras

### Funcionalidades Planeadas
- [ ] **Asignación de materias** a profesores
- [ ] **Programación académica** completa
- [ ] **Reportes avanzados** y dashboard
- [ ] **Notificaciones** en tiempo real
- [ ] **API REST** para integraciones
- [ ] **Backup automático** de base de datos

### Optimizaciones Técnicas
- [ ] **Migración a PostgreSQL** para producción
- [ ] **Cache con Redis** para mejor rendimiento
- [ ] **Tests unitarios** completos
- [ ] **Docker** para despliegue
- [ ] **CI/CD pipeline**

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema, contacta al equipo de desarrollo.

---

**Sistema de Gestión Académica v1.0**  
*Desarrollado con ❤️ usando Flask y Bootstrap*