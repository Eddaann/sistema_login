"""
Script de migración para agregar el sistema de Grupos
Este script crea:
1. Tabla 'grupo' para gestionar grupos académicos
2. Tabla 'grupo_materias' para relación many-to-many con materias
3. Actualiza 'horario_academico' para agregar grupo_id (opcional, para futura implementación)
"""

import sqlite3
from datetime import datetime

def migrate_add_grupos():
    """Migración para agregar sistema de grupos"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('instance/sistema_academico.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("INICIANDO MIGRACIÓN: Sistema de Grupos")
        print("=" * 60)
        
        # 1. Crear tabla grupo
        print("\n1. Creando tabla 'grupo'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grupo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo VARCHAR(20) NOT NULL UNIQUE,
                numero_grupo INTEGER NOT NULL,
                turno VARCHAR(1) NOT NULL,
                cuatrimestre INTEGER NOT NULL,
                carrera_id INTEGER NOT NULL,
                activo BOOLEAN DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                creado_por INTEGER NOT NULL,
                FOREIGN KEY (carrera_id) REFERENCES carrera(id),
                FOREIGN KEY (creado_por) REFERENCES user(id)
            )
        ''')
        print("   ✓ Tabla 'grupo' creada exitosamente")
        
        # 2. Crear tabla intermedia grupo_materias
        print("\n2. Creando tabla 'grupo_materias'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grupo_materias (
                grupo_id INTEGER NOT NULL,
                materia_id INTEGER NOT NULL,
                PRIMARY KEY (grupo_id, materia_id),
                FOREIGN KEY (grupo_id) REFERENCES grupo(id),
                FOREIGN KEY (materia_id) REFERENCES materia(id)
            )
        ''')
        print("   ✓ Tabla 'grupo_materias' creada exitosamente")
        
        # 3. Verificar si la columna grupo_id ya existe en horario_academico
        print("\n3. Verificando columna 'grupo_id' en 'horario_academico'...")
        cursor.execute("PRAGMA table_info(horario_academico)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'grupo_id' not in columns:
            print("   Agregando columna 'grupo_id' a 'horario_academico'...")
            # SQLite no permite agregar foreign key con ALTER TABLE
            # La constraint se puede agregar al crear la columna
            cursor.execute('''
                ALTER TABLE horario_academico
                ADD COLUMN grupo_id INTEGER REFERENCES grupo(id)
            ''')
            print("   ✓ Columna 'grupo_id' agregada exitosamente")
        else:
            print("   → Columna 'grupo_id' ya existe, omitiendo...")
        
        # 4. Crear índices para mejorar el rendimiento
        print("\n4. Creando índices...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grupo_carrera 
            ON grupo(carrera_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grupo_cuatrimestre 
            ON grupo(cuatrimestre)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grupo_materias_grupo 
            ON grupo_materias(grupo_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grupo_materias_materia 
            ON grupo_materias(materia_id)
        ''')
        print("   ✓ Índices creados exitosamente")
        
        # 5. Guardar cambios
        conn.commit()
        print("\n" + "=" * 60)
        print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("  ✓ Tabla 'grupo' creada")
        print("  ✓ Tabla 'grupo_materias' creada")
        print("  ✓ Columna 'grupo_id' verificada en 'horario_academico'")
        print("  ✓ Índices creados")
        print("\nAhora puedes:")
        print("  1. Crear grupos académicos desde el panel de administración")
        print("  2. Asignar materias a los grupos")
        print("  3. Los grupos tienen formato: {número}{turno}{carrera}{cuatrimestre}")
        print("     Ejemplo: 1MSC1 = Grupo 1, Matutino, Sistemas, Cuatrimestre 1")
        print("\n" + "=" * 60)
        
    except sqlite3.Error as e:
        print(f"\n❌ ERROR durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == '__main__':
    print("\n🚀 Iniciando migración del sistema de grupos...")
    print("Este proceso agregará las tablas necesarias para gestionar grupos académicos.\n")
    
    respuesta = input("¿Deseas continuar? (s/n): ")
    
    if respuesta.lower() == 's':
        if migrate_add_grupos():
            print("\n✅ Migración completada con éxito!")
        else:
            print("\n❌ La migración falló. Revisa los errores anteriores.")
    else:
        print("\n❌ Migración cancelada por el usuario.")
