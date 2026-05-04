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
        self.zoom_target = 1.0

    def seguir_sprite(self, sprite):
        """Hace que la cámara siga a un sprite."""
        self.camera.position = sprite.position

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Ajusta el zoom según el scroll del ratón."""
        nuevo_zoom = self.camera.zoom + (scroll_y * self.ZOOM_SENSITIVITY)
        self.camera.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, nuevo_zoom))

    def unproject(self, screen_pos):
        """Convierte coordenadas de pantalla a coordenadas del mundo."""
        return self.camera.unproject(screen_pos)

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