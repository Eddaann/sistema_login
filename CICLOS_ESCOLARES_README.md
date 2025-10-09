# Sistema de Ciclos Escolares

## Descripción
Se ha implementado un sistema de ciclos escolares que organiza los cuatrimestres en 3 ciclos que se repiten cada año académico.

## Distribución de Ciclos

### Ciclo 1: Cuatrimestres 1, 4, 7, 10
- **Período**: Año Actual - Año Actual
- **Ejemplo (2025)**: 2025 - 2025
- **Cuatrimestres**: 1, 4, 7, 10

### Ciclo 2: Cuatrimestres 2, 5, 8
- **Período**: Año Actual - Año Actual
- **Ejemplo (2025)**: 2025 - 2025
- **Cuatrimestres**: 2, 5, 8

### Ciclo 3: Cuatrimestres 0, 3, 6, 9
- **Período**: Año Actual - Año Siguiente
- **Ejemplo (2025)**: 2025 - 2026
- **Cuatrimestres**: 0, 3, 6, 9

## Cambios Implementados

### 1. Modelo Materia (`models.py`)
- **Nuevo método**: `get_ciclo_escolar()`
  - Calcula el ciclo escolar basado en el cuatrimestre
  - Retorna un diccionario con:
    - `ciclo`: Período del ciclo (ej: "2025 - 2026")
    - `numero`: Número del ciclo (1, 2 o 3)
    - `nombre`: Nombre descriptivo (ej: "Ciclo 3")

### 2. Modelo HorarioAcademico (`models.py`)
- **Campo actualizado**: `periodo_academico`
  - Ahora se calcula automáticamente basado en el ciclo de la materia
  - Formato: "YYYY - YYYY" (ej: "2025 - 2026")
- **Nuevos métodos**:
  - `get_ciclo_escolar()`: Obtiene la información del ciclo de la materia
  - `get_periodo_academico_display()`: Formatea el período para mostrar

### 3. Plantillas Actualizadas

#### Jefe de Carrera
- **materias.html**: Muestra el ciclo escolar en una nueva columna
- **horarios_academicos.html**: Muestra el ciclo escolar para cada horario

#### Administrador
- **materias.html**: Muestra el ciclo escolar en la tabla de materias
- **horarios_academicos.html**: Muestra el ciclo escolar con badge y nombre

## Ejemplo de Uso

```python
# Obtener información del ciclo de una materia
materia = Materia.query.get(1)
ciclo_info = materia.get_ciclo_escolar()

print(ciclo_info['ciclo'])   # "2025 - 2026"
print(ciclo_info['numero'])  # 3
print(ciclo_info['nombre'])  # "Ciclo 3"
```

## Cálculo del Ciclo

El ciclo se calcula usando la operación módulo 3 sobre el número de cuatrimestre:
- `cuatrimestre % 3 == 1` → Ciclo 1 (Año - Año)
- `cuatrimestre % 3 == 2` → Ciclo 2 (Año - Año)
- `cuatrimestre % 3 == 0` → Ciclo 3 (Año - Año+1)

## Actualización Automática

El año académico se actualiza automáticamente basándose en el año actual del sistema. No requiere configuración manual.

## Visualización

Los ciclos escolares se muestran en las siguientes vistas:
1. **Gestión de Materias** (Admin y Jefe de Carrera)
2. **Gestión de Horarios Académicos** (Admin y Jefe de Carrera)

Se utilizan badges de colores para una mejor identificación visual:
- **Badge info (azul)**: Muestra el período del ciclo
- **Texto pequeño (gris)**: Muestra el nombre del ciclo
