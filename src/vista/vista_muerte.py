import arcade
import time

class VistaGameOver(arcade.View):

    def __init__(self):
        super().__init__()
        self.bg_texture = arcade.load_texture("assets/fondos/fondo_muerte.png")
        self.fondo = arcade.load_font("assets/fuentes/Melted Monster.ttf")
        self.sonido_muerte = arcade.load_sound("assets/sonidos/muerte_personaje.wav")
        self.tiempo_inicio = time.time()
        self.audio_reproducido = False

    def on_update(self, delta_time: float):
        """Este método se encarga de revisar el reloj real de tu ordenador."""
        if not self.audio_reproducido:
            tiempo_actual = time.time()
            if tiempo_actual - self.tiempo_inicio >= 1.5:
                if self.sonido_muerte:
                    arcade.play_sound(self.sonido_muerte)
                self.audio_reproducido = True

    def on_draw(self):

        self.clear()
        self.window.dispatch_event('on_update', 1/60)
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
    
    def on_show_view(self):
        """Se ejecuta automáticamente justo cuando esta pantalla se vuelve activa."""
        self.window.ctx.sound_stream_player.volume = 1.0
        arcade.schedule(self.reproducir_audio, 1.5)

    def reproducir_audio(self, delta_time: float):
        """Función que activa el sonido y se desprograma automáticamente."""
        if self.sonido_muerte:
            arcade.play_sound(self.sonido_muerte)
        arcade.unschedule(self.reproducir_audio)

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