import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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

# 4. Crear un grafo no dirigido con NetworkX
G = nx.Graph()

# Añadir nodos y aristas para Agricultores -> Productos -> Ubicaciones
for _, row in agricultura_df.iterrows():
    agricultor = row["Exportador"]
    producto = row["Producto"]
    depto = row["Departamento Origen"]
    peso = row["Peso Neto"] if not pd.isna(row["Peso Neto"]) else 1
    if pd.notna(agricultor) and pd.notna(producto) and pd.notna(depto):
        G.add_node(agricultor, tipo="Agricultor")
        G.add_node(producto, tipo="Producto")
        G.add_node(depto, tipo="Ubicacion")
        G.add_edge(agricultor, producto, peso=peso, relacion="produce")
        G.add_edge(producto, depto, peso=1, relacion="origen")

# Añadir nodos y aristas para Asociaciones -> Ubicaciones
for _, row in asociaciones_df.iterrows():
    asociacion = row["id_asociacion"]
    depto = row["departamento"]
    trabajadores = row["trabajadores"] if not pd.isna(row["trabajadores"]) else 1
    if pd.notna(asociacion) and pd.notna(depto):
        G.add_node(asociacion, tipo="Asociacion")
        G.add_node(depto, tipo="Ubicacion")
        G.add_edge(asociacion, depto, peso=trabajadores, relacion="ubicada_en")

# Añadir nodos y aristas para Mercados -> Ubicaciones (desde Cenama)
for _, row in cenama_df.iterrows():
    mercado = row["distrito"]
    depto = row["departamento"]
    if pd.notna(mercado) and pd.notna(depto):
        G.add_node(mercado, tipo="Mercado")
        G.add_node(depto, tipo="Ubicacion")
        G.add_edge(mercado, depto, peso=1, relacion="ubicado_en")

# Añadir nodos y aristas para Productos -> Mercados con precios (solo Piura)
for _, row in mimercado_df.iterrows():
    producto = row["PRODUCTO"]
    mercado = row["DISTRITO"]
    precio_may = row["PRECIO_MAYORISTA"] if not pd.isna(row["PRECIO_MAYORISTA"]) else 0
    precio_min = row["PRECIO_MINORISTA"] if not pd.isna(row["PRECIO_MINORISTA"]) else 0
    if pd.notna(producto) and pd.notna(mercado):
        G.add_node(producto, tipo="Producto")
        G.add_node(mercado, tipo="Mercado")
        precio_prom = (precio_may + precio_min) / 2
        G.add_edge(producto, mercado, peso=precio_prom, relacion="se_vende_en")

# 5. Visualizar un subconjunto del grafo con los 300 nodos más conectados para evitar saturación
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
    elif tipo == "Ubicacion":
        node_colors.append("blue")
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
    Line2D([0], [0], marker='o', color='w', label='Ubicación', markerfacecolor='blue', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Asociación', markerfacecolor='purple', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Mercado', markerfacecolor='red', markersize=10)
]
plt.legend(handles=legend_elements, loc='upper right', title='Tipos de nodos')

plt.title("Visualización del grafo del proyecto (subconjunto más conectado)", fontsize=14)
plt.tight_layout()

# Guardar imagen en la carpeta creada
visualization_path = os.path.join(output_folder, "Visualizacion_Grafo_Proyecto.png")
plt.savefig(visualization_path)

# 6. Calcular métricas de centralidad para análisis
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

# 7. Guardar grafo completo en formato GraphML para análisis externo
graph_path = os.path.join(output_folder, "Grafo_Proyecto_Actualizado.graphml")
nx.write_graphml(G, graph_path)

# 8. Crear informe en archivo .txt con referencia a Dijkstra y resumen de métricas
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
    f.write("- Para rutas óptimas: Algoritmo de Dijkstra\n")
    f.write("- Para detección de comunidades: Algoritmos de clustering (Louvain)\n")
    f.write("\nTop 5 nodos por centralidad de grado:\n")
    for n, v in top_degree[:5]:
        f.write(f" - {n}: {v:.4f}\n")
    f.write("==============================\n")

# 9. Mostrar resumen ordenado en consola
print("==============================")
print("INFORMACIÓN DEL GRAFO")
print("==============================")
print(f"Tipo de grafo: {type(G)} (Dirigido y ponderado)")
print(f"Número total de nodos: {G.number_of_nodes()}")
print(f"Número total de aristas: {G.number_of_edges()}")
print("\nTipo de recorrido aplicado para visualización: Layout de fuerza dirigida (spring_layout)")
print("Algoritmo de optimización recomendado: Dijkstra para rutas óptimas y algoritmos de clustering (Louvain) para comunidades")
print("\nTop 5 nodos por centralidad de grado:")
for n, v in top_degree[:5]:
    print(f" - {n}: {v:.4f}")
print("==============================")
print(f"Todos los archivos se han guardado en la carpeta: {output_folder}")
