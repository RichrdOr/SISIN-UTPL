# SISIN-UTPL
Software para gestión de pólizas, siniestros, reportes y usuarios.

## Descripción
Este proyecto es un sistema de gestión para pólizas de seguro, siniestros, reportes y usuarios, desarrollado con Django y PostgreSQL.

## Requisitos
- Python 3.8+
- PostgreSQL
- Django 5.2.9

## Instalación y Configuración

1. **Clona el repositorio:**
   ```
   git clone <url-del-repositorio>
   cd SISIN-UTPL
   ```

2. **Instala las dependencias:**
   ```
   pip install -r requirements.txt
   ```

3. **Configura PostgreSQL:**
   - Asegúrate de tener PostgreSQL instalado y ejecutándose.
   - Crea una base de datos llamada `sisis_utpl`.
   - Actualiza las credenciales en `SISIN_UTPL/settings.py` si es necesario (usuario: postgres, contraseña: contraseña, host: localhost, puerto: 5432).

4. **Ejecuta las migraciones para crear las tablas:**
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Ejecuta el servidor de desarrollo:**
   ```
   python manage.py runserver
   ```

## Modelos
- **Usuario**: Gestiona información de usuarios (nombre, apellido, email, teléfono).
- **Poliza**: Gestiona pólizas de seguro con estados (activa, suspendida, cancelada, expirada).
- **Siniestro**: Gestiona siniestros relacionados con pólizas.
- **Reporte**: Gestiona reportes generados por usuarios.

## Uso
- Accede al admin de Django en `http://localhost:8000/admin/` para gestionar los datos.
- Las tablas se crean automáticamente al ejecutar las migraciones.
