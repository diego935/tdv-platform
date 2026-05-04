import arcade
import math
from vista.asset_manager import AssetManager
from abc import abstractmethod



class BaseItem(arcade.Sprite):
    def __init__(self, item_id, name, sprite_path, description="", durability=100.0):
        texture = AssetManager().get_texture(sprite_path)
        super().__init__(texture, scale=0.5)

        self.id = item_id 
        self.name = name
        self.description = description
        self.durability = durability
        
        self.quantity = 1
        self.max_stack = 1       # Por defecto no se apilan
        self.weight = 1.0        # Para sistemas de carga
        self.is_usable = True    # ¿Se puede clickear para 'Usar'?
        
        self.is_dropped = False  # Si está por ahí tirado se puede recoger 
        




class Proyectil(arcade.SpriteSolidColor):
    """
    Representa un proyectil (bala) disparado por un arma.
    Se mueve en línea recta y colisiona con enemigos y bloques.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        velocidad: float = 600.0,
        lifetime: float = 2.0,
        radio: float = 4.0
    ):
        """
        Inicializa el proyectil.

        Args:
            x: Posición inicial X
            y: Posición inicial Y
            angle: Ángulo de movimiento (grados)
            damage: Daño del proyectil
            velocidad: Velocidad en píxeles/segundo
            lifetime: Tiempo de vida en segundos
            radio: Radio del proyectil para colisiones
        """
        # Usar SpriteSolidColor con color amarillo/naranja
        size = int(radio * 2)
        super().__init__(
            width=size,
            height=size,
            color=arcade.color.YELLOW_ORANGE
        )

        self.center_x = x
        self.center_y = y
        self.angle = angle
        self.damage = damage
        self.velocidad = velocidad
        self.lifetime = lifetime
        self._timer = 0.0

        # Calcular vector de movimiento
        self._vx = math.cos(math.radians(angle)) * velocidad
        self._vy = math.sin(math.radians(angle)) * velocidad

    def on_update(self, delta_time: float = 1/60):
        """
        Actualiza la posición del proyectil.

        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        # Mover el proyectil
        self.center_x += self._vx * delta_time
        self.center_y += self._vy * delta_time

        # Actualizar timer de vida
        self._timer += delta_time
        if self._timer >= self.lifetime:
            self.kill()

    def on_collision_with_enemy(self, enemy):
        """
        Llamado cuando el proyectil colisiona con un enemigo.

        Args:
            enemy: El enemigo con el que colisionó
        """
        # Aplicar daño
        if hasattr(enemy, 'recibir_dano'):
            enemy.recibir_dano(self.damage)
        elif hasattr(enemy, 'vida'):
            enemy.vida -= self.damage

        # Destruir el proyectil
        self.kill()

    def on_collision_with_block(self, block):
        """
        Llamado cuando el proyectil colisiona con un bloque.

        Args:
            block: El bloque con el que colisionó
        """
        # Destruir el proyectil al impactar bloques
        self.kill()

