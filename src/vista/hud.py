import arcade

class HUD:
    def __init__(self):
        # Configuración de dimensiones
        self.ancho_barra = 200
        self.alto_barra = 20
        self.padding = 20
        self.slot_size = 50
        self.slot_margin = 10

    def draw(self, jugador):
        window = arcade.get_window()
        
        # --- 1. BARRAS DE ESTADO (Esquina Superior Izquierda) ---
        
        # Fondo Vida
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + self.ancho_barra/2, window.height - 30, self.ancho_barra, self.alto_barra),
            (50, 0, 0, 180)
        )
        # Barra Vida
        vida_ratio = max(0, jugador.vida) / 100
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.padding + (self.ancho_barra * vida_ratio)/2, window.height - 30, self.ancho_barra * vida_ratio, self.alto_barra),
            arcade.color.RED_DEVIL
        )

        # Barra Stamina (con lógica de color por cooldown)
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

        # --- 2. LOS 4 SLOTS SUPERIORES (Centrados arriba) ---
        
        total_width = (4 * self.slot_size) + (3 * self.slot_margin)
        start_x = (window.width - total_width) / 2 + (self.slot_size / 2)
        y_pos = window.height - 40

        for i in range(4):
            curr_x = start_x + (i * (self.slot_size + self.slot_margin))
            
            # ¿Es el slot seleccionado por el jugador (teclas 1-4)?
            es_activo = (i == jugador.indice_activo)
            
            slot_rect = arcade.rect.XYWH(curr_x, y_pos, self.slot_size, self.slot_size)
            
            # Fondo del slot
            arcade.draw_rect_filled(slot_rect, (20, 20, 20, 200))
            
            # Borde: Cian si está activo, gris si no
            color_borde = arcade.color.CYAN if es_activo else (200, 200, 200, 100)
            grosor = 3 if es_activo else 1
            arcade.draw_rect_outline(slot_rect, color_borde, border_width=grosor)
            
            # Indicador de número (tecla)
            arcade.draw_text(str(i+1), curr_x - 20, y_pos + 15, arcade.color.GRAY, font_size=7)

            # Dibujar el item si existe en ese índice del inventario
            if i < len(jugador.inventory) and jugador.inventory[i] is not None:
                item = jugador.inventory[i]
                # Importante: Usar draw_texture_rect para Arcade 3.x
                arcade.draw_texture_rect(
                    texture=item.texture,
                    rect=arcade.rect.XYWH(curr_x, y_pos, self.slot_size * 0.7, self.slot_size * 0.7)
                )
    def _dibujar_info_arma(self, jugador, window_width, window_height):
        """Dibuja la información del arma activa en la esquina inferior derecha."""
        # Obtener el arma activa
        arma = jugador.obtener_arma_activa()

        if arma is None:
            return

        # Posición base (esquina inferior derecha)
        info_x = window_width - self.padding
        info_y = self.padding + 60

        # Obtener información del arma
        info = arma.get_info_hud() if hasattr(arma, 'get_info_hud') else {}

        # Fondo del panel de arma
        panel_width = 180
        panel_height = 80
        arcade.draw_rect_filled(
            arcade.rect.XYWH(info_x - panel_width/2, info_y - panel_height/2, panel_width, panel_height),
            (20, 20, 20, 200)
        )

        # Nombre del arma
        arcade.draw_text(
            info.get('nombre', arma.name if hasattr(arma, 'name') else 'Arma'),
            info_x - panel_width + 10,
            info_y - 10,
            arcade.color.WHITE,
            font_size=14,
            bold=True
        )

        # Información de munición
        tipo = info.get('tipo', 'desconocido')
        if tipo == 'arma_fuego':
            municion_actual = info.get('municion_actual', 0)
            tamano_cargador = info.get('tamano_cargador', 0)
            esta_recargando = info.get('esta_recargando', False)

            if esta_recargando:
                # Mostrar barra de progreso de recarga
                recarga_progress = info.get('recarga_progress', 0)
                arcade.draw_text(
                    "RECARGANDO...",
                    info_x - panel_width + 10,
                    info_y - 35,
                    self.COLOR_RECARGANDO,
                    font_size=12
                )
                # Barra de progreso
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
                # Mostrar munición actual/cargador
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

                # Indicador de cooldown
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
            # Arma cuerpo a cuerpo - solo mostrar símbolo de infinito
            arcade.draw_text(
                "∞ Cuerpo a cuerpo",
                info_x - panel_width + 10,
                info_y - 35,
                arcade.color.LIGHT_GRAY,
                font_size=14
            )

            # Indicador de cooldown
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
