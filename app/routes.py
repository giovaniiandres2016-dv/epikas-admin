from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func
from werkzeug.security import check_password_hash
import re
from .models import db, Usuario, Cliente, Inventario, Venta, Importacion

main_bp = Blueprint('main', __name__)

# --- VISTAS HTML ---
@main_bp.route('/')
def login_page():
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# --- AUTENTICACIÓN ---
@main_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    usuario = Usuario.query.filter_by(username=username).first()
    if usuario and check_password_hash(usuario.password_hash, password):
        return jsonify({'message': 'Login exitoso', 'token': 'epika-session-token'}), 200
    
    return jsonify({'error': 'Credenciales incorrectas'}), 401

# --- API DASHBOARD / RESUMEN GENERAL ---
@main_bp.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    # 1. Ventas del Mes (calculadas sobre el total de ventas registradas o filtradas por mes actual)
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    ventas_totales = Venta.query.all()
    ventas_mes = sum(v.valor_total for v in ventas_totales) # Se puede refinar si se almacena fecha con datetime real
    
    # 2. Total por Cobrar (Suma de saldos pendientes)
    total_por_cobrar = sum(v.saldo for v in ventas_totales if v.saldo > 0)
    
    # 3. Ticket Promedio
    promedio_venta = (ventas_mes / len(ventas_totales)) if ventas_totales else 0
    
    # 4. Cliente Destacado (Mayor volumen de compras acumuladas)
    clientes_stats = db.session.query(
        Cliente, 
        func.sum(Venta.valor_total).label('total_compras')
    ).join(Venta, Cliente.id == Venta.cliente_id).group_by(Cliente.id).order_by(func.sum(Venta.valor_total).desc()).first()
    
    cliente_destacado = None
    if clientes_stats:
        cli, tot = clientes_stats
        cliente_destacado = {'nombre': cli.nombre, 'total': tot}

    # 5. Próximas Cuotas y Saldos Pendientes (Ventas con saldo > 0)
    cuotas_pendientes = []
    for v in ventas_totales:
        if v.saldo > 0:
            cliente_nombre = v.cliente.nombre if v.cliente else 'Cliente General'
            cuotas_pendientes.append({
                'cliente': cliente_nombre,
                'descripcion': v.descripcion or 'Sin descripción',
                'valor_total': v.valor_total,
                'abono': v.abono,
                'saldo': v.saldo
            })

    # 6. Alertas de Stock Bajo (stock <= 2)
    productos_bajo_stock = Inventario.query.filter(Inventario.stock <= 2).all()
    stock_bajo = [{
        'nombre': p.nombre,
        'talla': p.talla,
        'referencia': p.referencia,
        'stock': p.stock
    } for p in productos_bajo_stock]

    return jsonify({
        'ventas_mes': ventas_mes,
        'total_por_cobrar': total_por_cobrar,
        'promedio_venta': promedio_venta,
        'cliente_destacado': cliente_destacado,
        'cuotas_pendientes': cuotas_pendientes,
        'stock_bajo': stock_bajo
    }), 200

# --- API CLIENTES ---
@main_bp.route('/api/clientes', methods=['GET'])
def get_clientes():
    clientes = Cliente.query.all()
    resultado = []
    for c in clientes:
        total_compras = sum(v.valor_total for v in c.ventas)
        deuda_total = sum(v.saldo for v in c.ventas)
        cantidad_compras = len(c.ventas)
        tallas_str = f"{c.talla_calzado or '-'}/{c.talla_camiseta or '-'}/{c.talla_jean or '-'}"
        
        resultado.append({
            'id': c.id,
            'nombre': c.nombre,
            'documento': c.documento or 'S/D',
            'telefono': c.telefono or '',
            'ciudad': c.ciudad or 'S/C',
            'tallas': tallas_str,
            'talla_calzado': c.talla_calzado,
            'talla_camiseta': c.talla_camiseta,
            'talla_jean': c.talla_jean,
            'compras': cantidad_compras,
            'monto': total_compras,
            'deuda': deuda_total
        })
    return jsonify(resultado), 200

