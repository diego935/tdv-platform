import arcade
from typing import Optional
from vista.textos import TextManager
from vista.asset_manager import AssetManager
from utils.log import Log

# ==========================================
# EL MANAGER (Singleton)
# ==========================================
class InteractionManager:
    _instance = None

    def __new__(cls, player: Optional[arcade.Sprite] = None):
        if cls._instance is None:
            # Primera vez: se crea la instancia y se inicializa todo
            cls._instance = super(InteractionManager, cls).__new__(cls)
            cls._instance._init_manager(player)
        else:
            # Las siguientes veces: si nos pasan un player nuevo, lo actualizamos
            if player is not None:
                cls._instance.player = player
                
        return cls._instance

    def _init_manager(self, player: Optional[arcade.Sprite]):
        self.player = player
        self.all_interactables = arcade.SpriteList(use_spatial_hash=True, spatial_hash_cell_size=128)
        self.stats = {}

    def set_player(self, player: arcade.Sprite):
        self.player = player

    def clear(self):
        """Vacía las listas de trampas, monedas, estadísticas y desvincula al jugador viejo."""
        self.all_interactables.clear()
        self.stats.clear()
        self.player = None  
        Log.info("InteractionManager", "Estructuras de interacciones y trampas limpiadas.")

    def add_collectible(self, sprite, category, on_pickup, on_all_collected=None):
        Log.debug("InteractionManager", "Añadiendo collectible", sprite=str(sprite), category=category)
        sprite.is_trap = False
        sprite.category = category
        sprite.on_pickup = on_pickup
        if category not in self.stats:
            self.stats[category] = {"actual": 0, "total": 0, "callback": on_all_collected}
        self.stats[category]["total"] += 1
        self.all_interactables.append(sprite)
        Log.debug("InteractionManager", "Collectible añadido", objetos=[str(s) for s in self.all_interactables])

    def add_trap(self, sprite, on_trigger):
        Log.debug("InteractionManager", "Añadiendo trampa", sprite=str(sprite))
        sprite.is_trap = True
        sprite.on_trigger = on_trigger
        self.all_interactables.append(sprite)
        Log.debug("InteractionManager", "Trampa añadida", total=len(self.all_interactables))

    def update(self):
        if not self.player: return
        hit_list = arcade.check_for_collision_with_list(self.player, self.all_interactables)
        
        for obj in hit_list:
            if obj.is_trap:
                obj.on_trigger(self.player)
            else:
                obj.on_pickup()
                cat = obj.category
                self.stats[cat]["actual"] += 1
                if self.stats[cat]["actual"] == self.stats[cat]["total"]:
                    if self.stats[cat]["callback"]:
                        self.stats[cat]["callback"]()
                obj.remove_from_sprite_lists()

    def draw(self):
        self.all_interactables.draw()

class MissionCoin(arcade.Sprite):
    def __init__(self, x, y):
        texture = AssetManager().get_texture(":resources:images/items/gold_1.png")
        super().__init__(texture, scale=0.4)

        self.center_x = x
        self.center_y = y
        self.categoria = "monedas_ancestrales"
        self.item_id = "moneda_ancestral"

    def al_recoger(self):
        """Se ejecuta cuando el jugador toca ESTA moneda."""
        from dialog.quest_manager import EB
        EB.publish("item_collected", {"item_id": self.item_id})

        im = InteractionManager()
        datos = im.stats.get(self.categoria)

        actual = datos["actual"] + 1
        total = datos["total"]

        player = im.player
        if player:
            TextManager().show_message(
                f"{actual}/{total}",
                player.center_x,
                player.center_y + 30,
                (255, 215, 0)
            )

    @staticmethod
    def mision_completada():
        """Se ejecuta cuando se recoge la ÚLTIMA moneda de esta categoría."""
        im = InteractionManager()
        player = im.player
        
        if player:
            player.max_vida *=3
            player.vida = player.max_vida
            player.scale =  (player.scale[0]*1.5,player.scale[1]*1.5)
            player.color = arcade.color.GOLD
            
            TextManager().show_message(
                "¡PODER ANCESTRAL!", 
                player.center_x, 
                player.center_y + 60, 
                (0, 255, 255) # Cyan
            )

class SpikeTrap(arcade.Sprite):
    def __init__(self, x, y, damage_veneno = 20/3, tiempo_veneno= 3, tiempo_slow = 5, dano_base = 20, porcentajeSlow: float = 0.4):
        
        if (damage_veneno >0 and tiempo_veneno > 0): 
            texture = AssetManager().get_texture("assets/items/trampaVenenosa.png")
        else: 
            texture = AssetManager().get_texture("assets/items/trampa.png")

        
        super().__init__(texture, scale=0.045)
        
        self.center_x = x
        self.center_y = y
        self.damage = dano_base
        self.damage_veneno = damage_veneno
        self.tiempo_veneno= tiempo_veneno
        self.tiempo_slow = tiempo_slow
        self.porcentajeSlow= porcentajeSlow

    def activar(self, player):
        """Se ejecuta automáticamente cuando el jugador la pisa."""
        # Aplicamos daño
        player.pisa_trampa(self.damage, self.damage_veneno, self.tiempo_veneno, self.tiempo_slow, self.porcentajeSlow )
        
        
      
        # La trampa se destruye a sí misma
        self.remove_from_sprite_lists()