class WeaponBase(BaseItem):
    """
    Clase base para todas las armas del juego.
    Hereda de BaseItem para ser un item recogible/equipable.
    """

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
        """
        Inicializa el arma como un item.

        Args:
            item_id: ID del item
            nombre: Nombre del arma
            sprite_path: Ruta del sprite
            damage: Daño por ataque
            cooldown: Tiempo entre ataques (segundos)
            rango: Alcance del arma
            descripcion: Descripción del arma
        """
        super().__init__(item_id, nombre, sprite_path, descripcion, **kwargs)

        # Propiedades de arma
        self.damage = damage
        self.cooldown = cooldown
        self.rango = rango

        # Estado del cooldown
        self._timer_cooldown = 0.0
        self.esta_recargando = False

    @property
    def puede_usar(self) -> bool:
        """Retorna True si el arma puede usarse (cooldown terminado y no recargando)."""
        return self._timer_cooldown <= 0 and not self.esta_recargando

    @property
    def cooldown_progress(self) -> float:
        """Retorna el progreso del cooldown (0.0 a 1.0)."""
        if self.cooldown <= 0:
            return 0.0
        return min(1.0, max(0.0, 1.0 - (self._timer_cooldown / self.cooldown)))

    def actualizar(self, delta_time: float):
        """
        Actualiza el cooldown del arma.

        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        if self._timer_cooldown > 0:
            self._timer_cooldown -= delta_time
            if self._timer_cooldown < 0:
                self._timer_cooldown = 0

    def iniciar_cooldown(self):
        """Inicia el cooldown del arma."""
        self._timer_cooldown = self.cooldown

    @abstractmethod
    def usar(self, owner, target_x: float, target_y: float, proyectiles_list) -> bool:
        """
        Usa el arma.

        Args:
            owner: Entidad que usa el arma (normalmente el jugador)
            target_x: Posición X del objetivo
            target_y: Posición Y del objetivo
            proyectiles_list: Lista donde añadir proyectiles/hitboxes

        Returns:
            bool: True si se usó correctamente
        """
        pass

    @abstractmethod
    def recargar(self) -> bool:
        """
        Recarga el arma (si aplica).

        Returns:
            bool: True si se inició la recarga
        """
        pass

    def get_info_hud(self) -> dict:
        """
        Retorna información para mostrar en el HUD.

        Returns:
            dict: Información del arma (munición, estado, etc.)
        """
        return {
            'nombre': self.name,  # BaseItem guarda como 'name', no 'nombre'
            'damage': self.damage,
            'puede_usar': self.puede_usar,
            'cooldown_progress': self.cooldown_progress,
            'esta_recargando': self.esta_recargando,
        }

class Cuchillo(WeaponBase):
    """
    Cuchillo para ataques cuerpo a cuerpo.
    Crea un hitbox temporal en arco frente al jugador.
    """

    def __init__(self):
        """Inicializa el cuchillo con sus estadísticas."""
        super().__init__(
            item_id=101,
            nombre="Cuchillo",
            sprite_path="../assets/items/Cuchillo.jpg",
            damage=40,
            cooldown=0.6,
            rango=80.0,
            descripcion="Cuchillo afilado. Alto daño cuerpo a cuerpo, sin necesidad de munición."
        )

        # Configuración del hitbox
        self.offset_dist = 45.0  # Distancia desde el jugador
        self.hitbox_width = 70.0
        self.hitbox_height = 50.0
        self.lifetime_hitbox = 0.15  # Duración del hitbox
        self.arc_angle = 120.0  # Ángulo del arco de ataque

    def usar(self, owner, target_x: float, target_y: float, hitboxes_list) -> bool:
        """
        Crea un hitbox temporal para el ataque cuerpo a cuerpo.

        Args:
            owner: Entidad que ataca (jugador)
            target_x: Posición X del ratón (para dirección)
            target_y: Posición Y del ratón (para dirección)
            hitboxes_list: Lista donde añadir el hitbox

        Returns:
            bool: True si se creó el hitbox correctamente
        """
        if not self.puede_usar:
            return False

        # Calcular ángulo hacia el target
        angle_rad = math.atan2(target_y - owner.center_y, target_x - owner.center_x)
        angle_deg = math.degrees(angle_rad)

        # Crear hitbox temporal
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

        # Añadir a la lista de hitboxes
        hitboxes_list.append(hitbox)

        # Iniciar cooldown
        self.iniciar_cooldown()

        return True

    def recargar(self) -> bool:
        """
        El cuchillo no necesita recarga.

        Returns:
            bool: Siempre False
        """
        return False

    def get_info_hud(self) -> dict:
        """
        Retorna información específica del cuchillo para el HUD.

        Returns:
            dict: Información del arma cuerpo a cuerpo
        """
        info = super().get_info_hud()
        info.update({
            'tipo': 'arma_melee',
            'municion_actual': '∞',
            'tamano_cargador': '-',
            'municion_total': '-',
        })
        return info
class HitboxTemporal(arcade.SpriteSolidColor):
    """
    Hitbox que existe por un tiempo muy corto para detectar
    colisiones en ataques cuerpo a cuerpo.
    """

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
        """
        Inicializa el hitbox temporal.

        Args:
            owner: Entidad que creó el hitbox (jugador)
            angle: Ángulo de dirección del ataque (grados)
            offset_dist: Distancia desde el owner al centro del hitbox
            width: Ancho del área de impacto
            height: Alto del área de impacto
            damage: Daño del ataque
            lifetime: Tiempo de vida del hitbox
            arc_angle: Ángulo del arco de ataque (grados)
        """
        # Crear hitbox con color semi-transparente para debug (invisible en producción)
        super().__init__(
            width=int(width),
            height=int(height),
            color=(255, 255, 255, 1)  # Casi invisible
        )

        self.owner = owner
        self.damage = damage
        self.lifetime = lifetime
        self._timer = 0.0
        self.angle = angle
        self.arc_angle = arc_angle
        self.offset_dist = offset_dist

        # Lista de enemigos ya golpeados para evitar múltiples hits
        self._enemies_hit = set()

        # Calcular posición inicial
        self._actualizar_posicion()

    def _actualizar_posicion(self):
        """Actualiza la posición siguiendo al owner."""
        if self.owner:
            angle_rad = math.radians(self.angle)
            self.center_x = self.owner.center_x + math.cos(angle_rad) * self.offset_dist
            self.center_y = self.owner.center_y + math.sin(angle_rad) * self.offset_dist

    def on_update(self, delta_time: float = 1/60):
        """
        Actualiza el hitbox.

        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        # Seguir al owner
        self._actualizar_posicion()

        # Actualizar timer de vida
        self._timer += delta_time
        if self._timer >= self.lifetime:
            self.kill()

    def check_collision_with_enemy(self, enemy) -> bool:
        """
        Verifica si el hitbox colisiona con un enemigo.
        Solo daña una vez por enemigo.

        Args:
            enemy: Enemigo a verificar

        Returns:
            bool: True si hubo colisión y daño
        """
        # Verificar si ya golpeamos a este enemigo
        enemy_id = id(enemy)
        if enemy_id in self._enemies_hit:
            return False

        # Verificar colisión de caja
        if not self.collides_with_sprite(enemy):
            return False

        # Verificar si está dentro del arco de ataque
        dx = enemy.center_x - self.owner.center_x
        dy = enemy.center_y - self.owner.center_y
        angle_to_enemy = math.degrees(math.atan2(dy, dx))

        # Normalizar ángulos
        angle_diff = (angle_to_enemy - self.angle + 180) % 360 - 180

        if abs(angle_diff) <= self.arc_angle / 2:
            # Aplicar daño
            self._aplicar_dano(enemy)
            self._enemies_hit.add(enemy_id)
            return True

        return False

    def _aplicar_dano(self, enemy):
        """Aplica daño al enemigo."""
        if hasattr(enemy, 'recibir_dano'):
            enemy.recibir_dano(self.damage)
        elif hasattr(enemy, 'vida'):
            enemy.vida -= self.damage
            if hasattr(enemy, 'vida'):
                if enemy.vida <= 0:
                    enemy.vida = 0
