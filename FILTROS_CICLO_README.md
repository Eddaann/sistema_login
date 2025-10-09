# Filtros por Ciclo Escolar - Módulo de Materias

## Descripción
Se ha agregado la funcionalidad de filtrar materias por ciclo escolar tanto para administradores como para jefes de carrera.

## Funcionalidades Implementadas

### 1. Filtro por Ciclo Escolar
Los usuarios ahora pueden filtrar las materias por ciclo escolar:

- **Ciclo 1**: Muestra solo materias de cuatrimestres 1, 4, 7, 10
- **Ciclo 2**: Muestra solo materias de cuatrimestres 2, 5, 8
- **Ciclo 3**: Muestra solo materias de cuatrimestres 0, 3, 6, 9

### 2. Filtros Combinables
Los filtros se pueden combinar para búsquedas más específicas:

- **Para Administradores**:
  - Carrera
  - Ciclo Escolar
  - Cuatrimestre específico
  - Búsqueda por texto (nombre, código)

- **Para Jefes de Carrera**:
  - Ciclo Escolar
  - Cuatrimestre específico

### 3. Interfaz de Usuario

#### Administradores (`/admin/materias`)
- 4 filtros en la parte superior
- Diseño de 3 columnas para mejor organización
- Botón para limpiar filtros

#### Jefes de Carrera (`/jefe-carrera/materias`)
- Sección de filtros con card separado
- 2 filtros: Ciclo Escolar y Cuatrimestre
- Botón para filtrar y botón para limpiar

## Cambios en los Archivos

### 1. `forms.py`
- **FiltrarMateriasForm**: Agregado campo `ciclo` con opciones de Ciclo 1, 2 y 3
- Agregado Cuatrimestre 0 a las opciones de cuatrimestre

### 2. `app.py`

#### Ruta `gestionar_materias()` (Admin)
```python
# Nuevo filtro por ciclo
ciclo = int(ciclo_str) if ciclo_str and ciclo_str != '' else None

# Aplicar filtro por ciclo
if ciclo:
    if ciclo == 1:
        query = query.filter(Materia.cuatrimestre % 3 == 1)
    elif ciclo == 2:
        query = query.filter(Materia.cuatrimestre % 3 == 2)
    elif ciclo == 3:
        query = query.filter(Materia.cuatrimestre % 3 == 0)
```

#### Ruta `gestionar_materias_jefe()` (Jefe de Carrera)
- Agregada lógica completa de filtrado
- Soporte para filtro por ciclo y cuatrimestre
- Query optimizado para la carrera del jefe

### 3. Plantillas

#### `templates/admin/materias.html`
- Reorganizado layout de filtros a 4 columnas
- Agregado campo de ciclo escolar
- Actualizado formulario de exportación

#### `templates/jefe/materias.html`
- Agregada sección completa de filtros
- Card de filtros separado del listado
- Diseño responsive con botones de acción

## Uso

### Filtrar por Ciclo Escolar
1. Ir al módulo de Materias
2. Seleccionar el ciclo deseado del dropdown "Ciclo Escolar"
3. (Opcional) Combinar con otros filtros
4. Hacer clic en "Filtrar"

### Limpiar Filtros
- **Admin**: Hacer clic en "Limpiar Filtros"
- **Jefe**: Hacer clic en el botón "×"

## Ejemplo de Filtrado

### Caso 1: Ver todas las materias del Ciclo 3 (2025-2026)
- Seleccionar "Ciclo 3" en el filtro
- Se mostrarán materias de cuatrimestres 0, 3, 6, 9

### Caso 2: Ver solo materias del Cuatrimestre 3 de Ingeniería
- Carrera: Ingeniería en Sistemas
- Ciclo: Ciclo 3
- Cuatrimestre: Cuatrimestre 3

### Caso 3: Búsqueda combinada
- Ciclo: Ciclo 1
- Búsqueda: "Programación"
- Resultado: Solo materias con "Programación" en su nombre de los cuatrimestres 1, 4, 7, 10

## Lógica de Filtrado

El filtrado por ciclo utiliza la operación módulo:
```python
# Ciclo 1: cuatrimestre % 3 == 1
# Ciclo 2: cuatrimestre % 3 == 2
# Ciclo 3: cuatrimestre % 3 == 0
```

Esto permite que los cuatrimestres se distribuyan automáticamente en ciclos repetitivos.

## Beneficios

1. **Organización mejorada**: Las materias se pueden ver por períodos académicos
2. **Búsqueda más rápida**: Menos materias que revisar cuando se filtra por ciclo
3. **Planificación académica**: Facilita la visualización de materias por período escolar
4. **Compatibilidad**: Funciona con los filtros existentes sin conflictos
