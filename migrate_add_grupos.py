"""
Script de migración para agregar:
1. Campo 'grupo' a la tabla horario_academico
2. Tabla intermedia profesor_materias para relación many-to-many
"""

import sqlite3
import os

def migrate_database():
    """Ejecutar migración de la base de datos"""
    db_path = 'instance/sistema_academico.db'
    
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Iniciando migración...")
        
        # 1. Verificar si la columna 'grupo' ya existe
        cursor.execute("PRAGMA table_info(horario_academico)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'grupo' not in columns:
            print("Agregando columna 'grupo' a horario_academico...")
            cursor.execute("""
                ALTER TABLE horario_academico 
                ADD COLUMN grupo VARCHAR(10) DEFAULT 'A' NOT NULL
            """)
            print("✓ Columna 'grupo' agregada exitosamente")
        else:
            print("✓ Columna 'grupo' ya existe")
        
        # 2. Crear tabla profesor_materias si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profesor_materias (
                profesor_id INTEGER NOT NULL,
                materia_id INTEGER NOT NULL,
                PRIMARY KEY (profesor_id, materia_id),
                FOREIGN KEY (profesor_id) REFERENCES user(id),
                FOREIGN KEY (materia_id) REFERENCES materia(id)
            )
        """)
        print("✓ Tabla 'profesor_materias' creada/verificada")
        
        # 3. Migrar datos existentes: asignar profesores a materias basándose en horarios académicos
        print("Migrando asignaciones profesor-materia desde horarios académicos...")
        cursor.execute("""
            INSERT OR IGNORE INTO profesor_materias (profesor_id, materia_id)
            SELECT DISTINCT profesor_id, materia_id
            FROM horario_academico
            WHERE activo = 1
        """)
        
        rows_affected = cursor.rowcount
        print(f"✓ {rows_affected} asignaciones profesor-materia migradas")
        
        # Confirmar cambios
        conn.commit()
        print("\n¡Migración completada exitosamente!")
        
        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM profesor_materias")
        total_asignaciones = cursor.fetchone()[0]
        print(f"\nEstadísticas:")
        print(f"- Total de asignaciones profesor-materia: {total_asignaciones}")
        
        cursor.execute("SELECT COUNT(*) FROM horario_academico WHERE grupo IS NOT NULL")
        total_horarios = cursor.fetchone()[0]
        print(f"- Total de horarios con grupo asignado: {total_horarios}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Error durante la migración: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("=== Migración: Agregar Grupos y Relación Profesor-Materias ===\n")
    success = migrate_database()
    
    if success:
        print("\n✓ La base de datos ha sido actualizada correctamente")
        print("\nPróximos pasos:")
        print("1. Reinicia la aplicación Flask")
        print("2. Los horarios existentes tendrán grupo 'A' por defecto")
        print("3. Puedes asignar materias a profesores desde la gestión de profesores")
        print("4. Al crear horarios, ahora puedes especificar el grupo (A, B, C, etc.)")
    else:
        print("\n✗ La migración falló. Revisa los errores anteriores.")
