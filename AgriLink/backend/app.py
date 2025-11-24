from flask import Flask, jsonify, request
from flask_cors import CORS
from agricultor_service import agricultor_service
from algoritmos_service import algoritmos_service

app = Flask(__name__)
CORS(app)

# HEALTH CHECK
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "service": "AgriLink API"})

# AGRICULTORES
@app.route('/api/agricultores', methods=['GET'])
def get_agricultores():
    return jsonify(agricultor_service.obtener_agricultores())

@app.route('/api/agricultores/<int:agricultor_id>', methods=['GET'])
def get_agricultor(agricultor_id):
    agricultor = agricultor_service.obtener_agricultor(agricultor_id)
    return jsonify(agricultor) if agricultor else (jsonify({"error": "No encontrado"}), 404)

@app.route('/api/agricultores/<int:agricultor_id>', methods=['PUT'])
def update_agricultor(agricultor_id):
    agricultor = agricultor_service.actualizar_agricultor(agricultor_id, request.json)
    return jsonify(agricultor) if agricultor else (jsonify({"error": "No encontrado"}), 404)

@app.route('/api/agricultores', methods=['POST'])
def crear_agricultor():
    agricultor = agricultor_service.crear_agricultor(request.json)
    return jsonify(agricultor), 201

@app.route('/api/agricultores/<int:agricultor_id>', methods=['DELETE'])
def eliminar_agricultor(agricultor_id):
    resultado = agricultor_service.eliminar_agricultor(agricultor_id)
    if resultado:
        return jsonify({"mensaje": "Agricultor eliminado correctamente"})
    return jsonify({"error": "Agricultor no encontrado"}), 404

@app.route('/api/agricultores/<int:agricultor_id>/estadisticas', methods=['GET'])
def get_estadisticas_agricultor(agricultor_id):
    estadisticas = agricultor_service.obtener_estadisticas_agricultor(agricultor_id)
    return jsonify(estadisticas) if estadisticas else (jsonify({"error": "Agricultor no encontrado"}), 404)

# PRODUCTOS
@app.route('/api/productos', methods=['GET'])
def get_productos():
    agricultor_id = request.args.get('agricultor_id', type=int)
    productos = agricultor_service.obtener_productos(agricultor_id)
    return jsonify(productos)

@app.route('/api/productos', methods=['POST'])
def create_producto():
    producto = agricultor_service.crear_producto(request.json)
    return jsonify(producto), 201

@app.route('/api/productos/<int:producto_id>', methods=['GET'])
def get_producto(producto_id):
    producto = agricultor_service.obtener_producto(producto_id)
    return jsonify(producto) if producto else (jsonify({"error": "Producto no encontrado"}), 404)

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
def update_producto(producto_id):
    producto = agricultor_service.actualizar_producto(producto_id, request.json)
    return jsonify(producto) if producto else (jsonify({"error": "Producto no encontrado"}), 404)

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def delete_producto(producto_id):
    resultado = agricultor_service.eliminar_producto(producto_id)
    if resultado:
        return jsonify({"mensaje": "Producto eliminado correctamente"})
    return jsonify({"error": "Producto no encontrado"}), 404

# PEDIDOS
@app.route('/api/agricultores/<int:agricultor_id>/pedidos', methods=['GET'])
def get_pedidos_agricultor(agricultor_id):
    estado = request.args.get('estado')
    pedidos = agricultor_service.obtener_pedidos_agricultor(agricultor_id, estado)
    return jsonify(pedidos)

@app.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
def get_pedido(pedido_id):
    pedido = agricultor_service.obtener_pedido(pedido_id)
    return jsonify(pedido) if pedido else (jsonify({"error": "Pedido no encontrado"}), 404)

@app.route('/api/pedidos/<int:pedido_id>/estado', methods=['PUT'])
def update_estado_pedido(pedido_id):
    nuevo_estado = request.json.get('estado')
    if not nuevo_estado:
        return jsonify({"error": "Estado requerido"}), 400
    
    pedido = agricultor_service.actualizar_estado_pedido(pedido_id, nuevo_estado)
    return jsonify(pedido) if pedido else (jsonify({"error": "Pedido no encontrado"}), 404)

# RESEÑAS
@app.route('/api/agricultores/<int:agricultor_id>/resenas', methods=['GET'])
def get_resenas_agricultor(agricultor_id):
    resenas = agricultor_service.obtener_resenas_agricultor(agricultor_id)
    return jsonify(resenas)

@app.route('/api/resenas', methods=['POST'])
def crear_resena():
    resena = agricultor_service.crear_resena(request.json)
    return jsonify(resena), 201

# ALGORITMOS BÁSICOS
@app.route('/api/algoritmos/ruta-optima', methods=['GET'])
def get_ruta_optima():
    origen = request.args.get('origen')
    destino = request.args.get('destino')
    if not origen or not destino:
        return jsonify({"error": "Parámetros requeridos"}), 400
    return jsonify(algoritmos_service.encontrar_ruta_optima(origen, destino))

@app.route('/api/algoritmos/productos-relacionados/<producto>', methods=['GET'])
def get_productos_relacionados(producto):
    return jsonify(algoritmos_service.productos_relacionados(producto))

@app.route('/api/algoritmos/metricas', methods=['GET'])
def get_metricas():
    return jsonify(algoritmos_service.metricas_grafo())

# ENDPOINTS DE EXPLORACIÓN
@app.route('/api/algoritmos/explorar/<nodo>', methods=['GET'])
def explorar_nodo(nodo):
    """Ver qué conexiones tiene un nodo específico"""
    if nodo not in algoritmos_service.grafo:
        return jsonify({"error": f"Nodo '{nodo}' no encontrado"})
    
    conexiones = []
    for vecino in algoritmos_service.grafo.neighbors(nodo):
        conexiones.append({
            "nodo": vecino,
            "tipo": algoritmos_service.grafo.nodes[vecino].get('tipo', 'Desconocido'),
            "peso": algoritmos_service.grafo[nodo][vecino].get('peso', 1)
        })
    
    return jsonify({
        "nodo": nodo,
        "tipo": algoritmos_service.grafo.nodes[nodo].get('tipo', 'Desconocido'),
        "conexiones_salientes": conexiones,
        "total_conexiones": len(conexiones)
    })

@app.route('/api/algoritmos/nodos', methods=['GET'])
def listar_nodos():
    """Listar todos los nodos del grafo (primeros 50)"""
    todos_nodos = []
    for nodo, data in algoritmos_service.grafo.nodes(data=True):
        todos_nodos.append({
            "nombre": nodo,
            "tipo": data.get('tipo', 'Desconocido')
        })
    
    limite = request.args.get('limite', 50, type=int)
    return jsonify({
        "total_nodos": len(todos_nodos),
        "muestra_nodos": todos_nodos[:limite]
    })

@app.route('/api/algoritmos/nodos-por-tipo/<tipo>', methods=['GET'])
def nodos_por_tipo(tipo):
    """Listar nodos por tipo específico"""
    nodos_filtrados = []
    for nodo, data in algoritmos_service.grafo.nodes(data=True):
        if data.get('tipo') == tipo:
            nodos_filtrados.append(nodo)
    
    return jsonify({
        "tipo": tipo,
        "total": len(nodos_filtrados),
        "nodos": nodos_filtrados[:50]  # Primeros 50
    })

if __name__ == '__main__':
    print("Agrilink Backend iniciado")
    print("APIs Rest")
    app.run(debug=True, port=5000)