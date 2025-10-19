"""
Script para inicializar la disponibilidad de los profesores existentes
Marca todos los horarios como disponibles por defecto para facilitar el uso inicial
"""

from app import app
from models import db, User, Horario, DisponibilidadProfesor

def inicializar_disponibilidad_profesores():
    """Inicializar disponibilidad para todos los profesores sin disponibilidad configurada"""
    with app.app_context():
        print("=" * 60)
        print("Inicializando disponibilidad de profesores")
        print("=" * 60)
        
        # Obtener todos los profesores
        profesores = User.query.filter(
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).all()
        
        if not profesores:
            print("❌ No se encontraron profesores en el sistema")
            return
        
        print(f"✅ Se encontraron {len(profesores)} profesores")
        
        # Obtener todos los horarios activos
        horarios = Horario.query.filter_by(activo=True).all()
        
        if not horarios:
            print("❌ No se encontraron horarios en el sistema")
            return
        
        print(f"✅ Se encontraron {len(horarios)} horarios")
        
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
        
        profesores_actualizados = 0
        total_disponibilidades_creadas = 0
        
        for profesor in profesores:
            # Verificar si ya tiene disponibilidades configuradas
            disponibilidades_existentes = DisponibilidadProfesor.query.filter_by(
                profesor_id=profesor.id,
                activo=True
            ).count()
            
            if disponibilidades_existentes > 0:
                print(f"⏭️  {profesor.get_nombre_completo()} ya tiene disponibilidad configurada ({disponibilidades_existentes} registros)")
                continue
            
            print(f"\n📝 Configurando disponibilidad para: {profesor.get_nombre_completo()}")
            
            disponibilidades_profesor = 0
            for dia in dias_semana:
                for horario in horarios:
                    # Crear disponibilidad marcada como disponible por defecto
                    nueva_disponibilidad = DisponibilidadProfesor(
                        profesor_id=profesor.id,
                        horario_id=horario.id,
                        dia_semana=dia,
                        disponible=True,  # Por defecto disponible
                        creado_por=1  # Usar ID del admin (ajustar si es necesario)
                    )
                    db.session.add(nueva_disponibilidad)
                    disponibilidades_profesor += 1
            
            try:
                db.session.commit()
                print(f"   ✅ {disponibilidades_profesor} disponibilidades creadas")
                profesores_actualizados += 1
                total_disponibilidades_creadas += disponibilidades_profesor
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"✅ Profesores actualizados: {profesores_actualizados}")
        print(f"✅ Total de disponibilidades creadas: {total_disponibilidades_creadas}")
        print(f"📊 Promedio por profesor: {total_disponibilidades_creadas // profesores_actualizados if profesores_actualizados > 0 else 0}")
        print("=" * 60)
        print("\n💡 Los profesores ahora pueden personalizar su disponibilidad desde:")
        print("   Panel del Profesor → Disponibilidad Horaria")
        print("=" * 60)

if __name__ == '__main__':
    inicializar_disponibilidad_profesores()
