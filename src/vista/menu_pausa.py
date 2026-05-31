import arcade
from utils.log import Log
from utils.save_system import guardar_partida


class MenuPausa(arcade.View):

    def __init__(self, vista_juego):
        super().__init__()
        self.vista_juego = vista_juego

    def on_draw(self):
        self.clear()

        cx = self.window.width / 2

        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width,
            0,
            self.window.height,
            arcade.color.SMOKY_BLACK
        )

        arcade.draw_text(
            "MENÚ DE PAUSA",
            cx,
            self.window.height - 180,
            arcade.color.GOLDENROD,
            90,
            anchor_x="center",
            font_name="Georgia"
        )

        self._draw_button(
            cx,
            self.window.height / 2 + 100,
            "CONTINUAR",
            arcade.color.SMOKY_BLACK
        )

        self._draw_button(
            cx,
            self.window.height / 2,
            "GUARDAR PARTIDA",
            arcade.color.SMOKY_BLACK
        )

        self._draw_button(
            cx,
            self.window.height / 2 - 100,
            "SALIR AL MENÚ",
            arcade.color.SMOKY_BLACK
        )

        self._draw_button(
            cx,
            self.window.height / 2 - 200,
            "SALIR DEL JUEGO",
            arcade.color.SMOKY_BLACK
        )

    def _draw_button(self, cx, cy, text, color):
        left = cx - 200
        bottom = cy - 40
        ancho = 400
        alto = 80

        arcade.draw_lbwh_rectangle_filled(
            left,
            bottom,
            ancho,
            alto,
            color
        )

        arcade.draw_lbwh_rectangle_outline(
            left,
            bottom,
            ancho,
            alto,
            arcade.color.VENETIAN_RED,
            4
        )

        arcade.draw_text(
            text,
            cx,
            cy,
            arcade.color.GOLDENROD,
            28,
            anchor_x="center",
            anchor_y="center",
            font_name= "Times New Roman"
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.vista_juego)
            return

    def on_mouse_press(self, x, y, button, modifiers):

        cx = self.window.width / 2

        if (cx - 200 < x < cx + 200):
            
            # BOTÓN: CONTINUAR
            if (self.window.height / 2 + 60 < y < self.window.height / 2 + 140):
                self.window.show_view(self.vista_juego)
                return

            # BOTÓN: GUARDAR PARTIDA
            if (self.window.height / 2 - 40 < y < self.window.height / 2 + 40):
                self.guardar_partida()
                return

            # BOTÓN: SALIR AL MENÚ
            if (self.window.height / 2 - 140 < y < self.window.height / 2 - 60):
                from vista.menu_principal import MenuPrincipal
                self.vista_juego.limpiar_estado()
                self.window.show_view(MenuPrincipal())
                return

            # BOTÓN: SALIR DEL JUEGO
            if (self.window.height / 2 - 240 < y < self.window.height / 2 - 160):
                arcade.exit()
                return

    def guardar_partida(self):
        guardar_partida(self.vista_juego)
        Log.info("MenuPausa", "Partida guardada manualmente")