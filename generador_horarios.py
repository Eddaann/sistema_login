"""
Módulo para generación automática de horarios académicos usando Google OR-Tools CP-SAT Solver
"""
from models import db, User, Horario, Carrera, Materia, HorarioAcademico
from datetime import datetime
from ortools.sat.python import cp_model
from collections import defaultdict
import math

class GeneradorHorariosOR:
    """Clase para generar horarios académicos automáticamente usando Google OR-Tools"""

    def __init__(self, carrera_id, cuatrimestre, turno='matutino', dias_semana=None,
                 periodo_academico='2025-1', creado_por=None):
        """
        Inicializar el generador de horarios con OR-Tools

        Args:
            carrera_id: ID de la carrera
            cuatrimestre: Número del cuatrimestre
            turno: 'matutino', 'vespertino' o 'ambos'
            dias_semana: Lista de días de la semana ['lunes', 'martes', etc.]
            periodo_academico: Período académico (ej: '2025-1')
            creado_por: ID del usuario que genera los horarios
        """
        self.carrera_id = carrera_id
        self.cuatrimestre = cuatrimestre
        self.turno = turno
        self.dias_semana = dias_semana or ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        self.periodo_academico = periodo_academico
        self.creado_por = creado_por

        # Datos del proceso
        self.profesores = []
        self.materias = []
        self.horarios = []
        self.disponibilidades = {}  # Cache de disponibilidades por profesor

        # Modelo CP-SAT
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # Variables de decisión
        self.variables = {}  # (profesor_id, materia_id, horario_id, dia_idx) -> BoolVar

        # Resultados
        self.horarios_generados = []
        self.solucion_encontrada = False

    def cargar_datos(self):
        """Cargar datos necesarios para la generación"""
        from models import DisponibilidadProfesor

        # Cargar profesores de la carrera
        self.profesores = User.query.filter(
            User.carrera_id == self.carrera_id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).all()

        # Cargar materias del cuatrimestre
        self.materias = Materia.query.filter(
            Materia.carrera_id == self.carrera_id,
            Materia.cuatrimestre == self.cuatrimestre,
            Materia.activa == True
        ).all()

        # Cargar horarios según el turno
        if self.turno == 'ambos':
            self.horarios = Horario.query.filter_by(activo=True).order_by(Horario.orden).all()
        else:
            self.horarios = Horario.query.filter_by(
                turno=self.turno,
                activo=True
            ).order_by(Horario.orden).all()

        # Cargar disponibilidades de profesores
        self.cargar_disponibilidades()

        print(f"✅ Datos cargados: {len(self.profesores)} profesores, {len(self.materias)} materias, {len(self.horarios)} horarios")

    def cargar_disponibilidades(self):
        """Cargar las disponibilidades de todos los profesores"""
        from models import DisponibilidadProfesor

        for profesor in self.profesores:
            disponibilidades_profesor = DisponibilidadProfesor.query.filter(
                DisponibilidadProfesor.profesor_id == profesor.id,
                DisponibilidadProfesor.activo == True
            ).all()

            # Crear diccionario de disponibilidad por día y horario
            disponibilidad_dict = {}
            for dia in self.dias_semana:
                disponibilidad_dict[dia] = {}
                for horario in self.horarios:
                    # Por defecto, asumir disponible si no hay registro específico
                    disp = next((d for d in disponibilidades_profesor
                               if d.dia_semana == dia and d.horario_id == horario.id), None)
                    disponibilidad_dict[dia][horario.id] = disp.disponible if disp else True

            self.disponibilidades[profesor.id] = disponibilidad_dict

    def validar_datos(self):
        """Validar que hay suficientes datos para generar horarios"""
        if not self.profesores:
            raise ValueError("❌ No hay profesores disponibles para esta carrera")

        if not self.materias:
            raise ValueError("❌ No hay materias disponibles para este cuatrimestre")

        if not self.horarios:
            raise ValueError(f"❌ No hay horarios disponibles para el turno {self.turno}")

        # Verificar que hay suficientes profesores para las materias
        if len(self.profesores) < len(self.materias):
            print(f"⚠️  Advertencia: Hay {len(self.profesores)} profesores para {len(self.materias)} materias")

        return True

    def crear_variables_decision(self):
        """Crear variables de decisión booleanas para el modelo CP-SAT"""
        print("🔧 Creando variables de decisión...")

        for profesor in self.profesores:
            for materia in self.materias:
                for horario in self.horarios:
                    for dia_idx, dia in enumerate(self.dias_semana):
                        # Variable booleana: 1 si se asigna este profesor a esta materia en este horario y día
                        var_name = f"P{profesor.id}_M{materia.id}_H{horario.id}_D{dia_idx}"
                        self.variables[(profesor.id, materia.id, horario.id, dia_idx)] = self.model.NewBoolVar(var_name)

        print(f"✅ Creadas {len(self.variables)} variables de decisión")

    def agregar_restricciones(self):
        """Agregar todas las restricciones al modelo CP-SAT"""
        print("🔒 Agregando restricciones...")

        # 1. Cada materia debe tener exactamente las horas requeridas por semana
        self.restriccion_horas_materia()

        # 2. Un profesor no puede tener dos clases al mismo tiempo
        self.restriccion_no_conflicto_profesor()

        # 3. Un profesor no puede dar clases cuando no está disponible
        self.restriccion_disponibilidad_profesor()

        # 4. Un aula/horario no puede tener dos clases al mismo tiempo (simplificado)
        self.restriccion_no_conflicto_horario()

        # 5. Restricciones de carga horaria por profesor
        self.restriccion_carga_horaria_profesor()

        print("✅ Todas las restricciones agregadas")

    def restriccion_horas_materia(self):
        """Cada materia debe tener exactamente las horas requeridas por semana"""
        for materia in self.materias:
            horas_requeridas = self.calcular_horas_semanales_materia(materia)

            # Suma de todas las asignaciones para esta materia debe ser igual a horas requeridas
            asignaciones_materia = []
            for profesor in self.profesores:
                for horario in self.horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        asignaciones_materia.append(
                            self.variables.get((profesor.id, materia.id, horario.id, dia_idx),
                                             self.model.NewBoolVar(f"dummy_{profesor.id}_{materia.id}_{horario.id}_{dia_idx}"))
                        )

            if asignaciones_materia:
                self.model.Add(sum(asignaciones_materia) == horas_requeridas)

    def restriccion_no_conflicto_profesor(self):
        """Un profesor no puede tener dos clases al mismo tiempo"""
        for profesor in self.profesores:
            for horario in self.horarios:
                for dia_idx in range(len(self.dias_semana)):
                    # En un mismo horario y día, un profesor solo puede tener una materia
                    asignaciones_profesor_horario = []
                    for materia in self.materias:
                        var = self.variables.get((profesor.id, materia.id, horario.id, dia_idx))
                        if var:
                            asignaciones_profesor_horario.append(var)

                    if asignaciones_profesor_horario:
                        self.model.Add(sum(asignaciones_profesor_horario) <= 1)

    def restriccion_disponibilidad_profesor(self):
        """Un profesor no puede dar clases cuando no está disponible"""
        for profesor in self.profesores:
            for horario in self.horarios:
                for dia_idx, dia in enumerate(self.dias_semana):
                    # Si el profesor no está disponible, no puede tener clase
                    disponible = self.verificar_disponibilidad_profesor(profesor.id, horario.id, dia)

                    if not disponible:
                        for materia in self.materias:
                            var = self.variables.get((profesor.id, materia.id, horario.id, dia_idx))
                            if var:
                                self.model.Add(var == 0)

    def restriccion_no_conflicto_horario(self):
        """Un horario no puede tener dos clases al mismo tiempo (simplificación)"""
        # Esta es una simplificación. En un sistema real, consideraríamos aulas específicas
        for horario in self.horarios:
            for dia_idx in range(len(self.dias_semana)):
                # En un mismo horario y día, máximo una clase (simplificación)
                asignaciones_horario = []
                for profesor in self.profesores:
                    for materia in self.materias:
                        var = self.variables.get((profesor.id, materia.id, horario.id, dia_idx))
                        if var:
                            asignaciones_horario.append(var)

                if asignaciones_horario:
                    self.model.Add(sum(asignaciones_horario) <= 1)

    def restriccion_carga_horaria_profesor(self):
        """Restricciones de carga horaria máxima por profesor"""
        for profesor in self.profesores:
            # Calcular carga horaria máxima según tipo de profesor
            if profesor.is_profesor_completo():
                max_horas = 40  # 40 horas semanales para tiempo completo
            else:
                max_horas = 20  # 20 horas semanales para asignatura

            # Suma de todas las asignaciones del profesor
            asignaciones_profesor = []
            for materia in self.materias:
                for horario in self.horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get((profesor.id, materia.id, horario.id, dia_idx))
                        if var:
                            asignaciones_profesor.append(var)

            if asignaciones_profesor:
                self.model.Add(sum(asignaciones_profesor) <= max_horas)

    def agregar_funcion_objetivo(self):
        """Agregar función objetivo para optimizar la distribución"""
        print("🎯 Agregando función objetivo...")

        # Objetivo: minimizar la varianza en la carga horaria de profesores
        # (distribuir equitativamente la carga de trabajo)

        # Calcular la carga horaria de cada profesor
        cargas_horarias = []
        for profesor in self.profesores:
            carga_profesor = []
            for materia in self.materias:
                for horario in self.horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get((profesor.id, materia.id, horario.id, dia_idx))
                        if var:
                            carga_profesor.append(var)

            if carga_profesor:
                cargas_horarias.append(sum(carga_profesor))

        if cargas_horarias:
            # Minimizar la varianza de cargas horarias
            n_profesores = len(cargas_horarias)
            if n_profesores > 1:
                media_carga = sum(cargas_horarias) / n_profesores
                varianza = sum((carga - media_carga) ** 2 for carga in cargas_horarias)
                self.model.Minimize(varianza)

    def resolver_modelo(self):
        """Resolver el modelo CP-SAT"""
        print("🧠 Resolviendo modelo CP-SAT...")

        # Configurar solver
        self.solver.parameters.max_time_in_seconds = 300.0  # 5 minutos máximo
        self.solver.parameters.num_search_workers = 8  # Usar múltiples hilos

        # Resolver
        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            self.solucion_encontrada = True
            print("✅ ¡Solución encontrada!")
            return True
        else:
            print(f"❌ No se encontró solución. Estado: {status}")
            return False

    def interpretar_solucion(self):
        """Interpretar la solución encontrada y crear los horarios académicos"""
        print("📋 Interpretando solución...")

        # Limpiar horarios existentes para este período y carrera
        HorarioAcademico.query.filter(
            HorarioAcademico.periodo_academico == self.periodo_academico,
            HorarioAcademico.activo == True
        ).update({'activo': False})
        db.session.commit()

        horarios_creados = []

        # Recorrer todas las variables para encontrar asignaciones
        for (profesor_id, materia_id, horario_id, dia_idx), var in self.variables.items():
            if self.solver.Value(var) == 1:  # Si la variable es verdadera
                dia = self.dias_semana[dia_idx]

                # Crear horario académico
                horario_academico = HorarioAcademico(
                    profesor_id=profesor_id,
                    materia_id=materia_id,
                    horario_id=horario_id,
                    dia_semana=dia,
                    periodo_academico=self.periodo_academico,
                    creado_por=self.creado_por
                )

                db.session.add(horario_academico)
                horarios_creados.append(horario_academico)

                print(f"📅 Asignado: Prof {profesor_id} → Materia {materia_id} en {dia} horario {horario_id}")

        # Confirmar cambios
        db.session.commit()
        self.horarios_generados = horarios_creados

        print(f"✅ Se crearon {len(horarios_creados)} horarios académicos")
        return horarios_creados

    def calcular_horas_semanales_materia(self, materia):
        """Calcular horas semanales necesarias para una materia"""
        # Usar las horas reales configuradas en la materia
        horas_totales = materia.get_horas_totales()
        return max(horas_totales if horas_totales > 0 else 3, 1)  # Mínimo 1 hora

    def verificar_disponibilidad_profesor(self, profesor_id, horario_id, dia_semana):
        """Verificar si un profesor está disponible en ese horario y día"""
        if profesor_id not in self.disponibilidades:
            return True  # Si no hay registro de disponibilidad, asumir disponible

        disponibilidad_dia = self.disponibilidades[profesor_id].get(dia_semana, {})
        return disponibilidad_dia.get(horario_id, True)  # Por defecto disponible

    def generar_horarios(self):
        """Generar horarios académicos usando OR-Tools"""
        print("🚀 Iniciando generación de horarios con Google OR-Tools CP-SAT...")

        try:
            # Cargar y validar datos
            self.cargar_datos()
            self.validar_datos()

            # Crear modelo
            self.crear_variables_decision()
            self.agregar_restricciones()
            self.agregar_funcion_objetivo()

            # Resolver
            if self.resolver_modelo():
                horarios_generados = self.interpretar_solucion()
                estadisticas = self.obtener_estadisticas()

                return {
                    'exito': True,
                    'mensaje': f'✅ Se generaron {len(horarios_generados)} horarios académicos exitosamente usando OR-Tools',
                    'estadisticas': estadisticas,
                    'horarios_generados': horarios_generados,
                    'algoritmo': 'Google OR-Tools CP-SAT Solver'
                }
            else:
                return {
                    'exito': False,
                    'mensaje': '❌ No se pudo encontrar una solución factible con las restricciones dadas',
                    'estadisticas': None,
                    'horarios_generados': [],
                    'algoritmo': 'Google OR-Tools CP-SAT Solver'
                }

        except Exception as e:
            db.session.rollback()
            return {
                'exito': False,
                'mensaje': f'❌ Error al generar horarios: {str(e)}',
                'estadisticas': None,
                'horarios_generados': [],
                'algoritmo': 'Google OR-Tools CP-SAT Solver'
            }

    def obtener_estadisticas(self):
        """Obtener estadísticas de la generación"""
        if not self.horarios_generados:
            return {
                'total_horarios': 0,
                'profesores_utilizados': 0,
                'materias_asignadas': 0,
                'materias_totales': len(self.materias),
                'profesores_totales': len(self.profesores),
                'eficiencia': 0.0
            }

        total_horarios = len(self.horarios_generados)
        profesores_utilizados = len(set(h.profesor_id for h in self.horarios_generados))
        materias_asignadas = len(set(h.materia_id for h in self.horarios_generados))

        eficiencia = (materias_asignadas / len(self.materias)) * 100 if self.materias else 0

        return {
            'total_horarios': total_horarios,
            'profesores_utilizados': profesores_utilizados,
            'materias_asignadas': materias_asignadas,
            'materias_totales': len(self.materias),
            'profesores_totales': len(self.profesores),
            'eficiencia': round(eficiencia, 2)
        }


def generar_horarios_automaticos(carrera_id, cuatrimestre, turno='matutino', dias_semana=None,
                                periodo_academico='2025-1', creado_por=None):
    """
    Función principal para generar horarios académicos automáticamente usando Google OR-Tools

    Returns:
        dict: Resultado de la generación con estadísticas
    """
    try:
        generador = GeneradorHorariosOR(
            carrera_id=carrera_id,
            cuatrimestre=cuatrimestre,
            turno=turno,
            dias_semana=dias_semana,
            periodo_academico=periodo_academico,
            creado_por=creado_por
        )

        return generador.generar_horarios()

    except Exception as e:
        return {
            'exito': False,
            'mensaje': f'❌ Error crítico: {str(e)}',
            'estadisticas': None,
            'horarios_generados': [],
            'algoritmo': 'Google OR-Tools CP-SAT Solver'
        }