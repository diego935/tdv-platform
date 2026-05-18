import arcade
import time
from vista.menu_pausa import MenuPausa
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO, DISTANCIA_ACTUALIZACION
from entities.player import Jugador
from entities.enemy import *
from entities.pathfinding import SistemaNavegacion
from utils.log import Log

from entities.blocks import *
from vista.inventory import * 
from vista.inventory import NotaUI 
from vista.textos import TextManager 
from items.item_manager import * 
from items.items import * 
from items.weapons import *
from vista.hud import HUD
from vista.consola import * 
from vista.camera_manager import CameraManager
from vista.asset_manager import AssetManager
import random
from entities.enemy import EnemigoIA
from entities.enemy import EnemigoRanged
from items.colections import InteractionManager, SpikeTrap,MissionCoin
from items.weapons import Pistola, Cuchillo
import inspect

from dialog import DialogManager
from vista.dialog_ui import DialogUI
import json
from dialog.quest_manager import EB
from vista.vista_muerte import VistaGameOver
import os
from dialog.quest_manager import QM


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
        self.dm = None
        self.lista_npcs = []
        
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
        
        # Optimización de distancia
        self.DISTANCIA_ACTUALIZACION = DISTANCIA_ACTUALIZACION
        

        #Inicializar variables del mapa.
        self.CAPAS = {
            "suelo": "Suelo",
            "muros": "Pared",
            "eventos": "Eventos",
            "zonas": "Zonas",
            "npcs" : "NPCs",
            "overlay": "overlay",
            "enemigos": "Enemigos"
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
        #Cargar misiones guardadas
        self._cargar_misiones()
        QM.suscripcion_automatica()

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
        self.lista_proyectiles = arcade.SpriteList()
        self.item_manager = ItemManager() 
        self.text_manager = TextManager()

        # Configurar Jugador y Spawn
        eventos = self.tile_map.object_lists.get(self.CAPAS["eventos"], [])
        spawn = next((obj for obj in eventos if obj.name == "Spawnpoint"), None)
        self.lista_npcs = self.tile_map.object_lists.get(self.CAPAS["npcs"], [])
        
        # Crear sprites para NPCs desde objetos Tiled
        self.lista_npc_sprites = arcade.SpriteList()
        for npc_obj in self.lista_npcs:
            props = getattr(npc_obj, 'properties', {})
            sprite_path = props.get('sprite', '')
            scale = props.get('scale', 0.11)
            if sprite_path:
                tex = AssetManager().get_texture(sprite_path)
                npc_sprite = arcade.Sprite(tex, scale=scale)
                npc_sprite.center_x = (npc_obj.shape[0][0] + npc_obj.shape[2][0]) / 2
                npc_sprite.center_y = (npc_obj.shape[0][1] + npc_obj.shape[2][1]) / 2
                self.lista_npc_sprites.append(npc_sprite)
        
        self.sprite_jugador = Jugador()
        EB.subscribe("player_death", self._on_player_death)
        print("\n\n\n\n\n\n")
        print(self.sprite_jugador.__dict__)
        print("\n\n\n\n\n\n")

        
        if spawn:
            self.sprite_jugador.center_x = spawn.shape[0]
            self.sprite_jugador.center_y = map_height - spawn.shape[1]
        
        self.scene.add_sprite("Player", self.sprite_jugador)
        self.lista_jugadores.append(self.sprite_jugador)

        # Añadir NPCs a la lista de colisiones
        for npc_sprite in self.lista_npc_sprites:
            self.lista_bloques.append(npc_sprite)
        
        # Solo las PAREDES van a la lista de colisión
        muros_mapa = self.scene.get_sprite_list(self.CAPAS["muros"])
        if muros_mapa:
            for muro in muros_mapa:
                self.lista_bloques.append(muro)

        self.camera = CameraManager()
        self.hud = HUD()
        self.console = ConsoleUI()
        
        nota_prueba = Nota(500, "Se busca", "SE BUSCAN KORUS",
            "Si alguien lee esto...\nYo de niña tenía unos muñecos... \ny los he perdido \n¿me ayudas a encontrarlos? \n\nquizás recibas algo a cambio :)",
            "assets/items/Nota.png")
        nota_prueba.center_x = 106*32
        nota_prueba.center_y = 101*32
        self.item_manager.add_to_world(nota_prueba)
        
        self.sprite_jugador.inventory[0] = Pistola()
        self.sprite_jugador.inventory[1] = Cuchillo()

        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)
        self.nav_manager = SistemaNavegacion(self.lista_bloques)

        # Cargar enemigos desde Tiled
        Log.info("Game", f"Buscando capa de enemigos: {self.CAPAS.get('enemigos')}")
        enemigos_layer = self.tile_map.object_lists.get(self.CAPAS["enemigos"], [])
        Log.info("Game", f"Enemigos encontrados: {len(enemigos_layer)}")

        for enemy_obj in enemigos_layer:
            try:
                props = getattr(enemy_obj, 'properties', {})
                Log.info("Game", f"Enemigo: {getattr(enemy_obj, 'name', 'unnamed')}, props: {props}")

                enemy_id = props.get('tipo', 'bandido')
                subtipo = props.get('subtipo', 'melee')
                tipo_patrulla_str = props.get('tipo_patrulla', 'area')
                area_radio = props.get('area_radio', 500)
                dano = props.get('dano', 15.0)
                vista_rango = props.get('vista_rango', 800)

                if tipo_patrulla_str == 'waypoint':
                    tipo_patrulla = EnemigoIA.TIPO_WAYPOINT
                elif tipo_patrulla_str == 'area':
                    tipo_patrulla = EnemigoIA.TIPO_AREA
                elif tipo_patrulla_str == 'paredes':
                    tipo_patrulla = EnemigoIA.TIPO_PAREDES
                else:
                    tipo_patrulla = EnemigoIA.TIPO_AREA

                x = (enemy_obj.shape[0][0] + enemy_obj.shape[2][0]) / 2
                y = (enemy_obj.shape[0][1] + enemy_obj.shape[2][1]) / 2

                if subtipo == "ranged":
                    radio_R = props.get('radio_R', 450)
                    radio_r = props.get('radio_r', 200)
                    intervalo = props.get('intervalo', 2.0)
                    inteligencia = props.get('inteligencia', False)
                    rango_ataque = props.get('rango_ataque', 300)

                    enemigo = EnemigoRanged(
                        x=x, y=y,
                        tipo_patrulla=tipo_patrulla,
                        area_center=(x, y),
                        area_radio=area_radio,
                        dano_ataque=dano,
                        vista_rango=vista_rango,
                        radio_R=radio_R,
                        radio_r=radio_r,
                        intervalo_ataque=intervalo,
                        inteligencia=inteligencia,
                        rango_ataque=rango_ataque,
                        waypoints=None
                    )
                else:
                    velocidad = props.get('velocidad', 200)
                    velocidad_patrulla = props.get('velocidad_patrulla', 50)

                    if tipo_patrulla_str == "waypoint":
                        waypoints = [(x, y), (x+100, y), (x+100, y+100), (x, y+100)]
                        enemigo = EnemigoIA(
                            x=x, y=y,
                            tipo_patrulla=tipo_patrulla,
                            waypoints=waypoints,
                            dano_ataque=dano,
                            vista_rango=vista_rango,
                            velocidad=velocidad,
                            velocidad_patrulla=velocidad_patrulla
                        )
                    elif tipo_patrulla_str == "area":
                        enemigo = EnemigoIA(
                            x=x, y=y,
                            tipo_patrulla=tipo_patrulla,
                            area_center=(x, y),
                            area_radio=area_radio,
                            dano_ataque=dano,
                            vista_rango=vista_rango,
                            velocidad=velocidad,
                            velocidad_patrulla=velocidad_patrulla
                        )
                    else:
                        enemigo = EnemigoIA(
                            x=x, y=y,
                            tipo_patrulla=tipo_patrulla,
                            dano_ataque=dano,
                            vista_rango=vista_rango,
                            velocidad=velocidad,
                            velocidad_patrulla=velocidad_patrulla
                        )

                enemigo.enemy_id = enemy_id
                Log.info("Game", f"Enemigo creado: {enemy_id} en ({x}, {y})")

                self.lista_enemigos.append(enemigo)
            except Exception as e:
                Log.error("Game", f"Error creando enemigo: {e}")

        

        self.dm = DialogManager()
        self.dm.set_vista(self)
        # En tu setup del juego
        self.im = InteractionManager(self.sprite_jugador)

        # Añadir trampa
        trampa = SpikeTrap(106*32, 110*32)
        self.im.add_trap(trampa, trampa.activar)
        trampa = SpikeTrap(108*32, 110*32)
        self.im.add_trap(trampa, trampa.activar)
        trampa = SpikeTrap(109*32, 110*32)
        self.im.add_trap(trampa, trampa.activar)
        trampa = SpikeTrap(110*32, 110*32)
        self.im.add_trap(trampa, trampa.activar)

        # Añadir monedas
        for i in range(3):
            coin = MissionCoin((100 + (i*8))*32, 105*32)
            
            # Tienes que pasarle la categoría y las dos funciones de la moneda
            self.im.add_collectible(
                coin, 
                coin.categoria,         # "monedas_ancestrales"
                coin.al_recoger,        # Función al recoger una
                MissionCoin.mision_completada  # Función al recoger todas
            )

    def on_draw(self):
        self.clear()
        with self.camera.activate():
            self.scene.draw()            
            self.lista_bloques.draw()
            self.lista_puertas.draw()
            self.item_manager.draw()
            self.lista_proyectiles.draw()
            self.im.draw()
            self.lista_enemigos.draw()
            self.lista_jugadores.draw()
            self.lista_npc_sprites.draw()

            overlay = self.scene.get_sprite_list(self.CAPAS.get("overlay"))
            if overlay:
                overlay.draw()

            self.console.draw_world(self.lista_bloques, self.lista_enemigos, self.nav_manager, self.sprite_jugador)
            self.text_manager.draw()

        self.hud.draw(self.sprite_jugador)
        
        if self.show_inventory:
            mouse_pos = (self.mouse_pos_x, self.mouse_pos_y) if hasattr(self, 'mouse_pos_x') else None
            self.sprite_jugador.draw_inventory(mouse_pos)

        if self.sprite_jugador.vistaNota:
            NotaUI().draw(self.sprite_jugador.vistaNota.titulo, self.sprite_jugador.vistaNota.texto)

        if self.estado_actual == "DIALOGO":
            DialogUI().draw(self.dm.nodo_texto, self.dm.obtener_opciones())

        if self.estado_actual == "CONSOLE":
            self.console.draw()

    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)
        return (dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and dy < (sprite1.height / 2 + sprite2.height / 2 + margen))

    def on_update(self, delta_time):
        if self.estado_actual == "CONSOLE":
            self.console.update(delta_time, self)
            return
        if self.estado_actual == "DIALOGO" or self.show_inventory or self.sprite_jugador.vistaNota:
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
        
        player_x = self.sprite_jugador.center_x
        player_y = self.sprite_jugador.center_y
        
        for enemigo in self.lista_enemigos:
            dx = enemigo.center_x - player_x
            dy = enemigo.center_y - player_y
            if dx * dx + dy * dy > self.DISTANCIA_ACTUALIZACION ** 2:
                continue
            
            if hasattr(enemigo, 'update'):
                if hasattr(enemigo, 'puede_ver_player'):
                    sig = inspect.signature(enemigo.update)
                    if len(sig.parameters) >= 5:
                        enemigo.update(delta_time, self.sprite_jugador, self.lista_bloques, self.nav_manager, self.lista_proyectiles)
                    else:
                        enemigo.update(delta_time, self.sprite_jugador, self.lista_bloques, self.nav_manager)
                else:
                    enemigo.update(delta_time)

        for p in self.lista_proyectiles:
            dx = p.center_x - player_x
            dy = p.center_y - player_y
            if dx * dx + dy * dy > self.DISTANCIA_ACTUALIZACION ** 2:
                continue
            
            if hasattr(p, 'update'):
                p.update(delta_time, self.lista_bloques, self.lista_enemigos, self.sprite_jugador)
            elif hasattr(p, 'on_update'):
                p.on_update(delta_time)
            if hasattr(p, 'update_enemies'):
                p.update_enemies(self.lista_enemigos)
            if hasattr(p, '_actualizar_posicion'):
                p._actualizar_posicion()

        for p in self.lista_proyectiles[:]:
          if p.killed:
            self.lista_proyectiles.remove(p)
        
        arma = self.sprite_jugador.obtener_arma_activa()
        if arma and hasattr(arma, 'actualizar'):
            arma.actualizar(delta_time)

        self.physics_engine.update()
        self.camera.position = self.sprite_jugador.position
        self.text_manager.update()
        self.item_manager.update()
        self.im.update()

    def on_text_input(self, text):
        if self.estado_actual =="CONSOLE":
            self.console.input_text += text

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MenuPausa(self))
            return
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

        if self.sprite_jugador.vistaNota:
            if key == arcade.key.E:
                self.sprite_jugador.vistaNota = None
            return

        if self.show_inventory:
            if key == arcade.key.TAB:
                self.show_inventory = False
            elif key == arcade.key.Q:
                self.ejecutar_soltar_item()
            return

        if self.dm and self.estado_actual == "DIALOGO":
            if self.dm.on_key_press(key):
                self.estado_actual = "JUGANDO"
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
        
        for npc in self.lista_npcs:
            props = getattr(npc, 'properties', None)
            if props and props.get('dialogo'):
                dialogo = props['dialogo']
                if ':' in dialogo:
                    dialog_file, nodo_inicial = dialogo.split(':', 1)
                else:
                    dialog_file = dialogo
                    nodo_inicial = 'saludo'
                npc_x = (npc.shape[0][0] + npc.shape[2][0]) / 2
                npc_y = (npc.shape[0][1] + npc.shape[2][1]) / 2
                dx = abs(self.sprite_jugador.center_x - npc_x)
                dy = abs(self.sprite_jugador.center_y - npc_y)
                rango = props.get('rango', 80)
                if dx < rango and dy < rango * 1.5:
                    self.dm.cargar_dialogo(dialog_file)
                    self.dm.iniciar(nodo_inicial)
                    self.estado_actual = "DIALOGO"
                    return
        
        self.item_manager.intentar_recoger(self.sprite_jugador)

    def ejecutar_recargar(self):
        arma = self.sprite_jugador.obtener_arma_activa()
        if arma and hasattr(arma, 'recargar'):
            arma.recargar()

    def ejecutar_soltar_item(self):
        slot = self.sprite_jugador.vistaInventario.get_slot_at_pointer(self.mouse_pos_x, self.mouse_pos_y)
        if slot is not None:
            objeto = self.sprite_jugador.soltar_objeto(slot)
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
            if slot and slot < len(self.sprite_jugador.inventory):
                item = self.sprite_jugador.inventory[slot]
                ahora = time.time()
                es_doble_click = (slot == self._ultimo_click_slot and ahora - self._ultimo_click_tiempo < self._DOUBLE_CLICK_DELAY)
                self._ultimo_click_slot = slot
                self._ultimo_click_tiempo = ahora
                
                if item and hasattr(item, 'usar') and es_doble_click:
                    item.usar(self.sprite_jugador, slot, None, None, None)
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
    
    def cerrar_dialogo(self):
        if self.dm:
            self.dm.cerrar()
    
    def item_manager_add_item(self, item):
        self.item_manager.add_to_world(item)

    def _cargar_misiones(self):

        if not os.path.exists("savegame.json"):
            return

        try:
            with open("savegame.json", "r") as f:
                data = json.load(f)

            if "misiones" in data:
                QM.from_dict(data["misiones"])
        except Exception as e:
            pass


    def _on_player_death(self, data):
            self.window.show_view(VistaGameOver())

    def limpiar_estado(self):
        """Limpia a cero absoluto el estado visual, frena inputs y vacía los managers globales 
        sin destruir sus instancias, preparándolos para recibir datos nuevos."""
        Log.info("Game", "=== INICIANDO LIMPIEZA DEL ESTADO GLOBAL ===")

        # 1. Vaciar los managers por dentro llamando a sus nuevos métodos clear
        from dialog.dialog_system import DialogSystem

        QM.clear_manager()                             # Vacía progreso de misiones y el EventBus
        DialogSystem.get_instance().clear_manager()    # Resetea textos de diálogos, acciones y listeners UI
        ItemManager().clear()                          # Elimina los ítems esparcidos por el suelo
        InteractionManager().clear()                   # Limpia monedas, trampas y desvincula al jugador viejo

        # 2. Resetear estados lógicos internos de la interfaz de la vista
        self.estado_actual = "JUGANDO"
        self.show_inventory = False
        self._ultimo_click_slot = None
        self._ultimo_click_tiempo = 0.0

        # 3. Forzar el frenado de los inputs (soluciona el bug de caminar solos tras recargar)
        self.izquierda_presionado = False
        self.derecha_presionado = False
        self.arriba_presionado = False
        self.abajo_presionado = False
        self.shift_presionado = False

        # 4. Vaciar por completo las SpriteLists antiguas de Arcade para liberar memoria de video
        listas_a_limpiar = [
            'lista_jugadores', 'lista_enemigos', 'lista_puertas', 
            'lista_bloques', 'lista_npc_sprites', 'lista_proyectiles'
        ]
        for lista_attr in listas_a_limpiar:
            if hasattr(self, lista_attr) and getattr(self, lista_attr):
                getattr(self, lista_attr).clear()

        # 5. Re-inicializar las SpriteLists vacías listas para la nueva inyección de datos
        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques = arcade.SpriteList()
        self.lista_proyectiles = arcade.SpriteList()
        self.lista_npc_sprites = arcade.SpriteList()
        self.lista_npcs = []

        # 6. Reiniciar utilidades del motor de renderizado y UI básica de la pantalla
       
        self.text_manager = TextManager()
        self.camera = CameraManager()
        self.hud = HUD()
        self.console = ConsoleUI()
        
        Log.info("Game", "=== MUNDO LIMPIO: Todo listo para inyectar datos del JSON o Setup ===")