import arcade


class VistaGameOver(arcade.View):

    def __init__(self):
        super().__init__()
        self.bg_texture = arcade.load_texture("assets/fondos/fondo_muerte.png")
        self.fondo = arcade.load_font("assets/fuentes/Melted Monster.ttf")

    def on_draw(self):

        self.clear()

        arcade.draw_texture_rect(
            self.bg_texture,
            arcade.XYWH(
                self.window.width // 2,
                self.window.height // 2,
                self.window.width,
                self.window.height
            )
        )

        arcade.draw_text(
            "HAS MUERTO",
            self.window.width / 2,
            self.window.height / 2 + 80,
            arcade.color.BARN_RED,
            100,
            anchor_x="center",
            anchor_y="center",
            font_name= "Melted Monster",
            bold=True
        )

        boton_width = 600
        boton_height = 80

        center_x = self.window.width / 2
        center_y = 90

        left_btn = center_x - boton_width / 2
        right_btn = center_x + boton_width / 2
        bottom_btn = center_y - boton_height / 2
        top_btn = center_y + boton_height / 2

        arcade.draw_lrbt_rectangle_filled(
            left_btn,
            right_btn,
            bottom_btn,
            top_btn,
            arcade.color.SMOKY_BLACK
        )

        arcade.draw_lrbt_rectangle_outline(
            left_btn,
            right_btn,
            bottom_btn,
            top_btn,
            arcade.color.RED,
            3
        )

        arcade.draw_text(
            "VOLVER AL MENU PRINCIPAL",
            center_x,
            center_y,
            arcade.color.GOLDENROD,
            24,
            anchor_x="center",
            anchor_y="center",
            font_name="Times New Roman"
        )

    def on_mouse_press(self, x, y, button, modifiers):

        boton_width = 600
        boton_height = 80

        center_x = self.window.width / 2
        center_y = 90

        left_btn = center_x - boton_width / 2
        right_btn = center_x + boton_width / 2
        bottom_btn = center_y - boton_height / 2
        top_btn = center_y + boton_height / 2

        if left_btn <= x <= right_btn and bottom_btn <= y <= top_btn:

            from vista.menu_principal import MenuPrincipal

            self.window.show_view(MenuPrincipal())