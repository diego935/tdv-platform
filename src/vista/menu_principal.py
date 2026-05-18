import arcade
from vista.vista_historia import VistaHistoria
from vista.vista_ajustes import VistaAjustes
from vista.vista_partidas import VistaPartidas
from vista.game import VistaJuego


class MenuPrincipal(arcade.View):

    def __init__(self):
        super().__init__()
        self.botones = []
        self.bg_texture = arcade.load_texture("assets/fondos/fondo_principal.png")
        arcade.load_font("assets/fuentes/fuente_menu_principal.ttf")


    def on_show_view(self):

        if not hasattr(self.window, "musica_menu"):

           self.window.musica_menu = arcade.load_sound("assets/musica/banda_sonora.mp3", streaming=True)

        if not hasattr(self.window, "player_musica"):

            self.window.player_musica = None

        self.reproducir_musica()

    def reproducir_musica(self):

        if self.window.player_musica is None:

            self.window.player_musica = self.window.musica_menu.play(volume=0.5, loop=True)

    def detener_musica(self):

        if self.window.player_musica is not None:

            arcade.stop_sound(self.window.player_musica)
            self.window.player_musica = None

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
        self.bg_texture,
        arcade.XYWH(
            self.window.width // 2,
            self.window.height // 2,
            self.window.width,
            self.window.height
        ))

        center_x = self.window.width / 2
        center_y = self.window.height / 2
        half_width = self.window.width * 0.30
        half_height = self.window.height * 0.06

        # Título
        arcade.draw_text(
            "PILL OF SILENCE",
            self.window.width / 2,
            self.window.height - 200,
            (170, 20, 20),
            130,
            anchor_x="center",
            font_name="Waruna"
        )

        # BOTÓN 1 (JUGAR)

        bottom1 = center_y + self.window.height * 0.02 - half_height
        top1 = center_y + self.window.height * 0.10 + half_height

    
        arcade.draw_lrbt_rectangle_filled(
            center_x - half_width,
            center_x + half_width,
            center_y + self.window.height * 0.02 - half_height,
            center_y + self.window.height * 0.10 + half_height,
            arcade.color.SMOKY_BLACK)

        arcade.draw_lrbt_rectangle_outline(center_x - half_width, center_x + half_width, bottom1, top1, arcade.color.VENETIAN_RED, 3)

        # BOTÓN 2 (HISTORIA)

        bottom2 = center_y - self.window.height * 0.16 - half_height
        top2 = center_y - self.window.height * 0.14 + half_height

        arcade.draw_lrbt_rectangle_filled(
            center_x - half_width,
            center_x + half_width,
            center_y - self.window.height * 0.16 - half_height,
            center_y - self.window.height * 0.14 + half_height,
            arcade.color.SMOKY_BLACK)

        arcade.draw_lrbt_rectangle_outline(center_x - half_width, center_x + half_width, bottom2, top2, arcade.color.VENETIAN_RED, 3)

        # BOTÓN 3 (AJUSTES)

        bottom3 = center_y - self.window.height * 0.35 - half_height
        top3 = center_y - self.window.height * 0.32 + half_height

        arcade.draw_lrbt_rectangle_filled(
            center_x - half_width,
            center_x + half_width,
            center_y - self.window.height * 0.35 - half_height,
            center_y - self.window.height * 0.32 + half_height,
            arcade.color.SMOKY_BLACK)

        arcade.draw_lrbt_rectangle_outline(center_x - half_width, center_x + half_width, bottom3, top3, arcade.color.VENETIAN_RED, 3)

        # BOTÓN (SALIR DEL JUEGO)
        salir_width = 160
        salir_height = 40
        margen = 25

        salir_left = self.window.width - salir_width - margen
        salir_right = self.window.width - margen
        salir_bottom = margen
        salir_top = margen + salir_height

        arcade.draw_lrbt_rectangle_filled(salir_left, salir_right, salir_bottom, salir_top, arcade.color.SMOKY_BLACK)
        arcade.draw_lrbt_rectangle_outline(salir_left, salir_right, salir_bottom, salir_top, arcade.color.VENETIAN_RED, 2)
        
        # TEXTO BOTÓN 1 (JUGAR)
        arcade.draw_text(
        "JUGAR",
        center_x,
        center_y + self.window.height * 0.06,
        arcade.color.GOLDENROD,
        font_size=50,
        anchor_x="center",
        anchor_y="center",
        font_name="Times New Roman")

        # TEXTO BOTÓN HISTORIA
        arcade.draw_text(
        "HISTORIA",
        center_x,
        center_y - self.window.height * 0.15,
        arcade.color.GOLDENROD,
        font_size=30,
        anchor_x="center",
        anchor_y="center",
        font_name="Times New Roman")

        # TEXTO BOTÓN CONTROLES
        arcade.draw_text(
        "CONTROLES",
        center_x,
        center_y - self.window.height * 0.335,
        arcade.color.GOLDENROD,
        font_size=30,
        anchor_x="center",
        anchor_y="center",
        font_name="Times New Roman")

        # TEXTO BOTÓN SALIR
        arcade.draw_text(
        "SALIR DEL JUEGO",
        (salir_left + salir_right) / 2,
        (salir_bottom + salir_top) / 2,
        arcade.color.GOLDENROD,
        font_size=14,
        anchor_x="center",
        anchor_y="center",
        font_name="Times New Roman")

    def on_mouse_press(self, x, y, button, modifiers):
        center_x = self.window.width / 2
        center_y = self.window.height / 2
        half_width = self.window.width * 0.30
        half_height = self.window.height * 0.06

        # BOTÓN JUGAR -> VA A VISTA PARTIDAS
        left = center_x - half_width
        right = center_x + half_width
        bottom = center_y + self.window.height * 0.02 - half_height
        top = center_y + self.window.height * 0.10 + half_height

        if left <= x <= right and bottom <= y <= top:
            vista_partidas = VistaPartidas()
            self.window.show_view(vista_partidas)
            return

        # BOTÓN HISTORIA
        bottom = center_y - self.window.height * 0.16 - half_height
        top = center_y - self.window.height * 0.14 + half_height

        if left <= x <= right and bottom <= y <= top:
            self.window.show_view(VistaHistoria())
            return

        # BOTÓN AJUSTES
        bottom = center_y - self.window.height * 0.35 - half_height
        top = center_y - self.window.height * 0.32 + half_height

        if left <= x <= right and bottom <= y <= top:
            self.window.show_view(VistaAjustes())
            return
        
        # BOTÓN SALIR
        salir_width = 160
        salir_height = 40
        margen = 25

        salir_left = self.window.width - salir_width - margen
        salir_right = self.window.width - margen
        salir_bottom = margen
        salir_top = margen + salir_height

        if salir_left <= x <= salir_right and salir_bottom <= y <= salir_top:
            arcade.exit()
            return