import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import random # Necesario para la asignación aleatoria

# Obtener la carpeta donde está este script - ESTO ARREGLA TODOS LOS PROBLEMAS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Crear carpeta para guardar todos los archivos generados
output_folder = os.path.join(SCRIPT_DIR, "Proyecto_Grafo_Archivos")
os.makedirs(output_folder, exist_ok=True)

# 2. Cargar los datasets desde archivos Excel (USANDO RUTAS ABSOLUTAS)
agricultura_df = pd.read_excel(
    os.path.join(SCRIPT_DIR, "Agricultura_Transporte.xlsx"), 
    sheet_name="Agricultura_Transporte", 
    engine="openpyxl"
)
asociaciones_df = pd.read_excel(
    os.path.join(SCRIPT_DIR, "AsociacionesProductivas_2024.xlsx"), 
    sheet_name="AsociacionesProductivas_2024", 
    engine="openpyxl"
)
mimercado_df = pd.read_excel(
    os.path.join(SCRIPT_DIR, "MiMercado_DataSet_Julio.xlsx"), 
    engine="openpyxl"
)
cenama_df = pd.read_excel(
    os.path.join(SCRIPT_DIR, "Datos_Cenamav3.xlsx"), 
    engine="openpyxl"
)

# 3. Guardar un Excel combinado con todos los datasets para referencia
combined_excel_path = os.path.join(output_folder, "DataSet_Proyecto_Combinado.xlsx")
with pd.ExcelWriter(combined_excel_path, engine="openpyxl") as writer:
    agricultura_df.to_excel(writer, sheet_name="Agricultura", index=False)
    asociaciones_df.to_excel(writer, sheet_name="Asociaciones", index=False)
    mimercado_df.to_excel(writer, sheet_name="MiMercado", index=False)
    cenama_df.to_excel(writer, sheet_name="Cenama", index=False)

# =========================================================================
# 4. Definición de la matriz de conexiones de Departamentos (Ubigeo XX)
# =========================================================================
departamentos = {
    '01': 'CHACHAPOYAS',
    '02': 'HUARAZ',
    '03': 'ABANCAY',
    '04': 'AREQUIPA',
    '05': 'AYACUCHO', 
    '06': 'CAJAMARCA',
    '07': 'CALLAO',
    '08': 'CUSCO',
    '09': 'HUANCAVELICA',
    '10': 'HUANUCO', 
    '11': 'ICA',
    '12': 'HUANCAYO',
    '13': 'TRUJILLO',
    '14': 'CHICLAYO',
    '15': 'LIMA', 
    '16': 'IQUITOS',
    '17': 'PUERTO MALDONADO',
    '18': 'MOQUEGUA',
    '19': 'CERRO DE PASCO',
    '20': 'PIURA', 
    '21': 'PUNO',
    '22': 'MOYOBAMBA',
    '23': 'TACNA',
    '24': 'TUMBES',
    '25': 'PUCALLPA'
}
conexiones = {
    '01': ['06', '13', '16', '22'],
    '02': ['10', '13', '15'],
    '03': ['04', '05', '08'],
    '04': ['03', '05', '08', '11', '18', '21'],
    '05': ['03', '04', '08', '09', '11'],
    '06': ['01', '13', '14', '20'],
    '07': ['15'],
    '08': ['03', '04', '05', '12', '17', '21'],
    '09': ['05', '11', '12'],
    '10': ['02', '13', '15', '19', '22', '25'],
    '11': ['04', '05', '09', '15'],
    '12': ['08', '09', '15', '19', '25'],
    '13': ['01', '02', '06', '10', '14'],
    '14': ['06', '13', '20'],
    '15': ['02', '07', '10', '11', '12', '19'],
    '16': ['01', '22'],
    '17': ['08', '21'],
    '18': ['04', '21', '23'],
    '19': ['10', '12', '15'],
    '20': ['06', '14', '24'],
    '21': ['04', '08', '17', '18', '23'],
    '22': ['01', '10', '16'],
    '23': ['18', '21'],
    '24': ['20'],
    '25': ['10', '12']
}

# Crear una lista de productos y precios mayoristas de MiMercado para asignación aleatoria
productos_precios = []
for _, row in mimercado_df.iterrows():
    if pd.notna(row["PRODUCTO"]) and pd.notna(row["PRECIO_MAYORISTA"]):
        productos_precios.append({
            "producto": row["PRODUCTO"],
            "precio": row["PRECIO_MAYORISTA"]
        })

# 5. Crear un grafo DIRIGIDO (DiGraph)
G = nx.DiGraph() # CAMBIO CRÍTICO: De Graph a DiGraph

