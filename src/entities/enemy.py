import arcade
import pyvisgraph as vg
import threading
from shapely.geometry import box
from shapely.ops import unary_union



class Enemigo(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(width=32, height=32, color=arcade.color.BLOOD_RED)
        self.vida = 50
        self.pos_origen = None
        self.pos_destino = None
        self.ruta = []
        self.velocidad = 2
        self.vista = 500

    def establecer_ruta(self, destino, nav_manager):
        """Calcula la ruta desde donde está ahora hasta el destino"""
        self.pos_origen = self.position
        self.pos_destino = destino
        self.ruta = nav_manager.obtener_ruta(self.pos_origen, self.pos_destino)


    def check_jugador_en_vista(self, jugador):
        """Lógica propia del enemigo usando las herramientas del sistema"""
        # 1. Distancia física
        distancia = arcade.get_distance_between_sprites(self, jugador)
        if distancia > self.vista:
            return False

        # 2. Visión a través de muros (usando el Singleton)
        nav = SistemaNavegacion()
        return nav.tiene_linea_de_vision(self.position, jugador.position)


    def move(self):
        """Lógica de movimiento punto a punto"""
        if not self.ruta:
            return

        # Siguiente nodo en la lista
        destino_x, destino_y = self.ruta[0]
        
        if self.center_x < destino_x: self.change_x = self.velocidad
        elif self.center_x > destino_x: self.change_x = -self.velocidad
        else: self.change_x = 0

        if self.center_y < destino_y: self.change_y = self.velocidad
        elif self.center_y > destino_y: self.change_y = -self.velocidad
        else: self.change_y = 0

        # Si llegamos al nodo actual (con un margen de error), vamos al siguiente
        distancia = arcade.get_distance(self.center_x, self.center_y, destino_x, destino_y)
        if distancia < 5:
            self.ruta.pop(0)
            if not self.ruta:
                self.change_x = 0
                self.change_y = 0






#### RESTO DE ENEMIGOS 




























class SistemaNavegacion:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SistemaNavegacion, cls).__new__(cls)
        return cls._instance

    def __init__(self, lista_bloques=None):
        # Usamos 'inicializado' para que esto SOLO pase una vez en toda la vida del juego
        if not hasattr(self, 'inicializado'):
            self.g = vg.VisGraph()
            self.bloques_referencia = lista_bloques
            self.recalculando = False
            self.ultimo_conteo_bloques = 0 
            self.inicializado = True
            
            # Solo la primera vez calculamos
            if self.bloques_referencia:
                self.actualizar_grafo_async()
    def actualizar_grafo_async(self):
        if self.recalculando or not self.bloques_referencia:
            return
        
        self.recalculando = True
        
        hilo = threading.Thread(target=self._worker_build, args=(self.bloques_referencia, ))
        hilo.setDaemon(True) # Para que el hilo muera si cierras el juego
        hilo.start()

    def _worker_build(self, bloques_referencia):
        try:
            rectangulos = []
            for b in bloques_referencia:
                rectangulos.append((b.left, b.right, b.bottom, b.top))
            self.recalculando = True
            nuevo_grafo = vg.VisGraph()
            
            # 1. Convertimos los rectángulos de Arcade en objetos Shapely
            lista_shapely = []
            for left, right, bottom, top in rectangulos:
                if left < right and bottom < top:
                    lista_shapely.append(box(left, bottom, right, top))

            if not lista_shapely:
                # Si dejas el mundo vacío, al menos inicializamos un grafo limpio
                nuevo_grafo.build([])
                self.g = nuevo_grafo
                self.recalculando = False
                return

            # 2. FUSIONAMOS Y APLICAMOS OFFSET (Suma de Minkowski)
            # Primero unimos todos los bloques en una sola masa
            union_inicial = unary_union(lista_shapely)
            
            # Aplicamos el BUFFER (Inflado)
            # Si tu enemigo mide 32px, pon un buffer de 18 o 20px.
            # join_style=2 (MITRE) mantiene las esquinas cuadradas.
            ancho_enemigo = 32
            offset = (ancho_enemigo / 2) + 2  # Mitad del cuerpo + margen de seguridad
            union_inflada = union_inicial.buffer(offset, join_style=2)
            
            # 3. Extraemos los polígonos finales del resultado inflado
            poligonos_finales = []
            
            # El resultado del buffer siempre puede ser Polygon o MultiPolygon
            formas = union_inflada.geoms if hasattr(union_inflada, 'geoms') else [union_inflada]

            for forma in formas:
                if not forma.is_empty:
                    # Obtenemos el contorno exterior inflado
                    # Usamos simplify para eliminar puntos redundantes en líneas rectas
                    coords = list(forma.exterior.coords)
                    
                    # Convertimos a puntos de VisGraph
                    puntos_vg = [vg.Point(p[0], p[1]) for p in coords[:-1]]
                    poligonos_finales.append(puntos_vg)

            # 4. Construimos el grafo con las formas ya fusionadas e infladas
            if poligonos_finales:
                nuevo_grafo.build(poligonos_finales, workers=1)
                self.g = nuevo_grafo
                print(f"Grafo inflado: de {len(rectangulos)} bloques a {len(poligonos_finales)} formas (Offset: {offset}px).")

        except Exception as e:
            print(f"Error en la fusión/inflado de polígonos: {e}")
        finally:
            self.recalculando = False
    def obtener_ruta(self, inicio, destino):
        """
        Calcula la ruta más corta entre dos puntos usando el grafo actual.
        """
        # Cambiamos la validación para que no busque atributos inexistentes
        # Simplemente comprobamos si 'visgraph' existe (se crea al terminar build)
        if not self.g or not hasattr(self.g, 'visgraph'):
            return []

        try:
            # Convertimos las posiciones (x, y) a puntos de VisGraph
            p_start = vg.Point(inicio[0], inicio[1])
            p_end = vg.Point(destino[0], destino[1])
            
            # Calculamos la ruta. shortest_path devuelve una lista de objetos Point
            ruta_puntos = self.g.shortest_path(p_start, p_end)
            
            # Convertimos a tuplas (x, y) para que Arcade pueda dibujarlas
            return [(p.x, p.y) for p in ruta_puntos]
            
        except Exception as e:
            # Si el punto de inicio o fin está DENTRO de un polígono, dará error.
            # Es normal si el jugador o enemigo están solapados con un muro.
            print(f"Aviso: No se pudo calcular la ruta (punto obstruido): {e}")
            return []