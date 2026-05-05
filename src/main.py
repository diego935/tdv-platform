import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA
from vista.menu_principal import MenuPrincipal

def main():
    window = arcade.Window(ANCHO_VENTANA, ALTO_VENTANA, TITULO_VENTANA)
    vista_menu = MenuPrincipal()
    window.show_view(vista_menu)
    arcade.run()

if __name__ == "__main__":
    main()