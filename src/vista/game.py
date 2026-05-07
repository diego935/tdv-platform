import arcade
import time
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO
from entities.player import Jugador
from entities.enemy import *
from entities.pathfinding import SistemaNavegacion
from entities.blocks import *
from vista.inventory import * 
from vista.textos import TextManager 
from items.item_manager import * 
from items.items import * 
from items.weapons import *
from vista.hud import HUD
from vista.consola import * 
from vista.camera_manager import CameraManager
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
        
        # Zoom settings
        self.ZOOM_SENSITIVITY = 0.1
        self.MIN_ZOOM = 0.2
        self.MAX_ZOOM = 4.0
        

        #Inicializar variables del mapa.
        self.CAPAS = {
            "suelo": "Suelo",
            "muros": "Pared",
            "eventos": "Eventos",
            "zonas": "Zonas"
        }
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques = arcade.SpriteList()
        self.lista_jugadores = arcade.SpriteList()
        
        # Variables para doble click en inventario
        self._ultimo_click_slot = None
        self._ultimo_click_tiempo = 0.0
        self._DOUBLE_CLICK_DELAY = 0.3
        
    def setup(self):
        #Mapa--------------------------------------
        map_name = "assets/maps/mapa.tmx"
        layer_options = {self.CAPAS["muros"]: {"use_spatial_hash": True}}
        self.tile_map = arcade.load_tilemap(map_name, scaling=1, layer_options=layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        
        # Definimos map_height para evitar NameError
        map_height = self.tile_map.height * self.tile_map.tile_height

        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques = arcade.SpriteList()
        self.lista_proyectiles = []
        self.item_manager = ItemManager() 
        self.text_manager = TextManager()

        # Configurar Jugador y Spawn
        eventos = self.tile_map.object_lists.get(self.CAPAS["eventos"], [])
        spawn = next((obj for obj in eventos if obj.name == "Spawnpoint"), None)
        
        self.sprite_jugador = Jugador()
        if spawn:
            self.sprite_jugador.center_x = spawn.shape[0]
            self.sprite_jugador.center_y = map_height - spawn.shape[1]
        
        self.scene.add_sprite("Player", self.sprite_jugador)
        self.lista_jugadores.append(self.sprite_jugador)

        # Solo las PAREDES van a la lista de colisión 
        muros_mapa = self.scene.get_sprite_list(self.CAPAS["muros"])
        if muros_mapa:
            for muro in muros_mapa:
                self.lista_bloques.append(muro)

        self.camera = CameraManager()
        self.hud = HUD()
        self.console = ConsoleUI()

        for i in range(10):
            pedernal = BaseItem(1, f"Pedernal {i+1}", "assets/items/Flint.png")
            pedernal.center_x = random.randint(200, 600)
            pedernal.center_y = random.randint(200, 400)
            self.item_manager.add_to_world(pedernal)
        
        from items.weapons import Pistola, Cuchillo
        self.sprite_jugador.inventory[0] = Pistola()
        self.sprite_jugador.inventory[1] = Cuchillo()

        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)
        self.nav_manager = SistemaNavegacion(self.lista_bloques)

        from entities.enemy import EnemigoIA

        enemigo1 = EnemigoIA(
            x=500, y=300,
            tipo_patrulla=EnemigoIA.TIPO_WAYPOINT,
            waypoints=[(500, 300), (700, 300), (700, 500), (500, 500)],
            velocidad=100,
            velocidad_patrulla=60,
            vista_rango=400,
            tiempo_buscar=3.0
        )
        self.lista_enemigos.append(enemigo1)

        enemigo2 = EnemigoIA(
            x=200, y=500,
            tipo_patrulla=EnemigoIA.TIPO_AREA,
            area_center=(200, 500),
            area_radio=150,
            velocidad=100,
            velocidad_patrulla=50,
            vista_rango=350,
            tiempo_buscar=2.5
        )
        self.lista_enemigos.append(enemigo2)

        enemigo3 = EnemigoIA(
            x=800, y=200,
            tipo_patrulla=EnemigoIA.TIPO_PAREDES,
            velocidad=120,
            velocidad_patrulla=70,
            vista_rango=300,
            tiempo_buscar=2.0
        )
        self.lista_enemigos.append(enemigo3)

    def on_draw(self):
        self.clear()
        with self.camera.activate():
            self.scene.draw()            
            self.lista_bloques.draw()
            self.lista_puertas.draw()
            self.item_manager.draw()
            for p in self.lista_proyectiles:
                p.draw()
            self.lista_enemigos.draw()
            self.lista_jugadores.draw()
            self.console.draw_world(self.lista_bloques, self.lista_enemigos, self.nav_manager, self.sprite_jugador)
            self.text_manager.draw()

        self.hud.draw(self.sprite_jugador)
        
        if self.show_inventory:
            mouse_pos = (self.mouse_pos_x, self.mouse_pos_y) if hasattr(self, 'mouse_pos_x') else None
            self.sprite_jugador.draw_inventory(mouse_pos)

        if self.estado_actual == "CONSOLE":
            self.console.draw()

    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)
        return (dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and dy < (sprite1.height / 2 + sprite2.height / 2 + margen))

    def on_update(self, delta_time):
        if self.show_inventory or self.estado_actual== "CONSOLE":
            self.console.update(delta_time,self)

        self.sprite_jugador.move(
            self.arriba_presionado,
            self.abajo_presionado,
            self.izquierda_presionado,
            self.derecha_presionado,
            self.shift_presionado,
            delta_time
        )

        self.lista_puertas.update(delta_time)
        
        for enemigo in self.lista_enemigos:
            if hasattr(enemigo, 'update'):
                if hasattr(enemigo, 'puede_ver_player'):
                    enemigo.update(delta_time, self.sprite_jugador, self.lista_bloques, self.nav_manager)
                else:
                    enemigo.update(delta_time)

        for p in self.lista_proyectiles:
            if hasattr(p, 'update'):
                p.update(delta_time, self.lista_bloques, self.lista_enemigos)
            elif hasattr(p, 'on_update'):
                p.on_update(delta_time)
            if hasattr(p, 'update_enemies'):
                p.update_enemies(self.lista_enemigos)
            if hasattr(p, '_actualizar_posicion'):
                p._actualizar_posicion()

        self.lista_proyectiles = [p for p in self.lista_proyectiles if not p.killed]
        
        arma = self.sprite_jugador.obtener_arma_activa()
        if arma and hasattr(arma, 'actualizar'):
            arma.actualizar(delta_time)

        self.physics_engine.update()
        self.camera.position = self.sprite_jugador.position
        self.text_manager.update()
        self.item_manager.update()

    def on_text_input(self, text):
        if self.estado_actual =="CONSOLE":
            self.console.input_text += text

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F1:
            if self.estado_actual == "CONSOLE":
                self.estado_actual = "JUGANDO"
                self.console.active = False
            else:
                self.estado_actual = "CONSOLE"
                self.console.active = True
                self.console.input_text = ""
            return

        if self.estado_actual == "CONSOLE":
            if key == arcade.key.ENTER:
                self.procesar_comando(self.console.input_text)
                self.console.input_text = ""
                return
            elif key == arcade.key.BACKSPACE:
                self.console.input_text = self.console.input_text[:-1]
                return
            if (key >= arcade.key.A and key <= arcade.key.Z) or \
               (key >= arcade.key.KEY_0 and key <= arcade.key.KEY_9) or \
               key == arcade.key.SPACE or key == arcade.key.MINUS:
                char = chr(key)
                if modifiers & arcade.key.MOD_SHIFT:
                    char = char.upper()
                self.console.input_text += char
            return 

        if self.show_inventory:
            if key == arcade.key.TAB:
                self.show_inventory = False
            elif key == arcade.key.Q:
                self.ejecutar_soltar_item()
            return

        if key == arcade.key.TAB:
            self.show_inventory = True
            return

        if key in [arcade.key.W, arcade.key.UP]: self.arriba_presionado = True
        elif key in [arcade.key.S, arcade.key.DOWN]: self.abajo_presionado = True
        elif key in [arcade.key.A, arcade.key.LEFT]: self.izquierda_presionado = True
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.derecha_presionado = True
        elif key in [arcade.key.LSHIFT, arcade.key.RSHIFT]: self.shift_presionado = True

        if key == arcade.key.E:
            self.ejecutar_interaccion()
        elif key == arcade.key.R:
            self.ejecutar_recargar()
        elif key in [arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3, arcade.key.KEY_4]:
            self.sprite_jugador.indice_activo = key - arcade.key.KEY_1

    def ejecutar_interaccion(self):
        for puerta in self.lista_puertas:
            if self.cerca_con_margen(self.sprite_jugador, puerta, 15):
                puerta.interactuar()
                return 
        self.item_manager.intentar_recoger(self.sprite_jugador)

    def ejecutar_recargar(self):
        arma = self.sprite_jugador.obtener_arma_activa()
        if arma and hasattr(arma, 'recargar'):
            arma.recargar()

    def ejecutar_soltar_item(self):
        idx = self.sprite_jugador.indice_seleccionado
        if idx is not None:
            objeto = self.sprite_jugador.soltar_objeto(idx)
            if objeto:
                self.item_manager.add_to_world(objeto)
    
    def on_mouse_motion(self, x, y, dx, dy):
        window = self.window
        self.mouse_world_x, self.mouse_world_y = self.camera.unproject_with_origin(x, y, window.width, window.height)
        self.mouse_pos_x = x
        self.mouse_pos_y = y
        if self.show_inventory:
            slot = self.sprite_jugador.vistaInventario.get_slot_at_pointer(x, y)
            self.sprite_jugador.vistaInventario.set_hover(slot)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        window = self.window
        self.mouse_world_x, self.mouse_world_y = self.camera.unproject_with_origin(x, y, window.width, window.height)
        self.mouse_pos_x = x
        self.mouse_pos_y = y
        if self.show_inventory and self.sprite_jugador.vistaInventario._drag_source is not None:
            target = self.sprite_jugador.vistaInventario.get_slot_at_pointer(x, y)
            if target != self.sprite_jugador.vistaInventario._drag_source and target is not None:
                src = self.sprite_jugador.vistaInventario._drag_source
                self.sprite_jugador.inventory[src], self.sprite_jugador.inventory[target] = \
                    self.sprite_jugador.inventory[target], self.sprite_jugador.inventory[src]
                self.sprite_jugador.vistaInventario._drag_source = None

    def on_mouse_press(self, x, y, button, modifiers):
        if self.show_inventory and button == arcade.MOUSE_BUTTON_LEFT:
            slot = self.sprite_jugador.vistaInventario.get_slot_at_pointer(x, y)
            if slot is not None and slot < len(self.sprite_jugador.inventory):
                item = self.sprite_jugador.inventory[slot]
                ahora = time.time()
                es_doble_click = (slot == self._ultimo_click_slot and ahora - self._ultimo_click_tiempo < self._DOUBLE_CLICK_DELAY)
                self._ultimo_click_slot = slot
                self._ultimo_click_tiempo = ahora
                
                if item and hasattr(item, 'usar') and es_doble_click:
                    item.usar(self.sprite_jugador, None, None, None)
                elif item is not None:
                    self.sprite_jugador.vistaInventario._drag_source = slot
            return
        
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.sprite_jugador:
                target_x = self.mouse_world_x if self.mouse_world_x is not None else self.sprite_jugador.center_x + 100
                target_y = self.mouse_world_y if self.mouse_world_y is not None else self.sprite_jugador.center_y
                self.sprite_jugador.usar_arma_activa(target_x, target_y, self.lista_proyectiles)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.show_inventory and button == arcade.MOUSE_BUTTON_LEFT:
            self.sprite_jugador.vistaInventario._drag_source = None

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.UP]: self.arriba_presionado = False
        elif key in [arcade.key.S, arcade.key.DOWN]: self.abajo_presionado = False
        elif key in [arcade.key.A, arcade.key.LEFT]: self.izquierda_presionado = False
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.derecha_presionado = False
        elif key in [arcade.key.LSHIFT, arcade.key.RSHIFT]: self.shift_presionado = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        nuevo_zoom = self.camera.zoom + (scroll_y * self.ZOOM_SENSITIVITY)
        self.camera.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, nuevo_zoom))

    def procesar_comando(self, comando_raw):
        partes = comando_raw.strip().split()
        if not partes: return
        nombre_cmd = partes[0].lower()
        args = partes[1:]
        self.console.add_to_history(f"> {comando_raw}")
        if nombre_cmd in COMANDOS:
            try:
                resultado = COMANDOS[nombre_cmd](self, args)
                if resultado: self.console.add_to_history(resultado)
            except Exception as e: self.console.add_to_history(f"Error: {e}")
        else: self.console.add_to_history(f"Comando '{nombre_cmd}' no reconocido.")

    def cargar_objetos_del_mapa(self):
        pass