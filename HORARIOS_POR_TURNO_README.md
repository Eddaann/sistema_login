# 🕐 Sistema de Gestión de Horarios por Turno

## 📋 Descripción

El sistema de generación de horarios ahora **respeta estrictamente** el turno del grupo y solo utiliza los horarios configurados para ese turno específico.

---

## 🎯 Funcionamiento

### **Antes de la Corrección** ❌
El generador podía mezclar horarios de ambos turnos:
- Grupo matutino recibía clases en horario vespertino
- Grupo vespertino recibía clases en horario matutino
- No respetaba la configuración de horarios por turno

### **Después de la Corrección** ✅
El generador filtra horarios estrictamente por turno:
- Grupo matutino → Solo horarios matutinos (07:00 - 14:00)
- Grupo vespertino → Solo horarios vespertinos (14:00 - 21:00)
- Respeta completamente la configuración del admin

---

## 🔧 Configuración de Horarios

### **Acceso Administrativo**
```
Admin → Gestión de Horarios → Crear/Editar Horario
```

### **Campos Importantes**
1. **Nombre**: Descripción del bloque (ej: "1ra Hora")
2. **Turno**: **matutino** o **vespertino** (crítico para filtrado)
3. **Hora Inicio**: Hora de inicio del bloque
4. **Hora Fin**: Hora de fin del bloque
5. **Orden**: Orden secuencial del bloque

---

## 📊 Horarios Actuales Configurados

### Turno Matutino (07:00 - 14:00)
| Bloque | Horario | Duración |
|--------|---------|----------|
| 1ra Hora | 07:00 - 08:00 | 60 min |
| 2da Hora | 08:00 - 09:00 | 60 min |
| 3ra Hora | 09:00 - 10:00 | 60 min |
| 4ta Hora | 10:00 - 11:00 | 60 min |
| 5ta Hora | 11:00 - 12:00 | 60 min |
| 6ta Hora | 13:00 - 14:00 | 60 min |

**Total**: 6 bloques horarios

### Turno Vespertino (14:00 - 21:00)
| Bloque | Horario | Duración |
|--------|---------|----------|
| 1ra Hora | 14:00 - 15:00 | 60 min |
| 2da Hora | 15:00 - 16:00 | 60 min |
| 3ra Hora | 16:00 - 17:00 | 60 min |
| 4ta Hora | 18:00 - 19:00 | 60 min |
| 5ta Hora | 19:00 - 20:00 | 60 min |
| 6ta Hora | 20:00 - 21:00 | 60 min |

**Total**: 6 bloques horarios

---

## 🔄 Flujo de Generación

### 1. Identificación del Grupo
```python
grupo = Grupo.query.get(grupo_id)
turno_grupo = grupo.turno  # 'M' o 'V'
```

### 2. Conversión de Turno
```python
# Convertir de 'M'/'V' a 'matutino'/'vespertino'
turno_texto = 'matutino' if turno_grupo == 'M' else 'vespertino'
```

### 3. Filtrado de Horarios
```python
horarios = Horario.query.filter_by(
    turno=turno_texto,
    activo=True
).order_by(Horario.orden).all()
```

### 4. Generación Restringida
- Solo se crean asignaciones en los horarios filtrados
- No se mezclan turnos
- Respeto total a la configuración

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Grupo Matutino

**Configuración:**
- Grupo: 1MING-SIS1
- Turno: Matutino (M)
- Materias: 2 materias de 5 horas cada una

**Resultado:**
```
✅ Horarios generados:
📅 Materia 1 - Lunes 07:00-08:00
📅 Materia 1 - Martes 07:00-08:00
📅 Materia 1 - Miércoles 13:00-14:00
📅 Materia 1 - Jueves 13:00-14:00
📅 Materia 1 - Viernes 13:00-14:00

📅 Materia 2 - Lunes 08:00-09:00
📅 Materia 2 - Martes 09:00-10:00
📅 Materia 2 - Miércoles 09:00-10:00
📅 Materia 2 - Jueves 10:00-11:00
📅 Materia 2 - Viernes 11:00-12:00

✅ Todos los horarios están entre 07:00 y 14:00
```

### Ejemplo 2: Grupo Vespertino

**Configuración:**
- Grupo: 2VING-SIS3
- Turno: Vespertino (V)
- Materias: 3 materias de 5 horas cada una

**Resultado:**
```
✅ Horarios generados:
📅 Materia 1 - Lunes 14:00-15:00
📅 Materia 1 - Martes 15:00-16:00
📅 Materia 1 - Miércoles 16:00-17:00
📅 Materia 1 - Jueves 18:00-19:00
📅 Materia 1 - Viernes 19:00-20:00

[... más asignaciones ...]

✅ Todos los horarios están entre 14:00 y 21:00
```

---

## 🎓 Ventajas del Sistema

### Para Estudiantes
- ✅ Horarios consistentes con su turno
- ✅ No hay clases fuera de su horario inscrito
- ✅ Mejor organización personal

