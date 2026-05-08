import arcade
from vista.asset_manager import AssetManager


class BaseItem(arcade.Sprite):
    def __init__(self, item_id, name, sprite_path, description="", durability=100.0, scale = 0.5):
        texture = AssetManager().get_texture(sprite_path)
        super().__init__(texture, scale=scale)

        self.id = item_id 
        self.name = name
        self.description = description
        self.durability = durability
        
        self.quantity = 1
        self.max_stack = 1
        self.weight = 1.0
        self.is_usable = True
        self.is_dropped = False


    def usar(self, owner, slot, target_x=None, target_y=None, proyectiles_list=None) -> bool:
            print(self.puede_usar)
            if not self.puede_usar:
                return False

            se_pudo_curar = owner.iniciar_curacion(self.cantidad_curacion, self.tiempo_curacion)
            print("Se pudo curar:" ,se_pudo_curar)

            if se_pudo_curar:
                self.cantidad_usos -= 1
                self._timer_cooldown = self.cooldown
                
                if self.cantidad_usos <= 0:
                    owner.destruir_item_activo()
                
                return True
            
            return False


class Botiquin(BaseItem):
    def __init__(self):
        super().__init__(
            item_id=200,
            name="Botiquin",
            sprite_path="assets/items/botiquin.jpg",
            description="Botiquin de primeros auxilios. Cura gradualmente al usarlo."
        )
        
        self.cantidad_curacion = 15
        self.tiempo_curacion = 3.0
        self.cantidad_usos = 1
        self.cooldown = 1.0  
        self._timer_cooldown = 0.0
    
    @property
    def puede_usar(self) -> bool:
        return self._timer_cooldown <= 0

    def actualizar(self, delta_time: float):
        if self._timer_cooldown > 0:
            self._timer_cooldown -= delta_time

    def usar(self, owner, slot, target_x=None, target_y=None, proyectiles_list=None) -> bool:
        print(self.puede_usar)
        if not self.puede_usar:
            return False

        se_pudo_curar = owner.iniciar_curacion(self.cantidad_curacion, self.tiempo_curacion)
        print("Se pudo curar:" ,se_pudo_curar)

        if se_pudo_curar:
            self.cantidad_usos -= 1
            self._timer_cooldown = self.cooldown
            
            if self.cantidad_usos <= 0:
                owner.destruir_item_activo(slot)
            
            return True
        
        return False


class Nota(BaseItem):
    def __init__(self, item_id, nombre, titulo, texto, sprite_path):
        super().__init__(
            item_id=item_id,
            name=nombre,
            sprite_path=sprite_path,
            description="",
            scale= 0.05
        )
        self.titulo = titulo
        self.texto = texto

    def usar(self, owner, target_x=None, target_y=None, proyectiles_list=None) -> bool:
        owner.vistaNota = self
        return True