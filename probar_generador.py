"""
Script de prueba para verificar que el generador de horarios funciona correctamente
después de las correcciones
"""

from app import app
from models import db, Grupo
from generador_horarios import GeneradorHorariosOR

def probar_generador():
    """Probar el generador de horarios con un grupo de ejemplo"""
    with app.app_context():
        print("=" * 60)
        print("Prueba del Generador de Horarios")
        print("=" * 60)
        
        # Obtener el primer grupo disponible
        grupo = Grupo.query.first()
        
        if not grupo:
            print("❌ No se encontraron grupos en el sistema")
            print("   Crea un grupo primero para poder probar el generador")
            return
        
        print(f"✅ Usando grupo: {grupo.codigo}")
        print(f"   Carrera: {grupo.get_carrera_nombre()}")
        print(f"   Cuatrimestre: {grupo.cuatrimestre}")
        print(f"   Turno: {grupo.get_turno_display()}")
        print(f"   Materias: {len(grupo.materias)}")
        
        # Crear instancia del generador
        try:
            generador = GeneradorHorariosOR(
                carrera_id=grupo.carrera_id,
                cuatrimestre=grupo.cuatrimestre,
                turno='matutino' if grupo.turno == 1 else 'vespertino',
                dias_semana=['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
                periodo_academico='2025-1',
                creado_por=1,  # Admin
                grupo_id=grupo.id
            )
            print("\n✅ Generador inicializado correctamente")
            
        except Exception as e:
            print(f"\n❌ Error al inicializar el generador: {e}")
            return
        
        # Intentar generar horarios
        print("\n🚀 Iniciando generación de horarios...")
        print("-" * 60)
        
        try:
            resultado = generador.generar_horarios()
            
            if resultado['exito']:
                print("\n" + "=" * 60)
                print("✅ ¡ÉXITO! Horarios generados correctamente")
                print("=" * 60)
                print(f"Horarios creados: {resultado['horarios_creados']}")
                print(f"Tiempo de ejecución: {resultado.get('tiempo_ejecucion', 'N/A')} segundos")
                
                # Mostrar algunas estadísticas
                if 'horarios' in resultado and resultado['horarios']:
                    print(f"\nTotal de asignaciones: {len(resultado['horarios'])}")
                    
                    # Contar por día
                    dias_count = {}
                    for h in resultado['horarios']:
                        dia = h.dia_semana
                        dias_count[dia] = dias_count.get(dia, 0) + 1
                    
                    print("\nDistribución por día:")
                    for dia, count in sorted(dias_count.items()):
                        print(f"  {dia.capitalize()}: {count} horas")
                
            else:
                print("\n" + "=" * 60)
                print("❌ No se pudo generar una solución")
                print("=" * 60)
                print(f"Mensaje: {resultado.get('mensaje', 'Sin mensaje')}")
                
                # Sugerencias
                print("\n💡 Posibles causas:")
                print("   1. Disponibilidades de profesores muy restrictivas")
                print("   2. Pocos profesores para muchas materias")
                print("   3. Conflictos de horarios entre carreras")
                print("   4. Horarios disponibles insuficientes")
                
        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ ERROR durante la generación")
            print("=" * 60)
            print(f"Error: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            import traceback
            print("\nTraceback completo:")
            traceback.print_exc()

if __name__ == '__main__':
    probar_generador()
