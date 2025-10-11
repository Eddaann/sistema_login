# 🎓 Generación de Horarios por Grupo - Documentación

## 📋 Resumen de Cambios

Se ha rediseñado completamente el sistema de generación de horarios para trabajar con el **módulo de gestión de grupos**. Ahora el sistema es mucho más simple y directo, ya que toda la configuración está centralizada en los grupos.

---

## 🔄 Cambios Principales

### ❌ ANTES (Sistema Antiguo)
El usuario tenía que seleccionar:
- ✏️ Carrera
- ✏️ Ciclo escolar
- ✏️ Cuatrimestre
- ✏️ Turno (matutino/vespertino)
- ✏️ Días de la semana

El sistema buscaba **TODOS** los profesores de la carrera y **TODAS** las materias del cuatrimestre, sin importar si estaban relacionados o no.

**PROBLEMA:** No había garantía de que los profesores asignados impartieran las materias del cuatrimestre.

---

### ✅ AHORA (Sistema Nuevo)
El usuario solo selecciona:
- ✏️ **Grupo** (que ya contiene toda la configuración)
- ✏️ Días de la semana

El sistema usa automáticamente:
- ✅ Las **materias asignadas al grupo**
- ✅ Los **profesores que imparten esas materias** (relación profesor-materia)
- ✅ El **turno del grupo** (matutino/vespertino)
- ✅ El **cuatrimestre del grupo**
- ✅ La **carrera del grupo**

**BENEFICIO:** Garantiza que solo se asignen profesores que ya están configurados para impartir las materias del grupo.

---

## 🎯 Flujo de Trabajo Correcto

### 1️⃣ **Crear Grupo** (Módulo de Gestión de Grupos)
```
Admin → Grupos → Crear Grupo
- Código: 1MSC1
- Carrera: Ingeniería en Sistemas Computacionales
- Cuatrimestre: 1
- Turno: Matutino
- Número de grupo: 1
```

### 2️⃣ **Asignar Materias al Grupo**
```
Admin → Grupos → Ver Grupo → Asignar Materias
- Seleccionar materias del cuatrimestre 1 de Sistemas
- Ejemplo: Programación I, Matemáticas I, Inglés I, etc.
```

### 3️⃣ **Asignar Profesores a las Materias** (Módulo de Profesores)
```
Admin → Profesores → Ver Profesor → Asignar Materias
- Seleccionar las materias que el profesor impartirá
- Ejemplo: 
  - Profesor Juan García → Programación I, Estructuras de Datos
  - Profesora María López → Matemáticas I, Cálculo
```

### 4️⃣ **Generar Horarios** (Ahora es simple!)
```
Admin → Horarios Académicos → Generar Horarios
- Seleccionar: Grupo 1MSC1
- Seleccionar: Días de la semana (Lunes a Viernes)
- Clic en "Generar Horarios"
```

El sistema automáticamente:
- ✅ Toma las materias asignadas al grupo 1MSC1
- ✅ Busca los profesores que imparten esas materias
- ✅ Usa el turno matutino (del grupo)
- ✅ Genera horarios respetando disponibilidades

---

## 🔧 Archivos Modificados

### 1. `forms.py`
**Antes:**
```python
class GenerarHorariosForm(FlaskForm):
    carrera = SelectField('Carrera', ...)
    ciclo = SelectField('Ciclo Escolar', ...)
    cuatrimestre = SelectField('Cuatrimestre', ...)
    turno = SelectField('Turno', ...)
    # ... más campos
```

**Ahora:**
```python
class GenerarHorariosForm(FlaskForm):
    grupo_id = SelectField('Grupo', ...)  # ← Solo esto!
    dias_semana = SelectField('Días de la semana', ...)
    # ... días personalizados
```

---

### 2. `generador_horarios.py`
**Función principal actualizada:**
```python
def generar_horarios_automaticos(grupo_id=None, dias_semana=None, ...):
    # Si se proporciona grupo_id, extraer datos del grupo
    if grupo_id is not None:
        grupo = Grupo.query.get(grupo_id)
        
        # Validar que tenga materias
        if not grupo.materias:
            return error("El grupo no tiene materias asignadas")
        
        # Validar que las materias tengan profesores
        if grupo.get_materias_sin_profesor():
            return error("Hay materias sin profesor asignado")
        
        # Extraer configuración del grupo
        carrera_id = grupo.carrera_id
        cuatrimestre = grupo.cuatrimestre
        turno = 'matutino' if grupo.turno == 'M' else 'vespertino'
```

**Clase GeneradorHorariosOR actualizada:**
```python
def cargar_datos(self):
    if self.grupo_id:
        # Obtener materias del grupo
        self.materias = [m for m in self.grupo.materias if m.activa]
        
        # Obtener profesores que imparten esas materias
        profesores_set = set()
        for materia in self.materias:
            for profesor in materia.profesores:
                if profesor.activo:
                    profesores_set.add(profesor)
        self.profesores = list(profesores_set)
```

---

### 3. `app.py`
**Ruta actualizada:**
```python
@app.route('/admin/horarios-academicos/generar', methods=['GET', 'POST'])
def generar_horarios_academicos():
    # Cargar grupos activos
    grupos = Grupo.query.filter_by(activo=True).all()
    form.grupo_id.choices = [
        (str(g.id), f"{g.codigo} - {g.get_carrera_nombre()} - ...") 
        for g in grupos
    ]
    
    if form.validate_on_submit():
        resultado = generar_horarios_automaticos(
            grupo_id=int(form.grupo_id.data),  # ← Solo grupo_id
            dias_semana=dias_semana,
            ...
        )
```

---

