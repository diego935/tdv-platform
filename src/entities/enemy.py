import arcade
import random
import math
from entities.pathfinding import SistemaNavegacion


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


class Enemigo(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(width=32, height=32, color=arcade.color.RED)
        self.vida = 50
        self.pos_origen = None
        self.pos_destino = None
        self.ruta = []
        self.velocidad = 2
        self.vista = 500
        self.nav = SistemaNavegacion()


    def establecer_ruta(self, destino, nav_manager):
        self.pos_origen = self.position
        self.pos_destino = destino
        self.ruta = nav_manager.obtener_ruta(self.pos_origen, self.pos_destino)

    def check_jugador_en_vista(self, jugador):
        distancia = arcade.get_distance_between_sprites(self, jugador)
        if distancia > self.vista:
            return False

        return self.nav.tiene_linea_de_vision(self.position, jugador.position)

    def move(self):
        if not self.ruta:
            return

        destino_x, destino_y = self.ruta[0]
        
        if self.center_x < destino_x:
            self.change_x = self.velocidad
        elif self.center_x > destino_x:
            self.change_x = -self.velocidad
        else:
            self.change_x = 0

        if self.center_y < destino_y:
            self.change_y = self.velocidad
        elif self.center_y > destino_y:
            self.change_y = -self.velocidad
        else:
            self.change_y = 0

        distancia = arcade.get_distance(self.center_x, self.center_y, destino_x, destino_y)
        if distancia < 5:
            self.ruta.pop(0)
            if not self.ruta:
                self.change_x = 0
                self.change_y = 0


# ==================== ENEMIGO IA ====================

class EnemigoIA(arcade.SpriteSolidColor):
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
        velocidad: float = 80,
        velocidad_patrulla: float = 40,
        vista_rango: float = 300,
        tiempo_buscar: float = 3.0,
        tiempo_esperar: float = 1.0,
        tipo_ataque: str = "melee",
        dano_ataque: float = 10.0,
        rango_ataque: float = 40.0,
        tiempo_cortesia: float = 4.0
    ):
        super().__init__(width=32, height=32, color=arcade.color.RED)
        self.center_x = x
        self.center_y = y
        self.vida = 100

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

    def _check_transiciones(self, player, blocks_list, nav_manager):
        """Transiciones entre estados de la FSM."""

        if self._knockback_timer > 0:
            return

        puede_ver = self.puede_ver_player(player)
        
        # Actualizar timer de cortesía
        if puede_ver:
            self._timer_cortesia = self.tiempo_cortesia
            self._tiene_vista = True
        elif self._timer_cortesia > 0:
            self._timer_cortesia -= 1/60
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
                self.ultima_pos_player = self.ultima_pos_player or (
                    self.center_x, self.center_y
                )
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
        if hasattr(player, 'vida'):
            player.vida -= self.dano_ataque
            self._timer_ataque = self.tiempo_entre_ataques
            
            # Feedback visual
            print(f"Enemigo ataca! Daño: {self.dano_ataque}, Vida player: {player.vida}")

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
            self.ruta = nav_manager.encontrar_ruta(
                self.position,
                self.waypoint_actual
            ) or []

        self._mover_por_ruta(self.velocidad_patrulla)

    def _update_patrulla_area(self, delta_time, nav_manager):
        """Patrulla aleatoria dentro de un área."""
        if self._llegado_a_waypoint_aux(self.waypoint_actual):
            nuevo_punto = self._generar_punto_area()
            self.waypoint_actual = nuevo_punto
            self.ruta = nav_manager.encontrar_ruta(
                self.position,
                self.waypoint_actual
            ) or []

        self._mover_por_ruta(self.velocidad_patrulla)

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
            siguiente = self._encontrar_siguiente_punto_pared()
            self.waypoint_actual = siguiente
            self.ruta = nav_manager.encontrar_ruta(
                self.position,
                self.waypoint_actual
            ) or []

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
            self.ruta_actual = nav_manager.encontrar_ruta(
                self.position,
                destino
            ) or []

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
            punto_origen = self.pos_origen
            self.ruta = nav_manager.encontrar_ruta(
                self.position,
                punto_origen
            ) or []

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

        if nav_manager is None:
            nav_manager = self.nav
        if blocks_list is None:
            blocks_list = []

        # Manejar knockback
        if self._knockback_timer > 0:
            self._knockback_timer -= delta_time
            self.center_x += self._knockback_vel[0] * delta_time
            self.center_y += self._knockback_vel[1] * delta_time
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

        self._check_transiciones(player, blocks_list, nav_manager)

        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

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
            self.kill()