@main_bp.route('/api/clientes', methods=['POST'])
def create_cliente():
    data = request.get_json() or {}
    nuevo = Cliente(
        nombre=data.get('nombre'),
        documento=data.get('documento'),
        telefono=data.get('telefono'),
        ciudad=data.get('ciudad'),
        talla_calzado=data.get('talla_calzado'),
        talla_camiseta=data.get('talla_camiseta'),
        talla_jean=data.get('talla_jean')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@main_bp.route('/api/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    c = Cliente.query.get_or_404(id)
    data = request.get_json() or {}
    c.nombre = data.get('nombre', c.nombre)
    c.documento = data.get('documento', c.documento)
    c.telefono = data.get('telefono', c.telefono)
    c.ciudad = data.get('ciudad', c.ciudad)
    c.talla_calzado = data.get('talla_calzado', c.talla_calzado)
    c.talla_camiseta = data.get('talla_camiseta', c.talla_camiseta)
    c.talla_jean = data.get('talla_jean', c.talla_jean)
    db.session.commit()
    return jsonify(c.to_dict()), 200

@main_bp.route('/api/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Cliente eliminado'}), 200

# --- API INVENTARIO ---
@main_bp.route('/api/inventario', methods=['GET'])
def get_inventario():
    items = Inventario.query.all()
    return jsonify([i.to_dict() for i in items]), 200

@main_bp.route('/api/inventario', methods=['POST'])
def create_inventario():
    data = request.get_json() or {}
    nuevo = Inventario(
        nombre=data.get('nombre'),
        marca=data.get('marca', '-'),
        referencia=data.get('referencia', 'S/R'),
        categoria=data.get('categoria', 'Calzado'),
        talla=data.get('talla', '-'),
        color=data.get('color', '-'),
        precio_costo=float(data.get('precio_costo', 0)),
        precio_venta=float(data.get('precio_venta', 0)),
        stock=int(data.get('stock', 0))
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@main_bp.route('/api/inventario/<int:id>', methods=['PUT'])
def update_inventario(id):
    i = Inventario.query.get_or_404(id)
    data = request.get_json() or {}
    i.nombre = data.get('nombre', i.nombre)
    i.marca = data.get('marca', i.marca)
    i.referencia = data.get('referencia', i.referencia)
    i.categoria = data.get('categoria', i.categoria)
    i.talla = data.get('talla', i.talla)
    i.color = data.get('color', i.color)
    i.precio_costo = float(data.get('precio_costo', i.precio_costo))
    i.precio_venta = float(data.get('precio_venta', i.precio_venta))
    i.stock = int(data.get('stock', i.stock))
    db.session.commit()
    return jsonify(i.to_dict()), 200

@main_bp.route('/api/inventario/<int:id>', methods=['DELETE'])
def delete_inventario(id):
    i = Inventario.query.get_or_404(id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({'message': 'Producto eliminado'}), 200

# --- API VENTAS ---
@main_bp.route('/api/ventas', methods=['GET'])
def get_ventas():
    ventas = Venta.query.order_by(Venta.id.desc()).all()
    resultado = []
    for v in ventas:
        cliente_nombre = v.cliente.nombre if v.cliente else 'Cliente General'
        estado_venta = 'Completada' if v.saldo <= 0 else 'Pendiente'
        resultado.append({
            'id': v.id,
            'cliente': cliente_nombre,
            'descripcion': v.descripcion or 'Sin descripción',
            'valor_total': v.valor_total,
            'abono': v.abono,
            'saldo': v.saldo,
            'estado_venta': estado_venta,
            'fecha': datetime.now().strftime('%Y-%m-%d') # Ajustar si el modelo guarda timestamp real
        })
    return jsonify(resultado), 200

@main_bp.route('/api/ventas', methods=['POST'])
def create_venta():
    data = request.get_json() or {}
    cliente_id = data.get('cliente_id')

    if not cliente_id and data.get('nuevo_cliente'):
        nc = data['nuevo_cliente']
        nuevo_cli = Cliente(
            nombre=nc.get('nombre'),
            documento=nc.get('documento'),
            telefono=nc.get('telefono')
        )
        db.session.add(nuevo_cli)
        db.session.flush()
        cliente_id = nuevo_cli.id

    valor_total = float(data.get('valor_total', 0))
    abono = float(data.get('abono', 0))
    saldo = valor_total - abono

    nueva_v = Venta(
        cliente_id=cliente_id,
        inventario_id=data.get('inventario_id'),
        descripcion=data.get('descripcion'),
        valor_total=valor_total,
        abono=abono,
        saldo=saldo
    )
    db.session.add(nueva_v)

    if data.get('inventario_id'):
        inv = Inventario.query.get(data['inventario_id'])
        if inv and inv.stock > 0:
            inv.stock -= 1

    db.session.commit()
    return jsonify(nueva_v.to_dict()), 201

@main_bp.route('/api/ventas/<int:id>/abono', methods=['PUT'])
def abono_venta(id):
    v = Venta.query.get_or_404(id)
    data = request.get_json() or {}
    monto_abono = float(data.get('abono', 0))

    v.abono += monto_abono
    v.saldo = max(0.0, v.valor_total - v.abono)
    db.session.commit()
    return jsonify(v.to_dict()), 200

# --- API IMPORTACIONES ---
@main_bp.route('/api/importaciones', methods=['GET'])
def get_importaciones():
    imps = Importacion.query.order_by(Importacion.id.desc()).all()
    return jsonify([i.to_dict() for i in imps]), 200

@main_bp.route('/api/importaciones', methods=['POST'])
def create_importacion():
    data = request.get_json() or {}
    nueva = Importacion(
        codigo_caja=data.get('codigo_caja'),
        guia=data.get('guia'),
        empresa_transporte=data.get('empresa_transporte'),
        origen=data.get('origen', 'EEUU'),
        peso_libras=float(data.get('peso_libras', 0.0)),
        costo_usd=float(data.get('costo_usd', 0.0)),
        trm=float(data.get('trm', 0.0)),
        costo_flete_cop=float(data.get('costo_flete_cop', 0.0)),
        estado=data.get('estado', 'En Tránsito'),
        fecha_llegada=data.get('fecha_llegada')
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify(nueva.to_dict()), 201

@main_bp.route('/api/importaciones/<int:id>', methods=['PUT'])
def update_importacion(id):
    imp = Importacion.query.get_or_404(id)
    data = request.get_json() or {}
    imp.codigo_caja = data.get('codigo_caja', imp.codigo_caja)
    imp.guia = data.get('guia', imp.guia)
    imp.empresa_transporte = data.get('empresa_transporte', imp.empresa_transporte)
    imp.origen = data.get('origen', imp.origen)
    imp.peso_libras = float(data.get('peso_libras', imp.peso_libras))
    imp.costo_usd = float(data.get('costo_usd', imp.costo_usd))
    imp.trm = float(data.get('trm', imp.trm))
    imp.costo_flete_cop = float(data.get('costo_flete_cop', imp.costo_flete_cop))
    imp.estado = data.get('estado', imp.estado)
    imp.fecha_llegada = data.get('fecha_llegada', imp.fecha_llegada)
    db.session.commit()
    return jsonify(imp.to_dict()), 200

@main_bp.route('/api/importaciones/<int:id>', methods=['DELETE'])
def delete_importacion(id):
    imp = Importacion.query.get_or_404(id)
    db.session.delete(imp)
    db.session.commit()
    return jsonify({'message': 'Importación eliminada'}), 200

@main_bp.route('/api/parse-guia', methods=['POST'])
def parse_guia():
    if 'file' not in request.files:
        return jsonify({'error': 'Sin archivo'}), 400
    file = request.files['file']
    text_content = ""

    if file.filename.lower().endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text_content += (page.extract_text() or "") + "\n"
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        text_content = file.read().decode('utf-8', errors='ignore')

    guia_match = re.search(r'(?:Gu[íi]a|Tracking|#|Waybill)[:\s]*([A-Z0-9]{8,20})', text_content, re.IGNORECASE)
    if not guia_match:
        guia_match = re.search(r'\b(1Z[A-Z0-9]{16}|TBA[0-9]{12})\b', text_content, re.IGNORECASE)

    peso_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lbs?|libras?|lb)', text_content, re.IGNORECASE)
    peso_lbs = float(peso_match.group(1)) if peso_match else 0.0

    empresa = ''
    if re.search(r'coordinadora', text_content, re.IGNORECASE):
        empresa = 'Coordinadora'
    elif re.search(r'interrapidisimo', text_content, re.IGNORECASE):
        empresa = 'Interrapidísimo'
    elif re.search(r'servientrega', text_content, re.IGNORECASE):
        empresa = 'Servientrega'
    elif re.search(r'dhl', text_content, re.IGNORECASE):
        empresa = 'DHL'
    elif re.search(r'fedex', text_content, re.IGNORECASE):
        empresa = 'FedEx'

    return jsonify({
        'success': True,
        'extracted': {
            'guia': guia_match.group(1) if guia_match else '',
            'peso_libras': peso_lbs,
            'empresa_transporte': empresa
        }
    }), 200