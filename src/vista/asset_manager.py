import arcade

class AssetManager:
    _instance = None
    _textures = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
        return cls._instance

    def get_texture(self, path):
        if path not in self._textures:
            try:
                self._textures[path] = arcade.load_texture(path)
            except Exception as e:
                print(f"Error cargando {path}: {e}")
                # Generamos una textura de emergencia para no ver cuadros morados
                self._textures[path] = arcade.Texture.create_filled(f"err_{path}", (32, 32), arcade.color.MAGENTA)
        return self._textures[path]