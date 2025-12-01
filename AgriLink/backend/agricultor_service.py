from datetime import datetime, timedelta

class AgricultorService:
    def __init__(self):
        self.agricultores = self._inicializar_agricultores()
        self.productos = self._inicializar_productos()
        self.pedidos = self._inicializar_pedidos()
        self.resenas = self._inicializar_resenas()
    
    def _inicializar_agricultores(self):
        return [
            {
                "id": 1,
                "nombre": "Luis Mendoza",
                "email": "luis@agricultor.com",
                "telefono": "+51 987 654 321",
                "ubicacion": "Valle del Mantaro",
                "descripcion": "Agricultor de tercera generación especializado en papas y hortalizas",
                "fecha_registro": "2023-01-15",
                "rating": 4.8
            }
        ]
    
    def _inicializar_productos(self):
        return [
            {
                "id": 1,
                "nombre": "Papas frescas",
                "agricultor_id": 1,
                "precio": 7.2,
                "unidad": "kg",
                "stock": 14,
                "categoria": "Tubérculos",
                "descripcion": "Papas frescas de excelente calidad",
                "activo": True
            },
            {
                "id": 2,
                "nombre": "Mangos dulces",
                "agricultor_id": 1,
                "precio": 7.0,
                "unidad": "kg", 
                "stock": 8,
                "categoria": "Frutas",
                "descripcion": "Mangos jugosos de temporada",
                "activo": True
            }
        ]
    
    def _inicializar_pedidos(self):
        return [
            {
                "id": 1,
                "cliente": "Martín Torres",
                "agricultor_id": 1,
                "productos": [{"producto_id": 1, "cantidad": 2, "precio_unitario": 7.2}],
                "estado": "completado",
                "total": 14.4,
                "fecha_pedido": "2024-01-15T10:00:00Z",
                "fecha_entrega": "2024-01-16T14:00:00Z"
            }
        ]
    
    def _inicializar_resenas(self):
        return [
            {
                "id": 1,
                "agricultor_id": 1,
                "cliente": "Carlos López",
                "rating": 5,
                "comentario": "Excelente producto y servicio muy amable",
                "fecha": "2024-01-15"
            }
        ]
    
    # OPERACIONES CRUD PURAS
    def obtener_agricultores(self):
        return self.agricultores
    
    def obtener_agricultor(self, agricultor_id: int):
        #QuickFind:
        if not hasattr(self, '_agricultores_uf'):
            # Inicializar QuickFind una sola vez
            self._agricultores_uf = {}
            for agricultor in self.agricultores:
                self._agricultores_uf[agricultor['id']] = agricultor
    
        return self._agricultores_uf.get(agricultor_id)
    
    def actualizar_agricultor(self, agricultor_id: int, datos: dict):
        agricultor = self.obtener_agricultor(agricultor_id)
        if agricultor:
            agricultor.update(datos)
            return agricultor
        return None
    
    def obtener_productos(self, agricultor_id: int = None):
        if agricultor_id:
            return [p for p in self.productos if p['agricultor_id'] == agricultor_id]
        return self.productos
    
    def crear_producto(self, datos: dict):
        nuevo_id = max([p['id'] for p in self.productos]) + 1
        producto = {"id": nuevo_id, **datos}
        self.productos.append(producto)
        return producto
    
    def obtener_pedidos_agricultor(self, agricultor_id: int, estado: str = None):
        pedidos = [p for p in self.pedidos if p['agricultor_id'] == agricultor_id]
        if estado:
            pedidos = [p for p in pedidos if p['estado'] == estado]
        return pedidos
    
    def obtener_resenas_agricultor(self, agricultor_id: int):
        return [r for r in self.resenas if r['agricultor_id'] == agricultor_id]

agricultor_service = AgricultorService()