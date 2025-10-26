# 🎯 Mejoras al Generador de Horarios

## Fecha: 25 de Octubre, 2025

## 📋 Restricciones Implementadas

El generador de horarios ahora incluye **7 restricciones principales** para garantizar horarios óptimos y realistas:

### 1. ✅ Horas Semanales por Materia
- Cada materia debe tener **exactamente** las horas semanales configuradas
- Se respetan las horas teóricas + prácticas definidas en la materia
- **IMPORTANTE:** El generador usa `horas_teoricas + horas_practicas` de cada materia
- Ejemplo: Materia con 3h teóricas + 2h prácticas = 5 horas/semana a asignar
- Si una materia no tiene horas configuradas, se usan 3 horas por defecto
- Validación: máximo 15 horas por materia

### 2. ✅ Sin Conflictos de Profesor
- Un profesor **NO puede** tener dos clases simultáneamente
- Verifica día y horario para evitar sobreposiciones

### 3. ✅ Disponibilidad del Profesor
**IMPORTANTE:** El profesor **SOLO** puede dar clases en las horas que marcó como disponibles
- Si el profesor no tiene disponibilidad registrada en un horario, **NO se le asigna clase**
- El profesor debe marcar explícitamente sus horas disponibles en el módulo de disponibilidad

### 4. ✅ Máximo 3 Horas Seguidas de la Misma Materia
**RESTRICCIÓN CLAVE:** No puede haber más de **3 horas continuas** de la misma materia en un día
- Evita fatiga estudiantil
- Mejora la retención de conocimientos
- Distribuye las materias de forma equilibrada

### 5. ✅ Máximo 8 Horas Diarias por Profesor
**NUEVA RESTRICCIÓN:** Un profesor no puede trabajar más de **8 horas en un día**
- Respeta límites laborales razonables
- Previene sobrecarga de trabajo
- Mejora el desempeño docente

### 6. ✅ Carga Máxima Semanal
Límites semanales según tipo de profesor:
- **Profesor Tiempo Completo:** Máximo 40 horas/semana
- **Profesor por Asignatura:** Máximo 20 horas/semana

### 7. ✅ Sin Conflictos Entre Carreras
- Si un profesor imparte en múltiples carreras, no puede tener clases simultáneas
- Verifica horarios académicos existentes de otras carreras

## 🔄 Cambios Realizados

### 1. Disponibilidad de Profesores (Mejorada)
**ANTES:**
```python
# Si no había registro, asumía disponible (True)
disponibilidad_dict[dia][horario.id] = disp.disponible if disp else True
```

**AHORA:**
```python
# Si NO hay registro, NO está disponible (False)
if disp:
    disponibilidad_dict[dia][horario.id] = disp.disponible
else:
    disponibilidad_dict[dia][horario.id] = False
```

**IMPACTO:** Los profesores ahora **DEBEN** marcar explícitamente sus horas disponibles. Esto asegura que solo den clases cuando realmente pueden.

### 2. Restricción de 8 Horas Diarias (Nueva)
```python
def restriccion_horas_diarias_profesor(self):
    """Un profesor no puede trabajar más de 8 horas al día"""
    for profesor in self.profesores:
        for dia_idx in range(len(self.dias_semana)):
            asignaciones_profesor_dia = []
            # ... recolectar todas las asignaciones del día
            
            if asignaciones_profesor_dia:
                # Máximo 8 horas por día
                self.model.Add(sum(asignaciones_profesor_dia) <= 8)
```

### 3. Restricción de 3 Horas Máximo por Materia (Reforzada)
```python
def restriccion_distribucion_horas_materia(self):
    """Máximo 3 horas SEGUIDAS de la misma materia por día"""
    for materia in self.materias:
        for dia_idx in range(len(self.dias_semana)):
            asignaciones_materia_dia = []
            # ... recolectar asignaciones de la materia en el día
            
            if asignaciones_materia_dia:
                # ⚠️ IMPORTANTE: Máximo 3 horas por día
                self.model.Add(sum(asignaciones_materia_dia) <= 3)
```

