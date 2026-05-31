import arcade
import random
import math
from utils.log import Log
from entities.pathfinding import SistemaNavegacion
from items.weapons import Proyectil, ObjetivoProyectil
from vista.asset_manager import AssetManager
from dialog.quest_manager import EB



class DummyEnemy(arcade.SpriteSolidColor):
    def __init__(self, x=0, y=0):
        super().__init__(width=32, height=32, color=arcade.color.GREEN)
        self.center_x = x
        self.center_y = y
        self.vida = 100
        self._knockback_vel = (0, 0)
        self._knockback_timer = 0.0
        self._base_x = x
        self._base_y = y

    def recibir_dano(self, cantidad, fuente_x=None, fuente_y=None):
        self.vida -= cantidad
        if fuente_x is not None and fuente_y is not None:
            dx = self.center_x - fuente_x
            dy = self.center_y - fuente_y
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                self._knockback_vel = (dx/dist * 100, dy/dist * 100)
                self._knockback_timer = 0.15
                self._base_x = self.center_x
                self._base_y = self.center_y
        if self.vida <= 0:
            self.kill()

    def on_update(self, delta_time=1/60):
        super().on_update(delta_time)
        if self._knockback_timer > 0:
            self._knockback_timer -= delta_time
            self.center_x += self._knockback_vel[0] * delta_time
            self.center_y += self._knockback_vel[1] * delta_time
        else:
            self._base_x = self.center_x
            self._base_y = self.center_y


