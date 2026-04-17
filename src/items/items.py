import arcade


class BaseItem(arcade.Sprite):
    def __init__(self, item_id, name, sprite_path, description="", durability=100.0):
        super().__init__(filename=sprite_path)

        self.id = item_id 
        self.name = name
        self.description = description
        self.durability = durability
        
        self.quantity = 1
        self.max_stack = 1       # Por defecto no se apilan
        self.weight = 1.0        # Para sistemas de carga
        self.is_usable = True    # ¿Se puede clickear para 'Usar'?
        
        self.is_dropped = False  # Si está por ahí tirado se puede recoger 
        




