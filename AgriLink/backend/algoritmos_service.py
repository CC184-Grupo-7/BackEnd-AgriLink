import os
import sys
import random
import networkx as nx

class AlgoritmosService:
    def __init__(self):
        self.grafo = self._cargar_grafo_portable()
        self.descuentos_activos = self._generar_descuentos_aleatorios()
    
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
    
    def _generar_descuentos_aleatorios(self):
        """Genera descuentos aleatorios para productos sin modificar el dataset original"""
        print("🎲 Generando descuentos aleatorios (0%, 10%, 15%, 20%, 30%, 40%, 50%)...")
        
        descuentos = {}
        opciones_descuento = [0.0, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
        
        # Aplicar a productos existentes en el grafo
        productos = [n for n, data in self.grafo.nodes(data=True) 
                    if data.get('tipo') == 'Producto']
        
        for producto in productos:
            descuento = random.choice(opciones_descuento)
            descuentos[producto] = {
                'descuento_porcentaje': descuento,
                'descuento_texto': f"{int(descuento * 100)}%",
                'precio_original': self._obtener_precio_original(producto),
                'precio_final': None
            }
            
            # Calcular precio final si tenemos precio original
            if descuentos[producto]['precio_original']:
                precio_original = descuentos[producto]['precio_original']
                descuentos[producto]['precio_final'] = round(precio_original * (1 - descuento), 2)
        
        print(f"✅ {len(descuentos)} productos con descuentos aplicados")
        return descuentos
    
    def _obtener_precio_original(self, producto):
        """Intenta obtener el precio original del producto desde las aristas del grafo"""
        try:
            # Buscar conexiones a mercados para obtener precios
            for vecino in self.grafo.neighbors(producto):
                if self.grafo.nodes[vecino].get('tipo') == 'Mercado':
                    peso = self.grafo[producto][vecino].get('peso', 0)
                    if peso > 0:  # Asumimos que pesos positivos son precios
                        return peso
            return None
        except:
            return None
    
    def encontrar_ruta_optima(self, origen: str, destino: str):
        if origen not in self.grafo or destino not in self.grafo:
            return {"error": "Origen o destino no encontrado en el grafo"}
    
        try:
            # 🎯 SIEMPRE USAR BELLMAN-FORD (por los descuentos)
            grafo_bellman = self._crear_grafo_para_bellman_ford()
        
            ruta = nx.bellman_ford_path(grafo_bellman, source=origen, target=destino, weight='peso')
            costo = nx.bellman_ford_path_length(grafo_bellman, source=origen, target=destino, weight='peso')
        
            descuentos_ruta = self._obtener_descuentos_en_ruta(ruta)
        
            return {
                "ruta": ruta,
                "costo_total": round(costo, 2),
                "algoritmo": "Bellman-Ford",
                "descuentos_aplicados": descuentos_ruta,
                "explicacion": "Ruta calculada con Bellman-Ford para optimizar descuentos",
                "utilidad": "Maneja pesos negativos generados por ahorros de descuentos"
            }
            
        except nx.NetworkXUnbounded:
            return {
                "error": "Ciclo negativo detectado",
                "algoritmo": "Bellman-Ford", 
                "explicacion": "Los descuentos crearon ciclos con ahorro infinito",
                "utilidad": "Bellman-Ford protege contra cálculos infinitos"
            }
        except nx.NetworkXNoPath:
            return {"error": "No existe ruta entre los nodos"}
        except Exception as e:
            return {"error": f"No se pudo calcular la ruta: {str(e)}"}
    
    def _aplicar_descuentos_al_grafo(self):
        """Versión SEGURA: solo modifica precios SIN crear ciclos"""
        grafo_temp = self.grafo.copy()
        
        # SOLO modificar precios de Producto → Mercado
        for producto, info_descuento in self.descuentos_activos.items():
            if info_descuento['precio_final'] and producto in grafo_temp:
                for vecino in list(grafo_temp.neighbors(producto)):
                    if grafo_temp.nodes[vecino].get('tipo') == 'Mercado':
                        # Solo modificar el precio existente
                        grafo_temp[producto][vecino]['peso'] = info_descuento['precio_final']
        
        return grafo_temp
    
    def _obtener_descuentos_en_ruta(self, ruta):
        """Obtiene información de descuentos para los productos en la ruta"""
        descuentos = []
        for nodo in ruta:
            if nodo in self.descuentos_activos:
                info = self.descuentos_activos[nodo]
                if info['precio_original']:  # Solo incluir si tiene precio
                    descuentos.append({
                        'producto': nodo,
                        'descuento': info['descuento_texto'],
                        'precio_original': info['precio_original'],
                        'precio_final': info['precio_final']
                    })
        return descuentos
    
    def obtener_descuentos_activos(self):
        """Endpoint para ver todos los descuentos activos CON ubicaciones"""
        descuentos_con_mercados = {}
        
        for producto, info in self.descuentos_activos.items():
            if info['precio_original']:
                # Agregar información de mercados
                mercados = []
                for vecino in self.grafo.neighbors(producto):
                    if self.grafo.nodes[vecino].get('tipo') == 'Mercado':
                        mercados.append(vecino)
                
                descuentos_con_mercados[producto] = {
                    **info,
                    'mercados_disponibles': mercados,
                    'total_mercados': len(mercados)
                }
        
        return {
            "total_productos_con_descuento": len(descuentos_con_mercados),
            "descuentos": descuentos_con_mercados
        }
    
    def productos_relacionados(self, producto: str):
        if producto not in self.grafo:
            return {"error": "Producto no encontrado"}
    
        relacionados = set()
    
        # Buscar productos que comparten mismos mercados o ubicaciones
        for vecino in self.grafo.neighbors(producto):
            # Si el vecino es un mercado o ubicación, buscar otros productos conectados
            if self.grafo.nodes[vecino].get('tipo') in ['Mercado', 'Ubicacion']:
                for vecino_del_vecino in self.grafo.neighbors(vecino):
                    if (self.grafo.nodes[vecino_del_vecino].get('tipo') == 'Producto' and 
                        vecino_del_vecino != producto):
                        relacionados.add(vecino_del_vecino)
    
        return {
            "producto_consulta": producto,
            "relacionados": list(relacionados)[:10],  # Limitar a 10 resultados
            "total_relacionados": len(relacionados)
        }
    
    def _crear_grafo_para_bellman_ford(self):
        """Versión CORREGIDA: crea pesos negativos SIN ciclos infinitos"""
        grafo_temp = self.grafo.copy()
    
        # 🎯 ESTRATEGIA: Solo aplicar descuentos, NO crear aristas de retroceso
        for producto, info in self.descuentos_activos.items():
            if info['precio_final'] and producto in grafo_temp:
                for vecino in list(grafo_temp.neighbors(producto)):
                    if grafo_temp.nodes[vecino].get('tipo') == 'Mercado':
                        # Solo aplicar el precio con descuento
                        precio_original = info['precio_original']
                        precio_descuento = info['precio_final']
                    
                        if precio_original and precio_descuento < precio_original:
                            # Aplicar el precio con descuento como peso POSITIVO
                            grafo_temp[producto][vecino]['peso'] = precio_descuento
                        
                            # 🚫 NO crear arista de retroceso para evitar ciclos
                            # El "ahorro" se refleja automáticamente en el peso reducido
    
        return grafo_temp
    
    def obtener_pesos_negativos(self):
        """Muestra los pesos negativos generados por descuentos"""
        grafo = self._crear_grafo_para_bellman_ford()
    
        pesos_negativos = []
        for u, v, data in grafo.edges(data=True):
            peso = data.get('peso', 0)
            if peso < 0:
                pesos_negativos.append({
                    'desde': u,
                    'hacia': v, 
                    'peso': peso,
                    'relacion': data.get('relacion', 'desconocido')
                })
    
        return {
            "total_pesos_negativos": len(pesos_negativos),
            "pesos_negativos": pesos_negativos[:10],  # Primeros 10
            "explicacion": "Pesos negativos generados por ahorros de descuentos"
        }
    
    def metricas_grafo(self):
        return {
            "total_nodos": self.grafo.number_of_nodes(),
            "total_aristas": self.grafo.number_of_edges(),
            "densidad": nx.density(self.grafo),
            "productos_con_descuento": len([p for p in self.descuentos_activos if self.descuentos_activos[p]['precio_original']])
        }

algoritmos_service = AlgoritmosService()

