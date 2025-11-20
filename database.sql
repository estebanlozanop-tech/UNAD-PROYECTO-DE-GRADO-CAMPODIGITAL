-- Crear base de datos
CREATE DATABASE IF NOT EXISTS campodigital;
USE campodigital;

-- Tabla para usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Usa bcrypt o similar en la app
    name VARCHAR(255),
    phone VARCHAR(20),
    user_type ENUM('agricultor', 'consumidor') NOT NULL,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE
);

-- Tabla para productos
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    quantity DECIMAL(10, 2),
    unit VARCHAR(50),  -- kg, unidad, bulto, etc.
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    status ENUM('available', 'reserved', 'sold') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla para imágenes de productos
CREATE TABLE IF NOT EXISTS product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabla para conversaciones
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_conversation (product_id, buyer_id, seller_id)
);

-- Tabla para mensajes
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla para transacciones
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    payment_method VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla para calificaciones
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    rater_id INT NOT NULL,
    rated_id INT NOT NULL,
    score TINYINT NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (rater_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rated_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rating (transaction_id, rater_id, rated_id)
);

-- Índices para optimización
CREATE INDEX idx_products_location ON products (location_lat, location_lng);
CREATE INDEX idx_products_status ON products (status);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_messages_conversation ON messages (conversation_id, created_at);
CREATE INDEX idx_transactions_status ON transactions (status);

-- Ejemplo de inserción de datos (para prueba)
INSERT INTO users (email, password_hash, name, phone, user_type, location_lat, location_lng) VALUES
('agricultor1@example.com', 'hashed_password1', 'Juan Pérez', '3001234567', 'agricultor', 4.609710, -74.081749),
('consumidor1@example.com', 'hashed_password2', 'María López', '3019876543', 'consumidor', 4.609710, -74.081749);

INSERT INTO products (user_id, name, price, description, category, quantity, unit, location_lat, location_lng) VALUES
(1, 'Tomates Orgánicos', 5000.00, 'Cosecha fresca de la finca', 'Verduras', 10.0, 'kg', 4.609710, -74.081749),
(1, 'Lechugas', 3000.00, 'Verdes y crujientes', 'Verduras', 20.0, 'unidad', 4.610000, -74.082000);

INSERT INTO product_images (product_id, image_url, is_primary) VALUES
(1, 'https://storage.campodigital.com/products/tomate1.jpg', TRUE),
(1, 'https://storage.campodigital.com/products/tomate2.jpg', FALSE),
(2, 'https://storage.campodigital.com/products/lechuga1.jpg', TRUE);

INSERT INTO conversations (product_id, buyer_id, seller_id) VALUES
(1, 2, 1);

INSERT INTO messages (conversation_id, sender_id, message) VALUES
(1, 2, '¿Cuántos tomates tienes disponibles?'),
(1, 1, 'Tengo 10 kg. ¿Te interesa?');

-- Queries de ejemplo (optimizadas)

-- 1. Buscar productos disponibles cerca de una ubicación (ej. Bogotá)
SELECT p.*, u.name AS seller_name, u.phone, 
       (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = TRUE LIMIT 1) AS main_image
FROM products p
JOIN users u ON p.user_id = u.id
WHERE p.status = 'available'
AND ABS(p.location_lat - 4.609710) < 0.05
AND ABS(p.location_lng - -74.081749) < 0.05
ORDER BY 
    POW(p.location_lat - 4.609710, 2) + 
    POW(p.location_lng - -74.081749, 2) ASC
LIMIT 20;

-- 2. Obtener conversaciones de un usuario con mensajes no leídos
SELECT c.id, p.name AS product_name, 
       CASE 
           WHEN c.buyer_id = 2 THEN u_seller.name
           ELSE u_buyer.name
       END AS other_user_name,
       (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.read_at IS NULL AND m.sender_id != 2) AS unread_count,
       (SELECT message FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message,
       (SELECT created_at FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message_time
FROM conversations c
JOIN products p ON c.product_id = p.id
JOIN users u_seller ON c.seller_id = u_seller.id
JOIN users u_buyer ON c.buyer_id = u_buyer.id
WHERE c.buyer_id = 2 OR c.seller_id = 2
HAVING unread_count > 0
ORDER BY last_message_time DESC;

-- 3. Obtener estadísticas de ventas para un agricultor
SELECT 
    YEAR(t.created_at) AS year,
    MONTH(t.created_at) AS month,
    COUNT(t.id) AS total_sales,
    SUM(t.amount) AS total_revenue,
    AVG(r.score) AS average_rating
FROM transactions t
LEFT JOIN ratings r ON t.id = r.transaction_id AND r.rated_id = t.seller_id
WHERE t.seller_id = 1
AND t.status = 'completed'
GROUP BY YEAR(t.created_at), MONTH(t.created_at)
ORDER BY year DESC, month DESC;
