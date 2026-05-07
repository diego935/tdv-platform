import arcade

class ItemManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemManager, cls).__new__(cls)
            # Aquí vive la lista de Sprites u objetos en el suelo
            cls._instance.items_on_ground = arcade.SpriteList(use_spatial_hash=True) 
        return cls._instance

    def add_to_world(self, item):
        self.items_on_ground.append(item)

    def update(self):
        # Aquí podrías checkear si el jugador está cerca de algún item
        # para mostrar un mensaje de "Presiona E" automáticamente
        pass

    def draw(self):
        self.items_on_ground.draw()

    def intentar_recoger(self, jugador):
            for item in self.items_on_ground:
                if arcade.get_distance_between_sprites(jugador, item) < 50:
                    exito = jugador.recoger_objeto(item)
                    
                    if exito:
                        self.items_on_ground.remove(item)
                        return True
            return False

    def get_items_cercanos(self, jugador, distancia):
        items_cercanos = []
        for item in self.items_on_ground:
            if arcade.get_distance_between_sprites(jugador, item) < distancia:
                items_cercanos.append(item)
        return items_cercanos
