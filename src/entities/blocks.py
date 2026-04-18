import arcade

# --- CLASES DE OBJETOS ---

class Bloque(arcade.Sprite):
    def __init__(self, width, height, ruta_imagen=None, color=arcade.color.GRAY):
        super().__init__()
        
        if ruta_imagen:
            try:
                self.texture = arcade.load_texture(ruta_imagen)
            except Exception:
                self.texture = arcade.make_soft_square_texture(max(width, height), color, 255, 255)
        else:
            self.texture = arcade.make_soft_square_texture(max(width, height), color, 255, 255)

        self.width = width
        self.height = height

class Puerta(arcade.Sprite):
    def __init__(self, x, y, width, height, ruta_cerrada=None, ruta_abierta=None, tiempo_apertura= 0.5, tiempo_cierre= 0.5):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.width = width
        self.height = height

        # Tiempos de animación
        self.tiempo_apertura = tiempo_apertura
        self.tiempo_cierre = tiempo_cierre
        self.tiempo_estado = 0.0
        
        self.estado = "cerrada"
        self.activa_colision = True

        # Carga de texturas con Fallback
        self.frames = [
            self._cargar_tex(ruta_cerrada, arcade.color.DARK_BROWN, width, height),
            self._cargar_tex(ruta_abierta, arcade.color.DARK_GREEN, width, height)
        ]
        
        # El len es simplemente la longitud de esa lista
        self.cantidad_frames = len(self.frames) 
        
        # Inicializamos con el primer frame (cerrada)
        self.texture = self.frames[0]

    def _cargar_tex(self, ruta, color_alternativo, w, h):
        if ruta:
            try:
                return arcade.load_texture(ruta)
            except Exception:
                return arcade.make_soft_square_texture(max(w, h), color_alternativo, 255, 255)
        return arcade.make_soft_square_texture(max(w, h), color_alternativo, 255, 255)

    def interactuar(self):
        if self.estado == "cerrada":
            self.estado = "abriendo"
        elif self.estado == "abierta":
            self.estado = "cerrando"
        self.tiempo_estado = 0.0

    def update(self, delta_time=1/60):
        if self.estado == "abriendo":
            self.tiempo_estado += delta_time
            
            # Calculamos el progreso (de 0.0 a 1.0)
            progreso = min(self.tiempo_estado / self.tiempo_apertura, 1.0)
            
            # Mapeamos el progreso al índice de la lista de frames
            # Si hay 5 frames, los índices son 0, 1, 2, 3, 4
            indice = int(progreso * (len(self.frames) - 1))
            self.texture = self.frames[indice]

            if progreso >= 1.0:
                self.estado = "abierta"
                self.activa_colision = False

        elif self.estado == "cerrando":
            self.tiempo_estado += delta_time
            
            progreso = min(self.tiempo_estado / self.tiempo_cierre, 1.0)
            
            # Al cerrar, invertimos el índice (va del último al primero)
            indice = (len(self.frames) - 1) - int(progreso * (len(self.frames) - 1))
            self.texture = self.frames[indice]

            if progreso >= 1.0:
                self.estado = "cerrada"
                self.activa_colision = True





# --- FUNCIÓN CONSTRUCTORA ---

def crear_casa(x, y, ancho_habitable, alto_habitable, grosor, direcciones_puerta, ancho_puerta, ruta_pared=None):
    """
    Crea una estructura de casa evitando el solape de esquinas.
    """
    lista_bloques = arcade.SpriteList()
    lista_puertas = arcade.SpriteList()

    # Calculamos dimensiones totales para que las esquinas encajen perfecto
    ancho_total = ancho_habitable + (grosor * 2)
    alto_total = alto_habitable + (grosor * 2)

    # Definimos las 4 paredes (Nombre, es_horizontal, posicion_eje, largo_total)
    config_paredes = [
        ("NORTE", True,  y + alto_habitable // 2 + grosor // 2, ancho_total),
        ("SUR",   True,  y - alto_habitable // 2 - grosor // 2, ancho_total),
        ("OESTE", False, x - ancho_habitable // 2 - grosor // 2, alto_total),
        ("ESTE",  False, x + ancho_habitable // 2 + grosor // 2, alto_total),
    ]

    for nombre, es_horiz, pos_eje, largo_max in config_paredes:
        tiene_puerta = nombre in direcciones_puerta

        if not tiene_puerta:
            # Pared completa
            w, h = (largo_max, grosor) if es_horiz else (grosor, largo_max)
            bloque = Bloque(w, h, ruta_imagen=ruta_pared)
            bloque.position = (x, pos_eje) if es_horiz else (pos_eje, y)
            lista_bloques.append(bloque)
        else:
            # Pared partida en dos por una puerta
            largo_segmento = (largo_max - ancho_puerta) / 2
            offset = (largo_max / 2) - (largo_segmento / 2)

            # Creamos los dos segmentos de muro
            for i in [-1, 1]:
                w_seg, h_seg = (largo_segmento, grosor) if es_horiz else (grosor, largo_segmento)
                seg = Bloque(int(w_seg), int(h_seg), ruta_imagen=ruta_pared)
                if es_horiz:
                    seg.position = (x + (i * offset), pos_eje)
                else:
                    seg.position = (pos_eje, y + (i * offset))
                lista_bloques.append(seg)

            # Creamos la puerta en el hueco
            w_p, h_p = (ancho_puerta, grosor) if es_horiz else (grosor, ancho_puerta)
            puerta = Puerta(pos_eje if not es_horiz else x, 
                            pos_eje if es_horiz else y, 
                            int(w_p), int(h_p))
            lista_puertas.append(puerta)
            lista_bloques.append(puerta) # Añadida a bloques para las colisiones físicas

    return lista_puertas, lista_bloques