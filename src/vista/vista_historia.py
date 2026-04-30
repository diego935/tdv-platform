import arcade

class VistaHistoria(arcade.View):

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "HISTORIA", 400, 300,
            arcade.color.WHITE, 40,
            anchor_x="center"
        )

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

    def on_mouse_press(self, x, y, button, modifiers):

        left = 20
        right = 200
        top = self.window.height - 20
        bottom = self.window.height - 80

        if left <= x <= right and bottom <= y <= top:
            from menu import MenuPrincipal
            self.window.show_view(MenuPrincipal())