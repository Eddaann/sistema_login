# Gestión de Grupos y Asignación de Materias a Profesores

## 📋 Resumen de Cambios

Se han implementado las siguientes mejoras al sistema para permitir la gestión de grupos y la asignación de materias a profesores:

### 1. **Grupos en Horarios Académicos**
- Ahora cada horario académico incluye un campo `grupo` (A, B, C, D, etc.)
- Esto permite que la misma materia tenga múltiples grupos con diferentes profesores
- Ejemplo: "Matemáticas - Grupo A" con Profesor Juan, "Matemáticas - Grupo B" con Profesora María

### 2. **Relación Profesor-Materias**
- Nueva tabla intermedia `profesor_materias` para relación many-to-many
- Los profesores ahora tienen un atributo `materias` que lista todas las materias que imparten
- Permite asignar materias a profesores de forma independiente a los horarios

## 🔧 Cambios Técnicos

### Modelo `User` (Profesor)
```python
# Nuevo campo: relación con materias
materias = db.relationship('Materia', secondary='profesor_materias', 
                          backref=db.backref('profesores', lazy=True))
```

**Métodos disponibles:**
- `profesor.materias` - Lista de materias asignadas al profesor
- `materia.profesores` - Lista de profesores que imparten la materia

### Modelo `HorarioAcademico`
```python
# Nuevo campo obligatorio
grupo = db.Column(db.String(10), nullable=False, default='A')
```

**Métodos disponibles:**
- `horario.get_materia_codigo_grupo()` - Retorna "MAT-101 - Grupo A"
- `horario.grupo` - Código del grupo ('A', 'B', 'C', etc.)

## 📊 Estructura de Base de Datos

### Tabla `profesor_materias` (nueva)
```sql
CREATE TABLE profesor_materias (
    profesor_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    PRIMARY KEY (profesor_id, materia_id),
    FOREIGN KEY (profesor_id) REFERENCES user(id),
    FOREIGN KEY (materia_id) REFERENCES materia(id)
)
```

### Tabla `horario_academico` (modificada)
```sql
-- Nueva columna agregada
grupo VARCHAR(10) DEFAULT 'A' NOT NULL
```

## 💡 Casos de Uso

### Caso 1: Múltiples Grupos de la Misma Materia
```
Materia: Programación I (PRG-101)
- Grupo A: Profesor Juan García (Lunes 7:00-8:40)
- Grupo B: Profesora María López (Lunes 9:00-10:40)
- Grupo C: Profesor Pedro Sánchez (Martes 7:00-8:40)
```

### Caso 2: Profesor con Múltiples Materias
```
Profesor: Juan García
Materias asignadas:
- Programación I (PRG-101)
- Base de Datos (BDD-201)
- Estructura de Datos (EDD-301)

Horarios:
- PRG-101 Grupo A: Lunes 7:00-8:40
- BDD-201 Grupo A: Martes 9:00-10:40
- EDD-301 Grupo B: Miércoles 7:00-8:40
```

### Caso 3: Materia con Múltiples Profesores
```
Materia: Matemáticas I (MAT-101)
Profesores:
- Juan García (Grupo A)
- María López (Grupo B)
- Pedro Sánchez (Grupo C)
```

## 🎯 Flujo de Trabajo Recomendado

### 1. **Asignar Materias a Profesores** (Nuevo)
```python
# Asignar materias al profesor
profesor = User.query.get(profesor_id)
materia1 = Materia.query.get(materia1_id)
materia2 = Materia.query.get(materia2_id)

profesor.materias = [materia1, materia2]
db.session.commit()
```

### 2. **Crear Horarios con Grupos**
```python
# Crear horario para Grupo A
horario_a = HorarioAcademico(
    profesor_id=profesor1_id,
    materia_id=materia_id,
    horario_id=horario_id,
    dia_semana='lunes',
    grupo='A',  # ← Nuevo parámetro
    aula='A101',
    creado_por=admin_id
)

# Crear horario para Grupo B
horario_b = HorarioAcademico(
    profesor_id=profesor2_id,
    materia_id=materia_id,  # Misma materia
    horario_id=horario_id,
    dia_semana='lunes',
    grupo='B',  # ← Diferente grupo
    aula='A102',
    creado_por=admin_id
)

db.session.add(horario_a)
db.session.add(horario_b)
db.session.commit()
```

