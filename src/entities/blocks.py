import arcade

class Bloque(arcade.Sprite):
    def __init__(self, width=32, height=32, color=arcade.color.GRAY):
        super().__init__()

        # Arcade 2.x solo genera cuadrados, así que usamos el mayor lado
        size = max(width, height)

        # Creamos textura temporal
        self.texture = arcade.make_soft_square_texture(
            size,
            color,
            255,
            255
        )

        # Ajustamos tamaño real del sprite
        self.width = width
        self.height = height


class Puerta(arcade.Sprite):
    def __init__(self, x, y, width=32, height=64, tiempo_apertura=1.5, tiempo_cierre=1.0):
        super().__init__()
        self.center_x = x
        self.center_y = y

        self.width = width
        self.height = height

        self.tiempo_apertura = tiempo_apertura
        self.tiempo_cierre = tiempo_cierre

        self.estado = "cerrada"
        self.tiempo_estado = 0.0
        self.activa_colision = True

        self.texture_cerrada = arcade.make_soft_square_texture(width, arcade.color.DARK_BROWN, 255, 255)
        self.texture_abierta = arcade.make_soft_square_texture(width, arcade.color.DARK_GREEN, 255, 255)
        self.texture = self.texture_cerrada

    def interactuar(self):
        if self.estado == "cerrada":
            self.estado = "abriendo"
            self.tiempo_estado = 0.0
        elif self.estado == "abierta":
            self.estado = "cerrando"
            self.tiempo_estado = 0.0

    def update(self, delta_time=0.0, *args, **kwargs):
        if self.estado == "abriendo":
            self.tiempo_estado += delta_time
            if self.tiempo_estado >= self.tiempo_apertura:
                self.estado = "abierta"
                self.tiempo_estado = 0.0
                self.activa_colision = False
                self.texture = self.texture_abierta

        elif self.estado == "cerrando":
            self.tiempo_estado += delta_time
            if self.tiempo_estado >= self.tiempo_cierre:
                self.estado = "cerrada"
                self.tiempo_estado = 0.0
                self.activa_colision = True
                self.texture = self.texture_cerrada

def crear_casa(x, y, ancho_habitable, alto_habitable, grosor, direcciones_puerta, ancho_puerta):
    lista_bloques = []
    lista_puertas = []

    # Límites exteriores (aseguramos enteros)
    izquierda = x - ancho_habitable // 2 - grosor // 2
    derecha = x + ancho_habitable // 2 + grosor // 2
    abajo = y - alto_habitable // 2 - grosor // 2
    arriba = y + alto_habitable // 2 + grosor // 2

    def crear_pared_horizontal(y_pared, tiene_puerta):
        ancho_total = ancho_habitable + grosor * 2
        if not tiene_puerta:
            bloque = Bloque(ancho_total, grosor)
            bloque.center_x = x
            bloque.center_y = y_pared
            lista_bloques.append(bloque)
        else:
            # Segmento de pared a cada lado de la puerta
            lateral = (ancho_total - ancho_puerta) // 2
            
            # Bloque izquierdo
            bloque_izq = Bloque(lateral, grosor)
            bloque_izq.center_x = x - ancho_total // 2 + lateral // 2
            bloque_izq.center_y = y_pared
            lista_bloques.append(bloque_izq)

            # Bloque derecho
            bloque_der = Bloque(lateral, grosor)
            bloque_der.center_x = x + ancho_total // 2 - lateral // 2
            bloque_der.center_y = y_pared
            lista_bloques.append(bloque_der)

            # Puerta (el ancho_puerta ahora sí define el hueco real)
            puerta = Puerta(x, y_pared, width=ancho_puerta, height=grosor)
            lista_puertas.append(puerta)
            lista_bloques.append(puerta)

    def crear_pared_vertical(x_pared, tiene_puerta):
        alto_total = alto_habitable + grosor * 2
        if not tiene_puerta:
            bloque = Bloque(grosor, alto_total)
            bloque.center_x = x_pared
            bloque.center_y = y
            lista_bloques.append(bloque)
        else:
            # Segmento de pared arriba y abajo de la puerta
            lateral = (alto_total - ancho_puerta) // 2

            # Bloque inferior
            bloque_inf = Bloque(grosor, lateral)
            bloque_inf.center_x = x_pared
            bloque_inf.center_y = y - alto_total // 2 + lateral // 2
            lista_bloques.append(bloque_inf)

            # Bloque superior
            bloque_sup = Bloque(grosor, lateral)
            bloque_sup.center_x = x_pared
            bloque_sup.center_y = y + alto_total // 2 - lateral // 2
            lista_bloques.append(bloque_sup)

            # Puerta (Corregido: el height de la puerta es el ancho_puerta)
            puerta = Puerta(x_pared, y, width=grosor, height=ancho_puerta)
            lista_puertas.append(puerta)
            lista_bloques.append(puerta)

    # Construcción de las 4 paredes
    crear_pared_horizontal(arriba, "NORTE" in direcciones_puerta)
    crear_pared_horizontal(abajo, "SUR" in direcciones_puerta)
    crear_pared_vertical(izquierda, "OESTE" in direcciones_puerta)
    crear_pared_vertical(derecha, "ESTE" in direcciones_puerta)

    return lista_puertas, lista_bloques