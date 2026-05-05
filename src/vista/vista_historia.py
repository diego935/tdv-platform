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

        # TODO: Añadir texto de historia cuando esté definido
        arcade.draw_text(
            "(Pendiente de implementar)",
            self.window.width / 2,
            self.window.height / 2 - 50,
            arcade.color.GRAY,
            20,
            anchor_x="center"
        )