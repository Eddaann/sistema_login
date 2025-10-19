"""
Script para verificar los horarios configurados por turno
"""

from app import app
from models import Horario

def verificar_horarios():
    """Verificar horarios por turno"""
    with app.app_context():
        print("=" * 60)
        print("HORARIOS CONFIGURADOS EN EL SISTEMA")
        print("=" * 60)
        
        # Obtener todos los horarios
        horarios = Horario.query.filter_by(activo=True).order_by(Horario.turno, Horario.orden).all()
        
        if not horarios:
            print("❌ No hay horarios configurados")
            return
        
        # Agrupar por turno
        turnos = {}
        for horario in horarios:
            if horario.turno not in turnos:
                turnos[horario.turno] = []
            turnos[horario.turno].append(horario)
        
        # Mostrar horarios por turno
        for turno, horarios_turno in sorted(turnos.items()):
            print(f"\n{'='*60}")
            print(f"TURNO: {turno.upper()}")
            print(f"{'='*60}")
            print(f"Total de bloques: {len(horarios_turno)}")
            print(f"\n{'Nombre':<20} {'Inicio':<10} {'Fin':<10} {'Orden':<10}")
            print("-" * 60)
            
            for h in horarios_turno:
                print(f"{h.nombre:<20} {h.get_hora_inicio_str():<10} {h.get_hora_fin_str():<10} {h.orden:<10}")
            
            # Mostrar rango completo
            if horarios_turno:
                primer_horario = horarios_turno[0]
                ultimo_horario = horarios_turno[-1]
                print(f"\nRango completo: {primer_horario.get_hora_inicio_str()} - {ultimo_horario.get_hora_fin_str()}")
        
        print("\n" + "=" * 60)
        print(f"RESUMEN TOTAL")
        print("=" * 60)
        print(f"Total de horarios activos: {len(horarios)}")
        print(f"Turnos configurados: {', '.join(sorted(turnos.keys()))}")

if __name__ == '__main__':
    verificar_horarios()
