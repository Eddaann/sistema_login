#!/usr/bin/env python3
"""
Sistema de Backups Automáticos para el Sistema Académico
Ejecutar periódicamente para crear backups de la base de datos
"""
import os
import sys
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configurar logging
logging.basicConfig(
    filename='logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_app():
    """Crear aplicación Flask"""
    app = Flask(__name__)
    basedir = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "sistema_academico.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

def init_db(app):
    """Inicializar base de datos"""
    # Importar db desde models (igual que en app.py)
    from models import db, BackupHistory, ConfiguracionSistema

    # Inicializar db con la app (igual que en app.py)
    db.init_app(app)

    with app.app_context():
        return db, BackupHistory, ConfiguracionSistema

def crear_backup_automatico():
    """Crear backup automático de la base de datos"""
    try:
        app = create_app()
        db, BackupHistory, ConfiguracionSistema = init_db(app)

        with app.app_context():
            # Verificar frecuencia de backup
            backup_freq = ConfiguracionSistema.get_config('backup_frequency', 'daily')

            # Verificar si ya se hizo backup hoy (para frecuencia diaria)
            hoy = datetime.now().date()
            ultimo_backup = BackupHistory.query.filter(
                BackupHistory.fecha_creacion >= hoy,
                BackupHistory.tipo == 'automatico'
            ).first()

            if ultimo_backup and backup_freq == 'daily':
                logging.info("Backup diario ya realizado hoy")
                return True

            # Crear directorio de backups
            backup_dir = ConfiguracionSistema.get_config('backup_location', 'backups/')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                logging.info(f"Directorio de backups creado: {backup_dir}")

            # Generar nombre del archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_auto_{timestamp}.db'
            filepath = os.path.join(backup_dir, filename)

            # Copiar archivo de base de datos
            db_path = 'instance/sistema_academico.db'
            if not os.path.exists(db_path):
                logging.error(f"Archivo de base de datos no encontrado: {db_path}")
                return False

            shutil.copy2(db_path, filepath)
            logging.info(f"Backup creado: {filepath}")

            # Calcular tamaño y checksum
            file_size = os.path.getsize(filepath)
            with open(filepath, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Registrar en historial
            backup = BackupHistory(
                filename=filename,
                tipo='automatico',
                tamano=file_size,
                ruta_archivo=filepath
            )
            backup.checksum = checksum
            db.session.add(backup)
            db.session.commit()

            logging.info(f"Backup automático completado: {filename} ({file_size} bytes)")

            # Limpiar backups antiguos
            limpiar_backups_antiguos(backup_dir, ConfiguracionSistema, BackupHistory, db)

            return True

    except Exception as e:
        logging.error(f"Error al crear backup automático: {str(e)}")
        return False

def limpiar_backups_antiguos(backup_dir, ConfiguracionSistema, BackupHistory, db):
    """Limpiar backups antiguos según la política de retención"""
    try:
        retention_days = int(ConfiguracionSistema.get_config('backup_retention', '30'))

        # Calcular fecha límite
        fecha_limite = datetime.now() - timedelta(days=retention_days)

        # Obtener backups antiguos
        backups_antiguos = BackupHistory.query.filter(
            BackupHistory.fecha_creacion < fecha_limite,
            BackupHistory.tipo == 'automatico'
        ).all()

        backups_eliminados = 0
        for backup in backups_antiguos:
            try:
                # Eliminar archivo físico
                if os.path.exists(backup.ruta_archivo):
                    os.remove(backup.ruta_archivo)
                    logging.info(f"Backup antiguo eliminado: {backup.filename}")

                # Eliminar registro de base de datos
                db.session.delete(backup)
                backups_eliminados += 1

            except Exception as e:
                logging.error(f"Error al eliminar backup {backup.filename}: {str(e)}")

        if backups_eliminados > 0:
            db.session.commit()
            logging.info(f"Se eliminaron {backups_eliminados} backups antiguos")

    except Exception as e:
        logging.error(f"Error al limpiar backups antiguos: {str(e)}")

def crear_backup_manual():
    """Crear backup manual (llamado desde la interfaz web)"""
    return crear_backup_automatico()

def verificar_estado_backups():
    """Verificar estado del sistema de backups"""
    try:
        app = create_app()
        db, BackupHistory, ConfiguracionSistema = init_db(app)

        with app.app_context():
            # Obtener estadísticas
            total_backups = BackupHistory.query.count()
            backups_automaticos = BackupHistory.query.filter_by(tipo='automatico').count()
            backups_manuales = BackupHistory.query.filter_by(tipo='manual').count()

            # Obtener último backup
            ultimo_backup = BackupHistory.query.order_by(BackupHistory.fecha_creacion.desc()).first()

            # Verificar espacio en disco
            backup_dir = ConfiguracionSistema.get_config('backup_location', 'backups/')
            if os.path.exists(backup_dir):
                import shutil
                total, used, free = shutil.disk_usage(backup_dir)
                espacio_libre_gb = free / (1024**3)
            else:
                espacio_libre_gb = 0

            return {
                'total_backups': total_backups,
                'backups_automaticos': backups_automaticos,
                'backups_manuales': backups_manuales,
                'ultimo_backup': ultimo_backup.fecha_creacion if ultimo_backup else None,
                'espacio_libre_gb': round(espacio_libre_gb, 2),
                'backup_dir': backup_dir
            }

    except Exception as e:
        logging.error(f"Error al verificar estado de backups: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1]

        if comando == 'auto':
            success = crear_backup_automatico()
            print("✅ Backup automático completado" if success else "❌ Error en backup automático")
        elif comando == 'manual':
            success = crear_backup_manual()
            print("✅ Backup manual completado" if success else "❌ Error en backup manual")
        elif comando == 'status':
            status = verificar_estado_backups()
            if status:
                print("📊 Estado del Sistema de Backups:")
                print(f"   Total de backups: {status['total_backups']}")
                print(f"   Backups automáticos: {status['backups_automaticos']}")
                print(f"   Backups manuales: {status['backups_manuales']}")
                print(f"   Último backup: {status['ultimo_backup']}")
                print(f"   Espacio libre: {status['espacio_libre_gb']} GB")
            else:
                print("❌ Error al obtener estado del sistema de backups")
        else:
            print("Uso: python backup_manager.py [auto|manual|status]")
    else:
        # Ejecutar backup automático por defecto
        success = crear_backup_automatico()
        sys.exit(0 if success else 1)