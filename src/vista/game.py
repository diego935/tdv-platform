import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO
from entities.player import Jugador
from entities.enemy import *
from entities.blocks import *
from vista.inventory import * 
from vista.textos import TextManager 
from items.item_manager import * 
from items.items import * 
from vista.hud import HUD
from vista.consola import * 
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
        self.console = None
        self.mouse_world_x = None 
        self.mouse_world_y = None  
        self.nav_manager = None

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
        self.console = ConsoleUI()

        

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
        self.nav_manager = SistemaNavegacion(self.lista_bloques)


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
            self.console.draw_world(self.lista_bloques, self.lista_enemigos, self.nav_manager)
        
            # Dibujamos textos que están en el suelo o sobre objetos/NPCs
            self.text_manager.draw()

        # --- 2. CAPA DE INTERFAZ (UI) ---
        self.hud.draw(self.sprite_jugador)
        
        # El inventario suele ser fijo en pantalla para que el jugador lo vea siempre
        
        if self.show_inventory:
            self.sprite_jugador.draw_inventory() 
               
        if self.estado_actual == "CONSOLE":
            self.console.draw()

    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)

        return (
            dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and
            dy < (sprite1.height / 2 + sprite2.height / 2 + margen)
        )

    def on_update(self, delta_time):
        
        
        if self.show_inventory or self.estado_actual== "CONSOLE":
            self.console.update(delta_time,self     )

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
        cambio_detectado = False

        for puerta in self.lista_puertas:
            if puerta.activa_colision and puerta not in self.lista_bloques:
                self.lista_bloques.append(puerta)
                cambio_detectado = True
            elif not puerta.activa_colision and puerta in self.lista_bloques:
                self.lista_bloques.remove(puerta)
                cambio_detectado = True

        
        if cambio_detectado:
            self. nav_manager.actualizar_grafo_async()

        self.physics_engine.update()
        self.camera.position = self.sprite_jugador.position
        self.text_manager.update()
        self.item_manager.update()

    def on_text_input(self, text):
        if self.estado_actual =="CONSOLE":
            self.console.input_text += text


    def on_key_press(self, key, modifiers):
        # 1. Abrir/Cerrar consola
        if key == arcade.key.F1:
            if self.estado_actual == "CONSOLE":
                self.estado_actual = "JUGANDO"
                self.console.active = False
            else:
                self.estado_actual = "CONSOLE"
                self.console.active = True
                self.console.input_text = ""
            return

        # 2. SI LA CONSOLA ESTÁ ACTIVA
        if self.estado_actual == "CONSOLE":
            # Ejecutar comando
            if key == arcade.key.ENTER:
                self.procesar_comando(self.console.input_text)
                self.console.input_text = ""
                return
            
            # Borrar último carácter
            elif key == arcade.key.BACKSPACE:
                self.console.input_text = self.console.input_text[:-1]
                return

            # --- CAPTURA MANUAL DE CARACTERES ---
            # Solo permitimos teclas que "escriben" (Letras, Números, Espacio, Guión)
            if (key >= arcade.key.A and key <= arcade.key.Z) or \
               (key >= arcade.key.KEY_0 and key <= arcade.key.KEY_9) or \
               key == arcade.key.SPACE or key == arcade.key.MINUS:
                
                # Convertimos el código de tecla a carácter
                char = chr(key)
                
                # Si SHIFT está pulsado, pasamos a mayúsculas
                if modifiers & arcade.key.MOD_SHIFT:
                    char = char.upper()
                
                self.console.input_text += char
            
            # MUY IMPORTANTE: Bloqueamos cualquier otra acción mientras la consola está abierta
            return 

        # 3. ACCIONES DEL INVENTARIO (Solo si consola cerrada)
        if self.show_inventory:
            if key == arcade.key.TAB:
                self.show_inventory = False
            elif key == arcade.key.Q:
                self.ejecutar_soltar_item()
            return

        # 4. ACCIONES DE JUEGO NORMAL
        if key == arcade.key.TAB:
            self.show_inventory = True
            return

        # Movimiento
        if key in [arcade.key.W, arcade.key.UP]: self.arriba_presionado = True
        elif key in [arcade.key.S, arcade.key.DOWN]: self.abajo_presionado = True
        elif key in [arcade.key.A, arcade.key.LEFT]: self.izquierda_presionado = True
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.derecha_presionado = True
        elif key in [arcade.key.LSHIFT, arcade.key.RSHIFT]: self.shift_presionado = True

        # Interacción y Slots
        if key == arcade.key.E:
            self.ejecutar_interaccion()
        elif key in [arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3, arcade.key.KEY_4]:
            self.sprite_jugador.indice_activo = key - arcade.key.KEY_1


    def ejecutar_interaccion(self):
        """
        Lógica separada para no ensuciar el on_key_press
        Aqui se maneja la inteeracción con, puertas, objetos, posiblemente dialogos, todo lo que se active con la e 
        """
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
        self.mouse_world_x = x + self.camera.position.x - self.window.width / 2
        self.mouse_world_y = y + self.camera.position.y - self.window.height / 2
        if self.show_inventory:
            indice = self.sprite_jugador.vistaInventario.get_slot_at_pointer(x, y)
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
    

    def procesar_comando(self, comando_raw):
        partes = comando_raw.strip().split()
        if not partes:
            return

        nombre_cmd = partes[0].lower()
        args = partes[1:]
        
        self.console.add_to_history(f"> {comando_raw}")

        # Buscamos si el comando existe en nuestro diccionario de comandos.py
        if nombre_cmd in COMANDOS:
            try:
                # Ejecutamos la función pasando la vista (self) y los argumentos
                resultado = COMANDOS[nombre_cmd](self, args)
                if resultado:
                    self.console.add_to_history(resultado)
            except Exception as e:
                self.console.add_to_history(f"Error de ejecución: {e}")
        else:
            self.console.add_to_history(f"Comando '{nombre_cmd}' no reconocido.")