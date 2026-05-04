import arcade

class VistaPartidas(arcade.View):
    def on_draw(self):
        self.clear()


    # BOTÓN VOLVER
        left = 20
        right = 200
        top = self.window.height - 20
        bottom = self.window.height - 80

        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            arcade.color.SMOKY_BLACK
        )

        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.RED, 3
        )

        arcade.draw_text(
            "VOLVER",
            (left + right) / 2,
            (bottom + top) / 2,
            arcade.color.GOLDENROD,
            25,
            anchor_x="center",
            anchor_y="center",
            font_name = "Times New Roman"
        )
        
        # TEXTO SUPERIOR
        arcade.draw_text(
            "OPCIONES DE PARTIDA", 
            self.window.width / 2, 
            self.window.height / 2 + 150, 
            arcade.color.GOLDENROD, 
            40, 
            anchor_x="center",
            font_name = "Georgia"
        )

        #BOTONES DE PARTIDAS
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
            arcade.draw_text(
                texto, 
                center_x, 
                y, 
                arcade.color.GOLDENROD, 
                25,
                anchor_x="center", 
                anchor_y="center", 
                font_name="Times New Roman"
            )

    def on_mouse_press(self, x, y, button, modifiers):

        left = 20
        right = 200
        top = self.window.height - 20
        bottom = self.window.height - 80

        if left <= x <= right and bottom <= y <= top:
            from menu import MenuPrincipal
            self.window.show_view(MenuPrincipal())