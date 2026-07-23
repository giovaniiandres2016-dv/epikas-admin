import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Usuario, Cliente, Inventario, Venta, Importacion

# Listas de datos base con enfoque colombiano (Medellín/Antioquia y general)
NOMBRES = [
    "Carlos Andrés", "María Alejandra", "Juan David", "Ana Sofía", "Luis Fernando",
    "Valentina", "Santiago", "Manuela", "Alejandro", "Isabella", "Mateo", "Camila",
    "Daniel", "Mariana", "Felipe", "Luciana", "Esteban", "Sara", "Tomás", "Antonia"
]

APELLIDOS = [
    "Gómez", "Rodríguez", "López", "Pérez", "García", "Martínez", "Jiménez", "Ospina",
    "Betancourt", "Restrepo", "Echeverri", "Mejía", "Henao", "Arango", "Vásquez", "Valencia"
]

CIUDADES = ["Medellín", "Bello", "Envigado", "Itagüí", "Sabaneta", "Bogotá", "Cali", "Barranquilla"]

MARCAS_CALZADO = ["Nike", "Adidas", "Jordan", "New Balance", "Puma", "Converse", "Vans"]
MARCAS_ROPA = ["ÉPIKA", "Zara", "Levis", "Under Armour", "American Eagle"]
COLORES = ["Negro", "Blanco", "Gris", "Rojo", "Azul Oscuro", "Verde Militar", "Beige"]

TRANSPORTADORAS = ["Coordinadora", "Servientrega", "Interrapidísimo", "DHL", "FedEx"]
ORIGENES_IMPORTACION = ["Miami, FL", "Houston, TX", "New York, NY", "Los Angeles, CA"]

def generar_telefono():
    prefijos = ["300", "301", "302", "304", "305", "310", "311", "312", "313", "314", "320", "321"]
    return f"{random.choice(prefijos)}{random.randint(1000000, 9999999)}"

def generar_documento():
    return str(random.randint(10000000, 115000000))

def seed_database():
    app = create_app()
    with app.app_context():
        print("🌱 Iniciando inyección de datos de prueba (contexto Colombia)...")

        # 1. Limpiar base de datos respetando relaciones en cascada
        print("🧹 Limpiando registros anteriores...")
        Venta.query.delete()
        Inventario.query.delete()
        Cliente.query.delete()
        Importacion.query.delete()
        db.session.commit()

        # 2. Generar Clientes (20 registros)
        print("👥 Creando clientes...")
        clientes_objs = []
        for _ in range(20):
            nombre_completo = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
            cliente = Cliente(
                documento=generar_documento(),
                nombre=nombre_completo,
                telefono=generar_telefono(),
                ciudad=random.choice(CIUDADES),
                talla_calzado=str(random.choice([36, 37, 38, 39, 40, 41, 42, 43])),
                talla_camiseta=random.choice(["S", "M", "L", "XL"]),
                talla_jean=str(random.choice([28, 30, 32, 34, 36])),
                estado="Frecuente"
            )
            db.session.add(cliente)
            clientes_objs.append(cliente)
        db.session.commit()

        # 3. Generar Inventario (15 productos)
        print("📦 Creando inventario de productos...")
        inventario_objs = []
        categorias = ["Calzado", "Ropa", "Accesorios"]
        
        for _ in range(15):
            cat = random.choice(categorias)
            if cat == "Calzado":
                marca = random.choice(MARCAS_CALZADO)
                ref = f"NK-{random.randint(100, 999)}"
                costo = random.randint(180000, 350000)
                venta = costo * random.uniform(1.4, 1.7)
                talla = str(random.choice([38, 39, 40, 41, 42]))
            elif cat == "Ropa":
                marca = random.choice(MARCAS_ROPA)
                ref = f"EP-{random.randint(100, 999)}"
                costo = random.randint(60000, 140000)
                venta = costo * random.uniform(1.5, 1.8)
                talla = random.choice(["S", "M", "L", "XL"])
            else:
                marca = "ÉPIKA Accesorios"
                ref = f"ACC-{random.randint(10, 99)}"
                costo = random.randint(30000, 70000)
                venta = costo * random.uniform(1.6, 2.0)
                talla = "Única"

            color = random.choice(COLORES)
            item = Inventario(
                nombre=f"{marca} {ref} {color}",
                marca=marca,
                referencia=ref,
                categoria=cat,
                talla=talla,
                color=color,
                precio_costo=float(costo),
                precio_venta=float(round(venta, -3)), # Redondear a miles
                stock=random.randint(1, 8)
            )
            db.session.add(item)
            inventario_objs.append(item)
        db.session.commit()

        # 4. Generar Importaciones / Cajas (8 registros)
        print("✈️ Creando registros de importaciones y cajas...")
        estados_imp = ["En Casillero", "En Tránsito", "Entregado"]
        for i in range(1, 9):
            peso = round(random.uniform(3.5, 18.2), 2)
            usd = round(peso * random.uniform(4.5, 7.0), 2)
            trm = 3950.0
            flete_cop = usd * trm
            
            importacion = Importacion(
                codigo_caja=f"C-2026-0{i}",
                guia=f"1Z{random.randint(1000000000000000, 9999999999999999)}",
                empresa_transporte=random.choice(TRANSPORTADORAS),
                origen=random.choice(ORIGENES_IMPORTACION),
                peso_libras=peso,
                costo_usd=usd,
                trm=trm,
                costo_flete_cop=flete_cop,
                estado=random.choice(estados_imp),
                fecha_llegada=(datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            )
            db.session.add(importacion)
        db.session.commit()

        # 5. Generar Ventas y Cuentas por Cobrar (25 registros)
        print("💳 Creando transacciones de ventas y abonos...")
        for _ in range(25):
            cli = random.choice(clientes_objs)
            prod = random.choice(inventario_objs)
            
            valor_total = prod.precio_venta
            # Simular que un 40% de las ventas queden con saldo pendiente (crédito/separado)
            es_pendiente = random.random() < 0.4
            
            if es_pendiente:
                abono = round(valor_total * random.choice([0.3, 0.5, 0.7]), -3)
                saldo = valor_total - abono
            else:
                abono = valor_total
                saldo = 0.0

            dias_atras = random.randint(0, 45)
            fecha_venta = datetime.utcnow() - timedelta(days=dias_atras)

            venta = Venta(
                tipo="Venta",
                cliente_id=cli.id,
                inventario_id=prod.id,
                descripcion=f"{prod.nombre} (Talla: {prod.talla})",
                valor_total=valor_total,
                abono=abono,
                saldo=saldo,
                estado_venta="Pendiente" if saldo > 0 else "Completada",
                fecha=fecha_venta
            )
            db.session.add(venta)
        db.session.commit()

        print("✨ ¡Inyección completada con éxito! La base de datos contiene datos realistas adaptados al mercado colombiano.")

if __name__ == "__main__":
    seed_database()