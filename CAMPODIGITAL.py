# CampoDigital - Sistema de conexión entre agricultores y consumidores
# Código Python para interactuar con la base de datos

import mysql.connector
from mysql.connector import Error
import datetime
import hashlib
import os  # Importamos os pero no EX_CONFIG que no existe
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import json

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'campodigital',
    'user': 'root',  
    'password': 'DIOS1234',  
}

# Clase para manejar la conexión a la base de datos
class DatabaseManager:
    def __init__(self, config=DB_CONFIG):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("Conexión exitosa a la base de datos MySQL")
                return True
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            print("Conexión a MySQL cerrada")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            print("Consulta ejecutada exitosamente")
            return True
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            self.connection.rollback()
            return False

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error al obtener datos: {e}")
            return []

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error al obtener datos: {e}")
            return None

    def get_last_insert_id(self):
        return self.cursor.lastrowid

# Clase base para modelos
class BaseModel:
    def __init__(self, db_manager):
        self.db = db_manager

    def to_dict(self):
        # Convierte el objeto a un diccionario
        return {key: value for key, value in self.__dict__.items() 
                if not key.startswith('_') and key != 'db'}

# Clase para manejar usuarios
class UserModel(BaseModel):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def create_user(self, email, password, name, phone, user_type, 
                   location_lat=None, location_lng=None, address=None, bio=None):
        # Generar hash de la contraseña
        password_hash = self._hash_password(password)
        
        query = """
        INSERT INTO users (email, password_hash, name, phone, user_type, 
                         location_lat, location_lng, address, bio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (email, password_hash, name, phone, user_type, 
                 location_lat, location_lng, address, bio)
        
        if self.db.execute_query(query, params):
            return self.db.get_last_insert_id()
        return None

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        return self.db.fetch_one(query, (user_id,))

    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = %s"
        return self.db.fetch_one(query, (email,))

    def update_user(self, user_id, **kwargs):
        # Construir la consulta dinámicamente basada en los campos proporcionados
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE users SET {set_clause} WHERE id = %s"
        
        # Añadir el user_id al final de los parámetros
        params = list(kwargs.values())
        params.append(user_id)
        
        return self.db.execute_query(query, params)

    def verify_password(self, stored_hash, provided_password):
        # Verificar si la contraseña proporcionada coincide con el hash almacenado
        provided_hash = self._hash_password(provided_password)
        return stored_hash == provided_hash

    def _hash_password(self, password):
        # Método simple para hashear contraseñas (en producción usar bcrypt)
        return hashlib.sha256(password.encode()).hexdigest()

    def get_all_farmers(self):
        query = "SELECT * FROM users WHERE user_type = 'agricultor'"
        return self.db.fetch_all(query)

    def get_all_consumers(self):
        query = "SELECT * FROM users WHERE user_type = 'consumidor'"
        return self.db.fetch_all(query)

# Clase para manejar productos
class ProductModel(BaseModel):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def create_product(self, user_id, name, description, price, quantity, unit, 
                      category=None, harvest_date=None, is_organic=False):
        query = """
        INSERT INTO products (user_id, name, description, price, quantity, unit, 
                            category, harvest_date, is_organic)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (user_id, name, description, price, quantity, unit, 
                 category, harvest_date, is_organic)
        
        if self.db.execute_query(query, params):
            return self.db.get_last_insert_id()
        return None

    def get_product_by_id(self, product_id):
        query = """
        SELECT p.*, u.name as seller_name, u.phone as seller_phone 
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = %s
        """
        return self.db.fetch_one(query, (product_id,))

    def get_products_by_user(self, user_id):
        query = "SELECT * FROM products WHERE user_id = %s"
        return self.db.fetch_all(query, (user_id,))

    def get_available_products(self):
        query = """
        SELECT p.*, u.name as seller_name 
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.status = 'available'
        ORDER BY p.created_at DESC
        """
        return self.db.fetch_all(query)

    def get_products_by_category(self, category):
        query = """
        SELECT p.*, u.name as seller_name 
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.category = %s AND p.status = 'available'
        ORDER BY p.created_at DESC
        """
        return self.db.fetch_all(query, (category,))

    def update_product(self, product_id, **kwargs):
        # Construir la consulta dinámicamente basada en los campos proporcionados
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE products SET {set_clause} WHERE id = %s"
        
        # Añadir el product_id al final de los parámetros
        params = list(kwargs.values())
        params.append(product_id)
        
        return self.db.execute_query(query, params)

    def delete_product(self, product_id):
        query = "DELETE FROM products WHERE id = %s"
        return self.db.execute_query(query, (product_id,))

    def add_product_image(self, product_id, image_url, is_primary=False):
        query = """
        INSERT INTO product_images (product_id, image_url, is_primary)
        VALUES (%s, %s, %s)
        """
        return self.db.execute_query(query, (product_id, image_url, is_primary))

    def get_product_images(self, product_id):
        query = "SELECT * FROM product_images WHERE product_id = %s"
        return self.db.fetch_all(query, (product_id,))

