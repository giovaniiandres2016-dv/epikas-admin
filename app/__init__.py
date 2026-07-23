import os
from flask import Flask
from werkzeug.security import generate_password_hash
from .models import db, Usuario

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'epika_secret_key_super_segura'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///epikas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importación e instalación del Blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        
        # Crear usuario Admin predeterminado si no existe
        if not Usuario.query.filter_by(username='admin').first():
            admin_user = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                rol='Admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    return app