from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE FLASK Y BASE DE DATOS
# ============================================

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tareas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# ============================================
# MODELO DE DATOS (TABLA)
# ============================================

class Tarea(db.Model):
    """
    Modelo de la tabla 'tarea' en la base de datos
    """
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    completada = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """
        Convierte el objeto Tarea a un diccionario (para JSON)
        """
        return {
            'id': self.id,
            'texto': self.texto,
            'completada': self.completada,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }
    
    def __repr__(self):
        return f'<Tarea {self.id}: {self.texto}>'

# ============================================
# CREAR LAS TABLAS (si no existen)
# ============================================

with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada")

# ============================================
# RUTAS DE LA API
# ============================================

@app.route('/')
def inicio():
    """Información de la API"""
    return jsonify({
        "mensaje": "¡API Full Stack funcionando! 🚀",
        "version": "2.0",
        "base_datos": "SQLite",
        "endpoints": {
            "GET /api/tareas": "Obtener todas las tareas",
            "GET /api/tareas/<id>": "Obtener una tarea específica",
            "POST /api/tareas": "Crear una tarea nueva",
            "PUT /api/tareas/<id>": "Actualizar una tarea",
            "DELETE /api/tareas/<id>": "Eliminar una tarea"
        }
    })

@app.route('/api/tareas', methods=['GET'])
def obtener_tareas():
    """
    GET - Obtener todas las tareas de la base de datos
    """
    try:
        tareas = Tarea.query.all()
        print(f"📋 GET /api/tareas - Se encontraron {len(tareas)} tareas")
        return jsonify([tarea.to_dict() for tarea in tareas]), 200
    except Exception as e:
        print(f"❌ Error obteniendo tareas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tareas/<int:id>', methods=['GET'])
def obtener_tarea(id):
    """
    GET - Obtener una tarea específica por ID
    """
    try:
        tarea = Tarea.query.get(id)
        
        if not tarea:
            print(f"❌ GET /api/tareas/{id} - Tarea no encontrada")
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        print(f"✅ GET /api/tareas/{id} - Tarea encontrada")
        return jsonify(tarea.to_dict()), 200
    except Exception as e:
        print(f"❌ Error obteniendo tarea: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tareas', methods=['POST'])
def crear_tarea():
    """
    POST - Crear una nueva tarea en la base de datos
    Espera JSON: {"texto": "Hacer algo"}
    """
    try:
        datos = request.json
        
        # Validar datos
        if not datos or 'texto' not in datos:
            return jsonify({"error": "Falta el campo 'texto'"}), 400
        
        if not datos['texto'].strip():
            return jsonify({"error": "El texto no puede estar vacío"}), 400
        
        # Crear nueva tarea
        nueva_tarea = Tarea(
            texto=datos['texto'].strip(),
            completada=datos.get('completada', False)
        )
        
        # Guardar en la base de datos
        db.session.add(nueva_tarea)
        db.session.commit()
        
        print(f"✅ POST /api/tareas - Tarea creada: {nueva_tarea}")
        return jsonify(nueva_tarea.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creando tarea: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tareas/<int:id>', methods=['PUT'])
def actualizar_tarea(id):
    """
    PUT - Actualizar una tarea existente
    Espera JSON: {"texto": "...", "completada": true/false}
    """
    try:
        tarea = Tarea.query.get(id)
        
        if not tarea:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        datos = request.json
        
        # Actualizar campos si vienen en el request
        if 'texto' in datos:
            tarea.texto = datos['texto'].strip()
        if 'completada' in datos:
            tarea.completada = datos['completada']
        
        # Guardar cambios
        db.session.commit()
        
        print(f"✅ PUT /api/tareas/{id} - Tarea actualizada: {tarea}")
        return jsonify(tarea.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error actualizando tarea: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tareas/<int:id>', methods=['DELETE'])
def eliminar_tarea(id):
    """
    DELETE - Eliminar una tarea de la base de datos
    """
    try:
        tarea = Tarea.query.get(id)
        
        if not tarea:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        db.session.delete(tarea)
        db.session.commit()
        
        print(f"🗑️ DELETE /api/tareas/{id} - Tarea eliminada")
        return jsonify({"mensaje": "Tarea eliminada correctamente"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error eliminando tarea: {e}")
        return jsonify({"error": str(e)}), 500

# Ruta para servir el frontend
@app.route('/app')
def servir_app():
    """Sirve el frontend"""
    return send_from_directory('static', 'index.html')

# ============================================
# RUTA EXTRA: Estadísticas
# ============================================

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """
    GET - Obtener estadísticas de las tareas
    """
    try:
        total = Tarea.query.count()
        completadas = Tarea.query.filter_by(completada=True).count()
        pendientes = total - completadas
        
        return jsonify({
            "total": total,
            "completadas": completadas,
            "pendientes": pendientes
        }), 200
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# EJECUTAR EL SERVIDOR
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Servidor Flask Full Stack iniciando...")
    print("=" * 60)
    print("📡 API disponible en: http://localhost:5000")
    print("🌐 Frontend disponible en: http://localhost:5000/app")
    print("🗄️ Base de datos: SQLite (tareas.db)")
    print("💡 Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    app.run(debug=True, port=5000)