import arcade
import textwrap


class DialogUI:
    def __init__(self):
        self.panel_width = 600
        self.panel_height = 400
        self.panel_x = None
        self.panel_y = None

    def _centrar(self):
        window = arcade.get_window()
        if window:
            self.panel_x = window.width // 2
            self.panel_y = window.height // 2
        return self.panel_x, self.panel_y

    def _envolver_texto(self, texto, width=50):
        return textwrap.wrap(texto, width)

    def draw(self, texto, opciones, nombre_personaje=None):
        cx, cy = self._centrar()
        if cx is None:
            return

        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy, self.panel_width, self.panel_height),
            (25, 25, 35, 240)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy, self.panel_width, self.panel_height),
            arcade.color.GOLD,
            border_width=3
        )

        if nombre_personaje:
            arcade.draw_text(
                nombre_personaje,
                cx - self.panel_width // 2 + 20,
                cy + self.panel_height // 2 - 35,
                arcade.color.GOLD,
                font_size=18,
                bold=True
            )

        lineas = self._envolver_texto(texto, width=55)
        y_pos = cy + self.panel_height // 2 - 70
        for linea in lineas:
            arcade.draw_text(
                linea,
                cx - self.panel_width // 2 + 20,
                y_pos,
                arcade.color.WHITE,
                font_size=14,
                width=self.panel_width - 40,
                align="left"
            )
            y_pos -= 22

        if opciones:
            y_opciones = cy - 50
            arcade.draw_text(
                "¿Qué haces?",
                cx,
                y_opciones + 30,
                arcade.color.CYAN,
                font_size=14,
                anchor_x="center"
            )
            for clave, destino in opciones:
                numero = clave
                arcade.draw_text(
                    f"{numero}.",
                    cx - 200,
                    y_opciones,
                    arcade.color.YELLOW,
                    font_size=16,
                    font_name="calibri"
                )
                texto_opcion = f"{destino}"
                arcade.draw_text(
                    texto_opcion,
                    cx - 180,
                    y_opciones,
                    arcade.color.WHITE,
                    font_size=14
                )
                y_opciones -= 35
        else:
            arcade.draw_text(
                "Presiona E para cerrar",
                cx,
                cy - self.panel_height // 2 + 30,
                arcade.color.GRAY,
                font_size=12,
                anchor_x="center"
            )