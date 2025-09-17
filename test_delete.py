from app import app, db
from models import User, HorarioAcademico, DisponibilidadProfesor

print("=== TEST DE ELIMINACIÓN DE USUARIO ===")

with app.app_context():
    # Crear usuario de prueba
    test_user = User(
        username='test_delete',
        email='test_delete@example.com',
        password='password123',
        nombre='Test',
        apellido='Delete',
        rol='profesor_completo'
    )
    db.session.add(test_user)
    db.session.commit()

    user_id = test_user.id
    print(f"✅ Usuario creado con ID: {user_id}")

    # Verificar que existe
    user = User.query.get(user_id)
    if user:
        print(f"✅ Usuario encontrado: {user.username}")

        # Intentar eliminar
        try:
            # Eliminar relaciones
            HorarioAcademico.query.filter_by(profesor_id=user.id).delete()
            HorarioAcademico.query.filter_by(creado_por=user.id).delete()
            DisponibilidadProfesor.query.filter_by(profesor_id=user.id).delete()
            DisponibilidadProfesor.query.filter_by(creado_por=user.id).delete()

            # Eliminar usuario
            db.session.delete(user)
            db.session.commit()

            print("✅ Usuario eliminado exitosamente")

            # Verificar que ya no existe
            deleted_user = User.query.get(user_id)
            if deleted_user is None:
                print("✅ Confirmado: Usuario ya no existe en la base de datos")
            else:
                print("❌ Error: Usuario aún existe")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al eliminar usuario: {e}")
    else:
        print("❌ Usuario no encontrado")

print("Test completado")