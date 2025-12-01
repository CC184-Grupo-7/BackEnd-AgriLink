import os
import sys
import random
import networkx as nx
import time

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
            # ❗ CORRECCIÓN: Buscar conexiones a CAPITALES, no a mercados, para obtener precios
            for vecino in self.grafo.neighbors(producto):
                if self.grafo.nodes[vecino].get('tipo') == 'Capital': # <-- CAMBIADO: 'Capital' es donde está el precio en panda.py
                    peso = self.grafo[producto][vecino].get('peso', 0)
                    if peso > 0:
                        return peso
            return None
        except:
            return None
        
    def _obtener_ruta_y_costo(self, grafo, origen, destino, algoritmo):
        """
        Ejecuta un algoritmo de ruta, mide su rendimiento y captura el resultado.
        Devuelve un diccionario con (ruta, costo, tiempo, error, notas).
        """
        
        resultado = {
            "ruta": [],
            "costo": None,
            "tiempo_ms": 0.0,
            "error": None,
            "notas": ""
        }
        
        t_inicio = time.perf_counter()
        
        try:
            if algoritmo == 'Bellman-Ford':
                ruta = nx.bellman_ford_path(grafo, source=origen, target=destino, weight='peso')
                costo = nx.bellman_ford_path_length(grafo, source=origen, target=destino, weight='peso')
                resultado["notas"] = "Recomendado para optimización de costos con descuentos (pesos negativos)."
            
            elif algoritmo == 'Dijkstra':
                # Dijkstra fallará si hay pesos negativos. Lo ejecutamos para obtener la métrica de tiempo.
                # Lo más didáctico es dejar que falle para demostrar su no aplicabilidad.
                
                # Comprobamos la existencia de pesos negativos para añadir una nota clara antes de ejecutar
                hay_pesos_negativos = any(data['peso'] < 0 for u, v, data in grafo.edges(data=True))

                if hay_pesos_negativos:
                    # No ejecutamos el algoritmo, solo medimos el tiempo de la comprobación.
                    resultado["error"] = "Dijkstra no es aplicable."
                    resultado["notas"] = "Dijkstra no es apto para este grafo debido a la presencia de costos negativos (descuentos)."
                    t_fin = time.perf_counter()
                    resultado["tiempo_ms"] = (t_fin - t_inicio) * 1000
                    return resultado
                
                # Si por alguna razón no hubiera negativos, ejecutaría
                ruta = nx.shortest_path(grafo, source=origen, target=destino, weight='peso')
                costo = nx.shortest_path_length(grafo, source=origen, target=destino, weight='peso')
                resultado["notas"] = "Ruta calculada, pero el resultado podría ser subóptimo en caso de pesos negativos leves no detectados por NetworkX."
                
            else:
                resultado["error"] = "Algoritmo no soportado."
                t_fin = time.perf_counter()
                resultado["tiempo_ms"] = (t_fin - t_inicio) * 1000
                return resultado
            
            # Si el costo es None (no path found)
            if costo is None:
                raise nx.NetworkXNoPath()
                
            # Asignar resultados
            resultado["ruta"] = ruta
            resultado["costo"] = round(costo, 2)
            
        except nx.NetworkXNoPath:
            resultado["error"] = "No se encontró ruta."
        except nx.NetworkXUnbounded:
            resultado["error"] = "Ciclo de costo negativo detectado (ahorro infinito)."
            resultado["notas"] = "¡Ciclo negativo detectado! Esto indica un error en el modelo o un descuento máximo mal aplicado."
        except Exception as e:
            resultado["error"] = f"Error: {type(e).__name__}"
            
        t_fin = time.perf_counter()
        resultado["tiempo_ms"] = (t_fin - t_inicio) * 1000
        
        return resultado
    
    def encontrar_ruta_optima(self, origen: str, destino: str):
        if origen not in self.grafo or destino not in self.grafo:
            return {"error": "Origen o destino no encontrado en el grafo"}

        # 1. Pre-procesar el grafo 
        try:
            grafo_filtrado = self._crear_grafo_para_bellman_ford(origen, destino) 
        except Exception as e:
            return {"error": f"Error al pre-procesar el grafo: {str(e)}"}

        # 2. Ejecutar el algoritmo Bellman-Ford
        try:
            ruta = nx.bellman_ford_path(grafo_filtrado, source=origen, target=destino, weight='peso')
            costo_total = nx.bellman_ford_path_length(grafo_filtrado, source=origen, target=destino, weight='peso')
        except nx.NetworkXNoPath:
            return {"error": f"No se encontró ruta de {origen} a {destino} usando Bellman-Ford"}
        except Exception as e:
            return {"error": f"Error en la ejecución de Bellman-Ford: {str(e)}"}

        # 3. Formateo y Detalle de la Ruta
        
        # Generar las listas de nombres de la ruta
        ruta_geografica = []
        for nodo_id in ruta:
            nodo_info = self.obtener_info_geografica(nodo_id)
            
            if nodo_info['tipo'] == 'Asociacion' or nodo_info['tipo'] == 'Mercado':
                # Usamos el distrito para Asociaciones/Mercados
                ruta_geografica.append(nodo_info['distrito'])
            
            elif nodo_info['tipo'] == 'Capital':
                # LÓGICA CORREGIDA: Intentar obtener el nombre geográfico más relevante
                nombre_capital = nodo_info.get('departamento')
                
                # Si 'departamento' no está (es None o 'N/A'), intentamos con 'distrito' (nombre de la ciudad)
                if not nombre_capital or nombre_capital == 'N/A':
                    nombre_capital = nodo_info.get('distrito')
                
                # Si sigue sin nombre, usamos el ID del nodo como último recurso (UUID)
                if not nombre_capital or nombre_capital == 'N/A':
                    nombre_capital = nodo_id
                    
                ruta_geografica.append(nombre_capital)
            
            elif nodo_info['tipo'] == 'Producto':
                # Usamos el ID del nodo como nombre del producto (ej. Platano bellaco)
                ruta_geografica.append(nodo_info['id'])
            
            else:
                # Caso de seguridad para otros tipos de nodos
                ruta_geografica.append(nodo_info.get('id', 'N/A'))

        # ❗ LÓGICA DE REORDENAMIENTO: Mover el Producto al inicio de la lista (Mantenido)
        # La ruta óptima siempre viene como: [Asociación/Mercado, Producto, Capital, ...]
        if len(ruta_geografica) >= 2 and self.grafo.nodes[ruta[1]].get('tipo') == 'Producto':
            producto_nombre = ruta_geografica.pop(1)
            ruta_geografica.insert(0, producto_nombre)
        
        # 4. Obtener detalles de productos (para descuentos)
        # Nombre de la función corregido: _obtener_detalles_productos_en_ruta
        detalles_productos = self._obtener_detalles_productos_en_ruta(ruta) 
        
        # Formatear la lista de descuentos aplicados para la respuesta (si aplica)
        descuentos_aplicados = [
            {"producto": d["producto"], "descuento": f"{d['descuento_porcentaje']:.0f}%", 
             "precio_original": d["precio_inicial"], "precio_final": d["precio_final"]} 
            for d in detalles_productos if d.get('descuento_porcentaje', 0) > 0
        ]

        # 5. Construir la respuesta final
        return {
            "origen_geografico": self.obtener_info_geografica(origen),
            "destino_geografico": self.obtener_info_geografica(destino),
            "ruta_optima": {
                "algoritmo": "Bellman-Ford",
                "costo_total": round(costo_total, 2),
                "explicacion": "Ruta calculada con Bellman-Ford para optimizar costos, aprovechando los descuentos como pesos negativos.",
                "ruta": ruta,
                "ruta_geografica_detallada": ruta_geografica, 
                "detalles_productos": detalles_productos,
                "descuentos_aplicados": descuentos_aplicados,
                "utilidad": "Maneja costos de adquisición con descuento y costo de transporte."
            }
        }
        
    def _traducir_ruta_geografica(self, ruta_ids: list):
        """Traduce los IDs internos de la ruta a nombres geográficos o significativos."""
        ruta_traducida = []
        for nodo_id in ruta_ids:
            if nodo_id not in self.grafo:
                ruta_traducida.append(nodo_id)
                continue
                
            data = self.grafo.nodes[nodo_id]
            tipo = data.get('tipo', 'Desconocido')
            
            if tipo == 'Asociacion':
                # Asociación: Usar el Distrito (el punto más específico)
                ruta_traducida.append(data.get('distrito', nodo_id))
            elif tipo == 'Mercado':
                # Mercado: Usar el Distrito (el punto más específico)
                ruta_traducida.append(data.get('distrito', nodo_id))
            elif tipo == 'Capital':
                # Capital: Usar el nombre del Departamento (e.g., AMAZONAS, ÁNCASH)
                ruta_traducida.append(nodo_id)
            elif tipo == 'Producto':
                # Producto: Usar el nombre del Producto
                ruta_traducida.append(nodo_id)
            else:
                ruta_traducida.append(nodo_id) # Si es un ID de nodo sin tipo específico, dejar el ID
                
        return ruta_traducida
    
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
    
    def _crear_grafo_para_bellman_ford(self, origen: str, destino: str):
        """
        [CORREGIDO] Crea un grafo con PESOS NEGATIVOS (ahorros) para Bellman-Ford.
        El peso de la arista de adquisición será el valor NEGATIVO del descuento, 
        permitiendo que el algoritmo minimice el costo al maximizar el ahorro.
        """
        grafo_temp = self.grafo.copy()

        # 1. Identificar el Producto y la Capital de Origen legítima
        producto_en_ruta = None
        capital_origen_nombre = self.grafo.nodes[origen].get('departamento')

        for vecino in self.grafo.neighbors(origen):
            if self.grafo.nodes[vecino].get('tipo') == 'Producto':
                producto_en_ruta = vecino
                break
                
        if producto_en_ruta is None or capital_origen_nombre is None:
            return grafo_temp

        # 2. Aplicar el ahorro (PESO NEGATIVO) y limpiar aristas no legítimas
        info_descuento = self.descuentos_activos.get(producto_en_ruta)
        
        precio_final = info_descuento.get('precio_final') if info_descuento else None
        precio_original = info_descuento.get('precio_original') if info_descuento else None
        
        # Calculamos el ahorro (el valor del descuento monetario)
        descuento_monetario = precio_original - precio_final if precio_final is not None and precio_original is not None else 0
        
        # Para Bellman-Ford, el peso será el negativo del ahorro.
        peso_bellman_ford = -descuento_monetario
        
        # Iterar sobre las aristas de adquisición (Producto -> Capital)
        for u, v, data in list(grafo_temp.edges(data=True)):
            if u == producto_en_ruta and self.grafo.nodes[v].get('tipo') == 'Capital':
                
                if v == capital_origen_nombre:
                    # Aplicamos el peso NEGATIVO a esta arista LEGÍTIMA.
                    data['peso'] = peso_bellman_ford
                    data['relacion'] = 'descuento_negativo_aplicado'
                else:
                    # Es un ATJO NO LEGÍTIMO. Eliminar para asegurar la ruta correcta.
                    try:
                        grafo_temp.remove_edge(u, v)
                    except nx.NetworkXError:
                        pass
                        
        # ⚠️ IMPORTANTE: ELIMINAMOS LA SECCIÓN QUE REMOVÍA PESOS NEGATIVOS.
        # Esto permite que el peso_bellman_ford (negativo) sobreviva y Bellman-Ford funcione.
        
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
        
    def obtener_info_geografica(self, nodo_id: str):
        """Obtiene el Departamento, Provincia y Distrito de un nodo, si existen."""
        if nodo_id not in self.grafo:
            return {"departamento": "N/A", "provincia": "N/A", "distrito": "N/A", "tipo": "No encontrado"}

        data = self.grafo.nodes[nodo_id]
        
        # Asume que los atributos fueron cargados en panda.py
        return {
            "id": nodo_id,
            "tipo": data.get('tipo', 'Desconocido'),
            "departamento": data.get('departamento', 'N/A'),
            "provincia": data.get('provincia', 'N/A'),
            "distrito": data.get('distrito', 'N/A')
        }
    
    def _obtener_detalles_productos_en_ruta(self, ruta: list):
        detalles_productos = []
        descuentos_activos = self.descuentos_activos # Usamos la caché generada en __init__
        
        # Iteramos sobre los nodos de la ruta para encontrar los productos
        for i in range(len(ruta)):
            nodo_actual = ruta[i]
            
            # Solo nos interesan los nodos de tipo 'Producto'
            if self.grafo.nodes[nodo_actual].get('tipo') == 'Producto':
                producto_nombre = nodo_actual
                
                # 1. Obtenemos la información de precios y descuentos DE LA CACHÉ
                if producto_nombre in descuentos_activos and descuentos_activos[producto_nombre]['precio_original']:
                    info_descuento = descuentos_activos[producto_nombre]
                    
                    # 2. Buscamos la Asociación de Origen (para el campo asociacion_origen)
                    asociacion_origen = 'N/A'
                    for u_asociacion in self.grafo.predecessors(producto_nombre):
                        if self.grafo.nodes[u_asociacion].get('tipo') == 'Asociacion':
                            asociacion_origen = u_asociacion
                            break
                    
                    # 3. Construir el detalle del producto usando la información calculada
                    precio_inicial = info_descuento['precio_original']
                    descuento_porcentaje = info_descuento['descuento_porcentaje']
                    precio_final_calc = info_descuento['precio_final']
                    
                    # Cálculo de descuento monetario
                    descuento_monetario = precio_inicial * descuento_porcentaje
                    
                    detalles_productos.append({
                        "producto": producto_nombre,
                        "asociacion_origen": asociacion_origen,
                        "precio_inicial": round(precio_inicial, 2),
                        # Mostramos el descuento como un porcentaje (multiplicado por 100)
                        "descuento_porcentaje": round(descuento_porcentaje * 100, 2), 
                        "descuento_monetario": round(descuento_monetario, 2),
                        "precio_final": round(precio_final_calc, 2)
                    })
                    
        return detalles_productos
    
    def comparar_rutas_optimas(self, origen: str, destino: str):
        """
        Calcula la ruta óptima usando Bellman-Ford (peso negativo) y 
        Dijkstra (precio final positivo), comparando resultados, tiempos de 
        ejecución y la validez de cada uno.
        """
        
        # 0. Verificación de Nodos
        if origen not in self.grafo or destino not in self.grafo:
            return {
                "error": "Nodo no encontrado",
                "mensaje": "Verifique que los IDs de origen y destino existan en el grafo."
            }

        # --- 1. Ejecución de Bellman-Ford (El algoritmo CORRECTO para negativos) ---
        ruta_bf = []
        costo_bf = float('inf')
        mensaje_bf = "Error de ejecución."
        
        grafo_bf = self._crear_grafo_para_bellman_ford(origen, destino)
        
        inicio_bf = time.time()
        try:
            ruta_bf = nx.bellman_ford_path(grafo_bf, source=origen, target=destino, weight='peso')
            costo_bf = nx.bellman_ford_path_length(grafo_bf, source=origen, target=destino, weight='peso')
            mensaje_bf = "Ruta **ÓPTIMA** encontrada. Costo mínimo al manejar descuentos (pesos negativos)."
        except nx.NetworkXNoPath:
            costo_bf = float('inf')
            mensaje_bf = "No se encontró un camino entre los nodos."
        except nx.NetworkXUnbounded:
            costo_bf = -float('inf')
            mensaje_bf = "¡ATENCIÓN! Se detectó un **ciclo negativo** (ahorro infinito). Bellman-Ford lo detecta, confirmando su robustez."
        except Exception as e:
            mensaje_bf = f"Error inesperado en Bellman-Ford: {e}"
        finally:
            fin_bf = time.time()
            tiempo_bf_ms = round((fin_bf - inicio_bf) * 1000, 4)

        # --- 2. Ejecución de Dijkstra (El algoritmo RÁPIDO y AHORA ÓPTIMO) ---
        ruta_dj = []
        costo_dj = float('inf')
        mensaje_dj = "Error de ejecución."
        
        grafo_dj_optimo = self._crear_grafo_para_dijkstra_optimo(origen, destino) 
        
        inicio_dj = time.time()
        try:
            ruta_dj = nx.dijkstra_path(grafo_dj_optimo, source=origen, target=destino, weight='peso')
            costo_dj = nx.dijkstra_path_length(grafo_dj_optimo, source=origen, target=destino, weight='peso')
            
            mensaje_dj = "Ruta **ÓPTIMA** encontrada. El grafo fue modificado para usar precios finales POSITIVOS, permitiendo que Dijkstra encuentre el costo mínimo de manera más rápida."

        except nx.NetworkXNoPath:
            costo_dj = float('inf')
            mensaje_dj = "No se encontró un camino entre los nodos."
        except Exception as e:
            mensaje_dj = f"Error inesperado en Dijkstra: {e}"
        finally:
            fin_dj = time.time()
            tiempo_dj_ms = round((fin_dj - inicio_dj) * 1000, 4)

        # --- 3. Formato Final y Conclusión ---
        
        # 🌟🌟🌟 CAMBIO SOLICITADO AQUÍ 🌟🌟🌟
        # Se elimina el ID de origen (ruta[0]) y el ID de destino (ruta[-1]) 
        # para mostrar solo los nodos intermedios (Producto y Capitales).
        # Se aplica solo si la ruta tiene más de 2 nodos (ID_A, ID_B, ...).
        ruta_bf_display = ruta_bf[1:-1] if len(ruta_bf) > 2 else []
        ruta_dj_display = ruta_dj[1:-1] if len(ruta_dj) > 2 else []
        
        # Formatear los costos
        costo_bf_str = f"{costo_bf:.2f}" if costo_bf not in [float('inf'), -float('inf')] else ("Ciclo Negativo" if costo_bf == -float('inf') else "N/A")
        costo_dj_str = f"{costo_dj:.2f}" if costo_dj != float('inf') else "N/A"
        
        conclusion = "Ambos algoritmos encuentran la ruta óptima si el grafo se modifica (precios finales). Bellman-Ford es crucial para la robustez y la validación de la lógica de descuento (peso negativo)."
        if costo_bf == -float('inf'):
             conclusion = "¡ADVERTENCIA! El grafo contiene un ciclo negativo. Bellman-Ford lo detectó, confirmando su validez."
             
        return {
            "origen": origen,
            "destino": destino,
            "bellman_ford": {
                "estado": "Éxito",
                "ruta": ruta_bf_display,  # ⬅️ CAMBIO IMPLEMENTADO
                "costo_final": costo_bf_str,
                "validacion": mensaje_bf,
                "tiempo_ejecucion_ms": tiempo_bf_ms,
                "complejidad_teorica": "O(V * E)" 
            },
            "dijkstra": {
                "estado": "Éxito/Óptimo", 
                "ruta": ruta_dj_display,  # ⬅️ CAMBIO IMPLEMENTADO
                "costo_final": costo_dj_str,
                "validacion": mensaje_dj,
                "tiempo_ejecucion_ms": tiempo_dj_ms,
                "complejidad_teorica": "O(E + V log V)" 
            },
            "conclusion_principal": conclusion
        }
        
    def _crear_grafo_para_dijkstra_optimo(self, origen: str, destino: str):
        """
        Crea un grafo modificado para Dijkstra.
        Aplica el precio final POSITIVO (con descuento) como peso de la arista, 
        eliminando la necesidad de pesos negativos para encontrar la ruta óptima.
        """
        grafo_temp = self.grafo.copy()

        producto_en_ruta = None
        capital_origen_nombre = self.grafo.nodes[origen].get('departamento')

        for vecino in self.grafo.neighbors(origen):
            if self.grafo.nodes[vecino].get('tipo') == 'Producto':
                producto_en_ruta = vecino
                break
                
        if producto_en_ruta is None or capital_origen_nombre is None:
            return grafo_temp

        info_descuento = self.descuentos_activos.get(producto_en_ruta)
        precio_final = info_descuento.get('precio_final') if info_descuento else None
        
        # 🌟 CLAVE: Usar el precio_final POSITIVO para Dijkstra
        peso_dijkstra_optimo = precio_final
        
        # Iterar sobre las aristas de adquisición (Producto -> Capital)
        for u, v, data in list(grafo_temp.edges(data=True)):
            if u == producto_en_ruta and self.grafo.nodes[v].get('tipo') == 'Capital':
                
                if v == capital_origen_nombre and peso_dijkstra_optimo is not None:
                    # Aplicamos el peso POSITIVO (precio con descuento) a esta arista LEGÍTIMA.
                    data['peso'] = peso_dijkstra_optimo
                    data['relacion'] = 'precio_con_descuento_optimo'
                else:
                    # Es un ATJO NO LEGÍTIMO. Eliminar.
                    try:
                        grafo_temp.remove_edge(u, v)
                    except nx.NetworkXError:
                        pass
                        
        return grafo_temp
    
    def metricas_grafo(self):
        return {
            "total_nodos": self.grafo.number_of_nodes(),
            "total_aristas": self.grafo.number_of_edges(),
            "densidad": nx.density(self.grafo),
            "productos_con_descuento": len([p for p in self.descuentos_activos if self.descuentos_activos[p]['precio_original']])
        }
        
    def arbol_expansion_minima_kruskal(self):
        """
        [MST/Kruskal] Calcula el costo total mínimo para conectar a TODOS los nodos del grafo 
        utilizando el algoritmo de Kruskal para el Árbol de Expansión Mínima.
        """
        
        # Kruskal/Prim requiere que el grafo sea no dirigido para ser canónico, 
        # pero networkx lo adapta a grafos dirigidos o usa el algoritmo para encontrar 
        # el árbol de expansión. Usaremos el grafo base (dirigido).
        
        inicio_mst = time.time()
        try:
            # nx.minimum_spanning_tree utiliza Kruskal o Prim internamente.
            # Aquí, creamos una versión no dirigida del grafo para el cálculo canónico
            # de MST, asegurando que solo los pesos positivos (costos de transporte) sean considerados.
            
            grafo_no_dirigido = self.grafo.to_undirected(reciprocal=False)
            
            # El cálculo requiere pesos positivos, lo cual es estándar para MST
            mst = nx.minimum_spanning_tree(grafo_no_dirigido, weight='peso', algorithm='kruskal')
            
            # El costo total del MST es la suma de los pesos de las aristas seleccionadas
            costo_total_mst = sum(data['peso'] for u, v, data in mst.edges(data=True))
            
            # Obtener una lista de las aristas del MST para la visualización
            aristas_mst = [(u, v, round(data['peso'], 2)) for u, v, data in mst.edges(data=True)]

            mensaje = "Costo mínimo para CONECTAR TODA la red logística de AgriLink (sin ciclos)."
            
        except nx.NetworkXNoPath:
            costo_total_mst = 0
            aristas_mst = []
            mensaje = "No fue posible crear un árbol de expansión."
        except Exception as e:
            mensaje = f"Error inesperado en MST (Kruskal): {e}"
            costo_total_mst = 0
            aristas_mst = []
        finally:
            fin_mst = time.time()
            tiempo_mst_ms = round((fin_mst - inicio_mst) * 1000, 4)

        return {
            "algoritmo": "Kruskal (Árbol de Expansión Mínima)",
            "criterio": "Costo Mínimo para Conectar Todos los Nodos",
            "costo_total_mst": round(costo_total_mst, 2),
            "total_aristas_mst": len(aristas_mst),
            "tiempo_ejecucion_ms": tiempo_mst_ms,
            "mensaje": mensaje,
            "ejemplo_aristas": aristas_mst[:10], # Mostrar solo las primeras 10 aristas
            "complejidad_teorica": "O(E log E) o O(E log V)"
        }

algoritmos_service = AlgoritmosService()

