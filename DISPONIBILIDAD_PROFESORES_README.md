# 📅 Sistema de Disponibilidad Horaria para Profesores

## 📋 Descripción

El sistema de disponibilidad horaria permite que los profesores configuren los horarios en los que están disponibles para impartir clases. Esta información es utilizada automáticamente por el generador de horarios para crear horarios académicos óptimos que respeten las restricciones de cada profesor.

## ✨ Características Principales

### Para Profesores

1. **Configuración de Disponibilidad**
   - Interfaz visual tipo matriz (días × horarios)
   - Selección mediante checkboxes
   - Botones de selección rápida (todo, día completo, etc.)
   - Contador en tiempo real de horarios seleccionados
   - Resumen visual por día

2. **Acceso Fácil**
   - Disponible desde el panel del profesor
   - Actualizable en cualquier momento
   - Sin necesidad de permisos especiales

3. **Validaciones**
   - Confirmación si no se selecciona ningún horario
   - Guardado automático de configuración
   - Historial de cambios (registros antiguos quedan inactivos)

### Para el Sistema

1. **Generación Automática de Horarios**
   - El generador de horarios (`generador_horarios.py`) lee automáticamente las disponibilidades
   - Restricción integrada: no se asignan clases en horarios no disponibles
   - Optimización mediante Google OR-Tools CP-SAT

2. **Modelo de Datos**
   - Tabla `disponibilidad_profesor` en la base de datos
   - Campos: profesor_id, horario_id, dia_semana, disponible, activo
   - Relaciones con User y Horario

## 🚀 Uso

### Para Profesores

#### 1. Acceder a la Configuración

Desde el panel del profesor:
```
Panel del Profesor → Disponibilidad Horaria
```

O directamente:
```
/profesor/disponibilidad
```

#### 2. Configurar Horarios Disponibles

1. **Marcar horarios disponibles**:
   - Casilla marcada (✓) = Estás disponible
   - Casilla sin marcar = NO estás disponible

2. **Usar botones de selección rápida**:
   - **Seleccionar Todo**: Marca todos los horarios
   - **Deseleccionar Todo**: Desmarca todos los horarios
   - **[Día] Completo**: Selecciona/deselecciona un día específico

3. **Revisar el resumen**:
   - Contador total de horarios seleccionados
   - Contador por día en la parte inferior

4. **Guardar cambios**:
   - Click en "Guardar Disponibilidad"
   - Confirmación automática

#### 3. Ver Resultados

- Los horarios generados automáticamente respetarán tu disponibilidad
- No recibirás asignaciones en horarios marcados como no disponibles

### Para Administradores

#### Inicializar Disponibilidad de Profesores Existentes

Si ya tienes profesores en el sistema, ejecuta el script de inicialización:

```bash
python inicializar_disponibilidad.py
```

Este script:
- Busca todos los profesores activos
- Crea registros de disponibilidad marcando todos los horarios como disponibles
- Solo afecta a profesores sin disponibilidad configurada
- Muestra un resumen de los cambios realizados

#### Verificar Disponibilidad de un Profesor

Desde la consola de Python:

```python
from app import app
from models import User, DisponibilidadProfesor

with app.app_context():
    # Obtener un profesor
    profesor = User.query.filter_by(username='nombre_profesor').first()
    
    # Ver sus disponibilidades
    disponibilidades = DisponibilidadProfesor.query.filter_by(
        profesor_id=profesor.id,
        activo=True
    ).all()
    
    # Contar horarios disponibles
    disponibles = sum(1 for d in disponibilidades if d.disponible)
    print(f"Horarios disponibles: {disponibles}/{len(disponibilidades)}")
```

## 🔧 Implementación Técnica

### Estructura de la Base de Datos

```sql
CREATE TABLE disponibilidad_profesor (
    id INTEGER PRIMARY KEY,
    profesor_id INTEGER NOT NULL,
    horario_id INTEGER NOT NULL,
    dia_semana VARCHAR(10) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    creado_por INTEGER NOT NULL,
    FOREIGN KEY (profesor_id) REFERENCES user(id),
    FOREIGN KEY (horario_id) REFERENCES horario(id),
    FOREIGN KEY (creado_por) REFERENCES user(id)
);
```

### Modelo SQLAlchemy

```python
class DisponibilidadProfesor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)
    dia_semana = db.Column(db.String(10), nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
```

### Ruta Flask

```python
@app.route('/profesor/disponibilidad', methods=['GET', 'POST'])
@login_required
def profesor_disponibilidad():
    """Gestionar disponibilidad horaria del profesor"""
    # Implementación completa en app.py
```

