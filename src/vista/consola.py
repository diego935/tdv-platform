import arcade
import time 
from items.items import *
from entities.blocks import * 
from entities.enemy import *


class ConsoleUI:
    def __init__(self):
        self.active = False
        self.input_text = ""
        self.history = []
        self.background_color = (0, 0, 0, 150)
        self.flags = {
            "hitbox": False,
            "path": False,
            "grid": False,
            "test_nodes": False,
            "blocks" : False,
            "chunks": False
        }
        self.block_timer = 0.0
        self.test_origin = None
        self.test_dest = None
        self.test_path = []

    def log(self, text, tipo="INFO"):
        colores = {
            "INFO": arcade.color.WHITE,
            "ERROR": arcade.color.RED_DEVIL,
            "SUCCESS": arcade.color.LIME_GREEN,
            "CMD": arcade.color.CYAN
        }
        color = colores.get(tipo, arcade.color.WHITE)
        # Guardamos una tupla (texto, color)
        self.history.append((text, color))


    def draw_world(self, lista_bloques, lista_enemigos, nav_manager, sprite_jugador=None):
        """Dibuja cosas en las coordenadas del juego (dentro de la cámara)"""
        if not self.active:
            return
            
        if self.flags["chunks"]:
            # Obtenemos el tamaño de los chunks (por defecto 512 si no existe)
            size = getattr(nav_manager, "chunk_size", 512)
            
            # Dibujamos un área alrededor de la cámara (puedes ajustar el rango)
            window = arcade.get_window()
            cam_x, cam_y = window.current_camera.position
            
            start_x = int((cam_x - window.width) // size) * size
            end_x = int((cam_x + window.width) // size) * size
            start_y = int((cam_y - window.height) // size) * size
            end_y = int((cam_y + window.height) // size) * size

            for x in range(start_x, end_x + size, size):
                arcade.draw_line(x, start_y, x, end_y, arcade.color.ASH_GREY, 1)
            for y in range(start_y, end_y + size, size):
                arcade.draw_line(start_x, y, end_x, y, arcade.color.ASH_GREY, 1)
            
            # Opcional: Dibujar el ID del chunk en el centro
            for x in range(start_x, end_x, size):
                for y in range(start_y, end_y, size):
                    cx, cy = x // size, y // size
                    arcade.draw_text(f"[{cx},{cy}]", x + 5, y + 5, 
                                     arcade.color.ASH_GREY, 8)

        # 1. Dibujar Hitboxes (rectángulos verdes alrededor de bloques)
        if self.flags["hitbox"]:
            for bloque in lista_bloques:
                arcade.draw_rect_outline(bloque.rect, arcade.color.LIME_GREEN, 2)
            for enemigo in lista_enemigos:
                arcade.draw_rect_outline(enemigo.rect, arcade.color.RED, 2)

    
        if self.flags["path"] and sprite_jugador:
            for ene in lista_enemigos:
                ve_jugador = arcade.has_line_of_sight(ene.position, sprite_jugador.position, lista_bloques)
                color = arcade.color.RED if ve_jugador else arcade.color.GRAY
                arcade.draw_line(ene.center_x, ene.center_y,
                                sprite_jugador.center_x, sprite_jugador.center_y,
                                color, 1)

        # 2. Dibujar el Grid de pathfinding (celdas 32x32)
        if self.flags["grid"] and nav_manager.grafo:
            if hasattr(nav_manager.grafo, 'debug_dibujar_grid'):
                nav_manager.grafo.debug_dibujar_grid(
                    color_transitable=arcade.color.DARK_GREEN,
                    color_bloqueado=arcade.color.DARK_RED,
                    alpha=40
                )

        if self.flags["test_nodes"]:
            # Dibujar origen (Amarillo)
            if self.test_origin:
                arcade.draw_circle_filled(self.test_origin[0], self.test_origin[1], 10, arcade.color.YELLOW)
                arcade.draw_circle_outline(self.test_origin[0], self.test_origin[1], 10, arcade.color.BLACK, 2)
                arcade.draw_text("START", self.test_origin[0] + 12, self.test_origin[1] + 12, arcade.color.YELLOW, 12)

            # Dibujar destino (Naranja)
            if self.test_dest:
                arcade.draw_circle_filled(self.test_dest[0], self.test_dest[1], 10, arcade.color.ORANGE)
                arcade.draw_circle_outline(self.test_dest[0], self.test_dest[1], 10, arcade.color.BLACK, 2)
                arcade.draw_text("END", self.test_dest[0] + 12, self.test_dest[1] + 12, arcade.color.ORANGE, 12)

            # Dibujar la línea del camino resultante
            if self.test_path and len(self.test_path) > 1:
                # Línea principal
                arcade.draw_line_strip(self.test_path, arcade.color.CYAN, 4)
                # Puntos de la ruta
                for i, punto in enumerate(self.test_path):
                    color = arcade.color.WHITE if i == 0 else arcade.color.LIME_GREEN if i == len(self.test_path) - 1 else arcade.color.CYAN
                    radio = 6 if i in [0, len(self.test_path) - 1] else 4
                    arcade.draw_circle_filled(punto[0], punto[1], radio, color)
                    arcade.draw_circle_outline(punto[0], punto[1], radio, arcade.color.BLACK, 1)


    def update(self, delta_time, vista):
        if self.flags["blocks"]:
            self.block_timer += delta_time
            while self.block_timer >= 0.5:
                self.block_timer -= 0.5
                self.spawn_block(vista)
        else:
            self.block_timer = 0.0
    def spawn_block(self, vista):
        size = 32
        nuevo_bloque = Bloque(size, size, color=arcade.color.GRAY)
        nuevo_bloque.position = (vista.mouse_world_x, vista.mouse_world_y)
        vista.lista_bloques.append(nuevo_bloque)
            
        
    def draw(self):
        if not self.active:
            return
            
        window = arcade.get_window()
        
        # --- LÓGICA DEL PARPADEO ---
        # time.time() devuelve segundos (ej: 16485.45)
        # Multiplicamos por 2 para que cambie cada 0.5s y usamos % 2 para obtener 0 o 1
        mostrar_cursor = int(time.time() * 2) % 2 == 0
        cursor = "_" if mostrar_cursor else ""
        # ----------------------------

        # Fondo
        arcade.draw_rect_filled(
            arcade.rect.XYWH(window.width/2, window.height - 100, window.width, 200),
            self.background_color
        )
        
        # Dibujar el texto con el cursor dinámico
        arcade.draw_text(
            f"> {self.input_text}{cursor}", # <-- Aquí usamos la variable cursor
            20, window.height - 180,
            arcade.color.LIME_GREEN,
            font_size=14,
            font_name="Courier New"
        )
        
        # Historial
        for i, msg in enumerate(self.history[-5:]):
            arcade.draw_text(
                msg, 20, window.height - 150 + (i * 20),
                arcade.color.WHITE, font_size=10
            )

    def add_to_history(self, text):
        self.history.append(text)


def cmd_spawn(vista, args):
    nombre = args[0].lower() if args else "objeto"
    
    if nombre == "botiquin":
        nuevo_item = Botiquin() 
    else:
        nuevo_item = BaseItem(99, nombre.capitalize(), "assets/items/Flint.png")
    

    nuevo_item.center_x = vista.sprite_jugador.center_x + 60
    nuevo_item.center_y = vista.sprite_jugador.center_y
    
    vista.item_manager.add_to_world(nuevo_item)
    
    return f"Entidad '{nombre.capitalize()}' generada.", "SUCCESS"

def cmd_tp(vista, args):
    if len(args) < 2: return "Error: Uso -> tp <x> <y>", "ERROR"
    vista.sprite_jugador.position = (float(args[0])*32, float(args[1])*32)
    vista.camera.position = vista.sprite_jugador.position
    return f"Teletransportado a {args[0]}, {args[1]}", "SUCCESS"

def cmd_heal(vista, args):
    vista.sprite_jugador.vida = vista.sprite_jugador.stamina = 100
    return "Salud y stamina al máximo.", "SUCCESS"

def cmd_dummy(vista, args):
    try:
        from entities.enemy import DummyEnemy
        dummy = DummyEnemy(vista.mouse_world_x, vista.mouse_world_y)
        vista.lista_enemigos.append(dummy)
        return "Dummy enemigo creado!", "SUCCESS"
    except Exception as e:
        return f"Error: {e}", "ERROR"

def cmd_bloque(vista, args):
    try:
        size = int(args[0]) if args else 32
        nuevo_bloque = Bloque(size, size, color=arcade.color.GRAY)
        nuevo_bloque.position = (vista.mouse_world_x, vista.mouse_world_y)
        vista.lista_bloques.append(nuevo_bloque)
        vista.nav_manager.actualizar_desde_bloques(vista.lista_bloques)
        return "Bloque creado.", "SUCCESS"
    except: return "Error en tamaño.", "ERROR"

def cmd_bloques(vista, args):
    con = vista.console
    con.flags["blocks"] = not con.flags["blocks"]
    return f"blocks = {con.flags['blocks']}", "SUCCESS"


    
def cmd_nav(vista, args):
    """Comandos de navegacion/pathfinding."""
    if not args:
        return "Uso: nav [start | end | calc | update | clear]", "INFO"

    sub = args[0].lower()
    nav = vista.nav_manager
    con = vista.console

    if sub == "start":
        mouse_x, mouse_y = vista.mouse_world_x, vista.mouse_world_y
        con.test_origin = (mouse_x, mouse_y)
        con.flags["test_nodes"] = True
        return "Origen fijado.", "SUCCESS"

    elif sub == "end":
        mouse_x, mouse_y = vista.mouse_world_x, vista.mouse_world_y
        con.test_dest = (mouse_x, mouse_y)
        con.flags["test_nodes"] = True
        return "Destino fijado.", "SUCCESS"

    if sub == "calc":
        if not con.test_origin or not con.test_dest:
            return "Faltan puntos.", "ERROR"
        con.test_path = nav.encontrar_ruta(con.test_origin, con.test_dest)
        if con.test_path is None:
            con.test_path = []
            return "No se encontró ruta.", "ERROR"
        return f"Ruta: {len(con.test_path)} puntos.", "SUCCESS"

    elif sub == "update":
        nav.actualizar_desde_bloques(vista.lista_bloques)
        return "Grid actualizando...", "INFO"

    elif sub == "clear":
        con.test_origin = con.test_dest = None
        con.test_path = []
        return "Test de navegacion limpio.", "INFO"

    return "Subcomando no valido.", "ERROR"





def cmd_debug(vista, args):
    if not args:
        estados = ", ".join([f"{k}: {'ON' if v else 'OFF'}" for k, v in vista.console.flags.items()])
        return f"Flags actuales -> {estados}", "INFO"
    
    opcion = args[0].lower()
    
    mapping = {
        "hitbox": "hitbox",
        "path": "path",
        "grid": "grid",
        "nodes": "test_nodes",
        "chunks": "chunks"  
    }

    if opcion in mapping:
        key = mapping[opcion]
        vista.console.flags[key] = not vista.console.flags[key]
        estado = "ACTIVADO" if vista.console.flags[key] else "DESACTIVADO"
        return f"Debug {opcion}: {estado}", "SUCCESS"
    
    return f"La opción '{opcion}' no existe. Prueba con: hitbox, path, grid, nodes o chunks.", "ERROR"


def cmd_dmg(vista, args):
    """Inflige daño al jugador. Uso: damage <cantidad> Por defecto el daño es 10"""
    try:
        cantidad = float(args[0]) if args else 10.0
        
        vista.sprite_jugador.vida -= cantidad
        
        if vista.sprite_jugador.vida < 0:
            vista.sprite_jugador.vida = 0
            
        return f"Daño aplicado: -{cantidad} HP. Vida actual: {vista.sprite_jugador.vida}", "SUCCESS"
    except ValueError:
        return "Error: La cantidad de daño debe ser un número.", "ERROR"

COMANDOS = {
    "spawn": cmd_spawn,
    "tp": cmd_tp,
    "heal": cmd_heal,
    "dummy": cmd_dummy,
    "bloque": cmd_bloque,
    "nav": cmd_nav,
    "debug": cmd_debug, 
    "bloques": cmd_bloques,
    "damage": cmd_dmg,
}
