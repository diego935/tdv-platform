import arcade
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
        super().__init__(width=32, height=32, color=arcade.color.BLOOD_RED)
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