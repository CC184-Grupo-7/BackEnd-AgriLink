import os
import sys
import networkx as nx

class AlgoritmosService:
    def __init__(self):
        self.grafo = self._cargar_grafo_portable()
    
    def _cargar_grafo_portable(self):
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        
        rutas_relativas = [
            os.path.join(directorio_actual, "..", "Panditas"),
            os.path.join(directorio_actual, "..", "..", "Panditas"),  
        ]
        
        for ruta_rel in rutas_relativas:
            ruta_abs = os.path.abspath(ruta_rel)
            
            if os.path.exists(ruta_abs):
                print(f"Carpeta Panditas encontrada en: {ruta_abs}")
                graphml_path = os.path.join(ruta_abs, "Proyecto_Grafo_Archivos", "Grafo_Proyecto_Actualizado.graphml")
                print(f"Buscando grafo en: {graphml_path}")
                
                if os.path.exists(graphml_path):
                    try:
                        grafo = nx.read_graphml(graphml_path)
                        print(f"GRAFO CARGADO: {grafo.number_of_nodes()} nodos, {grafo.number_of_edges()} aristas")
                        return grafo
                    except Exception as e:
                        print(f"Error cargando GraphML: {e}")
                        continue
        
        print("No se pudo cargar el grafo real. Usando grafo vacío.")
        return nx.DiGraph()
    
    def encontrar_ruta_optima(self, origen: str, destino: str):
        if origen not in self.grafo or destino not in self.grafo:
            return {"error": "Origen o destino no encontrado en el grafo"}
        try:
            ruta = nx.bellman_ford_path(self.grafo, source=origen, target=destino, weight='peso')
            costo = nx.bellman_ford_path_length(self.grafo, source=origen, target=destino, weight='peso')
            return {
                "ruta": ruta,
                "costo_total": costo,
                "algoritmo": "Bellman-Ford"
            }
        except Exception as e:
            return {"error": f"No se pudo calcular la ruta: {e}"}
    
    def productos_relacionados(self, producto: str):
        if producto not in self.grafo:
            return {"error": "Producto no encontrado"}
    
        #QuickUnion:
        class MiniUnionFind:
            def __init__(self):
                self.parent = {}
            
            def find(self, x):
                if x not in self.parent:
                    self.parent[x] = x
                if self.parent[x] != x:
                    self.parent[x] = self.find(self.parent[x])
                return self.parent[x]
        
            def union(self, x, y):
                rootX, rootY = self.find(x), self.find(y)
                if rootX != rootY:
                    self.parent[rootY] = rootX
    
        uf = MiniUnionFind()
        relacionados = []
    
        # Usar QuickUnion para encontrar productos del mismo "grupo"
        for vecino in self.grafo.neighbors(producto):
            if self.grafo.nodes[vecino].get('tipo') == 'Producto' and vecino != producto:
                uf.union(producto, vecino)
                relacionados.append(vecino)
    
        return {
            "producto_consulta": producto,
            "relacionados": relacionados  # Misma lista, mismo orden
        }
    
    def metricas_grafo(self):
        return {
            "total_nodos": self.grafo.number_of_nodes(),
            "total_aristas": self.grafo.number_of_edges(),
            "densidad": nx.density(self.grafo)
        }

algoritmos_service = AlgoritmosService()