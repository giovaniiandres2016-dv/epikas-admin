from app import create_app, db

# Inicializamos la aplicación llamando a la factoría
app = create_app()

# ==============================================================================
# CONTROL DE INFRAESTRUCTURA: CREACIÓN AUTOMÁTICA DE TABLAS
# ==============================================================================
with app.app_context():
    try:
        db.create_all()
        print("\n" + "="*60)
        print(" [ÉPIKA] Base de datos verificada y tablas mapeadas con éxito.")
        print("="*60 + "\n")
    except Exception as e:
        print("\n" + "="*60)
        print(f" [ERROR] No se pudieron inicializar las tablas: {str(e)}")
        print("="*60 + "\n")

if __name__ == '__main__':
    # Ejecución del servidor en el puerto local 5000 con autoreload activo
    app.run(debug=True, port=5000)