### 3. **Consultar Información**
```python
# Obtener materias de un profesor
profesor = User.query.get(profesor_id)
materias_del_profesor = profesor.materias

# Obtener profesores de una materia
materia = Materia.query.get(materia_id)
profesores_de_materia = materia.profesores

# Obtener horarios por grupo
horarios_grupo_a = HorarioAcademico.query.filter_by(
    materia_id=materia_id,
    grupo='A'
).all()
```

## 🔄 Migración de Datos Existentes

La migración `migrate_add_grupos.py` realiza automáticamente:

1. ✅ Agrega columna `grupo` con valor 'A' por defecto a horarios existentes
2. ✅ Crea tabla `profesor_materias`
3. ✅ Migra asignaciones existentes desde `horario_academico` a `profesor_materias`

**Horarios existentes:**
- Todos los horarios existentes tienen grupo 'A' por defecto
- Puedes editarlos para asignar diferentes grupos (B, C, D, etc.)

## 📝 Ejemplos de Código

### Asignar múltiples materias a un profesor
```python
from models import User, Materia, db

profesor = User.query.filter_by(email='juan.garcia@example.com').first()
materias_codigos = ['PRG-101', 'BDD-201', 'EDD-301']

for codigo in materias_codigos:
    materia = Materia.query.filter_by(codigo=codigo).first()
    if materia and materia not in profesor.materias:
        profesor.materias.append(materia)

db.session.commit()
print(f"Materias asignadas a {profesor.get_nombre_completo()}: {len(profesor.materias)}")
```

### Crear múltiples grupos para una materia
```python
from models import HorarioAcademico, db

grupos = ['A', 'B', 'C']
profesores_ids = [1, 2, 3]  # Diferentes profesores
aulas = ['A101', 'A102', 'A103']

for grupo, profesor_id, aula in zip(grupos, profesores_ids, aulas):
    horario = HorarioAcademico(
        profesor_id=profesor_id,
        materia_id=materia_id,
        horario_id=horario_id,
        dia_semana='lunes',
        grupo=grupo,
        aula=aula,
        creado_por=current_user.id
    )
    db.session.add(horario)

db.session.commit()
print(f"Creados {len(grupos)} grupos para la materia")
```

### Consultar disponibilidad por grupo
```python
# Verificar si un grupo ya tiene horario asignado
def grupo_disponible(materia_id, grupo, dia, horario_id):
    existe = HorarioAcademico.query.filter_by(
        materia_id=materia_id,
        grupo=grupo,
        dia_semana=dia,
        horario_id=horario_id,
        activo=True
    ).first()
    return existe is None

# Uso
if grupo_disponible(materia_id, 'A', 'lunes', horario_id):
    # Crear nuevo horario para grupo A
    pass
else:
    print("El grupo A ya tiene horario en este día/hora")
```

## 🚀 Próximas Implementaciones Sugeridas

### Interfaces de Usuario
1. **Vista de Gestión de Profesores**
   - Agregar sección "Materias Asignadas"
   - Botón "Asignar Materias" con modal de selección múltiple

2. **Vista de Creación de Horarios**
   - Campo desplegable para seleccionar grupo (A, B, C, D, etc.)
   - Validación de conflictos por grupo

3. **Vista de Materias**
   - Mostrar profesores asignados a cada materia
   - Indicar cuántos grupos tiene cada materia

4. **Reportes**
   - Reporte de carga académica por profesor (por materia y grupo)
   - Reporte de grupos por materia
   - Reporte de distribución de profesores

### Validaciones Adicionales
- Evitar que un profesor tenga dos horarios simultáneos en el mismo grupo
- Validar que no haya solapamiento de aulas para el mismo horario
- Alertar si un profesor tiene carga académica excesiva

## 📞 Soporte

Para dudas o problemas con la implementación, consulta la documentación principal en `DOCUMENTATION.md`.
