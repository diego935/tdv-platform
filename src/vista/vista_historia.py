import arcade
from vista.menu_navegacion import MenuNavegacion


class VistaHistoria(MenuNavegacion):

    def on_draw(self):
        super().on_draw()

        arcade.draw_text(
            "HISTORIA", 
            self.window.width / 2, 
            self.window.height / 2 + 100,
            arcade.color.GOLDENROD, 
            50, 
            anchor_x="center",
            font_name="Georgia"
        )

        # Texto de la historia formateado con salto de línea y alineación centrada
        texto_historia = (
            "Soy un soldado aparentemente normal, uno más entre las filas.\n"
            "Sin previo aviso se me ha destinado a la ciudad más cercana.\n"
            "No conozco detalles sobre la misión, solo sé que debo ir yo solo y volver entero.\n"
            "Me han dicho que no pregunte nada, que solo debo ir, limpiar la ciudad y volver.\n"
            "Me han insistido mucho en que no me cuestione nada, incluso demasiado."
        )

        arcade.draw_text(
            texto_historia,
            self.window.width / 2,
            self.window.height / 2 - 100,
            arcade.color.GRAY,
            18,
            width=800,
            align="center",
            anchor_x="center",
            anchor_y="center",
            multiline=True,
            font_name="Arial"
        )