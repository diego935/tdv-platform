import arcade
import json


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
            "PAUSA",
            cx,
            self.window.height - 150,
            arcade.color.GOLDENROD,
            60,
            anchor_x="center"
        )

        self._draw_button(
            cx,
            self.window.height / 2 + 80,
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
            self.window.height / 2 - 80,
            "SALIR AL MENÚ",
            arcade.color.SMOKY_BLACK
        )

        self._draw_button(
            cx,
            self.window.height / 2 - 160,
            "SALIR DEL JUEGO",
            arcade.color.SMOKY_BLACK
        )

    def _draw_button(self, cx, cy, text, color):
        left = cx - 150
        bottom = cy - 30

        arcade.draw_lbwh_rectangle_filled(
            left,
            bottom,
            300,
            60,
            color
        )

        arcade.draw_lbwh_rectangle_outline(
            left,
            bottom,
            300,
            60,
            arcade.color.VENETIAN_RED,
            3
        )

        arcade.draw_text(
            text,
            cx,
            cy,
            arcade.color.GOLDENROD,
            20,
            anchor_x="center",
            anchor_y="center"
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.vista_juego)
            return

    def on_mouse_press(self, x, y, button, modifiers):

        cx = self.window.width / 2

        if (cx - 150 < x < cx + 150) and (self.window.height / 2 + 50 < y < self.window.height / 2 + 110):
            self.window.show_view(self.vista_juego)
            return

        if (cx - 150 < x < cx + 150) and (self.window.height / 2 - 30 < y < self.window.height / 2 + 30):
            self.guardar_partida()
            return

        if (cx - 150 < x < cx + 150) and (self.window.height / 2 - 110 < y < self.window.height / 2 - 50):
            from vista.menu_principal import MenuPrincipal
            self.window.show_view(MenuPrincipal())
            return

        if (cx - 150 < x < cx + 150) and (self.window.height / 2 - 190 < y < self.window.height / 2 - 130):
            arcade.exit()
            return

    def guardar_partida(self):

        jugador = self.vista_juego.sprite_jugador

        data = {
            "player": {
                "x": jugador.center_x,
                "y": jugador.center_y,
                "inventario": [
                    item.__class__.__name__ if item else None
                    for item in jugador.inventory
                ]
            }
        }

        with open("savegame.json", "w") as f:
            json.dump(data, f, indent=4)

        print("✔ Partida guardada correctamente")