#!/usr/bin/env python3
"""
Script para verificar la consistencia de datos entre usuarios y carreras
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Carrera

with app.app_context():
    print("=== VERIFICACIÓN DE DATOS DE JEFES DE CARRERA ===\n")
    
    # Buscar todos los usuarios con rol 'jefe_carrera'
    jefes = User.query.filter_by(rol='jefe_carrera', activo=True).all()
    
    print(f"Usuarios con rol 'jefe_carrera': {len(jefes)}")
    for jefe in jefes:
        print(f"  - {jefe.get_nombre_completo()} (ID: {jefe.id})")
        print(f"    Email: {jefe.email}")
        print(f"    Carrera ID: {jefe.carrera_id}")
        if jefe.carrera_id:
            carrera = Carrera.query.get(jefe.carrera_id)
            print(f"    Carrera: {carrera.nombre if carrera else 'No encontrada'}")
        print()
    
    print("\n=== VERIFICACIÓN DESDE EL LADO DE CARRERAS ===\n")
    
    # Buscar todas las carreras y verificar sus jefes
    carreras = Carrera.query.filter_by(activa=True).all()
    
    print(f"Carreras activas: {len(carreras)}")
    for carrera in carreras:
        print(f"  - {carrera.nombre} (ID: {carrera.id})")
        print(f"    Código: {carrera.codigo}")
        
        # Usar el método del modelo para buscar jefe
        jefe = carrera.get_jefe_carrera()
        if jefe:
            print(f"    Jefe según método get_jefe_carrera(): {jefe.get_nombre_completo()}")
        else:
            print(f"    Jefe según método get_jefe_carrera(): Sin asignar")
        
        # Buscar directamente en la base de datos
        jefe_directo = User.query.filter(
            User.carrera_id == carrera.id,
            User.rol == 'jefe_carrera',
            User.activo == True
        ).first()
        
        if jefe_directo:
            print(f"    Jefe según búsqueda directa: {jefe_directo.get_nombre_completo()}")
        else:
            print(f"    Jefe según búsqueda directa: Sin asignar")
        print()