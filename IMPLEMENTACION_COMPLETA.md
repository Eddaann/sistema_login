# 🎓 Sistema de Gestión de Materias y Grupos - Implementación Completa

## ✅ Resumen de Implementación

Se ha implementado un sistema completo para gestionar la asignación dinámica de materias a profesores y el manejo de grupos, considerando que los profesores cambian de materias cada cuatrimestre.

---

## 🔧 Cambios Realizados

### 1. **Base de Datos** ✓

#### Migración ejecutada exitosamente:
- ✅ Tabla `profesor_materias` creada (relación many-to-many)
- ✅ Campo `grupo` agregado a `horario_academico`
- ✅ Datos migrados automáticamente

**Archivo:** `migrate_add_grupos.py`

### 2. **Modelos (models.py)** ✓

#### Cambios en `User`:
```python
# Nueva relación many-to-many con materias
materias = db.relationship('Materia', secondary='profesor_materias', ...)
```

#### Cambios en `HorarioAcademico`:
```python
# Nuevo campo obligatorio
grupo = db.Column(db.String(10), nullable=False, default='A')

# Nuevo método
def get_materia_codigo_grupo(self):
    return f"{codigo} - Grupo {self.grupo}"
```

### 3. **Formularios (forms.py)** ✓

#### Nuevo formulario: `AsignarMateriasProfesorForm`
- Permite selección múltiple de materias
- Filtra materias por carreras del profesor
- Muestra información organizada por cuatrimestre

#### Actualizado: `EditarHorarioAcademicoForm`
- Agregado campo `grupo` con opciones A-F
- Validación de grupo requerido

### 4. **Rutas y Vistas (app.py)** ✓

#### Nuevas rutas:

1. **`/admin/profesores/<id>/materias` (GET, POST)**
   - Asignar/modificar materias de un profesor
   - Muestra materias actuales y permite actualización
   - Valida que el usuario sea profesor

2. **`/admin/profesores/<id>/materias/ver` (GET)**
   - Ver detalle de materias asignadas
   - Muestra horarios agrupados por materia y grupo
   - Estadísticas de carga académica

#### Rutas actualizadas:

1. **`/admin/horarios-academicos/<id>/editar`**
   - Ahora incluye campo grupo
   - Guarda y precarga el grupo correctamente

2. **`/jefe/horarios-academicos/<id>/editar`**
   - Incluye campo grupo para jefes de carrera
   - Misma funcionalidad que admin

### 5. **Plantillas HTML** ✓

#### Nuevas plantillas creadas:

1. **`templates/admin/asignar_materias_profesor.html`**
   - Interfaz para asignar materias
   - Select múltiple con opciones organizadas
   - Muestra materias actuales en tabla
   - Instrucciones claras de uso

2. **`templates/admin/ver_materias_profesor.html`**
   - Vista detallada de materias del profesor
   - Estadísticas de carga académica
   - Horarios agrupados por materia y grupo
   - Navegación expandible/colapsable

#### Plantillas actualizadas:

3. **`templates/admin/editar_horario_academico.html`**
   - Campo grupo agregado con opciones A-F
   - Texto de ayuda explicativo

4. **`templates/jefe/editar_horario_academico.html`**
   - Campo grupo en diseño de 3 columnas
   - Mismo comportamiento que admin

5. **`templates/admin/profesores.html`**
   - Botón "Materias" para asignar materias
   - Botón "Ver Detalles" para ver materias y horarios
   - Badge con contador de materias asignadas
   - Integrado en panel expandible

---

## 📚 Flujo de Trabajo Completo

### Escenario: Asignar materias a un profesor para un nuevo cuatrimestre

#### **Paso 1: Asignar Materias al Profesor**

1. Ir a **Gestión de Profesores**
2. Hacer clic en la fila del profesor para expandir detalles
3. Hacer clic en botón **"Materias"**
4. Seleccionar las materias del cuatrimestre (mantener Ctrl/Cmd para selección múltiple)
5. Guardar cambios

**Ruta:** `/admin/profesores/<id>/materias`

#### **Paso 2: Crear Horarios con Grupos**

1. Ir a **Horarios Académicos**
2. Generar o editar un horario
3. Seleccionar:
   - Profesor
   - Materia (solo las asignadas al profesor)
   - Día y hora
   - **Grupo** (A, B, C, D, E, F)
   - Aula
4. Guardar

