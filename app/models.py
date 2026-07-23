from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

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

    def to_dict(self):
        deuda = sum(v.saldo for v in self.ventas if v.saldo > 0)
        monto_total = sum(v.valor_total for v in self.ventas)
        ultima_venta = self.ventas[-1] if self.ventas else None

        return {
            'id': self.id,
            'nombre': self.nombre,
            'documento': self.documento or 'S/D',
            'telefono': self.telefono or '',
            'ciudad': self.ciudad or 'S/C',
            'talla_calzado': self.talla_calzado or '-',
            'talla_camiseta': self.talla_camiseta or '-',
            'talla_jean': self.talla_jean or '-',
            'tallas': f"{self.talla_calzado or '-'}/{self.talla_camiseta or '-'}/{self.talla_jean or '-'}",
            'compras': len(self.ventas),
            'monto': monto_total,
            'deuda': deuda,
            'ultimo_producto': ultima_venta.descripcion if ultima_venta else 'Ninguno'
        }

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

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'marca': self.marca or '-',
            'referencia': self.referencia or 'S/R',
            'categoria': self.categoria or 'Calzado',
            'talla': self.talla or '-',
            'color': self.color or '-',
            'precio_costo': self.precio_costo,
            'precio_venta': self.precio_venta,
            'stock': self.stock
        }

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

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M'),
            'cliente': self.cliente.nombre if self.cliente else 'Cliente Eliminado',
            'descripcion': self.descripcion,
            'valor_total': self.valor_total,
            'abono': self.abono,
            'saldo': self.saldo,
            'estado': 'Pendiente' if self.saldo > 0 else 'Completada'
        }

class Importacion(db.Model):
    __tablename__ = 'importaciones'
    id = db.Column(db.Integer, primary_key=True)
    codigo_caja = db.Column(db.String(50), unique=True, nullable=False)
    guia = db.Column(db.String(100), nullable=True)
    empresa_transporte = db.Column(db.String(100), nullable=True)
    origen = db.Column(db.String(100), default='EEUU')
    peso_libras = db.Column(db.Float, nullable=False, default=0.0)
    costo_usd = db.Column(db.Float, nullable=False, default=0.0)
    trm = db.Column(db.Float, nullable=False, default=0.0)
    costo_flete_cop = db.Column(db.Float, nullable=False, default=0.0)
    estado = db.Column(db.String(50), default='En Tránsito')
    fecha_llegada = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'codigo_caja': self.codigo_caja,
            'guia': self.guia or 'S/G',
            'empresa_transporte': self.empresa_transporte or 'S/E',
            'origen': self.origen or 'EEUU',
            'peso_libras': self.peso_libras,
            'costo_usd': self.costo_usd,
            'trm': self.trm,
            'costo_flete_cop': self.costo_flete_cop,
            'estado': self.estado,
            'fecha_llegada': self.fecha_llegada or '-'
        }