# =========================================================================
# 6. Añadir nodos y aristas para ASOCIACIONES -> PRODUCTOS -> CAPITALES
# =========================================================================
for _, row in asociaciones_df.iterrows():
    asociacion_id = row["id_asociacion"]
    depto = row["departamento"]
    ubigeo = str(row["ubigeo"]).zfill(6) # Asegurar formato Ubigeo
    depto_cod = ubigeo[:2]
    
    # 6.1. Nodo Asociación (Origen)
    if pd.notna(asociacion_id) and pd.notna(depto) and productos_precios:
        G.add_node(asociacion_id,
                   tipo="Asociacion",
                   departamento=depto,
                   provincia=row["provincia"], 
                   distrito=row["distrito"],
                   ubigeo=ubigeo)
    
        # 6.2. Asignar producto y precio aleatorio (de Piura, MiMercado)
        producto_elegido = random.choice(productos_precios)
        producto = producto_elegido["producto"]
        precio_mayorista = producto_elegido["precio"]
        
        G.add_node(producto, tipo="Producto")
        
        # Arista 1: Asociación -> Producto (Peso 0, representa la disponibilidad)
        G.add_edge(asociacion_id, producto, peso=0, relacion="vende")
        
        # 6.3. Nodo Capital Departamental (Ubigeo XX0101)
        capital_ubigeo = f"{depto_cod}0101"
        capital_nombre = departamentos.get(depto_cod)
        
        G.add_node(capital_nombre, tipo="Capital", ubigeo=capital_ubigeo, depto_cod=depto_cod)
        
        # Arista 2: Producto -> Capital (Peso = Precio Mayorista)
        # El peso es el precio, costo de adquirir el producto en esa ubicación capital.
        G.add_edge(producto, capital_nombre, peso=precio_mayorista, relacion="precio_adquisicion")
        
# =========================================================================
# 7. Añadir aristas de transporte entre CAPITALES
# =========================================================================
for codigo_origen, destinos in conexiones.items():
    capital_origen = departamentos.get(codigo_origen) # Obtiene 'Amazonas', 'Áncash', etc.
    
    if capital_origen:
        # Aseguramos que el nodo Capital de origen exista con el UBIGEO correcto
        # (El UBIGEO de la capital es el código de departamento + '0101')
        G.add_node(capital_origen, 
                   tipo="Capital", 
                   depto_cod=codigo_origen, 
                   ubigeo=f"{codigo_origen}0101")
        
        for codigo_destino in destinos:
            capital_destino = departamentos.get(codigo_destino)
            
            if capital_destino:
                # Aseguramos que el nodo Capital de destino exista
                G.add_node(capital_destino, 
                           tipo="Capital", 
                           depto_cod=codigo_destino, 
                           ubigeo=f"{codigo_destino}0101")
                
                # ❗ CRÍTICO: Usar un costo de transporte significativo (aleatorio entre 5.0 y 15.0)
                # Esto obliga a Bellman-Ford a elegir la ruta con el menor número de saltos.
                costo_transporte_aleatorio = random.uniform(5.0, 15.0) 
                
                # Arista 3: Capital -> Capital (respetando la matriz 'conexiones')
                # La arista va del nombre del departamento (Capital) al nombre del departamento vecino
                G.add_edge(
                    capital_origen, 
                    capital_destino, 
                    peso=costo_transporte_aleatorio, 
                    relacion="transporte_interdepartamental"
                )


# =========================================================================
# 8. Añadir nodos y aristas para MERCADOS (Cenama)
# =========================================================================
for _, row in cenama_df.iterrows():
    mercado_id = row["id_anonimo_cenama"]
    depto = row["departamento"]
    ubigeo = str(row["ubigeo"]).zfill(6)
    depto_cod = ubigeo[:2]
    
    if pd.notna(mercado_id) and pd.notna(depto):
        # Nodo Mercado (Destino)
        G.add_node(mercado_id,
                   tipo="Mercado",
                   departamento=depto,
                   provincia=row["provincia"], 
                   distrito=row["distrito"],
                   ubigeo=ubigeo)
        
        # Nodo Capital (ya debe existir)
        capital_nombre = departamentos.get(depto_cod, depto.upper())
        if capital_nombre in G:
            # Arista 4: Capital -> Mercado (Peso 0, Distribución final)
            # Permite alcanzar el DESTINO (Mercado) desde la red troncal.
            G.add_edge(capital_nombre, mercado_id, peso=0, relacion="distribucion_final")


