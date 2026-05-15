import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA
from vista.menu_principal import MenuPrincipal

class PantallaCompleta(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, fullscreen=True)

    def on_key_press(self, key, modifiers):
        # PRESIONAR ESCAPE PARA SALIR DE PANTALLA COMPLETA y F11 PARA VOVERLA A PONER
        if key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
            
            if not self.fullscreen:
                self.center_window()
                

def main():
   
    window = PantallaCompleta(ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA)
    vista_menu = MenuPrincipal()
    window.show_view(vista_menu)
    arcade.run()

if __name__ == "__main__":
    main()