#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el generador de horarios mejorado
"""

from app import app
from models import db, User, Carrera, Materia, Horario, Grupo
from generador_horarios import generar_horarios_automaticos, ORTOOLS_AVAILABLE

def test_generador_mejorado():
    """Probar el generador de horarios mejorado"""
    with app.app_context():
        print("🧪 Iniciando pruebas del generador mejorado...")
        
        # Verificar disponibilidad de OR-Tools
        print(f"📦 OR-Tools disponible: {'✅ Sí' if ORTOOLS_AVAILABLE else '❌ No'}")
        
        # Buscar datos de prueba
        carrera = Carrera.query.first()
        if not carrera:
            print("❌ No hay carreras en la base de datos para probar")
            return
            
        print(f"🎓 Carrera de prueba: {carrera.nombre}")
        
        # Buscar materias
        materias = Materia.query.filter_by(
            carrera_id=carrera.id, 
            cuatrimestre=1,
            activa=True
        ).limit(3).all()
        
        if not materias:
            print("❌ No hay materias para probar")
            return
            
        print(f"📚 Materias encontradas: {len(materias)}")
        for materia in materias:
            profesores_count = len(materia.profesores)
            print(f"  - {materia.nombre}: {profesores_count} profesores asignados")
        
        # Buscar profesores
        profesores = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).limit(3).all()
        
        print(f"👨‍🏫 Profesores encontrados: {len(profesores)}")
        
        # Buscar horarios
        horarios = Horario.query.filter_by(
            turno='matutino',
            activo=True
        ).limit(5).all()
        
        print(f"⏰ Horarios disponibles: {len(horarios)}")
        
        if not profesores or not horarios:
            print("❌ Datos insuficientes para probar")
            return
        
        # Probar generación
        print("\n🚀 Iniciando generación de horarios de prueba...")
        
        resultado = generar_horarios_automaticos(
            carrera_id=carrera.id,
            cuatrimestre=1,
            turno='matutino',
            dias_semana=['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
            periodo_academico='2025-1-TEST',
            creado_por=1  # Asumiendo que hay un usuario admin con ID 1
        )
        
        print(f"\n📊 Resultado de la generación:")
        print(f"  - Éxito: {'✅' if resultado['exito'] else '❌'}")
        print(f"  - Mensaje: {resultado['mensaje']}")
        print(f"  - Algoritmo: {resultado['algoritmo']}")
        
        if resultado['estadisticas']:
            stats = resultado['estadisticas']
            print(f"  - Horarios generados: {stats['total_horarios']}")
            print(f"  - Profesores utilizados: {stats['profesores_utilizados']}/{stats['profesores_totales']}")
            print(f"  - Materias asignadas: {stats['materias_asignadas']}/{stats['materias_totales']}")
            print(f"  - Eficiencia: {stats['eficiencia']}%")
        
        # Test del modelo Grupo mejorado
        print(f"\n🏫 Probando modelo Grupo mejorado...")
        
        grupo = Grupo.query.first()
        if grupo:
            resumen = grupo.get_resumen_completo()
            print(f"  - Grupo: {grupo.codigo}")
            print(f"  - Materias: {resumen['materias_count']}")
            print(f"  - Profesores: {resumen['profesores_count']}")
            print(f"  - Completitud: {resumen['completitud']}%")
            print(f"  - Estado: {resumen['estado']['texto']}")
            
            materias_sin_profesor = grupo.get_materias_sin_profesor()
            if materias_sin_profesor:
                print(f"  - ⚠️  Materias sin profesor: {len(materias_sin_profesor)}")
                for materia in materias_sin_profesor:
                    print(f"    * {materia.nombre}")
        else:
            print("  - ❌ No hay grupos para probar")
        
        print(f"\n✅ Pruebas completadas")

def test_distribucion_horas():
    """Probar la lógica de distribución de horas"""
    print(f"\n📊 Probando lógica de distribución de horas...")
    
    # Casos de prueba
    casos_prueba = [
        {'horas': 1, 'descripcion': '1 hora (mínimo)'},
        {'horas': 3, 'descripcion': '3 horas (típico)'},
        {'horas': 5, 'descripcion': '5 horas (1 por día ideal)'},
        {'horas': 8, 'descripcion': '8 horas (requiere agrupación)'},
        {'horas': 12, 'descripcion': '12 horas (máxima carga)'}
    ]
    
    for caso in casos_prueba:
        horas = caso['horas']
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        
        if horas <= 5:
            distribucion = "1 hora por día preferentemente"
        else:
            dias_necesarios = min(len(dias_semana), (horas + 2) // 3)  # Ceiling division con max 3 por día
            horas_por_dia = horas // dias_necesarios
            horas_extra = horas % dias_necesarios
            distribucion = f"{dias_necesarios} días, {horas_por_dia}h base"
            if horas_extra > 0:
                distribucion += f" (+{horas_extra} extra)"
        
        print(f"  - {caso['descripcion']}: {distribucion}")

if __name__ == "__main__":
    test_generador_mejorado()
    test_distribucion_horas()