class EnemigoIA(arcade.Sprite):
    """
    Enemigo con FSM de IA y 3 tipos de patrulla:
    - WAYPOINT_FIJO: patrulla entre puntos fijos
    - AREA_ALEATORIA: movimiento aleatorio dentro de un área
    - PAREDES: sigue las paredes del mapa
    """

    # Tipos de patrulla
    TIPO_WAYPOINT = "waypoint"
    TIPO_AREA = "area"
    TIPO_PAREDES = "paredes"

    # Estados de IA
    ESTADO_PATRULLAR = "patrullar"
    ESTADO_PERSEGUIR = "perseguir"
    ESTADO_BUSCAR = "buscar"
    ESTADO_RETURN = "return"
    ESTADO_ESPERAR = "esperar"

    def __init__(
        self,
        x: float,
        y: float,
        tipo_patrulla: str = TIPO_WAYPOINT,
        waypoints: list = None,
        area_center: tuple = None,
        area_radio: float = 100,
        velocidad: float = 320,
        velocidad_patrulla: float = 120,
        vista_rango: float = 32*25,
        tiempo_buscar: float = 3.0,
        tiempo_esperar: float = 1.0,
        tipo_ataque: str = "melee",
        dano_ataque: float = 10.0,
        rango_ataque: float = 40.0,
        tiempo_cortesia: float = 4.0
    ):
        super().__init__()


        assets = AssetManager()
        self.texture_up = assets.get_texture("assets/Enemigo/enemigo hacia arribaEscalado.png")
        self.texture_down = assets.get_texture("assets/Enemigo/enemigo hacia abajoEscalado.png")
        self.texture_left = assets.get_texture("assets/Enemigo/enemigo hacia izquierdaEscalado.png")
        self.texture_right = assets.get_texture("assets/Enemigo/enemigo hacia derechaEscalado.png")

        self.texture = self.texture_down

        self.scale = 0.3
        self.center_x = x
        self.center_y = y
        self.vida = 100
        self.enemy_id = "bandido"

        self.tipo_patrulla = tipo_patrulla

        self.waypoints = waypoints or [(x, y)]
        self._indice_waypoint = 0
        self.waypoint_actual = self.waypoints[0] if self.waypoints else (x, y)

        self.area_center = area_center or (x, y)
        self.area_radio = area_radio

        self.velocidad = velocidad
        self.velocidad_patrulla = velocidad_patrulla

        self.vista_rango = vista_rango
        self.tiempo_buscar = tiempo_buscar
        self.tiempo_esperar = tiempo_esperar
        
        # Sistema de ataque
        self.tipo_ataque = tipo_ataque
        self.dano_ataque = dano_ataque
        self.rango_ataque = rango_ataque
        self.tiempo_entre_ataques = 1.0
        self._timer_ataque = 0.0
        
        # Timer de cortesía (persigue aunque no vea al player)
        self.tiempo_cortesia = tiempo_cortesia
        self._timer_cortesia = 0.0
        self._tiene_vista = False

        self.nav = SistemaNavegacion()

        self.estado = self.ESTADO_PATRULLAR
        self.ultima_pos_player = None
        self.tiempo_busqueda = 0.0
        self.tiempo_espera = 0.0

        self.pos_origen = (x, y)
        self.ruta = []
        self.ruta_actual = []

        self._knockback_vel = (0, 0)
        self._knockback_timer = 0.0
        self._base_x = x
        self._base_y = y
        self._timer_recalculo_ruta = 0.0

        self.sonido_ataque = arcade.load_sound("assets/sonidos/sonido_enemigo.wav")

    def on_draw(self):
        super().on_draw()
        
        # Texto de estado
        color_texto = {
            self.ESTADO_PATRULLAR: arcade.color.GREEN,
            self.ESTADO_PERSEGUIR: arcade.color.RED,
            self.ESTADO_BUSCAR: arcade.color.YELLOW,
            self.ESTADO_RETURN: arcade.color.CYAN,
            self.ESTADO_ESPERAR: arcade.color.MAGENTA
        }.get(self.estado, arcade.color.WHITE)
        
        arcade.draw_text(
            self.estado.upper(),
            self.center_x,
            self.center_y + 25,
            color_texto,
            font_size=8,
            anchor_x="center"
        )
        
        # Mostrar tipo de ataque
        if self.tipo_ataque == "melee" and self._timer_ataque <= 0:
            color = arcade.color.RED
        elif self.tipo_ataque == "melee":
            color = arcade.color.GRAY
        else:
            color = arcade.color.WHITE
            
        arcade.draw_text(
            f"⚔{int(self.dano_ataque)}",
            self.center_x,
            self.center_y - 25,
            color,
            font_size=10,
            anchor_x="center"
        )

    def puede_ver_player(self, player) -> bool:
        """Check si el enemigo puede ver al player."""
        if player is None:
            return False

        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        distancia = math.sqrt(dx*dx + dy*dy)

        if distancia > self.vista_rango:
            return False

        if distancia > 0:
            tiene_vision = self.nav.tiene_linea_de_vision(
                self.position,
                player.position
            )
            return tiene_vision

        return True

    def _check_transiciones(self, player, blocks_list, nav_manager, deltatime):
        """Transiciones entre estados de la FSM."""

        if self._knockback_timer > 0:
            return

        puede_ver = self.puede_ver_player(player)
        
        # Actualizar timer de cortesía
        if puede_ver:
            self._timer_cortesia = self.tiempo_cortesia
            self._tiene_vista = True
        elif self._timer_cortesia > 0:
            self._timer_cortesia -= deltatime
            puede_ver = True  # Durante cortesía, sigue persiguiendo
        
        # Check distancia para ataque melee
        if player and self._puede_atacar(player):
            self._atacar(player)
            return

        if self.estado == self.ESTADO_PATRULLAR:
            if puede_ver:
                self.ultima_pos_player = (player.center_x, player.center_y)
                self.cambiar_estado(self.ESTADO_PERSEGUIR)

        elif self.estado == self.ESTADO_PERSEGUIR:
            if not puede_ver and self._timer_cortesia <= 0:
                if self.ultima_pos_player is None:
                    self.ultima_pos_player = (player.center_x, player.center_y)
                self.cambiar_estado(self.ESTADO_BUSCAR)
                self.tiempo_busqueda = 0.0
            elif self._llegado_a_destino(player.position, blocks_list):
                self.ultima_pos_player = (player.center_x, player.center_y)

        elif self.estado == self.ESTADO_BUSCAR:
            if puede_ver:
                self.cambiar_estado(self.ESTADO_PERSEGUIR)
            else:
                self.tiempo_busqueda += 1/60
                if self.tiempo_busqueda >= self.tiempo_buscar:
                    self.cambiar_estado(self.ESTADO_RETURN)

        elif self.estado == self.ESTADO_RETURN:
            if self._llegado_a_waypoint():
                self.cambiar_estado(self.ESTADO_ESPERAR)
                self.tiempo_espera = 0.0
            if puede_ver:
                self.cambiar_estado(self.ESTADO_PERSEGUIR)

        elif self.estado == self.ESTADO_ESPERAR:
            self.tiempo_espera += 1/60
            if self.tiempo_espera >= self.tiempo_esperar:
                self.cambiar_estado(self.ESTADO_PATRULLAR)
            if puede_ver:
                self.cambiar_estado(self.ESTADO_PERSEGUIR)
        
        # Update timer de ataque
        if self._timer_ataque > 0:
            self._timer_ataque -= 1/60

    def _puede_atacar(self, player) -> bool:
        """Check si puede atacar al player."""
        if self._timer_ataque > 0:
            return False
        
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        distancia = math.sqrt(dx*dx + dy*dy)
        
        return distancia <= self.rango_ataque
    
    def _atacar(self, player):
        """Realiza el ataque al player."""
        ataque_exitoso = False
        if hasattr(player, 'recibir_dano'):
            player.recibir_dano(self.dano_ataque, self.center_x, self.center_y)
            ataque_exitoso = True
            self._timer_ataque = self.tiempo_entre_ataques
            Log.debug("Enemigo", "Atacando jugador (recibir_dano)", dano=self.dano_ataque, vida_player=player.vida, tipo=self.tipo_ataque if hasattr(self, 'tipo_ataque') else 'unknown')
        elif hasattr(player, 'vida'):
            player.vida -= self.dano_ataque
            ataque_exitoso = True
            self._timer_ataque = self.tiempo_entre_ataques
            Log.debug("Enemigo", "Atacando jugador (vida directa)", dano=self.dano_ataque, vida_player=player.vida, tipo=self.tipo_ataque if hasattr(self, 'tipo_ataque') else 'unknown')
        if ataque_exitoso:
            self._timer_ataque = self.tiempo_entre_ataques
            if self.sonido_ataque:
                arcade.play_sound(self.sonido_ataque, volume=0.3)

    def _llegado_a_destino(self, destino, blocks_list, tolerancia: float = 10) -> bool:
        """Check si llegó a posición destino."""
        dx = self.center_x - destino[0]
        dy = self.center_y - destino[1]
        return math.sqrt(dx*dx + dy*dy) < tolerancia

    def _llegado_a_waypoint(self, tolerancia: float = 10) -> bool:
        """Check si llegó al waypoint actual."""
        return self._llegado_a_waypoint_aux(self.waypoint_actual, tolerancia)

    def _llegado_a_waypoint_aux(self, waypoint, tolerancia: float = 10) -> bool:
        """Helper para check waypoint."""
        if waypoint is None:
            return False
        if self.center_x is None or self.center_y is None:
            return False
        dx = self.center_x - waypoint[0]
        dy = self.center_y - waypoint[1]
        return math.sqrt(dx*dx + dy*dy) < tolerancia

    def cambiar_estado(self, nuevo_estado):
        """Cambia de estado."""
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            
            if nuevo_estado == self.ESTADO_BUSCAR:
                self.ruta_actual = []
            elif nuevo_estado == self.ESTADO_RETURN:
                self.ruta = []

    def _update_patrullar(self, delta_time, blocks_list, nav_manager):
        """Update del estado PATRULLAR."""

        if self.tipo_patrulla == self.TIPO_WAYPOINT:
            self._update_patrulla_waypoint(nav_manager)
        elif self.tipo_patrulla == self.TIPO_AREA:
            self._update_patrulla_area(delta_time, nav_manager)
        elif self.tipo_patrulla == self.TIPO_PAREDES:
            self._update_patrulla_paredes(delta_time, nav_manager)

    def _update_patrulla_waypoint(self, nav_manager):
        """Patrulla entre waypoints."""
        if not self.waypoints:
            return

        if self._llegado_a_waypoint():
            self._indice_waypoint = (self._indice_waypoint + 1) % len(self.waypoints)
            self.waypoint_actual = self.waypoints[self._indice_waypoint]

        if not self.ruta or self._llegado_a_waypoint():
            if self._timer_recalculo_ruta <= 0:
                self.ruta = nav_manager.encontrar_ruta(
                    self.position,
                    self.waypoint_actual
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta else random.uniform(0.3, 0.6)

        self._mover_por_ruta(self.velocidad_patrulla)

    def _update_patrulla_area(self, delta_time, nav_manager):
        """Patrulla aleatoria dentro de un área."""
        if self._llegado_a_waypoint_aux(self.waypoint_actual):
            self.waypoint_actual = self._generar_punto_area()
        
        dx = self.waypoint_actual[0] - self.center_x
        dy = self.waypoint_actual[1] - self.center_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            self.change_x = (dx / dist) * self.velocidad_patrulla
            self.change_y = (dy / dist) * self.velocidad_patrulla
        else:
            self.change_x = 0
            self.change_y = 0

    def _generar_punto_area(self) -> tuple:
        """Genera punto aleatorio dentro del área."""
        cx, cy = self.area_center
        r = self.area_radio

        while True:
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(0, r)
            x = cx + math.cos(angulo) * distancia
            y = cy + math.sin(angulo) * distancia
            return (x, y)

    def _update_patrulla_paredes(self, delta_time, nav_manager):
        """Patrulla siguiendo paredes."""
        if not self.ruta or self._llegado_a_waypoint_aux(self.waypoint_actual):
            if self._timer_recalculo_ruta <= 0:
                siguiente = self._encontrar_siguiente_punto_pared()
                self.waypoint_actual = siguiente
                self.ruta = nav_manager.encontrar_ruta(
                    self.position,
                    self.waypoint_actual
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta else random.uniform(0.3, 0.6)

        self._mover_por_ruta(self.velocidad_patrulla)

    def _encontrar_siguiente_punto_pared(self) -> tuple:
        """Encuentra siguiente punto en parede."""
        cx, cy = self.center_x, self.center_y

        offsets = [
            (32, 0), (-32, 0), (0, 32), (0, -32),
            (64, 0), (-64, 0), (0, 64), (0, -64),
            (96, 0), (-96, 0), (0, 96), (0, -96)
        ]

        for dx, dy in offsets:
            testeado = (cx + dx, cy + dy)
            nodo = self.nav.grafo.grid.get(
                self.nav.grafo._mundo_a_grid(testeado[0], testeado[1])
            )
            if nodo and nodo.transitable:
                return testeado

        return self.pos_origen

    def _update_perseguir(self, delta_time, player, blocks_list, nav_manager):
        """Update del estado PERSEGUIR."""
        if player is None:
            return

        destino = (player.center_x, player.center_y)

        if not self.ruta_actual or self._llegado_a_destino(destino, blocks_list):
            if self._timer_recalculo_ruta <= 0:
                self.ruta_actual = nav_manager.encontrar_ruta(
                    self.position,
                    destino
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta_actual else random.uniform(0.3, 0.6)

        self._mover_por_ruta(self.velocidad)

    def _update_buscar(self, delta_time, blocks_list, nav_manager):
        """Update del estado BUSCAR."""
        if not self.ultima_pos_player:
            self.cambiar_estado(self.ESTADO_RETURN)
            return

        if not self.ruta_actual or self._llegado_a_destino(self.ultima_pos_player, blocks_list):
            self.cambiar_estado(self.ESTADO_RETURN)
            return

        self._mover_por_ruta(self.velocidad_patrulla)

    def _update_return(self, delta_time, blocks_list, nav_manager):
        """Update del estado RETURN."""
        if self._llegado_a_waypoint():
            self.ruta = []
            return

        if not self.ruta:
            if self._timer_recalculo_ruta <= 0:
                punto_origen = self.pos_origen
                self.ruta = nav_manager.encontrar_ruta(
                    self.position,
                    punto_origen
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta else random.uniform(0.3, 0.6)

        self._mover_por_ruta(self.velocidad_patrulla)

    def _mover_por_ruta(self, velocidad):
        """Mueve al enemigo por la ruta actual."""
        if not self.ruta and not self.ruta_actual:
            self.change_x = 0
            self.change_y = 0
            return

        ruta = self.ruta_actual or self.ruta

        try:
            destino_x, destino_y = ruta[0]
        except (IndexError, TypeError):
            self.change_x = 0
            self.change_y = 0
            return

        dx = destino_x - self.center_x
        dy = destino_y - self.center_y
        distancia = math.sqrt(dx*dx + dy*dy)

        if distancia > 0:
            self.change_x = (dx / distancia) * velocidad
            self.change_y = (dy / distancia) * velocidad
        else:
            self.change_x = 0
            self.change_y = 0

        if distancia < 10:
            if self.ruta_actual:
                self.ruta_actual.pop(0)
            elif self.ruta:
                self.ruta.pop(0)

    def update(self, delta_time, player, blocks_list=None, nav_manager=None):
        """Update principal del enemigo IA."""
        if hasattr(self, '_timer_recalculo_ruta') and self._timer_recalculo_ruta > 0:
            self._timer_recalculo_ruta -= delta_time

        if nav_manager is None:
            nav_manager = self.nav
        if blocks_list is None:
            blocks_list = []

        # Manejar knockback con colisiones
        if self._knockback_timer > 0:
            self._knockback_timer -= delta_time
            old_x = self.center_x
            self.center_x += self._knockback_vel[0] * delta_time
            if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
                self.center_x = old_x
            
            old_y = self.center_y
            self.center_y += self._knockback_vel[1] * delta_time
            if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
                self.center_y = old_y
            return

        # FSM
        if self.estado == self.ESTADO_PATRULLAR:
            self._update_patrullar(delta_time, blocks_list, nav_manager)
        elif self.estado == self.ESTADO_PERSEGUIR:
            self._update_perseguir(delta_time, player, blocks_list, nav_manager)
        elif self.estado == self.ESTADO_BUSCAR:
            self._update_buscar(delta_time, blocks_list, nav_manager)
        elif self.estado == self.ESTADO_RETURN:
            self._update_return(delta_time, blocks_list, nav_manager)

        self._check_transiciones(player, blocks_list, nav_manager, delta_time)

        # Mover y resolver colisiones eje por eje
        old_x = self.center_x
        self.center_x += self.change_x * delta_time
        if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
            self.center_x = old_x

        old_y = self.center_y
        self.center_y += self.change_y * delta_time
        if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
            self.center_y = old_y

        if abs(self.change_x) > abs(self.change_y):

            if self.change_x > 0:
                self.texture = self.texture_right

            elif self.change_x < 0:
                self.texture = self.texture_left

        else:

            if self.change_y > 0:
                self.texture = self.texture_up

            elif self.change_y < 0:
                self.texture = self.texture_down

    def recibir_dano(self, cantidad: float, fuente_x: float = None, fuente_y: float = None):
        """Recibe daño del player."""
        self.vida -= cantidad
        if fuente_x is not None and fuente_y is not None:
            dx = self.center_x - fuente_x
            dy = self.center_y - fuente_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                self._knockback_vel = (dx/dist * 100, dy/dist * 100)
                self._knockback_timer = 0.15
                self._base_x = self.center_x
                self._base_y = self.center_y
        if self.vida <= 0:
            self._publicar_muerte()
            self.kill()

    def _publicar_muerte(self) -> None:
        """Publica evento de muerte para el sistema de misiones."""
        try:
            EB.publish("enemy_killed", {"enemy_id": self.enemy_id})
        except Exception:
            pass


# ==================== ENEMIGO RANGED ====================

class EnemigoRanged(EnemigoIA):
    """Enemigo que mantiene distancia y ataca a distancia con proyectiles."""
    
    ESTADO_MANTENER_DISTANCIA = "mantener_distancia"
    
    def __init__(
        self,
        x: float,
        y: float,
        radio_R: float = 450,
        radio_r: float = 200,
        intervalo_ataque: float = 2.0,
        velocidad_proyectil: float = 400,
        inteligencia: bool = False,
        offset_prediccion: float = 50,
        tipo_patrulla: str = EnemigoIA.TIPO_WAYPOINT,
        waypoints: list = None,
        area_center: tuple = None,
        area_radio: float = 100,
        velocidad: float = 300,
        velocidad_patrulla: float = 100,
        vista_rango: float = 32 * 25,
        tiempo_buscar: float = 3.0,
        tiempo_esperar: float = 1.0,
        dano_ataque: float = 5.0,
        rango_ataque: float = 300,
        tiempo_cortesia: float = 4.0
    ):
        super().__init__(
            x=x, y=y,
            tipo_patrulla=tipo_patrulla,
            waypoints=waypoints,
            area_center=area_center,
            area_radio=area_radio,
            velocidad=velocidad,
            velocidad_patrulla=velocidad_patrulla,
            vista_rango=vista_rango,
            tiempo_buscar=tiempo_buscar,
            tiempo_esperar=tiempo_esperar,
            tipo_ataque="ranged",
            dano_ataque=dano_ataque,
            rango_ataque=rango_ataque,
            tiempo_cortesia=tiempo_cortesia
        )
        
        self.radio_R = radio_R
        self.radio_r = radio_r
        self.radio_R_sq = radio_R * radio_R
        self.radio_r_sq = radio_r * radio_r
        self.intervalo_ataque = intervalo_ataque
        self.velocidad_proyectil = velocidad_proyectil
        self.inteligencia = inteligencia
        self.offset_prediccion = offset_prediccion
        
        self._timer_ataque_ranged = 0.0
        self._player_velocidad_buffer = [0, 0]
        self._direccion_lateral = 1  # 1 o -1 para cambiar de lado
    
    def _get_comando_distancia(self, player) -> str:
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        dist_sq = dx * dx + dy * dy
        
        if dist_sq > self.radio_R_sq:
            return "avanzar"
        elif dist_sq < self.radio_r_sq:
            return "retroceder"
        return "mantener"
    
    def _actualizar_buffer_player(self, player, delta_time):
        self._player_velocidad_buffer[0] = player.change_x
        self._player_velocidad_buffer[1] = player.change_y
    
    def _calcular_posicion_ataque(self, player) -> tuple:
        if self.inteligencia:
            pred_x = player.center_x + player.change_x * self.offset_prediccion
            pred_y = player.center_y + player.change_y * self.offset_prediccion
            return pred_x, pred_y
        return player.center_x, player.center_y
    
    def _mover_hacia_posicion(self, target_x, target_y, nav_manager, delta_time):
        if not self.ruta_actual or self._llegado_a_destino((target_x, target_y), [], tolerancia=50):
            if self._timer_recalculo_ruta <= 0:
                self.ruta_actual = nav_manager.encontrar_ruta(
                    self.position,
                    (target_x, target_y)
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta_actual else random.uniform(0.3, 0.6)

        if self.ruta_actual:
            try:
                dest_x, dest_y = self.ruta_actual[0]
                dx = dest_x - self.center_x
                dy = dest_y - self.center_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 5:
                    self.change_x = (dx / dist) * self.velocidad
                    self.change_y = (dy / dist) * self.velocidad
                else:
                    self.ruta_actual.pop(0)
                    self.change_x = 0
                    self.change_y = 0
            except (IndexError, TypeError):
                self.change_x = 0
                self.change_y = 0
        else:
            self.change_x = 0
            self.change_y = 0

    def _alejar_de_player(self, player, blocks_list, nav_manager, delta_time):
        target_x = self.center_x * 2 - player.center_x
        target_y = self.center_y * 2 - player.center_y

        if not self.ruta_actual:
            if self._timer_recalculo_ruta <= 0:
                self.ruta_actual = nav_manager.encontrar_ruta(
                    self.position,
                    (target_x, target_y)
                ) or []
                self._timer_recalculo_ruta = random.uniform(0.1, 0.2) if self.ruta_actual else random.uniform(0.3, 0.6)

        if self.ruta_actual:
            try:
                dest_x, dest_y = self.ruta_actual[0]
                dx = dest_x - self.center_x
                dy = dest_y - self.center_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 5:
                    self.change_x = (dx / dist) * self.velocidad
                    self.change_y = (dy / dist) * self.velocidad
                else:
                    self.ruta_actual.pop(0)
            except (IndexError, TypeError):
                self.change_x = 0
                self.change_y = 0
        else:
            dx = self.center_x - player.center_x
            dy = self.center_y - player.center_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.change_x = (dx / dist) * self.velocidad
                self.change_y = (dy / dist) * self.velocidad
    
    def _atacar_ranged(self, player, proyectiles_list):
        target_x, target_y = self._calcular_posicion_ataque(player)
        
        angle = math.degrees(math.atan2(
            target_y - self.center_y,
            target_x - self.center_x
        ))
        
        proyectil = Proyectil(
            x=self.center_x,
            y=self.center_y,
            angle=angle,
            damage=self.dano_ataque,
            velocidad=self.velocidad_proyectil,
            objetivo=ObjetivoProyectil.PLAYER
        )
        
        proyectiles_list.append(proyectil)
        self._timer_ataque_ranged = self.intervalo_ataque
        
        Log.debug("EnemigoRanged", "Proyectil lanzado",
                  dano=self.dano_ataque,
                  objetivo="PLAYER",
                  velocidad=self.velocidad_proyectil)
    
    def _puede_atacar_ranged(self, player) -> bool:
        if self._timer_ataque_ranged > 0:
            return False
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        rango_sq = self.rango_ataque * self.rango_ataque
        return (dx * dx + dy * dy) <= rango_sq
    
    def _update_mantener_distancia(self, player, blocks_list, nav_manager, delta_time):
        comando = self._get_comando_distancia(player)
        
        if comando == "avanzar":
            self._mover_hacia_posicion(player.center_x, player.center_y, nav_manager, delta_time)
        elif comando == "retroceder":
            self._alejar_de_player(player, blocks_list, nav_manager, delta_time)
        else:
            # En rango correcto: moverse lateralmente alrededor del player
            dx = player.center_x - self.center_x
            dy = player.center_y - self.center_y
            
            # Vector perpendicular para movimiento lateral
            perp_x = -dy
            perp_y = dx
            dist = math.sqrt(perp_x * perp_x + perp_y * perp_y)
            
            if dist > 0:
                # Moverse en dirección perpendicular (más lento que el normal)
                velocidad_lateral = self.velocidad * 0.5
                self.change_x = (perp_x / dist) * velocidad_lateral * self._direccion_lateral
                self.change_y = (perp_y / dist) * velocidad_lateral * self._direccion_lateral
                
                # Cambiar dirección ocasionalmente para no ser predecible
                if random.random() < 0.01:  # 1% de probabilidad por frame
                    self._direccion_lateral *= -1
    
    def _check_transiciones_ranged(self, player, blocks_list, nav_manager, deltatime):
        puede_ver = self.puede_ver_player(player)
        
        if puede_ver:
            self._timer_cortesia = self.tiempo_cortesia
            self._tiene_vista = True
        elif self._timer_cortesia > 0:
            self._timer_cortesia -= deltatime
            puede_ver = True
        
        if player and self._puede_atacar_ranged(player):
            self._atacar_ranged(player, getattr(self, '_proyectiles_list', []))
        
        if self.estado == self.ESTADO_PATRULLAR:
            if puede_ver:
                self.ultima_pos_player = (player.center_x, player.center_y)
                self.cambiar_estado(self.ESTADO_MANTENER_DISTANCIA)
        
        elif self.estado == self.ESTADO_MANTENER_DISTANCIA:
            if not puede_ver and self._timer_cortesia <= 0:
                if self.ultima_pos_player is None:
                    self.ultima_pos_player = (player.center_x, player.center_y)
                self.cambiar_estado(self.ESTADO_BUSCAR)
        
        elif self.estado == self.ESTADO_BUSCAR:
            if puede_ver:
                self.cambiar_estado(self.ESTADO_MANTENER_DISTANCIA)
            else:
                self.tiempo_busqueda += deltatime
                if self.tiempo_busqueda >= self.tiempo_buscar:
                    self.cambiar_estado(self.ESTADO_RETURN)
        
        elif self.estado == self.ESTADO_RETURN:
            if self._llegado_a_waypoint():
                self.cambiar_estado(self.ESTADO_ESPERAR)
                self.tiempo_espera = 0.0
            if puede_ver:
                self.cambiar_estado(self.ESTADO_MANTENER_DISTANCIA)
        
        elif self.estado == self.ESTADO_ESPERAR:
            self.tiempo_espera += deltatime
            if self.tiempo_espera >= self.tiempo_esperar:
                self.cambiar_estado(self.ESTADO_PATRULLAR)
            if puede_ver:
                self.cambiar_estado(self.ESTADO_MANTENER_DISTANCIA)
        
        if self._timer_ataque_ranged > 0:
            self._timer_ataque_ranged -= deltatime
    
    def update(self, delta_time, player, blocks_list=None, nav_manager=None, proyectiles_list=None):
        if hasattr(self, '_timer_recalculo_ruta') and self._timer_recalculo_ruta > 0:
            self._timer_recalculo_ruta -= delta_time

        if proyectiles_list is None:
            proyectiles_list = []
        self._proyectiles_list = proyectiles_list
        
        if nav_manager is None:
            nav_manager = self.nav
        if blocks_list is None:
            blocks_list = []
        
        if self._knockback_timer > 0:
            self._knockback_timer -= delta_time
            old_x = self.center_x
            self.center_x += self._knockback_vel[0] * delta_time
            if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
                self.center_x = old_x
            
            old_y = self.center_y
            self.center_y += self._knockback_vel[1] * delta_time
            if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
                self.center_y = old_y
            return
        
        self._actualizar_buffer_player(player, delta_time)
        
        if self.estado == self.ESTADO_PATRULLAR:
            self._update_patrullar(delta_time, blocks_list, nav_manager)
        elif self.estado == self.ESTADO_MANTENER_DISTANCIA:
            self._update_mantener_distancia(player, blocks_list, nav_manager, delta_time)
        elif self.estado == self.ESTADO_BUSCAR:
            self._update_buscar(delta_time, blocks_list, nav_manager)
        elif self.estado == self.ESTADO_RETURN:
            self._update_return(delta_time, blocks_list, nav_manager)
        
        self._check_transiciones_ranged(player, blocks_list, nav_manager, delta_time)
        
        # Mover y resolver colisiones eje por eje
        old_x = self.center_x
        self.center_x += self.change_x * delta_time
        if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
            self.center_x = old_x

        old_y = self.center_y
        self.center_y += self.change_y * delta_time
        if blocks_list and arcade.check_for_collision_with_list(self, blocks_list):
            self.center_y = old_y
        
        if abs(self.change_x) > abs(self.change_y):
            self.texture = self.texture_right if self.change_x > 0 else self.texture_left
        else:
            self.texture = self.texture_up if self.change_y > 0 else self.texture_down
