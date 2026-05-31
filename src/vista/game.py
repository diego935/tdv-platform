import arcade
import time
from vista.menu_pausa import MenuPausa
from config import (
    ANCHO_VENTANA, 
    ALTO_VENTANA, 
    COLOR_FONDO_JUEGO, 
    DISTANCIA_ACTUALIZACION,
    LINTERNA_APERTURA_GRADOS, 
    LINTERNA_ALCANCE,         
    LINTERNA_RADIO_JUGADOR,   
    LINTERNA_RADIO_MAX_MAPA,   
    LINTERNA_COLOR_OSCURIDAD,
    DURACION_DIA_SEGUNDOS, ALPHA_MIN_MEDIODIA, ALPHA_MAX_MEDIANOCHE)
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
import math

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
        self.timer_dia_noche = 0.0 
        self.alpha_actual_oscuridad = ALPHA_MIN_MEDIODIA
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
        
        self.playerDead= False; 
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
            "enemigos": "Enemigos",
            "arbustos": "Arbustos"
        }
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques = arcade.SpriteList()
        self.lista_jugadores = arcade.SpriteList()
        
        # Variables para doble click en inventario
        self._ultimo_click_slot = None
        self._ultimo_click_tiempo = 0.0
        self._DOUBLE_CLICK_DELAY = 0.3

       # variables sonido de fondo
        self.sonido_ambiente = None       
        self.reproductor_ambiente = None
        self.sonido_combate = None
        self.reproductor_combate = None
        self.en_combate = False
        self.DISTANCIA_ACTIVACION_COMBATE = 400.0
        
    def setup(self):
        #Cargar misiones guardadas
        self._cargar_misiones()
        QM.suscripcion_automatica()

        #Mapa--------------------------------------
        map_name = "assets/maps/mapa.tmx"
        layer_options = {
            self.CAPAS["muros"]: {"use_spatial_hash": True},
            "Arbustos": {"use_spatial_hash": True}
        }
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
        
        # Buscar zonas de activación de rejas en la zona segura (nombre: "activador")
        self.activadores_bounds = []
        for obj in eventos:
            name_lower = obj.name.lower() if obj.name else ""
            if name_lower == "activador":
                pts = obj.shape
                if isinstance(pts, list) and len(pts) >= 3:
                    self.activadores_bounds.append({
                        "x_min": min(p[0] for p in pts),
                        "x_max": max(p[0] for p in pts),
                        "y_min": min(p[1] for p in pts),
                        "y_max": max(p[1] for p in pts)
                    })
        
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


        
        if spawn:
            self.sprite_jugador.center_x = spawn.shape[0]
            self.sprite_jugador.center_y = spawn.shape[1]
        
        self.scene.add_sprite("Player", self.sprite_jugador)
        self.lista_jugadores.append(self.sprite_jugador)

        # Añadir NPCs a la lista de colisiones
        for npc_sprite in self.lista_npc_sprites:
            self.lista_bloques.append(npc_sprite)
        
        # Solo las PAREDES y ARBUSTOS van a la lista de colisión
        muros_mapa = self.scene.get_sprite_list(self.CAPAS["muros"])
        if muros_mapa:
            for muro in muros_mapa:
                self.lista_bloques.append(muro)

        arbustos_mapa = self.scene.get_sprite_list(self.CAPAS["arbustos"])
        if arbustos_mapa:
            for arbusto in arbustos_mapa:
                self.lista_bloques.append(arbusto)

        # Cargar las capas de Rejas y Palanca
        self.lista_rejas = self.scene.get_sprite_list("Rejas")
        self.lista_palanca = self.scene.get_sprite_list("Palanca")
        self.rejas_activas = False
        self.rejas_trial_activas = False
        self.rejas_segura_activas = False
        self.rejas_trial_sprites = []
        self.rejas_segura_sprites = []
        # Variables para el sistema de oleadas (trial) y spawn dinámico en Nido (ambos en Capa_spawn_enemigos)
        nido_layer = self.tile_map.object_lists.get("Capa_spawn_enemigos", [])
        self.zona_spawn = None
        self.zona_nido = None
        for obj in nido_layer:
            obj_name = getattr(obj, "name", "")
            if obj_name == "trial":
                self.zona_spawn = obj
            elif obj_name == "nido":
                self.zona_nido = obj

        self.oleadas_activas = False
        self.oleadas_completadas = False
        self.oleada_actual = 0
        self.max_oleadas = 3
        self.enemigos_oleada_actual = []
        self.timer_entre_oleadas = 0.0
        self.tiempo_espera_oleada = 5.0
        self.spawn_rate_nido = 6.0
        self.timer_spawn_nido = 0.0
        self.max_enemigos_nido = 15

        # Cargar textura de fondo fijo
        self.fondo_pantalla = arcade.load_texture("assets/fondos/fondo_bosque.png")


        self.camera = CameraManager()
        self.hud = HUD()
        self.console = ConsoleUI()
        
        # Buscar posiciones de Nota_bosque, Nota_palanca y nota_korus en la capa de Eventos
        pos_nota_bosque = None
        pos_nota_palanca = None
        pos_nota_korus = None
        self.objeto_palanca = None
        self.bounds_rejas_trial = None
        for obj in eventos:
            obj_name = getattr(obj, "name", "")
            if not obj_name:
                continue
            name_lower = obj_name.lower()
            if name_lower in ("nota_bosque", "nota_palanca", "nota_korus"):
                if isinstance(obj.shape, list) and len(obj.shape) >= 3:
                    x = (obj.shape[0][0] + obj.shape[2][0]) / 2
                    y = (obj.shape[0][1] + obj.shape[2][1]) / 2
                elif isinstance(obj.shape, tuple) or hasattr(obj.shape, "__len__"):
                    x = obj.shape[0]
                    y = obj.shape[1]
                else:
                    continue

                if name_lower == "nota_bosque":
                    pos_nota_bosque = (x, y)
                elif name_lower == "nota_palanca":
                    pos_nota_palanca = (x, y)
                elif name_lower == "nota_korus":
                    pos_nota_korus = (x, y)
            elif name_lower == "palanca":
                self.objeto_palanca = obj
            elif name_lower == "rejas_trial":
                pts = obj.shape
                if isinstance(pts, list) and len(pts) >= 3:
                    self.bounds_rejas_trial = {
                        "x_min": min(p[0] for p in pts),
                        "x_max": max(p[0] for p in pts),
                        "y_min": min(p[1] for p in pts),
                        "y_max": max(p[1] for p in pts)
                    }
                elif isinstance(pts, tuple) or hasattr(pts, "__len__"):
                    x = getattr(obj, "x", pts[0])
                    y = getattr(obj, "y", pts[1])
                    w = getattr(obj, "width", 0)
                    h = getattr(obj, "height", 0)
                    self.bounds_rejas_trial = {
                        "x_min": x,
                        "x_max": x + w,
                        "y_min": y,
                        "y_max": y + h
                    }
            elif name_lower == "rejas_segura":
                pts = obj.shape
                if isinstance(pts, list) and len(pts) >= 3:
                    self.bounds_rejas_segura = {
                        "x_min": min(p[0] for p in pts),
                        "x_max": max(p[0] for p in pts),
                        "y_min": min(p[1] for p in pts),
                        "y_max": max(p[1] for p in pts)
                    }
                elif isinstance(pts, tuple) or hasattr(pts, "__len__"):
                    x = getattr(obj, "x", pts[0])
                    y = getattr(obj, "y", pts[1])
                    w = getattr(obj, "width", 0)
                    h = getattr(obj, "height", 0)
                    self.bounds_rejas_segura = {
                        "x_min": x,
                        "x_max": x + w,
                        "y_min": y,
                        "y_max": y + h
                    }

        # Filtrar las rejas que pertenecen al trial
        self.rejas_trial_sprites = []
        if self.lista_rejas and self.bounds_rejas_trial:
            for reja in self.lista_rejas:
                if (self.bounds_rejas_trial["x_min"] <= reja.center_x <= self.bounds_rejas_trial["x_max"] and
                    self.bounds_rejas_trial["y_min"] <= reja.center_y <= self.bounds_rejas_trial["y_max"]):
                    self.rejas_trial_sprites.append(reja)
        
        if not self.rejas_trial_sprites and self.lista_rejas:
            self.rejas_trial_sprites = list(self.lista_rejas)

        # Filtrar las rejas que pertenecen a la zona segura
        self.rejas_segura_sprites = []
        if self.lista_rejas and getattr(self, "bounds_rejas_segura", None):
            for reja in self.lista_rejas:
                if (self.bounds_rejas_segura["x_min"] <= reja.center_x <= self.bounds_rejas_segura["x_max"] and
                    self.bounds_rejas_segura["y_min"] <= reja.center_y <= self.bounds_rejas_segura["y_max"]):
                    self.rejas_segura_sprites.append(reja)

        # Todas las rejas en el mapa inician inactivas (invisibles y sin colisiones físicas)
        if self.lista_rejas:
            for reja in self.lista_rejas:
                reja.visible = False

        nota_prueba = Nota(500, "Se busca", "SE BUSCAN KORUS",
            "Si alguien lee esto...\nYo de niña tenía unos muñecos... \ny los he perdido \n¿me ayudas a encontrarlos? \n\nquizás recibas algo a cambio :)",
            "assets/items/Nota.png")
        if pos_nota_korus:
            nota_prueba.center_x, nota_prueba.center_y = pos_nota_korus
        else:
            nota_prueba.center_x = (156 + 100) * 32
            nota_prueba.center_y = (151 + 100) * 32
        self.item_manager.add_to_world(nota_prueba)

        nota_bosque = Nota(500, "...", "Algo extraño pasa en este bosque", "Igual si pruebo a cruzarlo...", "assets/items/Nota.png")
        if pos_nota_bosque:
            nota_bosque.center_x, nota_bosque.center_y = pos_nota_bosque
        else:
            nota_bosque.center_x = (155.23 + 100) * 32
            nota_bosque.center_y = (80.52 + 100) * 32
        self.item_manager.add_to_world(nota_bosque)

        nota_palanca = Nota(501, "Nota", "Palanca", "Me pregunto que pasará si pulso la palanca...", "assets/items/Nota.png")
        if pos_nota_palanca:
            nota_palanca.center_x, nota_palanca.center_y = pos_nota_palanca
        else:
            nota_palanca.center_x = (85 + 100) * 32
            nota_palanca.center_y = (160 + 100) * 32
        self.item_manager.add_to_world(nota_palanca)

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
                x = (enemy_obj.shape[0][0] + enemy_obj.shape[2][0]) / 2
                y = (enemy_obj.shape[0][1] + enemy_obj.shape[2][1]) / 2

                # Si el enemigo está en la zona del nido, lo ignoramos para spawnearlo dinámicamente
                if self.zona_nido:
                    pts = self.zona_nido.shape
                    nido_x_min = min(p[0] for p in pts)
                    nido_x_max = max(p[0] for p in pts)
                    nido_y_min = min(p[1] for p in pts)
                    nido_y_max = max(p[1] for p in pts)
                    if nido_x_min <= x <= nido_x_max and nido_y_min <= y <= nido_y_max:
                        Log.info("Game", f"Ignorando enemigo pre-generado en zona del nido en ({x}, {y})")
                        continue

                props = getattr(enemy_obj, 'properties', {})
                Log.info("Game", f"Enemigo: {getattr(enemy_obj, 'name', 'unnamed')}, props: {props}")

                enemy_id = props.get('tipo', 'bandido')
                subtipo = props.get('subtipo', 'melee')
                tipo_patrulla_str = props.get('tipo_patrulla', 'area')
                area_radio = props.get('area_radio', 500)
                dano = props.get('dano', 5.0 if subtipo == 'ranged' else 15.0)
                vista_rango = props.get('vista_rango', 800)

                if tipo_patrulla_str == 'waypoint':
                    tipo_patrulla = EnemigoIA.TIPO_WAYPOINT
                elif tipo_patrulla_str == 'area':
                    tipo_patrulla = EnemigoIA.TIPO_AREA
                elif tipo_patrulla_str == 'paredes':
                    tipo_patrulla = EnemigoIA.TIPO_PAREDES
                else:
                    tipo_patrulla = EnemigoIA.TIPO_AREA

                if subtipo == "ranged":
                    radio_R = props.get('radio_R', 450)
                    radio_r = props.get('radio_r', 200)
                    intervalo = props.get('intervalo', 2.0)
                    inteligencia = props.get('inteligencia', False)
                    rango_ataque = props.get('rango_ataque', 300)
                    velocidad = props.get('velocidad', 300)

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
                        velocidad=velocidad,
                        waypoints=None
                    )
                else:
                    velocidad = props.get('velocidad', 320)
                    velocidad_patrulla = props.get('velocidad_patrulla', 120)

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

        # Añadir trampas desde el mapa Tiled (Eventos)
        for obj in eventos:
            obj_name = getattr(obj, "name", "")
            if not obj_name:
                continue
            
            name_lower = obj_name.lower()
            if name_lower in ("trampa", "trampa_venenosa"):
                if isinstance(obj.shape, list) and len(obj.shape) >= 3:
                    x = (obj.shape[0][0] + obj.shape[2][0]) / 2
                    y = (obj.shape[0][1] + obj.shape[2][1]) / 2
                elif isinstance(obj.shape, tuple) or hasattr(obj.shape, "__len__"):
                    x = obj.shape[0]
                    y = map_height - obj.shape[1]
                else:
                    Log.warning("Game", f"Objeto trampa {obj_name} con shape no soportada: {obj.shape}")
                    continue

                if name_lower == "trampa":
                    # Trampa común (sin veneno)
                    trampa = SpikeTrap(x, y, damage_veneno=0, tiempo_veneno=0)
                else:
                    # Trampa venenosa (con valores de veneno por defecto)
                    trampa = SpikeTrap(x, y)
                
                self.im.add_trap(trampa, trampa.activar)
                Log.info("Game", f"Trampa '{obj_name}' generada en ({x}, {y})")

        # Añadir monedas
        for i in range(3):
            coin = MissionCoin((150 + 100 + (i*8))*32, (155 + 100)*32)
            
            # Tienes que pasarle la categoría y las dos funciones de la moneda
            self.im.add_collectible(
                coin, 
                coin.categoria,         # "monedas_ancestrales"
                coin.al_recoger,        # Función al recoger una
                MissionCoin.mision_completada  # Función al recoger todas
            )
        
       #Cargar e iniciar sonido
        try:
            self.sonido_ambiente = arcade.load_sound("assets/musica/ambiente_basico.mp3")
            self.sonido_combate = arcade.load_sound("assets/musica/ambiente_PVP.mp3")
 
            self.reproductor_ambiente = arcade.play_sound(self.sonido_ambiente, volume=0.5, loop=True)
            Log.info("Audio", "Sonido ambiente continuo iniciado en bucle.")
        except Exception as e:
            Log.error("Audio", f"No se pudo cargar el sistema de audio: {e}")

    def on_draw(self):
        self.clear()

        if getattr(self, "fondo_pantalla", None):
            arcade.draw_texture_rect(
                self.fondo_pantalla,
                arcade.XYWH(
                    self.window.width // 2,
                    self.window.height // 2,
                    self.window.width,
                    self.window.height
                )
            )

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
            
            self.dibujar_linterna_vectorial()

            self.console.draw_world(self.lista_bloques, self.lista_enemigos, self.nav_manager, self.sprite_jugador)
            self.text_manager.draw()

            if self.playerDead:
                arcade.draw_lrbt_rectangle_filled(
                    self.sprite_jugador.position[0] - 2000,
                    self.sprite_jugador.position[0] + 2000,
                    self.sprite_jugador.position[1] - 2000,
                    self.sprite_jugador.position[1] + 2000,
                    (0, 0, 0, int(255 * self.it / 400))
                )

        self.hud.draw(self.sprite_jugador)
        
        # Dibujar información de oleadas
        if getattr(self, 'oleadas_activas', False):
            window = self.window
            arcade.draw_text(
                f"OLEADA {self.oleada_actual} / {self.max_oleadas}",
                window.width / 2,
                window.height - 100,
                arcade.color.RED,
                font_size=20,
                bold=True,
                anchor_x="center"
            )
            num_enemigos = len(self.enemigos_oleada_actual)
            arcade.draw_text(
                f"Enemigos restantes: {num_enemigos}",
                window.width / 2,
                window.height - 125,
                arcade.color.WHITE,
                font_size=12,
                bold=True,
                anchor_x="center"
            )
        elif getattr(self, 'timer_entre_oleadas', 0.0) > 0:
            window = self.window
            arcade.draw_text(
                f"Siguiente oleada en: {int(self.timer_entre_oleadas) + 1}s",
                window.width / 2,
                window.height - 100,
                arcade.color.GOLD,
                font_size=18,
                bold=True,
                anchor_x="center"
            )
        
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
        if self.playerDead: 
            delta_time *= (0.8)** int(self.it/20)
            self.it +=1
            if self.it >= 400: 
                self.window.show_view(VistaGameOver())
            return

        if self.estado_actual == "CONSOLE":
            self.console.update(delta_time, self)
            return
        if self.estado_actual == "DIALOGO" or self.show_inventory or self.sprite_jugador.vistaNota:
            return

        self.actualizar_oleadas(delta_time)

        # Actualizar spawn dinámico en la zona del nido
        if self.zona_nido:
            pts = self.zona_nido.shape
            nido_x_min = min(p[0] for p in pts)
            nido_x_max = max(p[0] for p in pts)
            nido_y_min = min(p[1] for p in pts)
            nido_y_max = max(p[1] for p in pts)
            
            enemigos_en_nido = 0
            for e in self.lista_enemigos:
                if e.vida > 0 and nido_x_min <= e.center_x <= nido_x_max and nido_y_min <= e.center_y <= nido_y_max:
                    enemigos_en_nido += 1
            
            if enemigos_en_nido < self.max_enemigos_nido:
                self.timer_spawn_nido -= delta_time
                if self.timer_spawn_nido <= 0:
                    self.spawnear_enemigo_nido()
                    self.timer_spawn_nido = self.spawn_rate_nido

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
        
        # Comprobar trigger de los activadores de la zona segura
        if not getattr(self, "rejas_segura_activas", False):
            en_activador = False
            if getattr(self, "activadores_bounds", None):
                for bounds in self.activadores_bounds:
                    if bounds["x_min"] <= player_x <= bounds["x_max"] and bounds["y_min"] <= player_y <= bounds["y_max"]:
                        en_activador = True
                        break

            if en_activador:
                # Al ser una zona segura no debe activar nada más (como las oleadas) aparte de las rejas
                self.activar_rejas(iniciar_oleadas=False)
        
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
        self.actualizar_ciclo_dia_noche(delta_time)

        # alternancia de música pvp y ambiente

        enemigo_cercano_detectado = False
        px = self.sprite_jugador.center_x
        py = self.sprite_jugador.center_y

        for enemigo in self.lista_enemigos:
            if hasattr(enemigo, 'vida') and enemigo.vida <= 0:
                continue
                
            dx = enemigo.center_x - px
            dy = enemigo.center_y - py
            distancia_cuadrada = dx * dx + dy * dy

            if distancia_cuadrada <= self.DISTANCIA_ACTIVACION_COMBATE ** 2:
                enemigo_cercano_detectado = True
                break

        # si hay enemigo
        if enemigo_cercano_detectado and not self.en_combate:
            self.en_combate = True
            Log.info("Audio", "¡Enemigo de oleada detectado cerca! Cambiando a música de combate.")
            
            if self.reproductor_ambiente:
                arcade.stop_sound(self.reproductor_ambiente)
                self.reproductor_ambiente = None
            
            if self.sonido_combate:
                self.reproductor_combate = arcade.play_sound(self.sonido_combate, volume=0.5, loop=True)

        # si ya no hay enemigos
        elif not enemigo_cercano_detectado and self.en_combate:
            self.en_combate = False
            Log.info("Audio", "Zona despejada de amenazas. Volviendo a la música ambiental.")
            
            if self.reproductor_combate:
                arcade.stop_sound(self.reproductor_combate)
                self.reproductor_combate = None
                
            if self.sonido_ambiente:
                self.reproductor_ambiente = arcade.play_sound(self.sonido_ambiente, volume=0.5, loop=True)
    

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
        elif key == arcade.key.F:
            if not self.sprite_jugador.linterna_encendida and self.sprite_jugador.linterna_bateria > 0:
                self.sprite_jugador.linterna_encendida = True
                Log.info("Linterna", "Linterna ENCENDIDA")
            else:
                self.sprite_jugador.linterna_encendida = False
                Log.info("Linterna", "Linterna APAGADA")
        elif key == arcade.key.R:
            self.ejecutar_recargar()
        elif key in [arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3, arcade.key.KEY_4]:
            self.sprite_jugador.indice_activo = key - arcade.key.KEY_1

    def ejecutar_interaccion(self):
        # Comprobar interacción con la palanca de Eventos (objeto "palanca")
        if getattr(self, 'objeto_palanca', None):
            obj = self.objeto_palanca
            pts = obj.shape
            esta_cerca = False
            if isinstance(pts, list) and len(pts) >= 3:
                x_min = min(p[0] for p in pts)
                x_max = max(p[0] for p in pts)
                y_min = min(p[1] for p in pts)
                y_max = max(p[1] for p in pts)
                if x_min - 30 <= self.sprite_jugador.center_x <= x_max + 30 and y_min - 30 <= self.sprite_jugador.center_y <= y_max + 30:
                    esta_cerca = True
            elif isinstance(pts, tuple) or hasattr(pts, "__len__"):
                cx = pts[0]
                cy = pts[1]
                dx = abs(self.sprite_jugador.center_x - cx)
                dy = abs(self.sprite_jugador.center_y - cy)
                if dx < 100 and dy < 100:
                    esta_cerca = True
            
            if esta_cerca:
                self.activar_rejas()
                return

        # Comprobar interacción con la palanca de la capa "Palanca" (legacy)
        if hasattr(self, 'lista_palanca') and self.lista_palanca:
            for palanca in self.lista_palanca:
                if self.cerca_con_margen(self.sprite_jugador, palanca, 30):
                    self.activar_rejas()
                    return

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

    def activar_rejas(self, iniciar_oleadas=True):
        if iniciar_oleadas:
            if getattr(self, "rejas_trial_activas", False):
                return

            # Activar las rejas del trial: mostrar sprites y añadir colisiones (bloquea el paso)
            if self.rejas_trial_sprites:
                for reja in self.rejas_trial_sprites:
                    reja.visible = True
                    if reja not in self.lista_bloques:
                        self.lista_bloques.append(reja)
            self.rejas_trial_activas = True
            Log.info("Palanca", "Rejas del Trial ACTIVADAS: colisiones añadidas y mostradas (paso bloqueado)")

            # Iniciar oleadas al cerrar las rejas
            if not getattr(self, "oleadas_activas", False) and not getattr(self, "oleadas_completadas", False):
                self.iniciar_oleadas()
        else:
            if getattr(self, "rejas_segura_activas", False):
                return

            # Activar las rejas de la zona segura: mostrar sprites y añadir colisiones (bloquea el paso)
            if self.rejas_segura_sprites:
                for reja in self.rejas_segura_sprites:
                    reja.visible = True
                    if reja not in self.lista_bloques:
                        self.lista_bloques.append(reja)
            self.rejas_segura_activas = True
            Log.info("Palanca", "Rejas de Zona Segura ACTIVADAS: colisiones añadidas y mostradas (paso bloqueado)")

        # Actualizar dinámicamente el motor de física y el pathfinding
        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)
        self.nav_manager.actualizar_desde_bloques(self.lista_bloques)

    def iniciar_oleadas(self):
        self.oleadas_activas = True
        self.oleada_actual = 1
        self.enemigos_oleada_actual = []
        self.timer_entre_oleadas = 0.0
        self.spawnear_oleada(self.oleada_actual)
        Log.info("Waves", "Sistema de oleadas iniciado en la zona Spawn")

    def spawnear_enemigo_nido(self):
        if not self.zona_nido:
            return
            
        pts = self.zona_nido.shape
        x_min = int(min(p[0] for p in pts))
        x_max = int(max(p[0] for p in pts))
        y_min = int(min(p[1] for p in pts))
        y_max = int(max(p[1] for p in pts))
        
        spawn_x, spawn_y = (x_min + x_max) / 2, (y_min + y_max) / 2
        
        # Buscar punto transitable
        for _ in range(50):
            rx = random.randint(x_min, x_max)
            ry = random.randint(y_min, y_max)
            gx = rx // 32
            gy = ry // 32
            nodo = self.nav_manager.grid_pathfinder.grid.get((gx, gy))
            if nodo and nodo.transitable:
                spawn_x, spawn_y = rx, ry
                break
                
        tipo = "ranged" if random.random() < 0.3 else "melee"
        
        if tipo == "ranged":
            enemigo = EnemigoRanged(
                x=spawn_x, y=spawn_y,
                tipo_patrulla=EnemigoIA.TIPO_AREA,
                area_center=(spawn_x, spawn_y),
                area_radio=250,
                dano_ataque=5.0,
                vista_rango=800,
                radio_R=450,
                radio_r=200,
                intervalo_ataque=2.0,
                inteligencia=False,
                rango_ataque=300,
                velocidad=300,
                velocidad_patrulla=100
            )
        else:
            enemigo = EnemigoIA(
                x=spawn_x, y=spawn_y,
                tipo_patrulla=EnemigoIA.TIPO_AREA,
                area_center=(spawn_x, spawn_y),
                area_radio=250,
                dano_ataque=15.0,
                vista_rango=800,
                velocidad=300,
                velocidad_patrulla=120
            )
            
        enemigo.enemy_id = "bandido"
        self.lista_enemigos.append(enemigo)
        Log.info("Game", f"Enemigo dinámico ({tipo}) spawneado en zona de nido en ({spawn_x}, {spawn_y})")

    def spawnear_enemigo(self, tipo="melee"):
        if not self.zona_spawn:
            return
        
        pts = self.zona_spawn.shape
        x_min = int(min(p[0] for p in pts))
        x_max = int(max(p[0] for p in pts))
        y_min = int(min(p[1] for p in pts))
        y_max = int(max(p[1] for p in pts))
        
        spawn_x, spawn_y = (x_min + x_max) / 2, (y_min + y_max) / 2
        
        # Intentar buscar un punto transitable
        for _ in range(50):
            rx = random.randint(x_min, x_max)
            ry = random.randint(y_min, y_max)
            gx = rx // 32
            gy = ry // 32
            nodo = self.nav_manager.grid_pathfinder.grid.get((gx, gy))
            if nodo and nodo.transitable:
                spawn_x, spawn_y = rx, ry
                break
                
        if tipo == "ranged":
            enemigo = EnemigoRanged(
                x=spawn_x, y=spawn_y,
                tipo_patrulla=EnemigoIA.TIPO_AREA,
                area_center=(spawn_x, spawn_y),
                area_radio=250,
                dano_ataque=5.0,
                vista_rango=800,
                radio_R=450,
                radio_r=200,
                intervalo_ataque=2.0,
                inteligencia=False,
                rango_ataque=300,
                velocidad=300,
                velocidad_patrulla=100
            )
        else:
            enemigo = EnemigoIA(
                x=spawn_x, y=spawn_y,
                tipo_patrulla=EnemigoIA.TIPO_AREA,
                area_center=(spawn_x, spawn_y),
                area_radio=250,
                dano_ataque=15.0,
                vista_rango=800,
                velocidad=300,
                velocidad_patrulla=120
            )
        
        enemigo.enemy_id = "bandido"
        self.lista_enemigos.append(enemigo)
        self.enemigos_oleada_actual.append(enemigo)

    def spawnear_oleada(self, num_oleada):
        config_oleadas = {
            1: {"melee": 5, "ranged": 1},
            2: {"melee": 7, "ranged": 2},
            3: {"melee": 10, "ranged": 4}
        }
        
        config = config_oleadas.get(num_oleada, {"melee": 2, "ranged": 0})
        self.enemigos_oleada_actual = []
        
        for _ in range(config["melee"]):
            self.spawnear_enemigo("melee")
        for _ in range(config["ranged"]):
            self.spawnear_enemigo("ranged")
            
        Log.info("Waves", f"Oleada {num_oleada} spawneada: {config['melee']} melee, {config['ranged']} ranged")

    def actualizar_oleadas(self, delta_time):
        # 1. Si las oleadas están activas
        if self.oleadas_activas:
            # Filtrar enemigos vivos de la oleada actual
            self.enemigos_oleada_actual = [e for e in self.enemigos_oleada_actual if e.vida > 0]
            
            # Si todos los enemigos de la oleada han sido derrotados
            if len(self.enemigos_oleada_actual) == 0:
                if self.timer_entre_oleadas == 0.0:
                    # Iniciar tiempo de espera para la siguiente oleada
                    if self.oleada_actual < self.max_oleadas:
                        self.timer_entre_oleadas = self.tiempo_espera_oleada
                        Log.info("Waves", f"Oleada {self.oleada_actual} superada. Preparando siguiente oleada...")
                    else:
                        # Completó todas las oleadas
                        self.oleadas_activas = False
                        self.oleadas_completadas = True
                        self.text_manager.show_message("¡ZONA LIMPIA! OLEADAS COMPLETADAS", self.sprite_jugador.center_x, self.sprite_jugador.center_y + 40, arcade.color.GREEN)
                        Log.info("Waves", "Todas las oleadas de la zona Spawn completadas")

                        # Abrir las rejas automáticamente al completar las oleadas
                        if getattr(self, "rejas_trial_activas", False) and self.rejas_trial_sprites:
                            for reja in self.rejas_trial_sprites:
                                reja.visible = False
                                if reja in self.lista_bloques:
                                    self.lista_bloques.remove(reja)
                            self.rejas_trial_activas = False
                            self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)
                            self.nav_manager.actualizar_desde_bloques(self.lista_bloques)
                            Log.info("Waves", "Rejas abiertas automáticamente al limpiar la zona")
                
        # 2. Temporizador de cuenta atrás entre oleadas
        if self.timer_entre_oleadas > 0:
            self.timer_entre_oleadas -= delta_time
            if self.timer_entre_oleadas <= 0:
                self.timer_entre_oleadas = 0.0
                self.oleada_actual += 1
                self.spawnear_oleada(self.oleada_actual)

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
        pass

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
        self.playerDead = True; 
        self.it = 0; 

    def limpiar_estado(self):
        """Limpia a cero absoluto el estado visual, frena inputs y vacía los managers globales 
        sin destruir sus instancias, preparándolos para recibir datos nuevos."""
        Log.info("Game", "=== INICIANDO LIMPIEZA DEL ESTADO GLOBAL ===")
        
        # Detener audio
        if self.reproductor_ambiente:
            arcade.stop_sound(self.reproductor_ambiente)
            self.reproductor_ambiente = None
        if self.reproductor_combate:
            arcade.stop_sound(self.reproductor_combate)
            self.reproductor_combate = None
        self.en_combate = False

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
        
        # 7. Reiniciar variables de oleadas y fondo
        self.zona_spawn = None
        self.oleadas_activas = False
        self.oleadas_completadas = False
        self.oleada_actual = 0
        self.enemigos_oleada_actual = []
        self.timer_entre_oleadas = 0.0
        self.fondo_pantalla = None

        Log.info("Game", "=== MUNDO LIMPIO: Todo listo para inyectar datos del JSON o Setup ===")

    def on_hide_view(self):
        Log.info("Audio", "Juego pausado: Silenciando pistas de audio.")
        
        if self.reproductor_ambiente:
            self.reproductor_ambiente.volume = 0.0
        if self.reproductor_combate:
            self.reproductor_combate.volume = 0.0

        if self.sprite_jugador and self.sprite_jugador.player_pasos:
            arcade.stop_sound(self.sprite_jugador.player_pasos)
            self.sprite_jugador.player_pasos = None
            self.sprite_jugador.sonando_pasos = False

    def on_show_view(self):
        Log.info("Audio", "Juego reanudado: Restaurando volumen de la pista activa.")

        if self.en_combate and self.reproductor_combate:
            self.reproductor_combate.volume = 0.5
        elif not self.en_combate and self.reproductor_ambiente:
            self.reproductor_ambiente.volume = 0.5


    def dibujar_linterna_vectorial(self):
            if self.mouse_world_x is None or self.mouse_world_y is None:
                return
            # 1. Posición central del jugador
            cx = self.sprite_jugador.center_x
            cy = self.sprite_jugador.center_y

            # 2. Calcular el ángulo hacia el ratón (en radianes)
            dx = self.mouse_world_x - cx
            dy = self.mouse_world_y - cy
            angulo_centro = math.atan2(dy, dx)

            # 3. Mapeo de parámetros desde el archivo Config
            apertura = math.radians(LINTERNA_APERTURA_GRADOS)
            alcance_luz = LINTERNA_ALCANCE
            radio_interior = LINTERNA_RADIO_JUGADOR
            radio_oscuridad = LINTERNA_RADIO_MAX_MAPA

            # Asignamos el color usando el alpha calculado dinámicamente
            color_oscuridad = (0, 0, 0, self.alpha_actual_oscuridad)

            # Si el día está muy claro, saltamos el dibujado para ahorrar procesamiento
            if self.alpha_actual_oscuridad <= 5:
                return

            # 4. Definir las zonas de luz y oscuridad
            angulo_luz_der = angulo_centro - apertura
            angulo_luz_izq = angulo_centro + apertura
            arco_negro = 2 * math.pi - (apertura * 2)

            # 5. Dibujar el anillo (donut) de oscuridad a trozos para evitar parpadeos
            segmentos = 24 
            for i in range(segmentos):
                a1 = angulo_luz_izq + (i * arco_negro / segmentos)
                a2 = angulo_luz_izq + ((i + 1) * arco_negro / segmentos)

                p1_in = (cx + math.cos(a1) * radio_interior, cy + math.sin(a1) * radio_interior)
                p2_in = (cx + math.cos(a2) * radio_interior, cy + math.sin(a2) * radio_interior)
                
                p1_out = (cx + math.cos(a1) * radio_oscuridad, cy + math.sin(a1) * radio_oscuridad)
                p2_out = (cx + math.cos(a2) * radio_oscuridad, cy + math.sin(a2) * radio_oscuridad)

                arcade.draw_polygon_filled([p1_in, p2_in, p2_out, p1_out], color_oscuridad)

            # 6. Dibujar las barreras frontales que limitan el alcance del cono de luz
            p_luz_der_out = (cx + math.cos(angulo_luz_der) * radio_oscuridad, cy + math.sin(angulo_luz_der) * radio_oscuridad)
            p_luz_izq_out = (cx + math.cos(angulo_luz_izq) * radio_oscuridad, cy + math.sin(angulo_luz_izq) * radio_oscuridad)

            p_luz_der_fin = (cx + math.cos(angulo_luz_der) * alcance_luz, cy + math.sin(angulo_luz_der) * alcance_luz)
            p_luz_izq_fin = (cx + math.cos(angulo_luz_izq) * alcance_luz, cy + math.sin(angulo_luz_izq) * alcance_luz)

            # Bloque frontal que tapa la luz sobrante a lo largo de la pantalla
            arcade.draw_polygon_filled([p_luz_der_fin, p_luz_der_out, p_luz_izq_out, p_luz_izq_fin], color_oscuridad)


    def actualizar_ciclo_dia_noche(self, delta_time): 
        self.timer_dia_noche = (self.timer_dia_noche + delta_time) % DURACION_DIA_SEGUNDOS

        progreso_ciclo = self.timer_dia_noche / DURACION_DIA_SEGUNDOS
        factor_oscuridad = (1.0 - math.cos(progreso_ciclo * 2 * math.pi)) / 2.0
        rango_alpha = ALPHA_MAX_MEDIANOCHE - ALPHA_MIN_MEDIODIA
        self.alpha_actual_oscuridad = int(ALPHA_MIN_MEDIODIA + (factor_oscuridad * rango_alpha))