# Clase para manejar pedidos
class OrderModel(BaseModel):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def create_order(self, buyer_id, seller_id, total_amount, delivery_address, 
                    delivery_date, payment_method='cash', notes=None):
        query = """
        INSERT INTO orders (buyer_id, seller_id, total_amount, delivery_address, 
                          delivery_date, payment_method, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (buyer_id, seller_id, total_amount, delivery_address, 
                 delivery_date, payment_method, notes)
        
        if self.db.execute_query(query, params):
            return self.db.get_last_insert_id()
        return None

    def add_order_detail(self, order_id, product_id, quantity, unit_price):
        subtotal = Decimal(quantity) * Decimal(unit_price)
        query = """
        INSERT INTO order_details (order_id, product_id, quantity, unit_price, subtotal)
        VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (order_id, product_id, quantity, unit_price, subtotal))

    def get_order_by_id(self, order_id):
        query = """
        SELECT o.*, 
               b.name as buyer_name, b.phone as buyer_phone,
               s.name as seller_name, s.phone as seller_phone
        FROM orders o
        JOIN users b ON o.buyer_id = b.id
        JOIN users s ON o.seller_id = s.id
        WHERE o.id = %s
        """
        return self.db.fetch_one(query, (order_id,))

    def get_order_details(self, order_id):
        query = """
        SELECT od.*, p.name as product_name, p.unit
        FROM order_details od
        JOIN products p ON od.product_id = p.id
        WHERE od.order_id = %s
        """
        return self.db.fetch_all(query, (order_id,))

    def get_orders_by_buyer(self, buyer_id):
        query = """
        SELECT o.*, u.name as seller_name
        FROM orders o
        JOIN users u ON o.seller_id = u.id
        WHERE o.buyer_id = %s
        ORDER BY o.created_at DESC
        """
        return self.db.fetch_all(query, (buyer_id,))

    def get_orders_by_seller(self, seller_id):
        query = """
        SELECT o.*, u.name as buyer_name
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = %s
        ORDER BY o.created_at DESC
        """
        return self.db.fetch_all(query, (seller_id,))

    def update_order_status(self, order_id, status):
        query = "UPDATE orders SET status = %s WHERE id = %s"
        return self.db.execute_query(query, (status, order_id))

    def update_payment_status(self, order_id, payment_status):
        query = "UPDATE orders SET payment_status = %s WHERE id = %s"
        return self.db.execute_query(query, (payment_status, order_id))

