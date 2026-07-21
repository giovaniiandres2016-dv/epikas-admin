from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), default='Admin')

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    documento = db.Column(db.String(50), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    talla_calzado = db.Column(db.String(20), nullable=True)
    talla_camiseta = db.Column(db.String(20), nullable=True)
    talla_jean = db.Column(db.String(20), nullable=True)
    estado = db.Column(db.String(50), default='Nuevo')
    ventas = db.relationship('Venta', backref='cliente', lazy=True, cascade="all, delete-orphan")

class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100), nullable=True)
    referencia = db.Column(db.String(50), nullable=True)
    categoria = db.Column(db.String(50), nullable=True)
    talla = db.Column(db.String(20), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    precio_costo = db.Column(db.Float, nullable=False, default=0.0)
    precio_venta = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), default='Venta')
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    inventario_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=True)
    descripcion = db.Column(db.Text, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    abono = db.Column(db.Float, default=0.0)
    saldo = db.Column(db.Float, nullable=False)
    estado_venta = db.Column(db.String(50), default='Completada')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)