**Ruta:** `/admin/horarios-academicos/<id>/editar`

#### **Paso 3: Ver Carga del Profesor**

1. En Gestión de Profesores, expandir profesor
2. Hacer clic en **"Ver Detalles"**
3. Ver:
   - Materias por cuatrimestre
   - Grupos asignados
   - Horarios programados
   - Total de créditos

**Ruta:** `/admin/profesores/<id>/materias/ver`

---

## 💡 Casos de Uso

### Caso 1: Profesor con Múltiples Grupos de la Misma Materia

**Ejemplo:** Profesor Juan imparte Matemáticas I

```
Matemáticas I (MAT-101)
├─ Grupo A: Lunes 7:00-8:40 Aula A101
├─ Grupo B: Lunes 9:00-10:40 Aula A102
└─ Grupo C: Martes 7:00-8:40 Aula A103
```

**Cómo configurar:**
1. Asignar materia MAT-101 al profesor
2. Crear 3 horarios académicos:
   - Todos con materia MAT-101
   - Cada uno con grupo diferente (A, B, C)
   - Diferentes días/horarios/aulas

### Caso 2: Cambio de Materias al Siguiente Cuatrimestre

**Escenario:** Fin de cuatrimestre, profesor cambia asignaciones

**Cómo actualizar:**
1. Ir a `/admin/profesores/<id>/materias`
2. Deseleccionar materias del cuatrimestre anterior
3. Seleccionar nuevas materias del siguiente cuatrimestre
4. Guardar
5. Crear nuevos horarios académicos para las nuevas materias

**Nota:** Los horarios antiguos quedan como histórico (no se eliminan automáticamente)

### Caso 3: Mismo Profesor en Múltiples Carreras

**Ejemplo:** Profesor imparte materias en 2 carreras

```
Profesor: María López
Carreras: Ingeniería en Sistemas, Ingeniería en Robótica

Materias asignadas:
├─ ING-SIS: Programación I (Grupos A, B)
└─ IRO: Robótica I (Grupo A)
```

**Cómo configurar:**
1. Asignar ambas carreras al profesor en su perfil
2. Asignar materias de ambas carreras
3. Crear horarios con grupos para cada materia

---

## 🎯 Características Principales

### ✨ Asignación Dinámica
- ✅ Materias se pueden cambiar cada cuatrimestre
- ✅ No hay restricción de materias "fijas" por profesor
- ✅ Histórico de asignaciones se mantiene

### 📊 Gestión de Grupos
- ✅ Múltiples grupos (A-F) por materia
- ✅ Diferentes profesores por grupo
- ✅ Identificación clara: "MAT-101 - Grupo A"

### 👀 Visualización Clara
- ✅ Ver todas las materias de un profesor
- ✅ Ver todos los grupos de una materia
- ✅ Ver horarios organizados por materia/grupo
- ✅ Estadísticas de carga académica

### 🔒 Validaciones
- ✅ Solo se pueden asignar materias de carreras del profesor
- ✅ Grupo es obligatorio al crear horarios
- ✅ Campo grupo incluido en edición

---

## 📋 Interfaz de Usuario

### Panel de Profesores
```
┌─────────────────────────────────────────────┐
│ Profesor: Juan García                       │
├─────────────────────────────────────────────┤
│ Email: juan@example.com                     │
│ Tipo: Profesor de Tiempo Completo          │
│ Carreras: ING-SIS, IRO                      │
│ Materias: [5] asignadas                     │
├─────────────────────────────────────────────┤
│ [Materias] [Ver Detalles] [Cerrar]         │
└─────────────────────────────────────────────┘
```

### Asignación de Materias
```
┌─────────────────────────────────────────────┐
│ Seleccionar Materias                        │
├─────────────────────────────────────────────┤
│ ☑ Cuatri 1 - PRG-101: Programación I        │
│ ☑ Cuatri 1 - MAT-101: Matemáticas I         │
│ ☐ Cuatri 2 - BDD-201: Base de Datos         │
│ ☑ Cuatri 2 - EDD-201: Estructuras de Datos  │
│ ☐ Cuatri 3 - ISW-301: Ingeniería Software   │
└─────────────────────────────────────────────┘
   [Cancelar] [Asignar Materias]
```

### Edición de Horario
```
┌─────────────────────────────────────────────┐
│ Profesor: [Juan García ▼]                   │
│ Día:      [Lunes ▼]                         │
│ Grupo:    [A ▼]  ← NUEVO                    │
│ Aula:     [A101]                            │
└─────────────────────────────────────────────┘
```

