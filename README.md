# Plataforma Calamar - Prototipo Funcional de Aplicación Móvil (MVP)

Este repositorio contiene el código base para un prototipo funcional de aplicación móvil destinada a conectar campesinos de Calamar (Colombia) con consumidores/compradores. Incluye funcionalidades clave como publicación de productos, geolocalización, módulo de temporadas agrícolas y base de datos inicial.

## Características
- **Base de Datos**: MySQL con tablas para usuarios, productos y temporadas agrícolas.
- **Procesamiento de Datos**: Script Python para manejar DataFrames, optimizar queries y simular sincronización.
- **Indicadores Clave**:
  - Prueba piloto exitosa: 80% de funcionalidades (Publicación, Chat, Notificación) operativas.
  - Documento ERS aprobado: 100% de requerimientos funcionales/no funcionales validados.
  - Geolocalización: 90% de productos con punto de entrega geo-referenciado.
  - Informe de Necesidades: Análisis de conectividad y alfabetización digital.
  - Base de Datos Inicial: Al menos 50 productos registrados.
  - Temporadas Agrícolas: Datos para 5 cultivos clave (Maíz, Yuca, Plátano, Café, Arroz).
  - Capacitación: Al menos 70% de campesinos capacitados.
  - Documentación: Informe final, manual técnico y repositorio de código.

## Instalación y Uso
1. **Base de Datos**:
   - Instala MySQL.
   - Ejecuta el script `database.sql` para crear la DB y poblar datos iniciales.

2. **Script Python**:
   - Instala dependencias: `pip install -r requirements.txt`.
   - Ejecuta `python app.py` para procesar datos y sincronizar temporadas.

3. **Integración Móvil**:
   - Para el MVP, integra con frameworks como React Native o Flutter. Usa APIs como Google Maps para geolocalización.
   - Backend: Considera PHP o Node.js para chat y notificaciones.

## Contribuciones
Este proyecto es parte de un esfuerzo colaborativo. Contribuciones son bienvenidas vía pull requests.

## Licencia
[Agrega una licencia si es necesario, ej. MIT].