# 9. Visualizar un subconjunto del grafo con los 300 nodos más conectados para evitar saturación
node_degree = sorted(G.degree, key=lambda x: x[1], reverse=True)[:300]
sub_nodes = [n for n, _ in node_degree]
H = G.subgraph(sub_nodes)

plt.figure(figsize=(18, 12))
pos = nx.spring_layout(H, seed=42)  # Layout de fuerza dirigida para visualización

# Asignar colores a nodos según su tipo para la leyenda
node_colors = []
for n in H.nodes():
    tipo = H.nodes[n].get("tipo", "")
    if tipo == "Agricultor":
        node_colors.append("green")
    elif tipo == "Producto":
        node_colors.append("orange")
    elif tipo == "Capital":
        node_colors.append("cyan") 
    elif tipo == "Asociacion":
        node_colors.append("purple")
    elif tipo == "Mercado":
        node_colors.append("red")
    else:
        node_colors.append("gray")

# Dibujar grafo sin etiquetas para mejor legibilidad
nx.draw(H, pos, node_color=node_colors, node_size=300, arrows=True)

# Crear leyenda para los colores de nodos
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Agricultor', markerfacecolor='green', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Producto', markerfacecolor='orange', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Capital', markerfacecolor='cyan', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Asociación', markerfacecolor='purple', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Mercado', markerfacecolor='red', markersize=10)
]
plt.legend(handles=legend_elements, loc='upper right', title='Tipos de nodos')

plt.title("Visualización del grafo del proyecto (subconjunto más conectado)", fontsize=14)
plt.tight_layout()

# Guardar imagen en la carpeta creada
visualization_path = os.path.join(output_folder, "Visualizacion_Grafo_Proyecto.png")
plt.savefig(visualization_path)

# 10. Calcular métricas de centralidad para análisis
degree_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)
closeness_centrality = nx.closeness_centrality(G)

# Obtener top 10 nodos por cada métrica
top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

# Guardar métricas en Excel dentro de la carpeta
metrics_df = pd.DataFrame({
    "Top Degree": [f"{n}: {v:.4f}" for n, v in top_degree],
    "Top Betweenness": [f"{n}: {v:.4f}" for n, v in top_betweenness],
    "Top Closeness": [f"{n}: {v:.4f}" for n, v in top_closeness]
})
metrics_path = os.path.join(output_folder, "Metricas_Grafo_Proyecto.xlsx")
metrics_df.to_excel(metrics_path, index=False)

# 11. Guardar grafo completo en formato GraphML para análisis externo
graph_path = os.path.join(output_folder, "Grafo_Proyecto_Actualizado.graphml")
nx.write_graphml(G, graph_path)

# 12. Crear informe en archivo .txt con referencia a Dijkstra y resumen de métricas
report_path = os.path.join(output_folder, "Informe_Grafo_Proyecto.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("==============================\n")
    f.write("INFORMACIÓN DEL GRAFO\n")
    f.write("==============================\n")
    f.write(f"Tipo de grafo: {type(G)} (Dirigido y ponderado)\n")
    f.write(f"Número total de nodos: {G.number_of_nodes()}\n")
    f.write(f"Número total de aristas: {G.number_of_edges()}\n")
    f.write("\nTipo de recorrido aplicado para visualización: Layout de fuerza dirigida (spring_layout)\n")
    f.write("Algoritmo de optimización recomendado:\n")
    f.write("- Para rutas óptimas: Bellman-Ford (por pesos negativos de descuentos)\n")
    f.write("- Para detección de comunidades: Algoritmos de clustering (Louvain)\n")
    f.write("\nTop 5 nodos por centralidad de grado:\n")
    for n, v in top_degree[:5]:
        f.write(f" - {n}: {v:.4f}\n")
    f.write("==============================\n")

# 13. Mostrar resumen ordenado en consola
print("==============================")
print("INFORMACIÓN DEL GRAFO")
print("==============================")
print(f"Tipo de grafo: {type(G)} (Dirigido y ponderado)")
print(f"Número total de nodos: {G.number_of_nodes()}")
print(f"Número total de aristas: {G.number_of_edges()}")
print("\nTipo de recorrido aplicado para visualización: Layout de fuerza dirigida (spring_layout)")
print("Algoritmo de optimización recomendado: Bellman-Ford para rutas óptimas y algoritmos de clustering (Louvain) para comunidades")
print("\nTop 5 nodos por centralidad de grado:")
for n, v in top_degree[:5]:
    print(f" - {n}: {v:.4f}")
print("==============================")
print(f"Todos los archivos se han guardado en la carpeta: {output_folder}")

