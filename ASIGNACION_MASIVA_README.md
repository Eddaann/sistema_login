# Módulo de Asignación Masiva de Materias

## Descripción General

El módulo de **Asignación Masiva de Materias** es una herramienta diseñada para facilitar la asignación de materias a múltiples profesores de forma eficiente, evitando el tedioso proceso de asignar materias profesor por profesor, cuatrimestre por cuatrimestre.

## Características Principales

### 1. Interfaz de Matriz
- **Visualización en tabla bidimensional**: Los profesores se muestran en filas y las materias en columnas
- **Identificación clara**: Cada materia se identifica por su cuatrimestre y código (ej: C1: MAT101)
- **Indicadores visuales**:
  - ✅ Check verde: Materia ya asignada al profesor
  - ☐ Checkbox: Permite crear nueva asignación

### 2. Filtros Inteligentes

#### Para Administradores:
- **Filtro por Carrera**: Muestra solo profesores y materias de una carrera específica
- **Filtro por Cuatrimestre**: Enfoca la vista en un cuatrimestre particular
- **Combinación de filtros**: Permite filtrar por carrera Y cuatrimestre simultáneamente

#### Para Jefes de Carrera:
- **Filtro por Cuatrimestre**: Muestra materias de un cuatrimestre específico
- **Restricción automática**: Solo muestra profesores y materias de su carrera asignada

### 3. Estadísticas en Tiempo Real
- **Profesores**: Total de profesores mostrados
- **Materias Disponibles**: Total de materias según filtros aplicados
- **Asignaciones Seleccionadas**: Contador dinámico de nuevas asignaciones
- **Asignaciones Actuales**: Total de asignaciones ya existentes

### 4. Controles de Selección Masiva
- **Seleccionar Todas**: Marca todas las asignaciones disponibles (excluye las ya existentes)
- **Limpiar Selección**: Desmarca todas las selecciones actuales
- **Contador dinámico**: Se actualiza en tiempo real al marcar/desmarcar casillas

## Acceso al Módulo

### Para Administradores:
1. Accede al **Dashboard Principal**
2. Busca la tarjeta "Asignación Masiva de Materias" (color rojo)
3. Haz clic en el botón **"Asignar"**
4. URL directa: `/admin/asignacion-masiva-materias`

### Para Jefes de Carrera:
1. Accede al **Dashboard Principal**
2. Busca la tarjeta "Asignación Masiva de Materias" (color rojo)
3. Haz clic en el botón **"Asignar"**
4. URL directa: `/jefe-carrera/asignacion-masiva-materias`

## Flujo de Trabajo

### Paso 1: Aplicar Filtros (Opcional)
```
1. Selecciona una carrera (solo admin)
2. Selecciona un cuatrimestre
3. Haz clic en "Filtrar"
```

### Paso 2: Revisar la Matriz
```
1. Revisa los profesores en las filas
2. Identifica las materias en las columnas (C1: MAT101, C2: FIS201, etc.)
3. Las marcas verdes ✅ indican asignaciones existentes
```

### Paso 3: Seleccionar Asignaciones
```
Opción A - Selección Manual:
  - Marca las casillas individualmente
  - El contador se actualiza automáticamente

Opción B - Selección Masiva:
  - Clic en "Seleccionar Todas" para marcar todas las disponibles
  - Opcionalmente, desmarca las que no deseas asignar
```

### Paso 4: Guardar
```
1. Verifica el contador de asignaciones seleccionadas
2. Haz clic en "Guardar X Asignaciones"
3. Confirma la acción en el diálogo
4. Espera el mensaje de confirmación
```

## Casos de Uso Prácticos

### Caso 1: Asignar todas las materias de un cuatrimestre
```
1. Filtra por "Cuatrimestre 1"
2. Haz clic en "Seleccionar Todas"
3. Guarda las asignaciones
```

### Caso 2: Asignar materias de una carrera específica
```
1. Filtra por "Carrera X"
2. Opcionalmente, filtra también por cuatrimestre
3. Selecciona las asignaciones deseadas
4. Guarda los cambios
```

