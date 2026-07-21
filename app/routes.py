from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from .models import db, Usuario, Cliente, Inventario, Venta

main_bp = Blueprint('main', __name__)
SECRET_KEY = 'tu_clave_secreta_super_segura'

# --- DECORADOR AUTENTICACIÓN JWT ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token no proporcionado'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = Usuario.query.filter_by(id=data['id']).first()
        except Exception:
            return jsonify({'message': 'Token inválido o expirado'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# --- RUTAS DE VISTAS ---
@main_bp.route('/')
def login_page():
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

# --- AUTH API ---
@main_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    user = Usuario.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Credenciales incorrectas'}), 401
        
    token = jwt.encode({
        'id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=8)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({'token': token, 'username': user.username}), 200

# --- API CLIENTES ---
@main_bp.route('/api/clientes', methods=['GET'])
@token_required
def get_clientes(current_user):
    clientes = Cliente.query.all()
    resultado = []
    for c in clientes:
        total_compras = sum(v.valor_total for v in c.ventas)
        deuda_total = sum(v.saldo for v in c.ventas if v.saldo > 0)
        resultado.append({
            'id': c.id,
            'documento': c.documento or 'S/D',
            'nombre': c.nombre,
            'telefono': c.telefono or 'S/T',
            'ciudad': c.ciudad or 'S/C',
            'tallas': f"{c.talla_calzado or '-'}/{c.talla_camiseta or '-'}/{c.talla_jean or '-'}",
            'talla_calzado': c.talla_calzado or '',
            'talla_camiseta': c.talla_camiseta or '',
            'talla_jean': c.talla_jean or '',
            'compras': len(c.ventas),
            'monto': total_compras,
            'deuda': deuda_total,
            'estado': c.estado
        })
    return jsonify(resultado), 200

@main_bp.route('/api/clientes', methods=['POST'])
@token_required
def create_cliente(current_user):
    data = request.get_json() or {}
    nuevo = Cliente(
        documento=data.get('documento'),
        nombre=data.get('nombre'),
        telefono=data.get('telefono'),
        ciudad=data.get('ciudad'),
        talla_calzado=data.get('talla_calzado'),
        talla_camiseta=data.get('talla_camiseta'),
        talla_jean=data.get('talla_jean')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'message': 'Cliente registrado exitosamente', 'id': nuevo.id, 'nombre': nuevo.nombre}), 201

@main_bp.route('/api/clientes/<int:id>', methods=['PUT'])
@token_required
def update_cliente(current_user, id):
    c = Cliente.query.get_or_404(id)
    data = request.get_json() or {}
    
    c.documento = data.get('documento', c.documento)
    c.nombre = data.get('nombre', c.nombre)
    c.telefono = data.get('telefono', c.telefono)
    c.ciudad = data.get('ciudad', c.ciudad)
    c.talla_calzado = data.get('talla_calzado', c.talla_calzado)
    c.talla_camiseta = data.get('talla_camiseta', c.talla_camiseta)
    c.talla_jean = data.get('talla_jean', c.talla_jean)
    
    db.session.commit()
    return jsonify({'message': 'Cliente actualizado'}), 200

@main_bp.route('/api/clientes/<int:id>', methods=['DELETE'])
@token_required
def delete_cliente(current_user, id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Cliente eliminado'}), 200

# --- API INVENTARIO ---
@main_bp.route('/api/inventario', methods=['GET'])
@token_required
def get_inventario(current_user):
    articulos = Inventario.query.all()
    resultado = []
    for a in articulos:
        resultado.append({
            'id': a.id,
            'nombre': a.nombre,
            'marca': a.marca or '-',
            'referencia': a.referencia or 'S/R',
            'categoria': a.categoria or 'General',
            'talla': a.talla or '-',
            'color': a.color or '-',
            'precio_costo': a.precio_costo,
            'precio_venta': a.precio_venta,
            'stock': a.stock
        })
    return jsonify(resultado), 200

@main_bp.route('/api/inventario', methods=['POST'])
@token_required
def create_inventario(current_user):
    data = request.get_json() or {}
    
    marca = data.get('marca', '').strip()
    referencia = data.get('referencia', '').strip()
    color = data.get('color', '').strip()
    
    # Nombre autogenerado: Marca + Referencia + Color
    nombre_calculado = data.get('nombre') or f"{marca} {referencia} {color}".strip()
    
    nuevo = Inventario(
        nombre=nombre_calculado,
        marca=marca,
        referencia=referencia,
        categoria=data.get('categoria', 'Calzado'),
        talla=data.get('talla'),
        color=color,
        precio_costo=float(data.get('precio_costo', 0)),
        precio_venta=float(data.get('precio_venta', 0)),
        stock=int(data.get('stock', 0))
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'message': 'Producto agregado al inventario'}), 201

@main_bp.route('/api/inventario/<int:id>', methods=['PUT'])
@token_required
def update_inventario(current_user, id):
    prod = Inventario.query.get_or_404(id)
    data = request.get_json() or {}
    
    prod.marca = data.get('marca', prod.marca)
    prod.referencia = data.get('referencia', prod.referencia)
    prod.color = data.get('color', prod.color)
    prod.nombre = data.get('nombre') or f"{prod.marca} {prod.referencia} {prod.color}".strip()
    prod.categoria = data.get('categoria', prod.categoria)
    prod.talla = data.get('talla', prod.talla)
    prod.precio_costo = float(data.get('precio_costo', prod.precio_costo))
    prod.precio_venta = float(data.get('precio_venta', prod.precio_venta))
    prod.stock = int(data.get('stock', prod.stock))
    
    db.session.commit()
    return jsonify({'message': 'Producto actualizado'}), 200

@main_bp.route('/api/inventario/<int:id>', methods=['DELETE'])
@token_required
def delete_inventario(current_user, id):
    prod = Inventario.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    return jsonify({'message': 'Producto eliminado'}), 200

# --- API VENTAS ---
@main_bp.route('/api/ventas', methods=['GET'])
@token_required
def get_ventas(current_user):
    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    resultado = []
    for v in ventas:
        resultado.append({
            'id': v.id,
            'tipo': v.tipo,
            'cliente': v.cliente.nombre if v.cliente else 'Desconocido',
            'cliente_id': v.cliente_id,
            'descripcion': v.descripcion,
            'valor_total': v.valor_total,
            'abono': v.abono,
            'saldo': v.saldo,
            'estado': v.estado_venta,
            'fecha': v.fecha.strftime('%d/%m/%Y')
        })
    return jsonify(resultado), 200

@main_bp.route('/api/ventas', methods=['POST'])
@token_required
def create_venta(current_user):
    data = request.get_json() or {}
    
    cliente_id = data.get('cliente_id')
    
    # Crear cliente nuevo sobre la marcha si se ingresaron sus datos en la venta
    nuevo_cliente_data = data.get('nuevo_cliente')
    if nuevo_cliente_data and not cliente_id:
        nuevo_c = Cliente(
            nombre=nuevo_cliente_data.get('nombre'),
            documento=nuevo_cliente_data.get('documento'),
            telefono=nuevo_cliente_data.get('telefono')
        )
        db.session.add(nuevo_c)
        db.session.flush() # Genera el ID del cliente antes de guardar la venta
        cliente_id = nuevo_c.id

    inventario_id = data.get('inventario_id')
    valor_total = float(data.get('valor_total', 0))
    abono = float(data.get('abono', 0))
    saldo = valor_total - abono
    
    # Descuenta stock si se seleccionó un producto
    if inventario_id:
        prod = Inventario.query.get(inventario_id)
        if prod and prod.stock > 0:
            prod.stock -= 1

    nueva = Venta(
        tipo=data.get('tipo', 'Venta'),
        cliente_id=cliente_id,
        inventario_id=inventario_id,
        descripcion=data.get('descripcion', ''),
        valor_total=valor_total,
        abono=abono,
        saldo=saldo,
        estado_venta='Pendiente' if saldo > 0 else 'Completada'
    )
    
    db.session.add(nueva)
    db.session.commit()
    return jsonify({'message': 'Transacción registrada correctamente'}), 201

@main_bp.route('/api/ventas/<int:id>/abono', methods=['PUT'])
@token_required
def abonar_venta(current_user, id):
    venta = Venta.query.get_or_404(id)
    data = request.get_json() or {}
    monto_abono = float(data.get('abono', 0))
    
    venta.abono += monto_abono
    venta.saldo = venta.valor_total - venta.abono
    if venta.saldo <= 0:
        venta.saldo = 0
        venta.estado_venta = 'Completada'
        
    db.session.commit()
    return jsonify({'message': 'Abono registrado con éxito'}), 200