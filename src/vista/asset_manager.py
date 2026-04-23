import arcade

class AssetManager:
    """
    Es otro Singleton y Flyweight
    
    """
    _instance = None
    _textures = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
        return cls._instance

    def get_texture(self, path):
        if path not in self._textures:
            try:
                # Cargamos y guardamos en el diccionario
                self._textures[path] = arcade.load_texture(path)
            except Exception as e:
                print(f"Error cargando {path}: {e}")
                # Textura de error (el clásico rosa/negro de motor de juegos)
                self._textures[path] = arcade.make_soft_square_texture(32, arcade.color.MAGENTA)
        return self._textures[path]