class Pistola(WeaponBase):
    """
    Pistola semi-automática con sistema de munición y recarga.
    """

    def __init__(self):
        """Inicializa la pistola con sus estadísticas."""
        super().__init__(
            item_id=100,
            nombre="Pistola",
            sprite_path="../assets/items/Pistola.jpg",
            damage=25,
            cooldown=0.4,
            rango=800.0,
            descripcion="Pistola semi-automática básica. Daño moderado, buena cadencia."
        )

        # Sistema de munición
        self.tamano_cargador = 12
        self.municion_actual = self.tamano_cargador
        self.municion_total = float('inf')  # Munición infinita total

        # Configuración del proyectil
        self.velocidad_proyectil = 600.0
        self.lifetime_proyectil = 2.0

        # Estado de recarga
        self._tiempo_recarga = 1.5
        self._timer_recarga = 0.0

    @property
    def puede_usar(self) -> bool:
        """Retorna True si se puede disparar (hay munición y no está recargando)."""
        return (
            self._timer_cooldown <= 0
            and not self.esta_recargando
            and self.municion_actual > 0
        )

    def usar(self, owner, target_x: float, target_y: float, proyectiles_list) -> bool:
        """
        Dispara un proyectil hacia la posición objetivo.

        Args:
            owner: Entidad que dispara (jugador)
            target_x: Posición X del ratón
            target_y: Posición Y del ratón
            proyectiles_list: Lista donde añadir el proyectil

        Returns:
            bool: True si se disparó correctamente
        """
        if not self.puede_usar:
            return False

        # Calcular ángulo hacia el target
        angle_rad = math.atan2(target_y - owner.center_y, target_x - owner.center_x)
        angle_deg = math.degrees(angle_rad)

        # Crear proyectil
        proyectil = Proyectil(
            x=owner.center_x,
            y=owner.center_y,
            angle=angle_deg,
            damage=self.damage,
            velocidad=self.velocidad_proyectil,
            lifetime=self.lifetime_proyectil
        )

        # Añadir a la lista de proyectiles
        proyectiles_list.append(proyectil)

        # Consumir munición
        self.municion_actual -= 1

        # Iniciar cooldown
        self.iniciar_cooldown()

        return True

    def recargar(self) -> bool:
        """
        Inicia la recarga del cargador.

        Returns:
            bool: True si se inició la recarga
        """
        if self.esta_recargando:
            return False

        if self.municion_actual >= self.tamano_cargador:
            return False  # Ya está lleno

        # Iniciar recarga
        self.esta_recargando = True
        self._timer_recarga = self._tiempo_recarga
        return True

    def actualizar(self, delta_time: float):
        """
        Actualiza cooldown y recarga.

        Args:
            delta_time: Tiempo transcurrido desde el último frame
        """
        super().actualizar(delta_time)

        # Actualizar recarga
        if self.esta_recargando:
            self._timer_recarga -= delta_time
            if self._timer_recarga <= 0:
                self._completar_recarga()

    def _completar_recarga(self):
        """Completa la recarga llenando el cargador."""
        self.municion_actual = self.tamano_cargador
        self.esta_recargando = False
        self._timer_recarga = 0.0

    def get_info_hud(self) -> dict:
        """
        Retorna información específica de la pistola para el HUD.

        Returns:
            dict: Información de munición y estado
        """
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

    def _get_recarga_progress(self) -> float:
        """Retorna el progreso de recarga (0.0 a 1.0)."""
        if not self.esta_recargando or self._tiempo_recarga <= 0:
            return 0.0
        return 1.0 - (self._timer_recarga / self._tiempo_recarga)


