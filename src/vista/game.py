import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO
from entities.player import Jugador
from entities.enemy import Enemigo
from entities.blocks import *
from vista.inventory import * 
from vista.textos import TextManager 
from items.item_manager import * 
from items.items import * 
import random


class VistaJuego(arcade.View):
    def __init__(self):
        super().__init__()
        self.sprite_jugador = None
        self.lista_jugadores = None
        self.lista_enemigos = None
        self.lista_puertas = None
        self.lista_bloques = None

        self.show_inventory = False 
        self.izquierda_presionado = False
        self.derecha_presionado = False
        self.arriba_presionado = False
        self.abajo_presionado = False

    def setup(self):
        self.window.background_color = COLOR_FONDO_JUEGO

        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques= arcade.SpriteList()
        self.item_manager = ItemManager() 
        self.text_manager = TextManager()
        

        self.sprite_jugador = Jugador()
        self.sprite_jugador.center_x = ANCHO_VENTANA // 2
        self.sprite_jugador.center_y = ALTO_VENTANA // 2
        self.lista_jugadores.append(self.sprite_jugador)
        
        """puerta = Puerta(ANCHO_VENTANA // 2 + 300, ALTO_VENTANA // 2, width=100, height=300, tiempo_apertura=1.5, tiempo_cierre=1.0)
        self.lista_puertas.append(puerta)
        self.lista_bloques.append(puerta)"""

        puertas, bloques = crear_casa(
            x=ANCHO_VENTANA // 2,
            y=ALTO_VENTANA // 2,
            ancho_habitable=500,
            alto_habitable=500,
            grosor=32,
            direcciones_puerta=["NORTE", "ESTE"],
            ancho_puerta=100
        )
        self.lista_puertas.extend(puertas)
        self.lista_bloques.extend(bloques)

        for i in range(10):
            pedernal = BaseItem(1, f"Pedernal {i+1}", "assets/items/Flint.png")
            
            # Posición aleatoria cerca del centro para probar
            pedernal.center_x = random.randint(200, 600)
            pedernal.center_y = random.randint(200, 400)
            
            # Los añadimos al Manager para que aparezcan en el suelo
            ItemManager().add_to_world(pedernal)



        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)


    def on_draw(self):
        self.clear()
        self.lista_bloques.draw()
        self.lista_puertas.draw()


        self.item_manager.draw()        

        # Si el inventario está abierto, llamar a la vista que hicimos antes
        if self.show_inventory:
            self.sprite_jugador.draw_inventory()

        self.text_manager.draw()
        self.lista_enemigos.draw()
        self.lista_jugadores.draw()
    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)

        return (
            dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and
            dy < (sprite1.height / 2 + sprite2.height / 2 + margen)
        )

    def on_update(self, delta_time):
        
        
        #if self.show_inventory: # Por si se quiere pausar el movimiento al abrir el inventario
        #    return 

        self.sprite_jugador.change_x = 0
        self.sprite_jugador.change_y = 0

        if self.arriba_presionado and not self.abajo_presionado:
            self.sprite_jugador.change_y = self.sprite_jugador.velocidad
        elif self.abajo_presionado and not self.arriba_presionado:
            self.sprite_jugador.change_y = -self.sprite_jugador.velocidad

        if self.izquierda_presionado and not self.derecha_presionado:
            self.sprite_jugador.change_x = -self.sprite_jugador.velocidad
        elif self.derecha_presionado and not self.izquierda_presionado:
            self.sprite_jugador.change_x = self.sprite_jugador.velocidad


        self.lista_puertas.update(delta_time)
        self.lista_jugadores.update()
        self.lista_enemigos.update()

        ## Sincroniza el estado de las puerts
        for puerta in self.lista_puertas:
            if puerta.activa_colision and puerta not in self.lista_bloques:
                self.lista_bloques.append(puerta)
            elif not puerta.activa_colision and puerta in self.lista_bloques:
                self.lista_bloques.remove(puerta)

        self.physics_engine.update()
        self.text_manager.update()
        self.item_manager.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = True
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = True
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = True
        elif key == arcade.key.E:
            for puerta in self.lista_puertas:
                if self.cerca_con_margen(self.sprite_jugador, puerta, margen=10):
                    puerta.interactuar()
                    break ## Se asume que solo se interactua con una puerta a la vez
            item_recogido = ItemManager().intentar_recoger(self.sprite_jugador)
        if key == arcade.key.TAB:
            # Esto invierte el valor: si es True pasa a False y viceversa
            self.show_inventory = not self.show_inventory
            
            # (Opcional) Pausar el juego o liberar el ratón
            # self.set_mouse_visible(self.show_inventory)
        if key == arcade.key.Q and self.show_inventory:
            idx = self.sprite_jugador.indice_seleccionado
                        
            if idx is not None:
                objeto_tirado = self.sprite_jugador.soltar_objeto(idx)
                
                if objeto_tirado:
                    objeto_tirado.center_x = self.sprite_jugador.center_x
                    objeto_tirado.center_y = self.sprite_jugador.center_y

                    # Lo registramos de nuevo en el mundo a través del Manager
                    ItemManager().add_to_world(objeto_tirado)
                    print(f"Soltaste {objeto_tirado.name}")

    def on_mouse_motion(self, x, y, dx, dy):
        if self.show_inventory:

            indice = self.sprite_jugador.vistaInventario.get_slot_at_pointer(x, y)
            
            # Guardamos el índice seleccionado para que el draw lo use
            self.sprite_jugador.indice_seleccionado = indice


    def on_mouse_press(self, x, y, button, modifiers):
        if self.show_inventory and button == arcade.MOUSE_BUTTON_LEFT:
            idx = self.sprite_jugador.indice_seleccionado
        
            if idx is not None and self.sprite_jugador.inventory[idx] is not None:
                # Aquí podrías soltarlo, usarlo o abrir su descripción
                print(f"Has clickeado en: {self.sprite_jugador.inventory[idx].name}")
                # self.sprite_jugador.soltar_objeto(idx)


    def on_key_release(self, key, modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = False
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = False
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = False
