# 🔧 Solución: Error "No se pudieron asignar todas las materias con las restricciones dadas"

## 🔍 Diagnóstico del Problema

Este error ocurre cuando el algoritmo de generación de horarios no puede encontrar una combinación válida para asignar todas las materias a los profesores dentro de los slots de horario disponibles.

## 📋 Causas Comunes

### 1. **Profesores No Asignados a Materias**
El problema más común es que aunque el grupo tiene materias, los profesores no están asignados a esas materias específicas.

**Cómo verificar:**
```
Admin → Profesores → Ver Profesor → Ver Materias Asignadas
```

**Solución:**
```
Admin → Profesores → Ver Profesor → Asignar Materias
```
Selecciona las materias que el profesor impartirá.

---

### 2. **Relación Many-to-Many No Sincronizada**
La relación entre profesores y materias (`profesor_materias`) puede no estar actualizada.

**Síntomas:**
- Las materias aparecen en el grupo
- Los profesores existen
- Pero el sistema dice "No hay profesores disponibles para [materia]"

**Solución:**
Ejecutar script de migración para sincronizar relaciones:
```bash
python migrate_add_grupos.py
```

---

### 3. **Insuficientes Slots de Horario**
No hay suficientes horarios disponibles para todas las materias.

**Ejemplo:**
- 5 materias × 4 horas = 20 horas totales necesarias
- Solo 3 horarios por día × 5 días = 15 horas disponibles
- ❌ No alcanza!

**Solución:**
```
Admin → Horarios → Crear más módulos de hora
```

---

### 4. **Restricciones de Disponibilidad Muy Estrictas**
Los profesores tienen muchas restricciones de disponibilidad que impiden asignaciones.

**Solución:**
```
Admin → Disponibilidad Profesores → Marcar más horarios como disponibles
```

---

### 5. **Conflictos con Horarios Existentes**
Ya hay horarios asignados que bloquean las posibilidades.

**Solución:**
```
Admin → Horarios Académicos → Limpiar horarios del período
```

---

## 🎯 Pasos para Solucionar

### Paso 1: Verificar el Grupo
```
Admin → Grupos → Ver Grupo [1MIRO1]
```
Verificar:
- ✅ Tiene materias asignadas
- ✅ Todas las materias tienen profesores (no debe haber materias sin profesor)

---

### Paso 2: Verificar Profesores
Para cada profesor que debería impartir materias en este grupo:

```
Admin → Profesores → [Nombre del Profesor] → Ver Materias
```

Verificar:
- ✅ El profesor tiene asignadas las materias del grupo
- ✅ Las materias coinciden con las del grupo

**Si faltan materias:**
```
Admin → Profesores → [Nombre del Profesor] → Asignar Materias
```
Seleccionar todas las materias que impartirá.

---

### Paso 3: Verificar Módulos de Horario
```
Admin → Horarios → Listar Horarios
```

Verificar:
- ✅ Hay suficientes módulos para el turno del grupo (Matutino/Vespertino)
- ✅ Los horarios están activos
- ✅ Cubren suficiente tiempo para todas las materias

**Cálculo aproximado:**
```
Horas necesarias = Σ(horas de cada materia)
Slots disponibles = (módulos por día) × (días de la semana)
```

Si `Horas necesarias > Slots disponibles`, necesitas más módulos.

---

### Paso 4: Revisar Logs de Depuración

Con la versión actualizada del código, ahora verás información detallada en la terminal:

```
📊 Iniciando asignación de 8 materias
👥 Profesores disponibles: 5
   - Juan García: 3 materias asignadas
   - María López: 2 materias asignadas
   ...

📚 Procesando materia: Programación I (ID: 45)
   Horas requeridas: 4
   Profesores que pueden impartir esta materia: 1
      - Juan García
   ✅ Programación I asignada a Juan García

📚 Procesando materia: Matemáticas I (ID: 46)
   Horas requeridas: 4
   Profesores que pueden impartir esta materia: 0
   ⚠️  No hay profesores disponibles para Matemáticas I
   📋 Verificando: esta materia está en las materias de los profesores?
      - Juan García: materias [45, 47, 48]
      - María López: materias [49, 50]
   ❌ No se pudo asignar Matemáticas I
```

Esto te dirá **exactamente** qué materia está fallando y por qué.

---

## 🔨 Solución Rápida (Caso Común)

