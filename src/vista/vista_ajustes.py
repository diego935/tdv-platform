import arcade
from vista.menu_navegacion import MenuNavegacion


class VistaAjustes(MenuNavegacion):
    def on_draw(self):
        super().on_draw()

        arcade.draw_text(
            "AJUSTES", 
            self.window.width / 2, 
            self.window.height / 2 + 100,
            arcade.color.GOLDENROD, 
            50, 
            anchor_x="center",
            font_name="Georgia"
        )

        # TODO: Añadir opciones de ajustes cuando estén definidas
        arcade.draw_text(
            "(Pendiente de implementar)",
            self.window.width / 2,
            self.window.height / 2 - 50,
            arcade.color.GRAY,
            20,
            anchor_x="center"
        )