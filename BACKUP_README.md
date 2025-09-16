# Sistema de Backups Automáticos

Este documento explica cómo configurar y usar el sistema de backups automáticos del Sistema Académico.

## Configuración

### 1. Configuración Básica

El sistema de backups se configura desde la interfaz web en **Administración > Configuración > Base de Datos**.

Opciones disponibles:
- **Frecuencia**: Cada hora, Diario, Semanal, Mensual, Deshabilitado
- **Retención**: Días a mantener los backups antiguos (por defecto: 30 días)
- **Ubicación**: Directorio donde se almacenan los backups (por defecto: `backups/`)

### 2. Configuración de Base de Datos

El sistema soporta múltiples tipos de base de datos:

#### SQLite (Predeterminado)
- Archivo local: `instance/sistema_academico.db`
- No requiere configuración adicional
- Backups automáticos disponibles

#### PostgreSQL
Requiere instalar el driver:
```bash
pip install psycopg2-binary
```

#### MySQL/MariaDB
Requiere instalar el driver:
```bash
pip install mysql-connector-python
```

## Uso del Sistema de Backups

### 1. Backup Manual

Desde la interfaz web:
1. Ir a **Administración > Configuración**
2. En la sección "Base de Datos", hacer clic en "Backup Ahora"
3. El sistema creará un backup inmediato y lo registrará en el historial

### 2. Backup Automático

#### Configuración del Cron Job (Linux/Mac)

Editar el crontab:
```bash
crontab -e
```

Agregar una de estas líneas según la frecuencia deseada:

```bash
# Backup diario a las 2:00 AM
0 2 * * * cd /ruta/al/proyecto && python backup_manager.py auto

# Backup semanal (domingos a las 2:00 AM)
0 2 * * 0 cd /ruta/al/proyecto && python backup_manager.py auto

# Backup cada hora
0 * * * * cd /ruta/al/proyecto && python backup_manager.py auto
```

#### Configuración de Tarea Programada (Windows)

1. Abrir "Programador de Tareas"
2. Crear nueva tarea básica
3. Configurar:
   - **Programa**: `python.exe`
   - **Argumentos**: `backup_manager.py auto`
   - **Directorio**: Ruta completa al proyecto
4. Establecer frecuencia deseada

### 3. Verificación del Estado

Para verificar el estado del sistema de backups:

```bash
python backup_manager.py status
```

Esto mostrará:
- Número total de backups
- Backups automáticos vs manuales
- Fecha del último backup
- Espacio libre en disco

## Comandos Disponibles

### Ejecutar Backup Automático
```bash
python backup_manager.py auto
```

### Ejecutar Backup Manual
```bash
python backup_manager.py manual
```

### Ver Estado del Sistema
```bash
python backup_manager.py status
```

## Estructura de Archivos

```
sistema_login/
├── backups/           # Directorio de backups
│   ├── backup_20250116_143000.db
│   └── backup_auto_20250116_020000.db
├── logs/             # Logs del sistema
│   └── backup.log
├── backup_manager.py # Script de gestión de backups
└── instance/
    └── sistema_academico.db  # Base de datos original
```

## Características del Sistema

### ✅ Funcionalidades Implementadas

- **Backups automáticos**: Programables por hora, día, semana o mes
- **Backups manuales**: Creación inmediata desde la interfaz web
- **Historial completo**: Registro de todos los backups con metadatos
- **Limpieza automática**: Eliminación de backups antiguos según política
- **Verificación de integridad**: Checksum SHA256 para validar backups
- **Múltiples formatos**: Soporte para SQLite, PostgreSQL, MySQL, MariaDB
- **Interfaz web**: Gestión completa desde el navegador
- **Logs detallados**: Registro de todas las operaciones
- **Monitoreo de espacio**: Verificación de espacio disponible

### 🔧 Mantenimiento

#### Limpieza Manual de Backups Antiguos
```bash
# El sistema automáticamente elimina backups según la política de retención
# Para limpieza manual, eliminar archivos del directorio backups/
# y registros de la tabla BackupHistory
```

#### Verificación de Integridad
Cada backup incluye un checksum SHA256 para verificar integridad:
```python
# Verificar checksum de un backup
import hashlib
with open('backups/backup_file.db', 'rb') as f:
    checksum = hashlib.sha256(f.read()).hexdigest()
```

#### Monitoreo de Logs
Los logs se almacenan en `logs/backup.log` con formato:
```
2025-01-16 14:30:00 - INFO - Backup automático completado: backup_auto_20250116_143000.db
```

## Solución de Problemas

### Error: "Archivo de base de datos no encontrado"
- Verificar que existe `instance/sistema_academico.db`
- Revisar permisos de lectura del archivo

### Error: "No se puede escribir en directorio de backups"
- Verificar permisos de escritura en el directorio `backups/`
- Crear el directorio manualmente si es necesario

### Error: "Driver de base de datos no encontrado"
- Instalar el driver correspondiente:
  - PostgreSQL: `pip install psycopg2-binary`
  - MySQL: `pip install mysql-connector-python`

### Backups no se ejecutan automáticamente
- Verificar que el cron job esté configurado correctamente
- Revisar logs en `logs/backup.log`
- Verificar que Python esté en el PATH del sistema

## Recomendaciones de Seguridad

1. **Almacenamiento**: Mantener backups en ubicación segura y separada
2. **Encriptación**: Considerar encriptar backups sensibles
3. **Acceso**: Limitar permisos de acceso a archivos de backup
4. **Monitoreo**: Revisar logs regularmente para detectar anomalías
5. **Retención**: Configurar política de retención según necesidades

## Soporte

Para soporte técnico o reportar problemas, consultar los logs del sistema o contactar al administrador.