"""
Sistema de armas del juego.
Las armas son items que pueden equiparse y usarse.
"""
import math
import arcade
from abc import abstractmethod
from items.items import BaseItem


# ==================== PROYECTIL ====================

class Proyectil:
    """Proyectil para armas de fuego."""

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        velocidad: float = 600.0,
        lifetime: float = 2.0,
        radio: float = 6.0
    ):
        self.center_x = x
        self.center_y = y
        self.angle = angle
        self.damage = damage
        self.velocidad = velocidad
        self.lifetime = lifetime
        self.radio = radio
        self._timer = 0.0
        self.alive = True

        self._vx = math.cos(math.radians(angle)) * velocidad
        self._vy = math.sin(math.radians(angle)) * velocidad

    def draw(self):
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radio, arcade.color.RED
        )

    def update(self, delta_time, blocks_list=None, enemies_list=None):
        self.center_x += self._vx * delta_time
        self.center_y += self._vy * delta_time
        self._timer += delta_time

        if blocks_list:
            for block in blocks_list:
                if self._check_collision(block):
                    self.alive = False
                    break

        if enemies_list:
            for enemy in enemies_list:
                if self._check_collision(enemy):
                    if hasattr(enemy, 'recibir_dano'):
                        enemy.recibir_dano(self.damage, self.center_x, self.center_y)
                    elif hasattr(enemy, 'vida'):
                        enemy.vida -= self.damage
                    self.alive = False
                    break

        if self._timer >= self.lifetime:
            self.alive = False

    def _check_collision(self, other) -> bool:
        if not hasattr(other, 'center_x') or not hasattr(other, 'center_y'):
            return False
        if not hasattr(other, 'width') or not hasattr(other, 'height'):
            return False
        dx = abs(self.center_x - other.center_x)
        dy = abs(self.center_y - other.center_y)
        return dx < (self.radio + other.width / 2) and dy < (self.radio + other.height / 2)

    @property
    def killed(self):
        return not self.alive


# ==================== WEAPON BASE ====================

class WeaponBase(BaseItem):
    """Clase base para todas las armas."""

    def __init__(
        self,
        item_id: int,
        nombre: str,
        sprite_path: str,
        damage: int,
        cooldown: float,
        rango: float,
        descripcion: str = "",
        **kwargs
    ):
        super().__init__(item_id, nombre, sprite_path, descripcion, **kwargs)

        self.damage = damage
        self.cooldown = cooldown
        self.rango = rango
        self._timer_cooldown = 0.0
        self.esta_recargando = False

    @property
    def puede_usar(self) -> bool:
        return self._timer_cooldown <= 0 and not self.esta_recargando

    @property
    def cooldown_progress(self) -> float:
        if self.cooldown <= 0:
            return 0.0
        return min(1.0, max(0.0, 1.0 - (self._timer_cooldown / self.cooldown)))

    def actualizar(self, delta_time: float):
        if self._timer_cooldown > 0:
            self._timer_cooldown -= delta_time
            if self._timer_cooldown < 0:
                self._timer_cooldown = 0

    def iniciar_cooldown(self):
        self._timer_cooldown = self.cooldown

    @abstractmethod
    def usar(self, owner, target_x: float, target_y: float, proyectiles_list) -> bool:
        pass

    @abstractmethod
    def recargar(self) -> bool:
        pass

    def get_info_hud(self) -> dict:
        return {
            'nombre': self.name,
            'damage': self.damage,
            'puede_usar': self.puede_usar,
            'cooldown_progress': self.cooldown_progress,
            'esta_recargando': self.esta_recargando,
        }


# ==================== PISTOLA ====================

class Pistola(WeaponBase):
    """Pistola semi-automática."""

    def __init__(self):
        super().__init__(
            item_id=100,
            nombre="Pistola",
            sprite_path="../assets/items/Pistola.jpg",
            damage=25,
            cooldown=0.4,
            rango=800.0,
            descripcion="Pistola semi-automática básica."
        )

        self.tamano_cargador = 12
        self.municion_actual = self.tamano_cargador
        self.municion_total = float('inf')
        self._tiempo_recarga = 1.5
        self._timer_recarga = 0.0
        self.velocidad_proyectil = 600.0
        self.lifetime_proyectil = 2.0

    @property
    def puede_usar(self) -> bool:
        return (self._timer_cooldown <= 0 and not self.esta_recargando and self.municion_actual > 0)

    def usar(self, owner, target_x, target_y, proyectiles_list) -> bool:
        if not self.puede_usar:
            return False

        angle_rad = math.atan2(target_y - owner.center_y, target_x - owner.center_x)
        angle_deg = math.degrees(angle_rad)

        proyectil = Proyectil(
            x=owner.center_x,
            y=owner.center_y,
            angle=angle_deg,
            damage=self.damage,
            velocidad=self.velocidad_proyectil,
            lifetime=self.lifetime_proyectil
        )

        proyectiles_list.append(proyectil)
        self.municion_actual -= 1
        self.iniciar_cooldown()
        return True

    def recargar(self) -> bool:
        if self.esta_recargando:
            return False
        if self.municion_actual >= self.tamano_cargador:
            return False

        self.esta_recargando = True
        self._timer_recarga = self._tiempo_recarga
        return True

    def actualizar(self, delta_time: float):
        super().actualizar(delta_time)

        if self.esta_recargando:
            self._timer_recarga -= delta_time
            if self._timer_recarga <= 0:
                self._completar_recarga()

    def _completar_recarga(self):
        """Completa la recarga llenando el cargador."""
        self.municion_actual = self.tamano_cargador
        self.esta_recargando = False
        self._timer_recarga = 0.0

    def _get_recarga_progress(self) -> float:
        """Retorna el progreso de recarga (0.0 a 1.0)."""
        if not self.esta_recargando or self._tiempo_recarga <= 0:
            return 0.0
        return 1.0 - (self._timer_recarga / self._tiempo_recarga)

    def get_info_hud(self) -> dict:
        info = super().get_info_hud()
        info.update({
            'tipo': 'arma_fuego',
            'municion_actual': self.municion_actual,
            'tamano_cargador': self.tamano_cargador,
            'municion_total': '∞',
            'esta_recargando': self.esta_recargando,
            'recarga_progress': self._get_recarga_progress(),
        })
        return info


