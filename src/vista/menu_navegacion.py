import arcade


class MenuNavegacion(arcade.View):
    """
    Clase base para vistas de menú con botón VOLVER común.
    Cada subclase define su destino al volver.
    """

    def __init__(self):
        super().__init__()
        self.destino_volver = None  # Override en subclase

    def _get_boton_volver_bounds(self):
        left = 20
        right = 200
        top = self.window.height - 20
        bottom = self.window.height - 80
        return left, right, bottom, top

    def _click_en_volver(self, x, y):
        left, right, bottom, top = self._get_boton_volver_bounds()
        return left <= x <= right and bottom <= y <= top

    def _destino_al_volver(self):
        from vista.menu_principal import MenuPrincipal
        return MenuPrincipal()

    def on_draw(self):
        self.clear()
        left, right, bottom, top = self._get_boton_volver_bounds()

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
            font_name="Times New Roman"
        )

    def on_mouse_press(self, x, y, button, modifiers):
        if self._click_en_volver(x, y):
            destino = self._destino_al_volver()
            if destino:
                self.window.show_view(destino)