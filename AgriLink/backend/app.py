from flask import Flask, jsonify, request
from flask_cors import CORS
# Asegúrate de que estos archivos estén disponibles en tu entorno
from agricultor_service import agricultor_service 
from algoritmos_service import algoritmos_service 

app = Flask(__name__)
CORS(app)

# HEALTH CHECK
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "service": "AgriLink API"})

# =========================================================================
# 1. ENDPOINTS DE AGRICULTORES (CRUD Y MOCK DATA)
# =========================================================================
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

# =========================================================================
# 2. ENDPOINTS DE PRODUCTOS, PEDIDOS, RESEÑAS (MOCK DATA)
# =========================================================================
@app.route('/api/productos', methods=['GET'])
def get_productos():
    return jsonify(agricultor_service.obtener_productos())

@app.route('/api/pedidos/agricultor/<int:agricultor_id>', methods=['GET'])
def get_pedidos_agricultor(agricultor_id):
    return jsonify(agricultor_service.obtener_pedidos_agricultor(agricultor_id))

@app.route('/api/resenas/agricultor/<int:agricultor_id>', methods=['GET'])
def get_resenas_agricultor(agricultor_id):
    return jsonify(agricultor_service.obtener_resenas_agricultor(agricultor_id))


# =========================================================================
# 3. ENDPOINTS DE ALGORITMOS (GRAFO Y COMPARACIÓN)
# =========================================================================

@app.route('/api/algoritmos/ruta-optima', methods=['GET'])
def get_ruta_optima():
    """
    Compara las rutas óptimas entre dos nodos usando Dijkstra y Bellman-Ford.
    Los parámetros se esperan ahora como QUERY PARAMS (e.g., ?origen=X&destino=Y).
    """
    # Los datos se esperan en los parámetros de consulta (query parameters) de la solicitud GET
    origen = request.args.get('origen')
    destino = request.args.get('destino')
    
    # Notar que el parámetro 'algoritmo' ya no es necesario aquí.

    if not origen or not destino:
        return jsonify({"error": "Faltan parámetros 'origen' y 'destino' en la URL (query params)."}), 400

    try:
        # LLAMADA OBLIGATORIA: Implementación del servicio de comparación de rutas
        resultado = algoritmos_service.comparar_rutas_optimas(origen, destino)
        return jsonify(resultado)

    except Exception as e:
        # Aquí puedes añadir más manejo de errores específicos si los hay
        return jsonify({"error": "Error interno al calcular la ruta óptima", "detalle": str(e)}), 500

@app.route('/api/algoritmos/productos-relacionados/<producto>', methods=['GET'])
def get_productos_relacionados(producto):
    """Obtiene información de descuento y productos relacionados en el grafo."""
    return jsonify(algoritmos_service.productos_relacionados(producto))

@app.route('/api/algoritmos/explorar-nodo/<nodo>', methods=['GET'])
def explorar_nodo(nodo):
    """Muestra los nodos y aristas salientes de un nodo específico."""
    if nodo not in algoritmos_service.grafo:
        return jsonify({"error": f"Nodo '{nodo}' no encontrado en el grafo"}), 404
    
    conexiones = []
    # Iterar sobre las aristas salientes
    for vecino, data in algoritmos_service.grafo[nodo].items():
        conexiones.append({
            "nodo": vecino,
            "peso": data.get('peso', 'N/A'),
            "relacion": data.get('relacion', 'desconocido')
        })
    
    node_data = algoritmos_service.grafo.nodes[nodo]
    
    respuesta = {
        "nodo": nodo,
        "tipo": node_data.get('tipo', 'Desconocido'),
        "conexiones_salientes": conexiones,
        "total_conexiones": len(conexiones)
    }
    
    # AGREGAR INFORMACIÓN DE DESCUENTOS SI ES UN PRODUCTO
    if node_data.get('tipo') == 'Producto':
        descuentos = algoritmos_service.obtener_descuentos_activos()
        if nodo in descuentos['descuentos']:
            respuesta["descuento"] = descuentos['descuentos'][nodo]
    
    return jsonify(respuesta)

@app.route('/api/algoritmos/pesos-negativos', methods=['GET'])
def get_pesos_negativos():
    """Ver los pesos negativos generados por descuentos (ahorro) para Bellman-Ford."""
    return jsonify(algoritmos_service.obtener_pesos_negativos())

@app.route('/api/algoritmos/info-bellman-ford', methods=['GET'])
def get_info_bellman_ford():
    """Información sobre Bellman-Ford y su uso con pesos negativos."""
    return jsonify({
        "algoritmo": "Bellman-Ford",
        "razon_uso": "Los descuentos generan pesos negativos (ahorros), y Bellman-Ford optimiza el costo neto.",
        "como_funciona": [
            "El grafo se modifica para incluir una arista de ahorro con peso NEGATIVO (ej. Capital -> Producto, peso: -5.5).",
            "Bellman-Ford encuentra la ruta con el costo total MÍNIMO, aprovechando los pesos negativos.",
            "Detecta ciclos negativos (ahorro infinito), lo cual es crucial para la robustez."
        ],
        "ejemplo": "Encuentra la mejor combinación de precio de adquisición (positivo) y descuento aplicado (negativo) para la ruta más barata."
    })

@app.route('/api/algoritmos/metricas-grafo', methods=['GET'])
def get_metricas_grafo():
    """Muestra métricas generales y de rendimiento del grafo."""
    return jsonify(algoritmos_service.metricas_grafo())

@app.route('/api/algoritmos/arbol-expansion-minima', methods=['GET'])
def get_mst_kruskal():
    """
    [FUNCIONALIDAD EXTRA] Calcula el costo y las aristas del Árbol de Expansión Mínima (MST) 
    utilizando el algoritmo de Kruskal, relevante para planificación de red.
    """
    try:
        resultado = algoritmos_service.arbol_expansion_minima_kruskal()
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"error": "Error interno al ejecutar MST (Kruskal)", "detalle": str(e)}), 500

if __name__ == '__main__':
    # NOTA: Asegúrate de ejecutar 'panda.py' para generar el grafo actualizado 
    # antes de correr la aplicación
    app.run(debug=True, port=5000)