---

## 🔄 Mantenimiento por Cuatrimestre

### Checklist al inicio de cuatrimestre:

- [ ] Revisar asignaciones de profesores por carrera
- [ ] Actualizar materias asignadas a cada profesor
- [ ] Generar nuevos horarios académicos
- [ ] Asignar grupos según demanda de estudiantes
- [ ] Verificar conflictos de horarios
- [ ] Validar asignación de aulas

---

## 📞 Funciones Disponibles por Código

### Consultar materias de un profesor
```python
profesor = User.query.get(profesor_id)
materias = profesor.materias  # Lista de objetos Materia
```

### Consultar profesores de una materia
```python
materia = Materia.query.get(materia_id)
profesores = materia.profesores  # Lista de objetos User
```

### Obtener horarios por grupo
```python
horarios = HorarioAcademico.query.filter_by(
    materia_id=materia_id,
    grupo='A',
    activo=True
).all()
```

### Asignar materias a un profesor
```python
profesor = User.query.get(profesor_id)
materias = Materia.query.filter(Materia.id.in_([1, 2, 3])).all()
profesor.materias = materias
db.session.commit()
```

---

## 🚀 Próximas Mejoras Sugeridas

### Corto plazo:
- [ ] Validación de conflictos de horarios por profesor
- [ ] Validación de conflictos de aulas
- [ ] Reporte de carga académica por profesor
- [ ] Exportar listado de materias por profesor a PDF

### Mediano plazo:
- [ ] Dashboard de estadísticas por cuatrimestre
- [ ] Histórico de asignaciones
- [ ] Comparador de carga entre cuatrimestres
- [ ] Sugerencias automáticas de grupos según capacidad

### Largo plazo:
- [ ] Integración con sistema de estudiantes
- [ ] Asignación automática de grupos según matrícula
- [ ] Optimización de horarios con IA
- [ ] App móvil para profesores

---

## ✅ Estado Final

| Componente | Estado | Archivo |
|------------|--------|---------|
| Migración DB | ✅ Completado | `migrate_add_grupos.py` |
| Modelo User | ✅ Actualizado | `models.py` |
| Modelo HorarioAcademico | ✅ Actualizado | `models.py` |
| Formulario Materias | ✅ Creado | `forms.py` |
| Formulario Horarios | ✅ Actualizado | `forms.py` |
| Ruta Asignar Materias | ✅ Creada | `app.py` |
| Ruta Ver Materias | ✅ Creada | `app.py` |
| Ruta Editar Horario Admin | ✅ Actualizada | `app.py` |
| Ruta Editar Horario Jefe | ✅ Actualizada | `app.py` |
| Template Asignar | ✅ Creado | `admin/asignar_materias_profesor.html` |
| Template Ver | ✅ Creado | `admin/ver_materias_profesor.html` |
| Template Editar Admin | ✅ Actualizado | `admin/editar_horario_academico.html` |
| Template Editar Jefe | ✅ Actualizado | `jefe/editar_horario_academico.html` |
| Template Profesores | ✅ Actualizado | `admin/profesores.html` |

---

## 📝 Notas Importantes

1. **Cambio de Cuatrimestre:**
   - Las materias NO se borran automáticamente
   - Debes actualizar manualmente las asignaciones
   - Los horarios antiguos quedan como histórico

2. **Grupos:**
   - Son obligatorios en todos los horarios
   - Permiten múltiples secciones de la misma materia
   - Se identifican con letras A-F (ampliable)

3. **Carreras del Profesor:**
   - Filtran las materias disponibles para asignar
   - Un profesor puede tener múltiples carreras
   - Las materias se muestran solo de esas carreras

4. **Permisos:**
   - Solo administradores pueden asignar materias
   - Jefes de carrera pueden editar horarios (incluyendo grupos)
   - Profesores solo ven su información

---

## 🎉 ¡Sistema Listo para Usar!

El sistema está completamente funcional y listo para gestionar:
- ✅ Asignación dinámica de materias cada cuatrimestre
- ✅ Múltiples grupos por materia
- ✅ Diferentes profesores por grupo
- ✅ Cambios flexibles de asignaciones
- ✅ Visualización clara de carga académica

**¡Listo para el nuevo cuatrimestre! 🚀**