### Integración con Generador de Horarios

El generador de horarios ya incluye la lógica necesaria:

```python
def cargar_disponibilidades(self):
    """Cargar las disponibilidades de todos los profesores"""
    for profesor in self.profesores:
        disponibilidades_profesor = DisponibilidadProfesor.query.filter(
            DisponibilidadProfesor.profesor_id == profesor.id,
            DisponibilidadProfesor.activo == True
        ).all()
        # Procesar y guardar en cache

def restriccion_disponibilidad_profesor(self):
    """Un profesor no puede dar clases cuando no está disponible"""
    for profesor in self.profesores:
        for horario in self.horarios:
            for dia_idx, dia in enumerate(self.dias_semana):
                disponible = self.verificar_disponibilidad_profesor(
                    profesor.id, horario.id, dia
                )
                if not disponible:
                    # Forzar variable a 0 (no asignar)
                    self.model.Add(var == 0)
```

## 📊 Flujo de Trabajo

```
1. Profesor se registra/inicia sesión
   ↓
2. Accede a "Disponibilidad Horaria"
   ↓
3. Selecciona horarios disponibles
   ↓
4. Guarda configuración
   ↓
5. Sistema almacena en base de datos
   ↓
6. Administrador genera horarios
   ↓
7. Generador lee disponibilidades
   ↓
8. Generador respeta restricciones
   ↓
9. Horarios creados sin conflictos
```

## ⚠️ Consideraciones Importantes

### Para Profesores

1. **Primera configuración**: Por defecto, todos los horarios están disponibles
2. **Actualización**: Puedes cambiar tu disponibilidad en cualquier momento
3. **Efecto**: Los cambios solo afectan a horarios futuros, no a los ya asignados
4. **Recomendación**: Sé preciso para evitar conflictos personales

### Para Administradores

1. **Verificación**: Siempre verifica las disponibilidades antes de generar horarios
2. **Comunicación**: Informa a los profesores sobre la importancia de mantener actualizada su disponibilidad
3. **Conflictos**: Si el generador no encuentra solución, puede deberse a disponibilidades muy restrictivas
4. **Balance**: Busca un equilibrio entre flexibilidad y restricciones

## 🐛 Solución de Problemas

### El generador no encuentra solución

**Posibles causas:**
- Disponibilidades muy restrictivas
- Pocos horarios disponibles comunes entre profesores
- Demasiadas materias para los horarios disponibles

**Soluciones:**
1. Pedir a los profesores ampliar su disponibilidad
2. Reducir la carga horaria por materia
3. Contratar más profesores
4. Ajustar los turnos (matutino/vespertino)

### Los horarios generados no respetan la disponibilidad

**Verificar:**
1. Que la disponibilidad esté marcada como `activo=True`
2. Que los registros tengan el `profesor_id` correcto
3. Que los horarios estén en el sistema
4. Que el día de la semana esté bien escrito ('lunes', no 'Lunes')

**Consulta SQL para verificar:**
```sql
SELECT p.nombre, p.apellido, dp.dia_semana, h.hora_inicio, h.hora_fin, dp.disponible
FROM disponibilidad_profesor dp
JOIN user p ON dp.profesor_id = p.id
JOIN horario h ON dp.horario_id = h.id
WHERE dp.activo = 1 AND p.id = [ID_PROFESOR]
ORDER BY dp.dia_semana, h.hora_inicio;
```

## 📈 Mejoras Futuras

1. **Disponibilidad temporal**: Configurar disponibilidad para períodos específicos
2. **Importación masiva**: Subir disponibilidades mediante CSV
3. **Preferencias**: Marcar horarios preferidos vs. aceptables
4. **Notificaciones**: Alertar a profesores cuando hay conflictos
5. **Historial**: Ver cambios históricos de disponibilidad
6. **Reportes**: Análisis de disponibilidad por carrera/departamento

## 📞 Soporte

Para dudas o problemas:
- Profesores: Contactar al administrador o jefe de carrera
- Administradores: Revisar logs del sistema y base de datos
- Desarrolladores: Consultar `models.py`, `app.py` y `generador_horarios.py`

## 📝 Registro de Cambios

### Versión 1.0 (Octubre 2025)
- ✅ Implementación inicial del sistema de disponibilidad
- ✅ Interfaz visual para profesores
- ✅ Integración con generador de horarios
- ✅ Script de inicialización
- ✅ Documentación completa

---

**Desarrollado para el Sistema de Gestión de Horarios Académicos**