# ==================== HITBOX TEMPORAL ====================

class HitboxTemporal(arcade.SpriteSolidColor):
    """Hitbox temporal para ataques cuerpo a cuerpo."""

    def __init__(
        self,
        owner,
        angle: float,
        offset_dist: float = 40.0,
        width: float = 60.0,
        height: float = 40.0,
        damage: int = 40,
        lifetime: float = 0.15,
        arc_angle: float = 90.0
    ):
        super().__init__(
            width=int(width),
            height=int(height),
            color=(255, 255, 255, 200)
        )

        self.owner = owner
        self.damage = damage
        self.lifetime = lifetime
        self._timer = 0.0
        self.angle = angle
        self.arc_angle = arc_angle
        self.offset_dist = offset_dist
        self._enemies_hit = set()
        self.alive = True

        self._actualizar_posicion()

    def draw(self):
        pass

    def update_enemies(self, enemies_list):
        """Check collision with enemies"""
        if not enemies_list:
            return
        for enemy in enemies_list:
            self.verificar_colision(enemy)

    def _actualizar_posicion(self):
        if self.owner:
            angle_rad = math.radians(self.angle)
            self.center_x = self.owner.center_x + math.cos(angle_rad) * self.offset_dist
            self.center_y = self.owner.center_y + math.sin(angle_rad) * self.offset_dist

    def on_update(self, delta_time: float = 1/60):
        self._actualizar_posicion()
        self._timer += delta_time
        if self._timer >= self.lifetime:
            self.alive = False

    @property
    def killed(self):
        return not self.alive

    def verificar_colision(self, enemy) -> bool:
        enemy_id = id(enemy)
        if enemy_id in self._enemies_hit:
            return False

        if not self.collides_with_sprite(enemy):
            return False

        dx = enemy.center_x - self.owner.center_x
        dy = enemy.center_y - self.owner.center_y
        angle_to_enemy = math.degrees(math.atan2(dy, dx))
        angle_diff = (angle_to_enemy - self.angle + 180) % 360 - 180

        if abs(angle_diff) <= self.arc_angle / 2:
            self._aplicar_daño(enemy)
            self._enemies_hit.add(enemy_id)
            return True
        return False

    def _aplicar_daño(self, enemy):
        if hasattr(enemy, 'recibir_dano'):
            enemy.recibir_dano(self.damage, self.owner.center_x, self.owner.center_y)
        elif hasattr(enemy, 'vida'):
            enemy.vida -= self.damage


# ==================== CUCHILLO ====================

class Cuchillo(WeaponBase):
    """Cuchillo para ataques cuerpo a cuerpo."""

    def __init__(self):
        super().__init__(
            item_id=101,
            nombre="Cuchillo",
            sprite_path="../assets/items/Cuchillo.jpg",
            damage=40,
            cooldown=0.6,
            rango=80.0,
            descripcion="Cuchillo afilado."
        )

        self.offset_dist = 45.0
        self.hitbox_width = 70.0
        self.hitbox_height = 50.0
        self.lifetime_hitbox = 0.15
        self.arc_angle = 120.0

    def usar(self, owner, target_x, target_y, proyectiles_list) -> bool:
        if not self.puede_usar:
            return False

        angle_rad = math.atan2(target_y - owner.center_y, target_x - owner.center_x)
        angle_deg = math.degrees(angle_rad)

        hitbox = HitboxTemporal(
            owner=owner,
            angle=angle_deg,
            offset_dist=self.offset_dist,
            width=self.hitbox_width,
            height=self.hitbox_height,
            damage=self.damage,
            lifetime=self.lifetime_hitbox,
            arc_angle=self.arc_angle
        )

        proyectiles_list.append(hitbox)
        self.iniciar_cooldown()
        return True

    def recargar(self) -> bool:
        return False

    def get_info_hud(self) -> dict:
        info = super().get_info_hud()
        info.update({
            'tipo': 'arma_melee',
            'municion_actual': '∞',
            'tamano_cargador': '-',
            'municion_total': '-',
        })
        return info