class Botiquin(BaseItem):
    """
    Objeto recogible que cura gradualmente al jugador. 
    """
    def __init__(self):
        super().__init__(
            item_id=200,
            name="Botiquín",
            sprite_path="assets/items/botiquin.jpg",
            description="Botiquín de primeros auxilios. Cura gradualmente al usarlo."
        )
        
        # Todo esto ahora está correctamente dentro del __init__
        self.cantidad_curacion = 15
        self.tiempo_curacion = 3.0
        self.cantidad_usos = 1
        
        # Variables necesarias para el cooldown (enfriamiento)
        self.cooldown = 0.0 
        self._timer_cooldown = 0.0
        self._curando = False
    
    @property
    def puede_usar(self) -> bool:
        """Devuelve True si el botiquín se puede usar."""
        return self._timer_cooldown <= 0
    
    def actualizar(self, delta_time: float):
        """Actualiza el estado del botiquín."""
        if self._timer_cooldown > 0:
            self._timer_cooldown -= delta_time
            if self._timer_cooldown < 0:
                self._timer_cooldown = 0

    def usar(self, owner, target_x=None, target_y=None, proyectiles_list=None) -> bool:
            if not self.puede_usar:
                return False
            
            exito = False

            if hasattr(owner, 'iniciar_curacion'):
                exito = owner.iniciar_curacion(self.cantidad_curacion, self.tiempo_curacion)
            
            if exito:
                self.cantidad_usos -= 1
                if self.cantidad_usos <= 0 and hasattr(owner, 'destruir_item_activo'):
                    owner.destruir_item_activo()
                return True
                