### 4. Mensajes de Diagnóstico Mejorados
```python
# Muestra resumen de restricciones al iniciar
print("="*70)
print("📋 RESTRICCIONES APLICADAS:")
print("   1. ✓ Cada materia debe tener sus horas semanales requeridas")
# ...

# Validación de horas por materia
print("🔍 Validando horas de materias...")
print(f"   ✓ {materia.codigo}: {materia.horas_teoricas}h teóricas + {materia.horas_practicas}h prácticas = {horas_totales}h/semana")

# Muestra horas disponibles por profesor
print(f"   ✓ {profesor.get_nombre_completo()}: {total_horas_disponibles} horas disponibles")

# Advierte si hay pocas horas disponibles
if total_horas_disponibles < 5:
    print(f"   ⚠️  ADVERTENCIA: Profesor tiene solo {total_horas_disponibles} horas disponibles")

# Advierte sobre materias sin horas configuradas
if horas_totales == 0:
    print(f"⚠️  Advertencia: Materia {materia.codigo} no tiene horas configuradas. Usando 3 horas por defecto.")
```

## 📊 Ejemplo de Uso

### Escenario
- **Materia:** Programación Web (6 horas/semana)
- **Profesor:** Juan Pérez (Tiempo Completo)
- **Disponibilidad:** Lunes a Viernes, 8:00-14:00

### Resultado Esperado
✅ **Distribución válida:**
- Lunes: 2 horas (8:00-10:00)
- Miércoles: 2 horas (10:00-12:00)
- Viernes: 2 horas (8:00-10:00)

❌ **Distribución inválida:**
- Lunes: 4 horas seguidas ❌ (supera 3h máximo)
- Martes: 2 horas
- Horario no disponible: 16:00 ❌ (fuera de disponibilidad)

## 🎓 Recomendaciones

### Para Administradores
1. **Asegurar que todos los profesores registren su disponibilidad**
2. Verificar que haya suficientes bloques horarios disponibles
3. Revisar materias con muchas horas (>6h) para distribución óptima

### Para Jefes de Carrera
1. Coordinar disponibilidad de profesores antes de generar horarios
2. Validar que las horas teóricas/prácticas de materias sean correctas
3. Revisar los horarios generados antes de publicarlos

### Para Profesores
1. **Marcar disponibilidad real en el sistema**
2. Considerar límite de 8 horas/día al establecer disponibilidad
3. Actualizar disponibilidad si cambian circunstancias personales

## 🔍 Solución de Problemas

### "No se encontró solución factible"
**Causas posibles:**
1. Profesores sin disponibilidad registrada
2. Pocas horas disponibles vs. horas requeridas
3. Conflictos entre carreras no resueltos
4. Restricciones muy estrictas para el número de materias

**Soluciones:**
1. Verificar disponibilidad de todos los profesores
2. Agregar más bloques horarios disponibles
3. Aumentar disponibilidad de profesores
4. Ajustar horas de materias si es posible

### Horarios desbalanceados
**Si un profesor tiene muy pocas horas:**
- Revisar que esté asignado a las materias correctas
- Verificar su disponibilidad horaria

**Si un profesor está sobrecargado:**
- Verificar restricción de 8h/día y 40h/semana
- Distribuir materias entre más profesores

## 📝 Notas Técnicas

- **Motor:** Google OR-Tools CP-SAT Solver
- **Tipo de problema:** Programación con restricciones (CSP)
- **Complejidad:** NP-Completo
- **Tiempo de solución:** Variable según restricciones (típicamente 1-30 segundos)

## ✅ Checklist de Validación

Antes de generar horarios, verificar:
- [ ] **Materias tienen horas teóricas y prácticas configuradas correctamente**
- [ ] Todos los profesores tienen disponibilidad registrada
- [ ] Hay suficientes bloques horarios en el sistema
- [ ] Profesores asignados a materias del grupo
- [ ] Periodo académico configurado correctamente
- [ ] Total de horas requeridas no excede bloques disponibles

### Validación de Horas por Materia
El generador valida automáticamente:
1. ✅ Materias con horas configuradas se muestran detalladamente
2. ⚠️ Materias sin horas usan 3 horas por defecto
3. ⚠️ Materias con más de 15 horas se limitan automáticamente
4. 📊 Muestra total de horas semanales vs. bloques disponibles

---
**Generador de Horarios v2.0** - Sistema de Gestión Académica
