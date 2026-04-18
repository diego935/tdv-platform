import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO
from entities.player import Jugador
from entities.enemy import Enemigo
from entities.blocks import *
from vista.inventory import * 
from vista.textos import TextManager 
from items.item_manager import * 
from items.items import * 
from vista.hud import HUD
import random


class VistaJuego(arcade.View):
    def __init__(self):
        super().__init__()
        self.sprite_jugador = None
        self.lista_jugadores = None
        self.lista_enemigos = None
        self.lista_puertas = None
        self.lista_bloques = None
        self.camera = None
        self.hud = None 
        self.estado_actual = "MENU"

        self.show_inventory = False 
        self.izquierda_presionado = False
        self.derecha_presionado = False
        self.arriba_presionado = False
        self.abajo_presionado = False
        self.shift_presionado = False
        

    def setup(self):
        self.window.background_color = COLOR_FONDO_JUEGO

        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques= arcade.SpriteList()
        self.item_manager = ItemManager() 
        self.text_manager = TextManager()
        self.camera = arcade.camera.Camera2D()
        self.estado_actual ="JUGANDO"
        self.hud = HUD()
        

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
            pedernal = BaseItem(1, f"Pedernal {i+1}", "../assets/items/Flint.png")
            
            # Posición aleatoria cerca del centro para probar
            pedernal.center_x = random.randint(200, 600)
            pedernal.center_y = random.randint(200, 400)
            
            # Los añadimos al Manager para que aparezcan en el suelo
            ItemManager().add_to_world(pedernal)



        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)


    def on_draw(self):
        self.clear()

        # --- 1. CAPA DEL MUNDO ---
        # Todo lo que esté aquí dentro se moverá cuando el jugador camine
        with self.camera.activate():
            self.lista_bloques.draw()
            self.lista_puertas.draw()
            self.item_manager.draw()
            self.lista_enemigos.draw()
            self.lista_jugadores.draw()
        
            # Dibujamos textos que están en el suelo o sobre objetos/NPCs
            self.text_manager.draw()

        # --- 2. CAPA DE INTERFAZ (UI) ---
        self.hud.draw(self.sprite_jugador)
        
        # El inventario suele ser fijo en pantalla para que el jugador lo vea siempre
        
        if self.show_inventory:
            self.sprite_jugador.draw_inventory()    

    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)

        return (
            dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and
            dy < (sprite1.height / 2 + sprite2.height / 2 + margen)
        )

    def on_update(self, delta_time):
        
        
        if self.show_inventory: # Por si se quiere pausar el movimiento al abrir el inventario
            return 

        self.sprite_jugador.move(
        self.arriba_presionado,
        self.abajo_presionado,
        self.izquierda_presionado,
        self.derecha_presionado,
        self.shift_presionado,
        delta_time
    )


        self.lista_puertas.update(delta_time)
        self.lista_enemigos.update()

        ## Sincroniza el estado de las puerts
        for puerta in self.lista_puertas:
            if puerta.activa_colision and puerta not in self.lista_bloques:
                self.lista_bloques.append(puerta)
            elif not puerta.activa_colision and puerta in self.lista_bloques:
                self.lista_bloques.remove(puerta)

        self.physics_engine.update()
        self.camera.position = self.sprite_jugador.position
        self.text_manager.update()
        self.item_manager.update()
    def on_key_press(self, key, modifiers):
        # --- 1. ACCIONES DE INTERFAZ (Prioridad máxima) ---
        if key == arcade.key.TAB:
            self.show_inventory = not self.show_inventory
            return # Si tocamos la interfaz, no queremos que el jugador haga nada más

        if self.show_inventory:
            # Si el inventario está abierto, solo escuchamos la tecla Q para soltar
            if key == arcade.key.Q:
                self.ejecutar_soltar_item()
            return

        # --- 2. ACCIONES DEL MUNDO (Solo si el inventario está cerrado) ---
        
        # Movimiento (Banderas)
        if key in [arcade.key.W, arcade.key.UP]: self.arriba_presionado = True
        elif key in [arcade.key.S, arcade.key.DOWN]: self.abajo_presionado = True
        elif key in [arcade.key.A, arcade.key.LEFT]: self.izquierda_presionado = True
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.derecha_presionado = True
        elif key in [arcade.key.LSHIFT, arcade.key.RSHIFT]: self.shift_presionado = True

        if key in [arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3, arcade.key.KEY_4]:
            indice = key - arcade.key.KEY_1
            
            if self.estado_actual == "JUGANDO":
                self.sprite_jugador.indice_activo = indice
            elif self.estado_actual == "DIALOGO":
                pass


        # Interacción (Lógica de la Vista, porque implica otros objetos)
        elif key == arcade.key.E:
            self.ejecutar_interaccion()

    def ejecutar_interaccion(self):
        """Lógica separada para no ensuciar el on_key_press"""
        for puerta in self.lista_puertas:
            if self.cerca_con_margen(self.sprite_jugador, puerta, 15):
                puerta.interactuar()
                return # Prioridad a la puerta
                
        # Si no hay puertas, intentamos recoger del suelo
        self.item_manager.intentar_recoger(self.sprite_jugador)

    def ejecutar_soltar_item(self):
        idx = self.sprite_jugador.indice_seleccionado # El que marca el ratón en el inventario
        if idx is not None:
            objeto = self.sprite_jugador.soltar_objeto(idx)
            if objeto:
                self.item_manager.add_to_world(objeto)

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
            # Liberar movimiento
            if key in [arcade.key.W, arcade.key.UP]:
                self.arriba_presionado = False
            elif key in [arcade.key.S, arcade.key.DOWN]:
                self.abajo_presionado = False
            elif key in [arcade.key.A, arcade.key.LEFT]:
                self.izquierda_presionado = False
            elif key in [arcade.key.D, arcade.key.RIGHT]:
                self.derecha_presionado = False
            elif key in [arcade.key.LSHIFT, arcade.key.RSHIFT]:
                self.shift_presionado = False