### 4. `templates/admin/generar_horarios.html`
**Formulario simplificado:**
```html
<!-- ANTES: Muchos campos -->
<select name="carrera">...</select>
<select name="ciclo">...</select>
<select name="cuatrimestre">...</select>
<select name="turno">...</select>

<!-- AHORA: Un solo campo principal -->
<select name="grupo_id">
    <option>1MSC1 - Ing. Sistemas - Cuatri 1 - Matutino</option>
    <option>2MSC1 - Ing. Sistemas - Cuatri 1 - Vespertino</option>
    ...
</select>
```

---

## ✅ Validaciones Automáticas

El sistema ahora valida automáticamente:

1. **Grupo existe:**
   ```python
   if not grupo:
       return error("No se encontró el grupo")
   ```

2. **Grupo tiene materias:**
   ```python
   if not grupo.materias:
       return error("El grupo no tiene materias asignadas")
   ```

3. **Materias tienen profesores:**
   ```python
   materias_sin_profesor = grupo.get_materias_sin_profesor()
   if materias_sin_profesor:
       return error(f"Materias sin profesor: {lista_materias}")
   ```

---

## 🎨 Interfaz de Usuario

### Mensaje de Error Mejorado
Si intentas generar horarios sin configurar el grupo correctamente:

```
❌ Error al generar horarios: Hay materias sin profesor asignado: 
   Programación I, Matemáticas I. 
   
   Debe asignar profesores a todas las materias del grupo.
```

### Información en Pantalla
```
📚 Cargando datos del grupo 1MSC1:
   - Carrera: Ingeniería en Sistemas Computacionales
   - Cuatrimestre: 1
   - Turno: Matutino
   - Materias asignadas: 8
   - Profesores asignados: 5
```

---

## 📊 Comparación de Flujos

### ANTES (Complicado)
```
1. Ir a "Generar Horarios"
2. Seleccionar carrera
3. Seleccionar ciclo escolar
4. Seleccionar cuatrimestre
5. Seleccionar turno
6. Esperar a que el sistema busque TODOS los profesores de la carrera
7. Esperar a que el sistema busque TODAS las materias del cuatrimestre
8. Rezar para que haya coincidencias profesor-materia 🙏
9. Generar (probablemente con errores)
```

### AHORA (Simple)
```
1. Configurar grupo una vez (materias + profesores)
2. Ir a "Generar Horarios"
3. Seleccionar grupo
4. Generar ✅
```

---

## 🔐 Garantías del Nuevo Sistema

✅ **Solo profesores asignados**: El sistema solo considera profesores que imparten las materias del grupo.

✅ **Solo materias del grupo**: No se generan horarios para materias que no están en el grupo.

✅ **Turno correcto**: Usa el turno configurado en el grupo (no hay confusión).

✅ **Validación previa**: Verifica que todo esté configurado antes de intentar generar.

✅ **Mensajes claros**: Si falta algo, te dice exactamente qué falta.

---

## 📝 Ejemplo Completo

### Escenario: Generar horario para Grupo 1MSC1

#### 1. Configuración del Grupo
```
Grupo: 1MSC1
- Carrera: Ingeniería en Sistemas Computacionales
- Cuatrimestre: 1
- Turno: Matutino
- Número: 1
```

#### 2. Materias del Grupo (ya asignadas)
- Programación I (4 hrs/semana)
- Matemáticas I (4 hrs/semana)
- Inglés I (2 hrs/semana)
- Química (3 hrs/semana)
- Desarrollo Humano (2 hrs/semana)

#### 3. Profesores Asignados
- **Prof. Juan García**: Programación I
- **Profa. María López**: Matemáticas I
- **Prof. Carlos Ruiz**: Inglés I
- **Profa. Ana Martínez**: Química
- **Prof. Luis Hernández**: Desarrollo Humano

#### 4. Generar Horarios
```
Ir a: Admin → Horarios Académicos → Generar Horarios
Seleccionar: 1MSC1 - Ing. Sistemas - Cuatri 1 - Matutino
Días: Lunes a Viernes
Clic: Generar Horarios
```

#### 5. Resultado
```
✅ Horarios generados exitosamente!
   - 15 horarios creados
   - 5 profesores utilizados
   - 5 materias asignadas
   - Eficiencia: 100%
```

---

## 🚀 Ventajas del Nuevo Sistema

1. **Menos Errores**: Imposible asignar un profesor a una materia que no imparte.
2. **Más Rápido**: No hay que configurar carrera, ciclo, cuatrimestre y turno cada vez.
3. **Más Claro**: Todo está en el grupo, un solo lugar para configurar.
4. **Mejor Control**: El administrador configura los grupos una vez y reutiliza.
5. **Validación Automática**: El sistema verifica que todo esté bien antes de generar.

---

## 🎯 Recomendaciones

1. **Configure los grupos primero**: Antes de generar horarios, asegúrese de que los grupos tengan materias y profesores.

2. **Revise el módulo de grupos**: Use la función "Ver Materias del Grupo" para verificar que todo esté completo.

3. **Un grupo = Un horario**: Cada grupo debe generar su propio horario independiente.

4. **Reutilice configuraciones**: Una vez configurado un grupo, puede generar horarios múltiples veces.

---

## 📞 Soporte

Si encuentra algún problema:
1. Verifique que el grupo tenga materias asignadas
2. Verifique que todas las materias tengan al menos un profesor
3. Verifique que los profesores estén activos
4. Verifique que las materias estén activas

---

## 🎓 Conclusión

El nuevo sistema de generación de horarios por grupo es:
- ✅ Más simple de usar
- ✅ Más confiable
- ✅ Más rápido
- ✅ Más fácil de mantener
- ✅ Más intuitivo

**¡Disfrute del nuevo sistema!** 🚀
