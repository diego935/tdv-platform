"""
Gestor de cámara.
Maneja zoom, posición y conversión de coordenadas.
"""
import arcade


class CameraManager:
    """Maneja la cámara del juego."""

    ZOOM_SENSITIVITY = 0.1
    MIN_ZOOM = 0.2
    MAX_ZOOM = 4.0

    def __init__(self):
        self.camera = arcade.camera.Camera2D()
        self.camera.zoom = 1.0
        self.zoom_target = 1.0

    def seguir_sprite(self, sprite):
        """Hace que la cámara siga a un sprite."""
        self.camera.position = sprite.position

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Mantiene el zoom fijo en 1.0."""
        pass

    def unproject(self, screen_pos):
        """Convierte coordenadas de pantalla a coordenadas del mundo."""
        return self.camera.unproject(screen_pos)

    def unproject_with_origin(self, screen_x, screen_y, window_width, window_height):
        """Convierte coordenadas de pantalla a coordenadas del mundo considerando zoom y posición de cámara."""
        cam_x, cam_y = self.camera.position
        zoom = self.camera.zoom
        
        world_x = (screen_x - window_width / 2) / zoom + cam_x
        world_y = (screen_y - window_height / 2) / zoom + cam_y
        
        return world_x, world_y

    def project(self, world_pos):
        """Convierte coordenadas del mundo a coordenadas de pantalla."""
        return self.camera.project(world_pos)

    def activate(self):
        """Context manager para activar la cámara."""
        return self.camera.activate()

    @property
    def position(self):
        return self.camera.position

    @position.setter
    def position(self, value):
        self.camera.position = value

    @property
    def zoom(self):
        return self.camera.zoom

    @zoom.setter
    def zoom(self, value):
        self.camera.zoom = value