El problema más común es que **las materias del grupo no están asignadas a los profesores**.

### Ejemplo Práctico

**Grupo:** 1MIRO1 (Ingeniería en Robótica, Cuatri 1, Matutino)

**Materias del Grupo:**
1. Programación I
2. Matemáticas I
3. Física I
4. Inglés I

**Profesores del Grupo:**
- Prof. Juan García
- Profa. María López
- Prof. Carlos Ruiz

**❌ PROBLEMA:** Los profesores NO tienen asignadas estas materias en el módulo de profesores.

**✅ SOLUCIÓN:**

1. **Asignar materias a Juan García:**
   ```
   Admin → Profesores → Juan García → Asignar Materias
   Seleccionar: Programación I, Física I
   Guardar
   ```

2. **Asignar materias a María López:**
   ```
   Admin → Profesores → María López → Asignar Materias
   Seleccionar: Matemáticas I
   Guardar
   ```

3. **Asignar materias a Carlos Ruiz:**
   ```
   Admin → Profesores → Carlos Ruiz → Asignar Materias
   Seleccionar: Inglés I
   Guardar
   ```

4. **Generar horarios nuevamente:**
   ```
   Admin → Horarios Académicos → Generar Horarios
   Seleccionar Grupo: 1MIRO1
   Generar
   ```

---

## 📊 Verificación Final

Antes de generar horarios, usa esta checklist:

### ✅ Checklist Pre-Generación

- [ ] El grupo existe y está activo
- [ ] El grupo tiene materias asignadas
- [ ] Cada materia del grupo tiene AL MENOS un profesor asignado
- [ ] Los profesores están activos
- [ ] Las materias están activas
- [ ] Hay módulos de horario para el turno del grupo
- [ ] Los módulos de horario están activos
- [ ] El total de horas requeridas ≤ slots disponibles

---

## 🐛 Script de Diagnóstico

Puedes crear un script para verificar todo automáticamente:

```python
from models import Grupo, db

grupo_id = 1  # Cambiar por el ID de tu grupo
grupo = Grupo.query.get(grupo_id)

print(f"🔍 Diagnóstico del Grupo {grupo.codigo}")
print(f"=" * 50)

# Verificar materias
print(f"\n📚 Materias del Grupo: {len(grupo.materias)}")
for materia in grupo.materias:
    profesores = [p.get_nombre_completo() for p in materia.profesores if p.activo]
    status = "✅" if profesores else "❌"
    print(f"{status} {materia.nombre} → {', '.join(profesores) if profesores else 'SIN PROFESOR'}")

# Verificar profesores
print(f"\n👥 Profesores del Grupo: {len(grupo.get_profesores_asignados())}")
for profesor in grupo.get_profesores_asignados():
    materias_del_grupo = [m for m in profesor.materias if m in grupo.materias]
    print(f"   {profesor.get_nombre_completo()}: {len(materias_del_grupo)} materias")

# Verificar horarios
from models import Horario
turno = 'matutino' if grupo.turno == 'M' else 'vespertino'
horarios = Horario.query.filter_by(turno=turno, activo=True).count()
print(f"\n⏰ Módulos de Horario ({turno}): {horarios}")

# Calcular capacidad
horas_necesarias = sum(m.get_horas_totales() for m in grupo.materias)
dias_semana = 5  # Lunes a Viernes
slots_disponibles = horarios * dias_semana
print(f"\n📊 Capacidad:")
print(f"   Horas necesarias: {horas_necesarias}")
print(f"   Slots disponibles: {slots_disponibles}")
print(f"   Status: {'✅ Suficiente' if slots_disponibles >= horas_necesarias else '❌ Insuficiente'}")
```

---

## 📞 Siguientes Pasos

1. **Ejecuta el diagnóstico** con los logs mejorados
2. **Identifica qué materia está fallando**
3. **Asigna el profesor faltante a esa materia**
4. **Intenta generar horarios nuevamente**

Si el problema persiste después de asignar todos los profesores correctamente, puede ser un problema de capacidad (no hay suficientes slots de horario).

---

## 🎯 Conclusión

El error "No se pudieron asignar todas las materias" casi siempre significa:
- **90% de los casos**: Profesores no asignados a materias
- **5% de los casos**: Insuficientes módulos de horario
- **5% de los casos**: Restricciones de disponibilidad muy estrictas

Usa los logs de depuración para identificar exactamente qué está fallando.
