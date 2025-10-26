# 📐 Guía de Diseño Estandarizado para Módulos

## 🎯 Objetivo
Crear una experiencia consistente y predecible en todos los módulos del sistema.

## 📋 Estructura Estándar de Página

Todos los módulos deben seguir esta estructura en orden:

```html
<!-- 1. ENCABEZADO: Título + Botones de Acción Principal -->
<div class="row">
    <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>
                <i class="fas fa-[icono] me-2"></i>
                [Título del Módulo]
            </h2>
            <div>
                <!-- Botón Volver (siempre primero) -->
                <a href="{{ url_for('dashboard') }}" class="btn btn-secondary me-2">
                    <i class="fas fa-arrow-left me-1"></i>
                    Volver al Dashboard
                </a>
                
                <!-- Botones de acción agrupados -->
                <div class="btn-group" role="group">
                    <a href="#" class="btn btn-primary">
                        <i class="fas fa-plus me-1"></i>
                        Agregar
                    </a>
                    <!-- Más botones según necesidad -->
                </div>
            </div>
        </div>
    </div>
</div>

<!-- 2. ESTADÍSTICAS (Opcional - solo si aplica) -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-[color] text-white">
            <!-- Estadística -->
        </div>
    </div>
    <!-- Más estadísticas -->
</div>

<!-- 3. FILTROS (Si el módulo tiene búsqueda/filtrado) -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-filter me-2"></i>
                    Filtros de Búsqueda
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    <!-- Campos de filtro -->
                </div>
                <!-- Contador de resultados -->
                <div class="mt-3">
                    <span id="contador-resultados" class="badge bg-primary">
                        Mostrando <span id="total-visible">X</span> de Y elementos
                    </span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- 4. CONTENIDO PRINCIPAL (Tabla / Cards / Contenido) -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-list me-2"></i>
                    Lista de [Elementos]
                </h5>
            </div>
            <div class="card-body">
                <!-- Tabla o contenido -->
            </div>
        </div>
    </div>
</div>
```

## 🎨 Colores de Botones Estandarizados

| Acción | Color | Ejemplo |
|--------|-------|---------|
| Volver/Cancelar | `btn-secondary` | Volver al Dashboard |
| Agregar/Crear | `btn-primary` | Agregar Materia |
| Importar/Cargar | `btn-success` | Importar Excel |
| Editar | `btn-outline-primary` | Editar |
| Ver/Consultar | `btn-info` o `btn-outline-info` | Ver Detalles |
| Eliminar | `btn-outline-danger` | Eliminar |
| Exportar | `btn-warning` | Exportar PDF |
| Gestionar | `btn-dark` o color específico | Gestionar Horarios |

## 📍 Ubicaciones Fijas

### ✅ SIEMPRE en el Encabezado (arriba derecha):
- Botón "Volver al Dashboard"
- Botones de acción principal (Agregar, Importar, etc.)
- Botones de navegación relacionada (Gestionar X)

### ✅ SIEMPRE en Card de Filtros (si aplica):
- Campos de búsqueda
- Selectores de filtro
- Botón "Limpiar filtros"
- Contador de resultados

### ✅ SIEMPRE en la Tabla (columna Acciones):
- Botones de acción por registro (Editar, Eliminar, Ver)
- Agrupados en `btn-group` para mantener orden

### ❌ NUNCA:
- Botones flotando en medio del contenido
- Botones de acción principal dentro de tarjetas
- Mezclar botones de diferentes niveles de acción

## 📏 Espaciado Estándar

```css
mb-4  /* Separación entre secciones principales */
mb-3  /* Separación entre elementos dentro de una sección */
me-2  /* Espacio entre botones horizontales */
me-1  /* Espacio entre icono y texto en botón */
g-3   /* Gap en row para formularios/filtros */
```

## 🔄 Módulos a Estandarizar

### ✅ Ya Estandarizados:
- [ ] Dashboard
- [x] Gestión de Profesores
- [x] Gestión de Usuarios
- [x] Gestión de Grupos
- [x] Gestión de Materias (parcial)

### 🔧 Pendientes de Estandarizar:
- [ ] Gestión de Carreras
- [ ] Gestión de Horarios
- [ ] Horarios Académicos
- [ ] Asignación de Materias (profesor/grupo)
- [ ] Configuración
- [ ] Reportes

## 💡 Ejemplos de Implementación

### Ejemplo 1: Módulo Simple (sin filtros ni estadísticas)
```
1. Encabezado + Botones
2. Tabla de contenido
```

### Ejemplo 2: Módulo Completo
```
1. Encabezado + Botones
2. Estadísticas
3. Filtros
4. Tabla de contenido
```

### Ejemplo 3: Módulo de Consulta
```
1. Encabezado + Botones
2. Filtros
3. Resultados/Cards
```

## 🎯 Beneficios de la Estandarización

1. ✅ **Consistencia**: Usuarios saben dónde encontrar cada elemento
2. ✅ **Eficiencia**: Menos tiempo buscando opciones
3. ✅ **Mantenibilidad**: Más fácil agregar nuevos módulos
4. ✅ **Profesionalismo**: Interfaz pulida y coherente
5. ✅ **Accesibilidad**: Navegación predecible

## 📝 Checklist para Nuevos Módulos

Antes de considerar un módulo completo, verificar:

- [ ] Título con icono a la izquierda
- [ ] Botón "Volver" siempre presente (arriba derecha)
- [ ] Botones de acción principal agrupados
- [ ] Filtros en card separado (si aplica)
- [ ] Contador de resultados visible
- [ ] Tabla/contenido en card con header
- [ ] Colores de botones según estándar
- [ ] Espaciado consistente (mb-4, mb-3, etc.)
- [ ] Sin botones flotantes en medio del contenido

---
**Versión:** 1.0  
**Fecha:** Octubre 25, 2025  
**Sistema de Gestión Académica**
