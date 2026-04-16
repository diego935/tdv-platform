import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_MENU
from vista.game import VistaJuego

class MenuPrincipal(arcade.View):
    def on_show_view(self):
        self.window.background_color = COLOR_FONDO_MENU

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "PILL OF SILENCE",
            ANCHO_VENTANA // 2,
            ALTO_VENTANA // 2 + 50,
            arcade.color.RED_DEVIL,
            font_size=50,
            anchor_x="center",
            bold=True
        )
        arcade.draw_text(
            "Haz clic para acatar las órdenes...",
            ANCHO_VENTANA // 2,
            ALTO_VENTANA // 2 - 30,
            arcade.color.GRAY,
            font_size=20,
            anchor_x="center"
        )

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        vista_juego = VistaJuego()
        vista_juego.setup()
        self.window.show_view(vista_juego)
