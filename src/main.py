"""
Pill of Silence 
"""
import arcade

# Configuracion de la ventana
ANCHO_VENTANA = 1280
ALTO_VENTANA = 720
TITULO_VENTANA = "Pill of Silence"

# Colores
COLOR_FONDO_MENU = arcade.color.EERIE_BLACK
COLOR_FONDO_JUEGO = arcade.color.DARK_SLATE_GRAY

class Jugador(arcade.SpriteSolidColor):
    """ 
    El jugador es un cuadrado representativo. Faltan los sprites
    """
    def __init__(self):
        super().__init__(width=32, height=32, color=arcade.color.AQUAMARINE)
        self.vida = 100
        self.municion = 30
        self.velocidad = 5

    # Args y kwargs recogen datos inutiles que lanza delta_time para que no de error
    def update(self, *args, **kwargs):
        # El movimiento básico se actualiza aquí
        self.center_x += self.change_x
        self.center_y += self.change_y

class Enemigo(arcade.SpriteSolidColor):
    """
    Clase base para definir los enemigos
    """
    def __init__(self):
        super().__init__(width=32, height=32, color=arcade.color.BLOOD_RED)
        self.vida = 50

class MenuPrincipal(arcade.View):
    """
     Pantalla de inicio del juego. (Menu principal)
    """
    def on_show_view(self):
        self.window.background_color = COLOR_FONDO_MENU

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "PILL OF SILENCE", 
            ANCHO_VENTANA // 2, ALTO_VENTANA // 2 + 50,
            arcade.color.RED_DEVIL, font_size=50, anchor_x="center", bold=True
        )
        arcade.draw_text(
            "Haz clic para acatar las órdenes...", 
            ANCHO_VENTANA // 2, ALTO_VENTANA // 2 - 30,
            arcade.color.GRAY, font_size=20, anchor_x="center"
        )

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        # Al hacer clic, instanciamos y mostramos la vista del juego
        vista_juego = VistaJuego()
        vista_juego.setup()
        self.window.show_view(vista_juego)


class VistaJuego(arcade.View):
    """
        Pantalla principal de acción.
    """
    def __init__(self):
        super().__init__()
        
        # Declaracion de variables 
        self.sprite_jugador = None
        self.lista_jugadores = None
        self.lista_enemigos = None
        
        # Teclas presionadas
        self.izquierda_presionado = False
        self.derecha_presionado = False
        self.arriba_presionado = False
        self.abajo_presionado = False

    def setup(self):
        """ Configura el juego y reinicia las variables. """
        self.window.background_color = COLOR_FONDO_JUEGO
        
        # Inicializar listas de sprites
        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()

        # Crear al jugador en el centro
        self.sprite_jugador = Jugador()
        self.sprite_jugador.center_x = ANCHO_VENTANA // 2
        self.sprite_jugador.center_y = ALTO_VENTANA // 2
        self.lista_jugadores.append(self.sprite_jugador)

        # TODO: Crear mapa (TileMap)
        # TODO: Generar enemigos

    def on_draw(self):
        """
          Dibuja los sprites en pantalla. 
        """
        self.clear()
        
        # Dibujar todos los sprites
        self.lista_jugadores.draw()
        self.lista_enemigos.draw()
        
        # TODO: Dibujar UI (Vida, Munición)

    def on_update(self, delta_time):
        """ 
        Lógica y movimiento que ocurre cada frame. 
        """
        
        # Calcular velocidad del jugador basada en las teclas presionadas
        self.sprite_jugador.change_x = 0
        self.sprite_jugador.change_y = 0

        if self.arriba_presionado and not self.abajo_presionado:
            self.sprite_jugador.change_y = self.sprite_jugador.velocidad
        elif self.abajo_presionado and not self.arriba_presionado:
            self.sprite_jugador.change_y = -self.sprite_jugador.velocidad
            
        if self.izquierda_presionado and not self.derecha_presionado:
            self.sprite_jugador.change_x = -self.sprite_jugador.velocidad
        elif self.derecha_presionado and not self.izquierda_presionado:
            self.sprite_jugador.change_x = self.sprite_jugador.velocidad

        # Actualizar todos los sprites
        self.lista_jugadores.update()
        self.lista_enemigos.update()

    def on_key_press(self, key, modifiers):
        """
          Modifica la velocidad según la tecla que se pulse. 
         """
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = True
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = True
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = True

    def on_key_release(self, key, modifiers):
        """
          Desactiva el estado de tecla presionada al soltar la tecla.
            """
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = False
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = False
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = False

def main():
    """ 
    Función principal de ejecución 
    """
    window = arcade.Window(ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA)
    vista_menu = MenuPrincipal()
    window.show_view(vista_menu)
    arcade.run()

if __name__ == "__main__":
    main()