### Caso 3: Asignar materias solo a ciertos profesores
```
1. Aplica filtros para reducir la lista de profesores
2. Revisa fila por fila
3. Marca solo las casillas de los profesores deseados
4. Guarda las asignaciones
```

## Ventajas del Módulo

### ✅ Eficiencia
- **Reducción de tiempo**: De minutos/horas a segundos
- **Menos clics**: Una operación vs. múltiples formularios
- **Proceso paralelo**: Asigna a múltiples profesores simultáneamente

### ✅ Visibilidad
- **Vista completa**: Toda la información en una pantalla
- **Estado actual**: Fácil identificación de asignaciones existentes
- **Estadísticas**: Información en tiempo real

### ✅ Control
- **Filtros flexibles**: Enfoca solo en lo necesario
- **Confirmación**: Diálogo de confirmación antes de guardar
- **Feedback claro**: Mensajes de éxito/error detallados

### ✅ Usabilidad
- **Interfaz intuitiva**: Diseño tipo hoja de cálculo familiar
- **Scroll optimizado**: Primera columna fija al hacer scroll horizontal
- **Responsive**: Adaptable a diferentes tamaños de pantalla

## Detalles Técnicos

### Permisos
- **Admin**: Acceso completo a todas las carreras y profesores
- **Jefe de Carrera**: Solo profesores y materias de su carrera asignada

### Validaciones
- **Duplicados**: No permite asignar materias ya asignadas
- **Pertenencia**: Jefes solo pueden asignar profesores/materias de su carrera
- **Existencia**: Verifica que profesores y materias existan

### Formato de Datos
- Las asignaciones se envían como: `profesor_id-materia_id`
- Ejemplo: `15-42` (profesor 15, materia 42)

### Transacción
- Todas las asignaciones se procesan en una sola transacción
- Si hay error, se hace rollback completo
- Mensajes de éxito/error detallados

## Limitaciones Conocidas

1. **Scroll en tablas grandes**: Con muchas materias (>50), puede ser necesario scroll horizontal
2. **Solo nuevas asignaciones**: No permite eliminar asignaciones existentes (usar gestión individual)
3. **Sin edición de horarios**: Solo asigna materias, no configura horarios

## Recomendaciones de Uso

### ✅ Buenas Prácticas
- Usa filtros para reducir la cantidad de datos mostrados
- Revisa las estadísticas antes de guardar
- Confirma las selecciones antes de hacer clic en guardar
- Usa "Limpiar Selección" si te equivocas, no recargues la página

### ❌ Evitar
- No intentes asignar todas las materias de todas las carreras sin filtrar
- No cierres la pestaña mientras se guardan los cambios
- No uses el botón "Atrás" del navegador después de guardar

## Solución de Problemas

### Problema: No aparecen profesores o materias
**Solución**: 
- Verifica que existan profesores activos
- Verifica que existan materias activas
- Limpia los filtros aplicados

### Problema: El botón "Guardar" está deshabilitado
**Solución**: 
- Marca al menos una casilla
- El botón solo se habilita con selecciones activas

### Problema: Error al guardar
**Solución**: 
- Verifica tu conexión a internet
- Revisa que tengas los permisos necesarios
- Contacta al administrador si persiste

## Mejoras Futuras Potenciales

- [ ] Exportar matriz a Excel
- [ ] Importar asignaciones desde CSV
- [ ] Opción de "desasignar" en la misma interfaz
- [ ] Filtro por tipo de profesor (completo/asignatura)
- [ ] Vista previa de cambios antes de guardar
- [ ] Historial de asignaciones masivas
- [ ] Comparar asignaciones entre cuatrimestres

## Notas de Versión

### Versión 1.0 (Actual)
- ✅ Matriz de asignación profesor-materia
- ✅ Filtros por carrera y cuatrimestre
- ✅ Estadísticas en tiempo real
- ✅ Selección masiva
- ✅ Confirmación de cambios
- ✅ Soporte para admin y jefe de carrera
- ✅ Validaciones de permisos
- ✅ Interfaz responsive

## Soporte

Para dudas o problemas con el módulo:
1. Consulta esta documentación
2. Revisa la sección "Ayuda" dentro del módulo
3. Contacta al administrador del sistema
