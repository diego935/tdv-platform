import arcade
from vista.menu_navegacion import MenuNavegacion
from vista.menu import VistaJuego


class VistaPartidas(MenuNavegacion):
    def on_draw(self):
        super().on_draw()

        # TEXTO SUPERIOR
        arcade.draw_text(
            "SELECCION DE PARTIDA", 
            self.window.width / 2, 
            self.window.height / 2 + 150, 
            arcade.color.GOLDENROD, 
            40, 
            anchor_x="center",
            font_name="Georgia"
        )

        # BOTONES DE PARTIDAS
        boton_width = 400
        boton_height = 80
        center_x = self.window.width / 2
        y_nueva = self.window.height / 2 + 60
        y_seguir = self.window.height / 2 - 60

        for y, texto in [(y_nueva, "NUEVA PARTIDA"), (y_seguir, "CONTINUAR PARTIDA")]:
            left_btn = center_x - boton_width / 2
            right_btn = center_x + boton_width / 2
            bottom_btn = y - boton_height / 2
            top_btn = y + boton_height / 2

            arcade.draw_lrbt_rectangle_filled(left_btn, right_btn, bottom_btn, top_btn, arcade.color.SMOKY_BLACK)
            arcade.draw_lrbt_rectangle_outline(left_btn, right_btn, bottom_btn, top_btn, arcade.color.RED, 3)
            
            color_texto = arcade.color.GOLDENROD if texto == "NUEVA PARTIDA" else arcade.color.GRAY
            arcade.draw_text(
                texto, 
                center_x, 
                y, 
                color_texto, 
                25,
                anchor_x="center", 
                anchor_y="center", 
                font_name="Times New Roman"
            )

    def on_mouse_press(self, x, y, button, modifiers):
        # Check boton VOLVER primero
        if self._click_en_volver(x, y):
            super().on_mouse_press(x, y, button, modifiers)
            return

        # Check botones de partida
        boton_width = 400
        boton_height = 80
        center_x = self.window.width / 2
        y_nueva = self.window.height / 2 + 60

        left_btn = center_x - boton_width / 2
        right_btn = center_x + boton_width / 2
        bottom_btn = y_nueva - boton_height / 2
        top_btn = y_nueva + boton_height / 2

        # NUEVA PARTIDA -> VA A VISTA JUEGO
        if left_btn <= x <= right_btn and bottom_btn <= y <= top_btn:
            vista_juego = VistaJuego()
            vista_juego.setup()
            self.window.show_view(vista_juego)
            return

        # CONTINUAR PARTIDA (deshabilitado de momento)
        y_seguir = self.window.height / 2 - 60
        bottom_btn = y_seguir - boton_height / 2
        top_btn = y_seguir + boton_height / 2
        
        if left_btn <= x <= right_btn and bottom_btn <= y <= top_btn:
            # TODO: Implementar carga de partidas guardadas
            pass