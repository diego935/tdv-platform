import arcade
from vista.menu_navegacion import MenuNavegacion
from vista.game import VistaJuego
from utils.save_system import hay_partida_guardada


class VistaPartidas(MenuNavegacion):
    def on_draw(self):
        super().on_draw()

        arcade.draw_text(
            "SELECCIÓN DE PARTIDA", 
            self.window.width / 2, 
            self.window.height / 2 + 220, 
            arcade.color.GOLDENROD, 
            40, 
            anchor_x="center",
            font_name="Georgia"
        )

        boton_width = 500 
        boton_height = 110
        center_x = self.window.width / 2
        
        y_nueva = self.window.height / 2 + 80
        y_seguir = self.window.height / 2 - 80

        hay_guardado = hay_partida_guardada()

        for y, texto in [(y_nueva, "NUEVA PARTIDA"), (y_seguir, "CONTINUAR PARTIDA")]:
            left_btn = center_x - boton_width / 2
            right_btn = center_x + boton_width / 2
            bottom_btn = y - boton_height / 2
            top_btn = y + boton_height / 2

            arcade.draw_lrbt_rectangle_filled(left_btn, right_btn, bottom_btn, top_btn, arcade.color.SMOKY_BLACK)
            arcade.draw_lrbt_rectangle_outline(left_btn, right_btn, bottom_btn, top_btn, arcade.color.RED, 3)
            
            color_texto = arcade.color.GOLDENROD if (texto == "NUEVA PARTIDA" or hay_guardado) else arcade.color.GRAY
            arcade.draw_text(
                texto, 
                center_x, 
                y, 
                color_texto, 
                28,
                anchor_x="center", 
                anchor_y="center", 
                font_name="Times New Roman"
            )

    def on_mouse_press(self, x, y, button, modifiers):
        if self._click_en_volver(x, y):
            super().on_mouse_press(x, y, button, modifiers)
            return

        boton_width = 400
        boton_height = 80
        center_x = self.window.width / 2
        y_nueva = self.window.height / 2 + 60

        left_btn = center_x - boton_width / 2
        right_btn = center_x + boton_width / 2
        bottom_btn = y_nueva - boton_height / 2
        top_btn = y_nueva + boton_height / 2

        if left_btn <= x <= right_btn and bottom_btn <= y <= top_btn:
            if self.window.player_musica is not None:
                arcade.stop_sound(self.window.player_musica)
                self.window.player_musica = None

            vista_juego = VistaJuego()
            vista_juego.setup(load_saved=False)
            self.window.show_view(vista_juego)
            return

        y_seguir = self.window.height / 2 - 60
        bottom_btn = y_seguir - boton_height / 2
        top_btn = y_seguir + boton_height / 2
        
        if left_btn <= x <= right_btn and bottom_btn <= y <= top_btn:
            if not hay_partida_guardada():
                return

            if self.window.player_musica is not None:
                arcade.stop_sound(self.window.player_musica)
                self.window.player_musica = None

            vista_juego = VistaJuego()
            vista_juego.setup(load_saved=True)
            self.window.show_view(vista_juego)
