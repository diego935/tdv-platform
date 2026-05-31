import arcade
from vista.asset_manager import AssetManager
from utils.log import Log


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
        pass

    def to_dict(self):
        return {
            "__type__": self.__class__.__name__,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "durability": self.durability,
            "quantity": self.quantity,
            "is_dropped": self.is_dropped,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "_timer_cooldown": getattr(self, '_timer_cooldown', 0.0),
        }


def item_from_dict(data):
    tipo = data.get("__type__", "")
    try:
        if tipo == "Pistola":
            from items.weapons import Pistola
            item = Pistola()
            item.municion_actual = data.get("municion_actual", item.tamano_cargador)
            item._timer_cooldown = data.get("_timer_cooldown", 0.0)
            item.esta_recargando = data.get("esta_recargando", False)
            item._timer_recarga = data.get("_timer_recarga", 0.0)
        elif tipo == "Cuchillo":
            from items.weapons import Cuchillo
            item = Cuchillo()
            item._timer_cooldown = data.get("_timer_cooldown", 0.0)
        elif tipo == "Botiquin":
            item = Botiquin()
            item.cantidad_usos = data.get("cantidad_usos", 1)
            item._timer_cooldown = data.get("_timer_cooldown", 0.0)
        elif tipo == "Nota":
            item = Nota(
                item_id=data.get("id", 0),
                nombre=data.get("name", ""),
                titulo=data.get("titulo", ""),
                texto=data.get("texto", ""),
                sprite_path=data.get("sprite_path", "assets/items/Nota.png")
            )
        else:
            return None

        item.is_dropped = data.get("is_dropped", False)

        if item.is_dropped:
            item.center_x = data.get("center_x", 0)
            item.center_y = data.get("center_y", 0)

        return item
    except Exception as e:
        Log.error("item_from_dict", f"Error recreando item {tipo}: {e}")
        return None


class Botiquin(BaseItem):
    def __init__(self):
        super().__init__(
            item_id=200,
            name="Botiquin",
            sprite_path="assets/items/botiquin.png",
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

    def usar(self, owner,slot=None, target_x=None, target_y=None, proyectiles_list=None) -> bool:
        Log.debug("Botiquin", "Verificando uso", puede_usar=self.puede_usar)
        if not self.puede_usar:
            return False

        se_pudo_curar = owner.iniciar_curacion(self.cantidad_curacion, self.tiempo_curacion)
        Log.info("Botiquin", "Curación aplicada", exito=se_pudo_curar, cantidad=self.cantidad_curacion, tiempo=self.tiempo_curacion)

        if se_pudo_curar:
            self.cantidad_usos -= 1
            self._timer_cooldown = self.cooldown
            
            if self.cantidad_usos <= 0:
                owner.destruir_item_activo(slot if slot else None)

            return True
        return False

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "cantidad_curacion": self.cantidad_curacion,
            "tiempo_curacion": self.tiempo_curacion,
            "cantidad_usos": self.cantidad_usos,
            "cooldown": self.cooldown,
            "_timer_cooldown": self._timer_cooldown,
        })
        return d


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

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "titulo": self.titulo,
            "texto": self.texto,
        })
        return d
