import arcade


class HUD:
    def __init__(self):
        self.ancho_barra = 200
        self.alto_barra = 20
        self.padding = 20
        self.slot_size = 50
        self.slot_margin = 10

        self.COLOR_MUNICION = arcade.color.WHITE
        self.COLOR_RECARGANDO = arcade.color.ORANGE
        self.COLOR_COOLDOWN = arcade.color.GRAY

    def draw(self, jugador):
        window = arcade.get_window()

        if window is None:
            return

        self._dibujar_barras_estado(jugador, window)
        self._dibujar_slots(jugador, window)
        self._dibujar_info_arma(jugador, window.width, window.height)

    def _dibujar_barras_estado(self, jugador, window):
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + self.ancho_barra/2, window.height - 30, self.ancho_barra, self.alto_barra),
            (50, 0, 0, 180)
        )
        vida_ratio = max(0, jugador.vida) / 100
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + (self.ancho_barra * vida_ratio)/2, window.height - 30, self.ancho_barra * vida_ratio, self.alto_barra),
            arcade.color.RED_DEVIL
        )

        color_stamina = arcade.color.APPLE_GREEN
        if jugador.stamina_cooldown_timer > 0:
            color_stamina = arcade.color.GRAY if jugador.stamina > 0 else arcade.color.BITTER_LEMON

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + self.ancho_barra/2, window.height - 55, self.ancho_barra, self.alto_barra / 2),
            (30, 30, 30, 180)
        )
        stamina_ratio = jugador.stamina / 100
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + (self.ancho_barra * stamina_ratio)/2, window.height - 55, self.ancho_barra * stamina_ratio, self.alto_barra / 2),
            color_stamina
        )

    def _dibujar_slots(self, jugador, window):
        total_width = (4 * self.slot_size) + (3 * self.slot_margin)
        start_x = (window.width - total_width) / 2 + (self.slot_size / 2)
        y_pos = window.height - 40

        for i in range(4):
            curr_x = start_x + (i * (self.slot_size + self.slot_margin))

            es_activo = (i == jugador.indice_activo)

            slot_rect = arcade.rect.XYWH(curr_x, y_pos, self.slot_size, self.slot_size)

            arcade.draw_rect_filled(slot_rect, (20, 20, 20, 200))

            color_borde = arcade.color.CYAN if es_activo else (200, 200, 200, 100)
            grosor = 3 if es_activo else 1
            arcade.draw_rect_outline(slot_rect, color_borde, border_width=grosor)

            arcade.draw_text(str(i+1), curr_x - 20, y_pos + 15, arcade.color.GRAY, font_size=7)

            if i < len(jugador.inventory) and jugador.inventory[i] is not None:
                item = jugador.inventory[i]
                if hasattr(item, 'texture') and item.texture is not None:
                    arcade.draw_texture_rect(
                        texture=item.texture,
                        rect=arcade.rect.XYWH(curr_x, y_pos, self.slot_size * 0.7, self.slot_size * 0.7)
                    )

    def _dibujar_info_arma(self, jugador, window_width, window_height):
        arma = jugador.obtener_arma_activa()

        if arma is None:
            return

        info_x = window_width - self.padding
        info_y = self.padding + 60

        info = arma.get_info_hud() if hasattr(arma, 'get_info_hud') else {}

        panel_width = 180
        panel_height = 80
        arcade.draw_rect_filled(
            arcade.rect.XYWH(info_x - panel_width/2, info_y - panel_height/2, panel_width, panel_height),
            (20, 20, 20, 200)
        )

        arcade.draw_text(
            info.get('nombre', arma.name if hasattr(arma, 'name') else 'Arma'),
            info_x - panel_width + 10,
            info_y - 10,
            arcade.color.WHITE,
            font_size=14,
            bold=True
        )

        tipo = info.get('tipo', 'desconocido')
        if tipo == 'arma_fuego':
            municion_actual = info.get('municion_actual', 0)
            tamano_cargador = info.get('tamano_cargador', 0)
            esta_recargando = info.get('esta_recargando', False)

            if esta_recargando:
                recarga_progress = info.get('recarga_progress', 0)
                arcade.draw_text(
                    "RECARGANDO...",
                    info_x - panel_width + 10,
                    info_y - 35,
                    self.COLOR_RECARGANDO,
                    font_size=12
                )
                barra_width = 140
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(info_x - panel_width/2, info_y - 55, barra_width, 10),
                    (50, 50, 50, 180)
                )
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        info_x - panel_width/2 - barra_width/2 + (barra_width * recarga_progress)/2,
                        info_y - 55,
                        barra_width * recarga_progress,
                        10
                    ),
                    self.COLOR_RECARGANDO
                )
            else:
                color_municion = self.COLOR_MUNICION
                if municion_actual == 0:
                    color_municion = arcade.color.RED
                elif municion_actual <= tamano_cargador // 4:
                    color_municion = arcade.color.YELLOW

                texto_municion = f"{municion_actual}/{tamano_cargador}"
                arcade.draw_text(
                    texto_municion,
                    info_x - panel_width + 10,
                    info_y - 35,
                    color_municion,
                    font_size=16,
                    bold=True
                )

                cooldown_progress = info.get('cooldown_progress', 0)
                if cooldown_progress < 1.0:
                    barra_width = 140
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(info_x - panel_width/2, info_y - 55, barra_width, 6),
                        (50, 50, 50, 180)
                    )
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(
                            info_x - panel_width/2 - barra_width/2 + (barra_width * cooldown_progress)/2,
                            info_y - 55,
                            barra_width * cooldown_progress,
                            6
                        ),
                        self.COLOR_COOLDOWN
                    )

        elif tipo == 'arma_melee':
            arcade.draw_text(
                "∞ Cuerpo a cuerpo",
                info_x - panel_width + 10,
                info_y - 35,
                arcade.color.LIGHT_GRAY,
                font_size=14
            )

            cooldown_progress = info.get('cooldown_progress', 0)
            if cooldown_progress < 1.0:
                barra_width = 140
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(info_x - panel_width/2, info_y - 55, barra_width, 6),
                    (50, 50, 50, 180)
                )
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        info_x - panel_width/2 - barra_width/2 + (barra_width * cooldown_progress)/2,
                        info_y - 55,
                        barra_width * cooldown_progress,
                        6
                    ),
                    self.COLOR_COOLDOWN
                )