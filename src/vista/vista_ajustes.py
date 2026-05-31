import arcade
from vista.menu_navegacion import MenuNavegacion


class VistaAjustes(MenuNavegacion):
    def __init__(self):
        super().__init__()
        self.bg_texture = arcade.load_texture("assets/fondos/controles.png")

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
            texture=self.bg_texture,
            rect=arcade.XYWH(
                self.window.width // 2,
                self.window.height // 2,
                self.window.width,
                self.window.height
            )
        )

        self.dibujar_boton_volver()

        arcade.draw_text(
            "CONTROLES DEL JUEGO", 
            self.window.width / 2, 
            self.window.height - 80,
            arcade.color.GOLDENROD, 
            40, 
            anchor_x="center",
            font_name="Georgia"
        )