# Clase para manejar reseñas
class ReviewModel(BaseModel):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def create_review(self, reviewer_id, reviewed_id, rating, comment, order_id=None, product_id=None):
        query = """
        INSERT INTO reviews (reviewer_id, reviewed_id, rating, comment, order_id, product_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (reviewer_id, reviewed_id, rating, comment, order_id, product_id)
        
        if self.db.execute_query(query, params):
            return self.db.get_last_insert_id()
        return None

    def get_reviews_by_product(self, product_id):
        query = """
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.reviewer_id = u.id
        WHERE r.product_id = %s
        ORDER BY r.created_at DESC
        """
        return self.db.fetch_all(query, (product_id,))

    def get_reviews_by_user(self, user_id):
        query = """
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.reviewer_id = u.id
        WHERE r.reviewed_id = %s
        ORDER BY r.created_at DESC
        """
        return self.db.fetch_all(query, (user_id,))

    def get_average_rating_by_product(self, product_id):
        query = """
        SELECT AVG(rating) as average_rating
        FROM reviews
        WHERE product_id = %s
        """
        result = self.db.fetch_one(query, (product_id,))
        return result['average_rating'] if result and result['average_rating'] else 0

    def get_average_rating_by_user(self, user_id):
        query = """
        SELECT AVG(rating) as average_rating
        FROM reviews
        WHERE reviewed_id = %s
        """
        result = self.db.fetch_one(query, (user_id,))
        return result['average_rating'] if result and result['average_rating'] else 0

# Clase para manejar mensajes
class MessageModel(BaseModel):
    def __init__(self, db_manager):
        super().__init__(db_manager)

    def send_message(self, sender_id, receiver_id, message):
        query = """
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (%s, %s, %s)
        """
        params = (sender_id, receiver_id, message)
        
        if self.db.execute_query(query, params):
            return self.db.get_last_insert_id()
        return None

    def get_conversation(self, user1_id, user2_id):
        query = """
        SELECT m.*, 
               s.name as sender_name,
               r.name as receiver_name
        FROM messages m
        JOIN users s ON m.sender_id = s.id
        JOIN users r ON m.receiver_id = r.id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.created_at ASC
        """
        params = (user1_id, user2_id, user2_id, user1_id)
        return self.db.fetch_all(query, params)

    def mark_as_read(self, message_id):
        query = "UPDATE messages SET is_read = TRUE WHERE id = %s"
        return self.db.execute_query(query, (message_id,))

    def get_unread_messages_count(self, user_id):
        query = """
        SELECT COUNT(*) as unread_count
        FROM messages
        WHERE receiver_id = %s AND is_read = FALSE
        """
        result = self.db.fetch_one(query, (user_id,))
        return result['unread_count'] if result else 0

# Aplicación principal
class CampoDigitalApp:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.connect()
        
        # Inicializar modelos
        self.user_model = UserModel(self.db_manager)
        self.product_model = ProductModel(self.db_manager)
        self.order_model = OrderModel(self.db_manager)
        self.review_model = ReviewModel(self.db_manager)
        self.message_model = MessageModel(self.db_manager)

    def close(self):
        self.db_manager.disconnect()

    # Ejemplo de flujo de compra
    def purchase_flow_example(self):
        # 1. Registrar usuarios (agricultor y consumidor)
        farmer_id = self.user_model.create_user(
            email="nuevo_agricultor@ejemplo.com",
            password="contraseña123",
            name="Pedro Agricultor",
            phone="3001112233",
            user_type="agricultor",
            location_lat=4.6234,
            location_lng=-74.0836,
            address="Finca La Esperanza, Vía Choachí",
            bio="Agricultor de productos orgánicos con 10 años de experiencia"
        )
        
        consumer_id = self.user_model.create_user(
            email="nuevo_consumidor@ejemplo.com",
            password="contraseña456",
            name="Laura Consumidora",
            phone="3109998877",
            user_type="consumidor",
            location_lat=4.6560,
            location_lng=-74.0595,
            address="Calle 93 #11-30, Bogotá",
            bio="Amante de los productos frescos y orgánicos"
        )
        
        print(f"Agricultor creado con ID: {farmer_id}")
        print(f"Consumidor creado con ID: {consumer_id}")
        
        # 2. Agricultor publica productos
        yuca_id = self.product_model.create_product(
            user_id=farmer_id,
            name="Yuca Fresca",
            description="Yuca recién cosechada, ideal para sancocho y acompañamientos",
            price=2500.00,
            quantity=80.00,
            unit="kg",
            category="Tubérculos",
            harvest_date=datetime.date.today() - datetime.timedelta(days=3),
            is_organic=False
        )
        
        platano_id = self.product_model.create_product(
            user_id=farmer_id,
            name="Plátano Hartón",
            description="Plátano hartón verde para patacones y cocidos",
            price=3000.00,
            quantity=100.00,
            unit="kg",
            category="Plátanos",
            harvest_date=datetime.date.today() - datetime.timedelta(days=2),
            is_organic=False
        )
        
        # 3. Añadir imágenes a los productos
        self.product_model.add_product_image(
            product_id=yuca_id,
            image_url="https://ejemplo.com/imagenes/yuca1.jpg",
            is_primary=True
        )
        
        self.product_model.add_product_image(
            product_id=platano_id,
            image_url="https://ejemplo.com/imagenes/platano1.jpg",
            is_primary=True
        )
        
        print(f"Productos creados: Yuca (ID: {yuca_id}), Plátano (ID: {platano_id})")
        
        # 4. Consumidor realiza un pedido
        order_id = self.order_model.create_order(
            buyer_id=consumer_id,
            seller_id=farmer_id,
            total_amount=22500.00,  # 5kg de yuca + 5kg de plátano
            delivery_address="Calle 93 #11-30, Bogotá",
            delivery_date=datetime.date.today() + datetime.timedelta(days=2),
            payment_method="transfer",
            notes="Por favor entregar en la mañana"
        )
        
        # 5. Añadir detalles del pedido
        self.order_model.add_order_detail(
            order_id=order_id,
            product_id=yuca_id,
            quantity=5.00,
            unit_price=2500.00
        )
        
        self.order_model.add_order_detail(
            order_id=order_id,
            product_id=platano_id,
            quantity=5.00,
            unit_price=3000.00
        )
        
        print(f"Pedido creado con ID: {order_id}")
        
        # 6. Actualizar estado del pedido
        self.order_model.update_order_status(order_id, "confirmed")
        self.order_model.update_payment_status(order_id, "completed")
        
        print("Estado del pedido actualizado a 'confirmado' y pago 'completado'")
        
        # 7. Consumidor deja reseñas
        review_yuca_id = self.review_model.create_review(
            reviewer_id=consumer_id,
            reviewed_id=farmer_id,
            rating=5,
            comment="Excelente yuca, muy fresca y de buen tamaño",
            order_id=order_id,
            product_id=yuca_id
        )
        
        review_platano_id = self.review_model.create_review(
            reviewer_id=consumer_id,
            reviewed_id=farmer_id,
            rating=4,
            comment="Buen plátano, aunque algunos estaban un poco maduros",
            order_id=order_id,
            product_id=platano_id
        )
        
        print(f"Reseñas creadas: {review_yuca_id}, {review_platano_id}")
        
        # 8. Agricultor y consumidor intercambian mensajes
        message_id = self.message_model.send_message(
            sender_id=consumer_id,
            receiver_id=farmer_id,
            message="¡Gracias por los productos! ¿Tendrás maracuyá disponible próximamente?"
        )
        
        response_id = self.message_model.send_message(
            sender_id=farmer_id,
            receiver_id=consumer_id,
            message="¡Con gusto! Sí, tendré maracuyá fresca en dos semanas aproximadamente."
        )
        
        print(f"Mensajes intercambiados: {message_id}, {response_id}")
        
        # 9. Mostrar información del pedido completo
        order_info = self.order_model.get_order_by_id(order_id)
        order_details = self.order_model.get_order_details(order_id)
        
        print("\n--- Información del Pedido ---")
        print(f"Pedido #{order_info['id']}")
        print(f"Comprador: {order_info['buyer_name']} ({order_info['buyer_phone']})")
        print(f"Vendedor: {order_info['seller_name']} ({order_info['seller_phone']})")
        print(f"Total: ${order_info['total_amount']}")
        print(f"Estado: {order_info['status']}")
        print(f"Estado de pago: {order_info['payment_status']}")
        print(f"Dirección de entrega: {order_info['delivery_address']}")
        print(f"Fecha de entrega: {order_info['delivery_date']}")
        
        print("\n--- Detalles del Pedido ---")
        for detail in order_details:
            print(f"- {detail['product_name']}: {detail['quantity']} {detail['unit']} x ${detail['unit_price']} = ${detail['subtotal']}")

# Función principal para ejecutar la aplicación
def main():
    app = CampoDigitalApp()
    try:
        # Ejecutar el ejemplo de flujo de compra
        app.purchase_flow_example()
        
        # Ejemplo de búsqueda de productos
        print("\n--- Búsqueda de Productos Disponibles ---")
        available_products = app.product_model.get_available_products()
        for product in available_products:
            print(f"- {product['name']}: ${product['price']} por {product['unit']} (Vendedor: {product['seller_name']})")
        
    finally:
        app.close()

if __name__ == "__main__":
    main()