### Para Profesores
- ✅ Disponibilidades respetadas por turno
- ✅ Sin conflictos entre turnos
- ✅ Carga horaria más clara

### Para Administradores
- ✅ Control total sobre horarios por turno
- ✅ Flexibilidad para configurar bloques
- ✅ Generación automática precisa

---

## ⚙️ Configuración Avanzada

### Agregar Nuevos Bloques Horarios

#### Turno Matutino
```python
nuevo_horario = Horario(
    nombre='7ma Hora',
    turno='matutino',
    hora_inicio=time(12, 0),  # 12:00
    hora_fin=time(13, 0),     # 13:00
    orden=7,
    creado_por=admin_id
)
```

#### Turno Vespertino
```python
nuevo_horario = Horario(
    nombre='7ma Hora',
    turno='vespertino',
    hora_inicio=time(21, 0),  # 21:00
    hora_fin=time(22, 0),     # 22:00
    orden=7,
    creado_por=admin_id
)
```

### Modificar Horarios Existentes

1. Acceder a "Gestión de Horarios"
2. Editar el horario deseado
3. Cambiar turno, horarios o orden
4. Guardar cambios
5. Regenerar horarios para aplicar cambios

---

## 🔍 Verificación del Sistema

### Script de Verificación
Usa el script `verificar_horarios.py` para revisar la configuración:

```bash
python verificar_horarios.py
```

**Salida esperada:**
```
============================================================
HORARIOS CONFIGURADOS EN EL SISTEMA
============================================================

TURNO: MATUTINO
Total de bloques: 6
Rango completo: 07:00 - 14:00

TURNO: VESPERTINO
Total de bloques: 6
Rango completo: 14:00 - 21:00

RESUMEN TOTAL
Total de horarios activos: 12
Turnos configurados: matutino, vespertino
```

### Logs del Generador
Al generar horarios, verás:

```
⏰ Filtrando horarios solo del turno: matutino
   📍 Horarios cargados: 07:00 - 14:00
   📊 Total de bloques horarios: 6
```

O para vespertino:

```
⏰ Filtrando horarios solo del turno: vespertino
   📍 Horarios cargados: 14:00 - 21:00
   📊 Total de bloques horarios: 6
```

---

## 🐛 Solución de Problemas

### Error: "No hay horarios configurados para el turno X"

**Causa:** No existen horarios activos para ese turno en la base de datos

**Solución:**
1. Ve a Admin → Gestión de Horarios
2. Verifica que hay horarios con `turno='matutino'` o `turno='vespertino'`
3. Verifica que están marcados como `activo=True`
4. Crea nuevos horarios si es necesario

### Los horarios se mezclan entre turnos

**Causa:** Horarios mal configurados en la base de datos

**Solución:**
1. Ejecuta `verificar_horarios.py` para ver la configuración
2. Corrige el campo `turno` en horarios mal clasificados
3. Asegúrate de usar 'matutino' o 'vespertino' (minúsculas)

### El generador no encuentra solución

**Causa posible:** Muy pocos horarios para el turno

**Solución:**
1. Verifica la cantidad de bloques horarios disponibles
2. Considera agregar más bloques al turno
3. Reduce la carga horaria de las materias
4. Verifica disponibilidades de profesores para ese turno

---

## 📝 Notas Técnicas

### Modelo de Datos

**Tabla: `horario`**
```sql
turno VARCHAR(20) NOT NULL  -- 'matutino' o 'vespertino'
```

**Tabla: `grupo`**
```sql
turno VARCHAR(1) NOT NULL   -- 'M' o 'V'
```

### Conversión de Turnos

El sistema convierte automáticamente:
- `'M'` (Grupo) → `'matutino'` (Horario)
- `'V'` (Grupo) → `'vespertino'` (Horario)

### Código Clave

**Archivo:** `generador_horarios.py` línea ~70
```python
# Convertir turno de 'M'/'V' a 'matutino'/'vespertino'
self.turno = 'matutino' if self.grupo.turno == 'M' else 'vespertino'
```

**Archivo:** `generador_horarios.py` línea ~126
```python
# Filtrar horarios por turno
self.horarios = Horario.query.filter_by(
    turno=self.turno,
    activo=True
).order_by(Horario.orden).all()
```

---

## ✅ Checklist de Implementación

- [x] Filtrado de horarios por turno
- [x] Conversión de turnos (M/V → matutino/vespertino)
- [x] Logs informativos sobre horarios cargados
- [x] Script de verificación de horarios
- [x] Pruebas exitosas con grupo matutino
- [x] Documentación completa

---

## 📞 Soporte

Para dudas o problemas:
- **Administradores**: Revisar configuración en Gestión de Horarios
- **Desarrolladores**: Consultar código en `generador_horarios.py`
- **Documentación**: Este archivo + `DISPONIBILIDAD_PROFESORES_README.md`

---

**Última actualización:** 18 de Octubre de 2025
**Sistema de Gestión de Horarios Académicos**
