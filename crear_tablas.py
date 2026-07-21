from app import create_app, db
from app.models import Usuario, Producto

# Creamos una instancia de la aplicación
app = create_app()

# Usamos el contexto de la app para conectarnos a la base de datos y crear las tablas
with app.app_context():
    db.create_all()
    print("✅ ¡Las tablas de Usuarios y Productos se han creado con éxito en PostgreSQL!")