import arcade
import threading
from entities.pathfinding import SistemaNavegacion



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

    def __init__(self, lista_bloques=None, chunk_size=512):
        if not hasattr(self, 'inicializado'):
            self.chunk_size = chunk_size
            self.bloques_referencia = lista_bloques
            self.grafos_chunks = {} 
            self.poligonos_inflados = {} # Guardamos la geometría para validar puntos
            self.recalculando = False
            self.inicializado = True
            
            if self.bloques_referencia:
                self.actualizar_grafo_async()

    def _get_chunk_coord(self, x, y):
        return (int(x // self.chunk_size), int(y // self.chunk_size))

    def actualizar_grafo_async(self):
        if self.recalculando or not self.bloques_referencia: return
        self.recalculando = True
        
        # Extraer datos de Sprites
        rects = [{'l': b.left, 'r': b.right, 'b': b.bottom, 't': b.top, 
                  'cx': b.center_x, 'cy': b.center_y} for b in self.bloques_referencia]

        hilo = threading.Thread(target=self._worker_chunks_visgraph, args=(rects,))
        hilo.daemon = True
        hilo.start()

    def _worker_chunks_visgraph(self, rects):
        try:
            distribucion = collections.defaultdict(list)
            for r in rects:
                coord = self._get_chunk_coord(r['cx'], r['cy'])
                distribucion[coord].append(r)

            nuevos_grafos = {}
            nuevos_polis = {}
            offset = 22 # Aumentamos el inflado para evitar colisiones físicas

            for coord, bloques_zona in distribucion.items():
                lista_shapely = [box(r['l'], r['b'], r['r'], r['t']) for r in bloques_zona]
                
                # Fusión e Inflado
                union_inflada = unary_union(lista_shapely).buffer(offset, join_style=2)
                
                # Recorte al chunk
                l, b_c = coord[0] * self.chunk_size, coord[1] * self.chunk_size
                chunk_area = box(l, b_c, l + self.chunk_size, b_c + self.chunk_size)
                union_final = union_inflada.intersection(chunk_area)
                
                nuevos_polis[coord] = union_final

                poligonos_vg = []
                formas = union_final.geoms if hasattr(union_final, 'geoms') else [union_final]
                for forma in formas:
                    if not forma.is_empty and hasattr(forma, 'exterior'):
                        puntos_vg = [vg.Point(p[0], p[1]) for p in forma.exterior.coords[:-1]]
                        poligonos_vg.append(puntos_vg)

                g_local = vg.VisGraph()
                g_local.build(poligonos_vg, workers=1)
                nuevos_grafos[coord] = g_local

            self.grafos_chunks = nuevos_grafos
            self.poligonos_inflados = nuevos_polis
            print(f"Navegación lista: {len(nuevos_grafos)} chunks.")
        except Exception as e: print(f"Error: {e}")
        finally: self.recalculando = False

    def obtener_ruta(self, inicio, destino):
        c_inicio = self._get_chunk_coord(*inicio)
        c_destino = self._get_chunk_coord(*destino)

        # 1. Macro BFS
        chunk_path = self._get_macro_path(c_inicio, c_destino)
        if not chunk_path: return [inicio, destino]

        # 2. Construcción por tramos
        full_path = []
        actual = self._corregir_punto(inicio, c_inicio) # Aseguramos que el inicio sea válido
        
        for i, coord in enumerate(chunk_path):
            if i == len(chunk_path) - 1:
                meta = self._corregir_punto(destino, c_destino)
            else:
                raw_border = self._get_border_point(coord, chunk_path[i+1], destino)
                meta = self._corregir_punto(raw_border, coord)
            
            segmento = self._get_local_path(actual, meta, coord)
            if not full_path: full_path.extend(segmento)
            else: full_path.extend(segmento[1:])
            actual = meta

        return self.suavizar_ruta(full_path)

    def _corregir_punto(self, punto, coord):
        """Si el punto está dentro de un muro inflado, lo saca a la superficie"""
        poly = self.poligonos_inflados.get(coord)
        if not poly or poly.is_empty: return punto
        
        p_shapely = Point(punto)
        if poly.contains(p_shapely):
            # Proyectamos el punto al exterior del polígono más cercano
            return (poly.exterior.interpolate(poly.exterior.project(p_shapely)).coords[0])
        return punto

    def _get_local_path(self, p1, p2, coord):
        grafo = self.grafos_chunks.get(coord)
        if not grafo or not hasattr(grafo, 'visgraph'): return [p1, p2]
        try:
            ruta = grafo.shortest_path(vg.Point(p1[0], p1[1]), vg.Point(p2[0], p2[1]))
            return [(p.x, p.y) for p in ruta]
        except: return [p1, p2]

    def _get_macro_path(self, start, end):
        queue = collections.deque([start]); came_from = {start: None}
        while queue:
            curr = queue.popleft()
            if curr == end: break
            for nxt in [(curr[0]+1, curr[1]), (curr[0]-1, curr[1]), (curr[0], curr[1]+1), (curr[0], curr[1]-1)]:
                if nxt not in came_from:
                    came_from[nxt] = curr
                    queue.append(nxt)
        if end not in came_from: return []
        path = []; curr = end
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        return path[::-1]

    def _get_border_point(self, c1, c2, destino):
        l, r = c1[0]*self.chunk_size, (c1[0]+1)*self.chunk_size
        b, t = c1[1]*self.chunk_size, (c1[1]+1)*self.chunk_size
        p = 30 
        if c2[0] > c1[0]: return (r, max(b+p, min(t-p, destino[1])))
        if c2[0] < c1[0]: return (l, max(b+p, min(t-p, destino[1])))
        if c2[1] > c1[1]: return (max(l+p, min(r-p, destino[0])), t)
        return (max(l+p, min(r-p, destino[0])), b)

    def suavizar_ruta(self, ruta):
        if len(ruta) < 3: return ruta
        suavizada = [ruta[0]]
        i = 0
        while i < len(ruta) - 1:
            encontrado = False
            for j in range(len(ruta) - 1, i, -1):
                # IMPORTANTE: has_line_of_sight debe recibir la SpriteList original
                if arcade.has_line_of_sight(suavizada[-1], ruta[j], self.bloques_referencia):
                    suavizada.append(ruta[j])
                    i = j; encontrado = True; break
            if not encontrado:
                i += 1; suavizada.append(ruta[i])
        return suavizada





















"""

class SistemaNavegacion:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SistemaNavegacion, cls).__new__(cls)
        return cls._instance

    def __init__(self, lista_bloques=None, chunk_size=512):
        if not hasattr(self, 'inicializado'):
            self.chunk_size = chunk_size
            self.bloques_referencia = lista_bloques
            self.grafos_chunks = {} 
            self.recalculando = False
            self.inicializado = True
            
            if self.bloques_referencia:
                self.actualizar_grafo_async()

    def _get_chunk_coord(self, x, y):
        return (int(x // self.chunk_size), int(y // self.chunk_size))


    def _get_chunk_path(self, start_coord, end_coord):
        from collections import deque
        queue = deque([start_coord])
        came_from = {start_coord: None}

        while queue:
            current = queue.popleft()
            if current == end_coord: break

            for neighbor in self._get_neighbors(current):
                if neighbor not in came_from:
                    # VALIDACIÓN CRÍTICA:
                    # ¿El punto de paso entre estos dos chunks está dentro de un bloque?
                    # Dentro de _get_chunk_path, cambia la validación crítica:
                    p_paso = self._get_border_point_between(current, neighbor, start_coord, end_coord)

                    # Si el punto de unión está DENTRO de un bloque, este camino entre chunks no es válido
                    for bloque in self.bloques_referencia:
                        if bloque.collides_with_point(p_paso):
                            continue # Este borde está bloqueado por un muro, busca otro vecino
                    
                    came_from[neighbor] = current
                    queue.append(neighbor)

        if end_coord not in came_from: return []
        
        path = []
        curr = end_coord
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        return path[::-1]

    def actualizar_grafo_async(self):
        if self.recalculando or not self.bloques_referencia:
            return
        
        self.recalculando = True
        bloques_copia = list(self.bloques_referencia)
        
        # El 'Worker' es este hilo ejecutando la función _worker_chunks
        hilo = threading.Thread(target=self._worker_chunks, args=(bloques_copia,))
        hilo.daemon = True
        hilo.start()

    def _worker_chunks(self, bloques):
        Este es el WORKER: Procesa la geometría en segundo plano
        try:
            distribucion = {}
            for b in bloques:
                coord = self._get_chunk_coord(b.center_x, b.center_y)
                distribucion.setdefault(coord, []).append(b)

            nuevos_grafos = {}

            for coord, bloques_zona in distribucion.items():
                l, b_c = coord[0] * self.chunk_size, coord[1] * self.chunk_size
                r, t = l + self.chunk_size, b_c + self.chunk_size
                chunk_rect = box(l, b_c, r, t)

                # Procesamiento Shapely (Tu lógica original)
                # Busca esta parte en tu _worker_chunks
                lista_shapely = []
                for bl in bloques_zona:
                    # Engordamos el bloque 2 píxeles hacia cada lado para cerrar las grietas
                    padding = 2 
                    caja_engordada = box(
                        bl.left - padding, 
                        bl.bottom - padding, 
                        bl.right + padding, 
                        bl.top + padding
                    )
                    lista_shapely.append(caja_engordada)

                # Al hacer la unión ahora, esos píxeles extra harán que los bloques
                # se "fundan" en una sola masa impenetrable.
                union = unary_union(lista_shapely).buffer(18, join_style=2)
                
                # Sellar bordes para que los muros sean impenetrables
                union_final = union.intersection(chunk_rect)

                poligonos_vg = []
                formas = union_final.geoms if hasattr(union_final, 'geoms') else [union_final]
                for forma in formas:
                    if not forma.is_empty and hasattr(forma, 'exterior'):
                        puntos_vg = [vg.Point(p[0], p[1]) for p in forma.exterior.coords[:-1]]
                        poligonos_vg.append(puntos_vg)

                g_chunk = vg.VisGraph()
                g_chunk.build(poligonos_vg, workers=1)
                nuevos_grafos[coord] = g_chunk

            self.grafos_chunks = nuevos_grafos
        except Exception as e:
            print(f"Error en worker de navegación: {e}")
        finally:
            self.recalculando = False
    def suavizar_ruta(self, ruta):
        if len(ruta) < 3: return ruta
        
        suavizada = [ruta[0]]
        i = 0
        while i < len(ruta) - 1:
            encontrado = False
            # Buscamos el punto más lejano visible sin chocar con NADA
            for j in range(len(ruta) - 1, i, -1):
                # IMPORTANTE: check_line es más preciso a veces que has_line_of_sight
                # Asegúrate de que bloques_referencia tenga TODOS los muros
                if arcade.has_line_of_sight(suavizada[-1], ruta[j], self.bloques_referencia):
                    suavizada.append(ruta[j])
                    i = j
                    encontrado = True
                    break
            if not encontrado:
                i += 1
                suavizada.append(ruta[i])
        return suavizada
    def obtener_ruta(self, inicio, destino):
        # 1. Generamos la ruta "bruta" uniendo los segmentos de cada chunk
        ruta_bruta = self._generar_ruta_por_chunks(inicio, destino)
        
        # Si la ruta es muy corta o no hay bloques para validar, devolvemos tal cual
        if len(ruta_bruta) <= 2 or not self.bloques_referencia:
            return ruta_bruta

        return ruta_bruta
        # 2. SUAVIZADO (String Pulling)
        # Este algoritmo "tensa la cuerda": si puedo ver el punto C desde el A, borro el B.
        ruta_final = [ruta_bruta[0]]
        current_idx = 0
        
        while current_idx < len(ruta_bruta) - 1:
            best_next_idx = current_idx + 1
            
            # Buscamos desde el final de la lista hacia atrás el punto más lejano visible
            for check_idx in range(len(ruta_bruta) - 1, current_idx + 1, -1):
                p1 = ruta_bruta[current_idx]
                p2 = ruta_bruta[check_idx]
                
                # arcade.has_line_of_sight usa los hitboxes reales de los sprites
                if arcade.has_line_of_sight(p1, p2, self.bloques_referencia, max_distance=1000):
                    best_next_idx = check_idx
                    break
            
            ruta_final.append(ruta_bruta[best_next_idx])
            current_idx = best_next_idx
            
        return ruta_final

    def _generar_ruta_por_chunks(self, inicio, destino):
        Encapsulamos tu lógica de unión de segmentos aquí
        coord_inicio = self._get_chunk_coord(inicio[0], inicio[1])
        coord_destino = self._get_chunk_coord(destino[0], destino[1])

        if coord_inicio == coord_destino:
            return self._get_local_path(inicio, destino, coord_inicio)

        chunk_path = self._get_chunk_path(coord_inicio, coord_destino)
        if not chunk_path: 
            return [inicio, destino]

        full_path = []
        puntos_actuales = inicio

        for i in range(len(chunk_path)):
            c_curr = chunk_path[i]
            if i == len(chunk_path) - 1:
                p_meta = destino
            else:
                p_meta = self._get_border_point_between(c_curr, chunk_path[i+1], puntos_actuales, destino)

            segmento = self._get_local_path(puntos_actuales, p_meta, c_curr)
            
            if not full_path:
                full_path.extend(segmento)
            else:
                full_path.extend(segmento[1:])
            
            puntos_actuales = p_meta

        return full_path


    def _get_local_path(self, p1, p2, coord):
        Cálculo real de VisGraph en un solo chunk
        grafo = self.grafos_chunks.get(coord)
        if not grafo or not hasattr(grafo, 'visgraph'):
            return [p1, p2]
        try:
            ruta = grafo.shortest_path(vg.Point(p1[0], p1[1]), vg.Point(p2[0], p2[1]))
            return [(p.x, p.y) for p in ruta]
        except:
            return [p1, p2]

    def _get_border_point_between(self, c1, c2, inicio, destino):
        l, r, b, t = c1[0]*self.chunk_size, (c1[0]+1)*self.chunk_size, c1[1]*self.chunk_size, (c1[1]+1)*self.chunk_size
        
        # Añadimos un margen de 10px para que no pase rozando el vértice del chunk
        padding = 10 

        if c2[0] > c1[0]: # Derecha
            return (r, max(b + padding, min(t - padding, destino[1])))
        if c2[0] < c1[0]: # Izquierda
            return (l, max(b + padding, min(t - padding, destino[1])))
        if c2[1] > c1[1]: # Arriba
            return (max(l + padding, min(r - padding, destino[0])), t)
        return (max(l + padding, min(r - padding, destino[0])), b) # Abajo

    def _get_border_point(self, inicio, destino, coord_chunk):
        Calcula un punto de salida del chunk actual en dirección al objetivo
        l = coord_chunk[0] * self.chunk_size
        r = l + self.chunk_size
        b = coord_chunk[1] * self.chunk_size
        t = b + self.chunk_size
        
        # Un punto simple: el centro del borde que esté más cerca del destino
        target_x = max(l + 5, min(r - 5, destino[0]))
        target_y = max(b + 5, min(t - 5, destino[1]))
        
        return (target_x, target_y)
    
    def _get_neighbors(self, coord):
        x, y = coord
        candidatos = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        vecinos_validos = []

        for v in candidatos:
            # 1. ¿Existe el chunk o es transitable?
            if v in self.grafos_chunks or self._chunk_es_vacio(v):
                # 2. VALIDACIÓN GEOMÉTRICA: ¿El paso entre chunks está obstruido?
                p_paso = self._get_border_point_between(coord, v, (0,0), (0,0)) # Simplificado para test
                
                # Verificamos si el punto de unión cae dentro de CUALQUIER bloque
                bloqueado = False
                for b in self.bloques_referencia:
                    if b.collides_with_point(p_paso):
                        bloqueado = True
                        break
                
                if not bloqueado:
                    vecinos_validos.append(v)
        return vecinos_validos

    def _chunk_es_vacio(self, coord):
        # Lógica para saber si un chunk fuera del diccionario es caminable
        return True

"""



"""

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
        
        #Calcula la ruta más corta entre dos puntos usando el grafo actual.
        
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
"""
