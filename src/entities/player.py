import arcade
from vista.inventory import *
from vista.textos import *
from vista.asset_manager import AssetManager
import math
from entities.estados import *


class Jugador(arcade.Sprite):
    def __init__(self):
        super().__init__()
        
        self.max_vida = 100.0
        self.vida = self.max_vida
        self.curacion_pendiente = 0.0
        self.velocidad_curacion = 0.0
        self.vel_caminar = 5
        self.velocidad = self.vel_caminar
        self.vel_correr = 10
        self.capacidad = 8 # NOTE: Está hardcodeada la capacidad del inventario.  
        self.inventory = [None] * self.capacidad
        self.vistaInventario = BaseInventoryUI(self.capacidad)
        self.vistaNota = None 
        self.indice_seleccionado = None
        self.indice_activo = 0
        self.stamina = 100; 
        self.max_stamina = 100.0
        self.stamina_cooldown_timer = 0.0
        self.stamina_delay= 1.5 
        self.stamina_exhausted_delay = 3.0
        self.tasa_consumo_stamina = 25
        self.tasa_regen_stamina = 25
        self.slowed = 1.0
        self.estados = []
        #Curacion
        self.tasa_regen_hp = 25
        self.direccion = "down"
        assets = AssetManager()
        self.texturas = {
            "up": assets.get_texture("assets/Jugador/Soldado hacia arriba_reescalado.png"),
            "down": assets.get_texture("assets/Jugador/Soldado hacia abajo_reescalado.png"),
            "left": assets.get_texture("assets/Jugador/Soldado hacia izquierda_reescalado.png"),
            "right": assets.get_texture("assets/Jugador/Soldado hacia derecha_reescalado.png"),
        }

        self.texturas_right_walk = [
        arcade.load_texture("assets/Jugador/andandoHaciaDerecha/sprite_0_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaDerecha/sprite_1_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaDerecha/sprite_2_reescalado.png")]
        self.texturas_up_walk = [
        arcade.load_texture("assets/Jugador/andandoHaciaArriba/sprite_0_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaArriba/sprite_1_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaArriba/sprite_2_reescalado.png")
        ]
        self.texturas_left_walk = [
        arcade.load_texture("assets/Jugador/andandoHaciaIzquierda/sprite_0_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaIzquierda/sprite_1_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaIzquierda/sprite_2_reescalado.png")
        ]

        self.texturas_down_walk = [
        arcade.load_texture("assets/Jugador/andandoHaciaAbajo/sprite_0_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaAbajo/sprite_1_reescalado.png"),
        arcade.load_texture("assets/Jugador/andandoHaciaAbajo/sprite_2_reescalado.png")
        ]

        self.frame_animacion = 0
        self.timer_animacion = 0
        self.velocidad_animacion = 0.12

        self.texture = self.texturas[self.direccion]
        
        self.scale = 0.25
        self.original_scale = self.scale

        self.sonido_pasos = arcade.load_sound("assets/sonidos/caminar.wav")
        self.sonido_trampa = arcade.load_sound("assets/sonidos/trampa.wav")
        self.sonido_queja = arcade.load_sound("assets/sonidos/queja_jugador.wav")
        self.player_pasos = None
        self.sonando_pasos = False
        self.speed_sonido = 1.0


    def draw_inventory(self, mouse_pos=None): 
        self.vistaInventario.draw(self.inventory, self.vistaInventario._drag_source if hasattr(self.vistaInventario, '_drag_source') else None, mouse_pos)

    def actualizar_estados(self, delta_time: float):
        estados_restantes = []
        for estado in self.estados:
            if not estado.actualizar(self, delta_time):
                self.estados.remove(estado)




    def recoger_objeto(self, objeto):
            try:
                # Buscamos el primer hueco vacío
                indice = self.inventory.index(None)
                self.inventory[indice] = objeto
                objeto.is_dropped = False 
                return True # Confirmamos que se pudo recoger
            except ValueError:
                # Si no hay 'None', es que está lleno
                TextManager().show_message("INVENTARIO LLENO", self.center_x, self.center_y + 40)
                return False # Avisamos que no hubo espacio

    def soltar_objeto(self, index):
        """
        Extrae el objeto del inventario y lo prepara para el suelo.
        """
        # 1. Verificamos que el índice sea válido y no esté ya vacío
        if 0 <= index < len(self.inventory) and self.inventory[index] is not None:
            # Extraemos el objeto
            objeto = self.inventory[index]
            
            # 2. Vaciamos el slot
            self.inventory[index] = None
                
            # 3. Configuramos el objeto para el mundo
            objeto.is_dropped = True
            objeto.center_x = self.center_x
            objeto.center_y = self.center_y
              
            # 4. Lo devolvemos para que el ItemManager lo añada a su lista
            return objeto
           
        return None


    def move(self, arriba, abajo, izq, der, shift, delta_time):
        

        self.actualizar_estados(delta_time)

        intencion_movimiento = arriba or abajo or izq or der
        
        #Logica de velocidad
        if shift and intencion_movimiento and self.stamina > 0:
            self.velocidad_actual = self.vel_correr
            self.stamina -= self.tasa_consumo_stamina * delta_time
            self.stamina_cooldown_timer = self.stamina_delay
            if self.stamina <= 0:
                self.stamina = 0
                self.stamina_cooldown_timer = self.stamina_exhausted_delay
        else:
            self.velocidad_actual = self.vel_caminar
            if self.stamina_cooldown_timer > 0:
                self.stamina_cooldown_timer -= delta_time
            elif self.stamina < self.max_stamina:
                self.stamina += self.tasa_regen_stamina * delta_time

        # 3. Calcular change_x y change_y
        self.change_x = 0
        self.change_y = 0

        if arriba and not abajo:
            self.change_y = self.velocidad_actual
            self.direccion = "up"
        elif abajo and not arriba:
            self.change_y = -self.velocidad_actual
            self.direccion = "down"

        if izq and not der:
            self.change_x = -self.velocidad_actual
            self.direccion = "left"
        elif der and not izq:
            self.change_x = self.velocidad_actual
            self.direccion = "right"

        self.change_x *= self.slowed
        self.change_y *= self.slowed
        
        moviendose = self.change_x != 0 or self.change_y != 0
        if moviendose:

            self.timer_animacion += delta_time

            if self.timer_animacion >= self.velocidad_animacion:
                self.timer_animacion = 0
                self.frame_animacion += 1

            if self.direccion == "right":
                frames = self.texturas_right_walk

            elif self.direccion == "left":
                frames = self.texturas_left_walk

            elif self.direccion == "up":
                frames = self.texturas_up_walk

            else:
                frames = self.texturas_down_walk

            if self.frame_animacion >= len(frames):
                self.frame_animacion = 0

            self.texture = frames[self.frame_animacion]

        else:
            self.frame_animacion = 0
            self.texture = self.texturas[self.direccion]


        #sonido movimiento
        corriendo = (shift and moviendose and self.stamina > 0 and self.velocidad_actual == self.vel_correr)

        if moviendose:
            velocidad_sonido = 1.5 if corriendo else 1.0
            if not self.sonando_pasos:
                self.player_pasos = self.sonido_pasos.play(loop=True, volume=0.3, speed=velocidad_sonido)
                self.sonando_pasos = True
                self.speed_sonido = velocidad_sonido
            elif self.speed_sonido != velocidad_sonido:
                arcade.stop_sound(self.player_pasos)
                self.player_pasos = self.sonido_pasos.play(loop=True, volume=0.3, speed=velocidad_sonido)
                self.speed_sonido = velocidad_sonido

        else:

            if self.sonando_pasos:

                arcade.stop_sound(self.player_pasos)

                self.sonando_pasos = False


    def cambiar_slot(self, indice):
        if 0 <= indice < 4:
            self.indice_activo = indice

    def obtener_arma_activa(self):
        if 0 <= self.indice_activo < len(self.inventory):
            return self.inventory[self.indice_activo]
        return None

    def usar_arma_activa(self, target_x, target_y, proyectiles_list):
        arma = self.obtener_arma_activa()
        if arma and hasattr(arma, 'usar'):
            return arma.usar(self, target_x= target_x, target_y = target_y, proyectiles_list= proyectiles_list)
        return False     

    def iniciar_curacion(self, cantidad, tiempo):
        if self.vida >= self.max_vida:
            return False
        self.estados.append(Sanacion(cantidad, tiempo))
        return True

    def destruir_item_activo(self, slot= None):
        """ Elimina el item actual del inventario (cuando se gasta) """
        if slot: 
            self.inventory[slot] = None 
            return
        if 0 <= self.indice_activo < len(self.inventory):
            self.inventory[self.indice_activo] = None

    def recibir_dano(self, cantidad: float, fuente_x: float = None, fuente_y: float = None):
        self.vida -= cantidad
        if fuente_x is not None and fuente_y is not None:
            dx = self.center_x - fuente_x
            dy = self.center_y - fuente_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                self._knockback_vel = (dx/dist * 100, dy/dist * 100)
                self._knockback_timer = 0.15
                self._base_x = self.center_x
                self._base_y = self.center_y
        if self.vida <= 0:
            self.vida =0
            
            #Aqui se llama a la pantalla de muerte
            pass 


    def pisa_trampa(self, daño_base: int, daño_veneno: float, tiempo_veneno: float, tiempo_slow: float, porcentajeSlow:float): 
        arcade.play_sound(self.sonido_trampa, volume=0.3)
        arcade.play_sound(self.sonido_queja, volume=0.4)
        self.recibir_dano(daño_base)
        if (daño_veneno >0 and tiempo_veneno >0): self.estados.append(Veneno(daño_veneno, tiempo_veneno))
        self.slowed *= porcentajeSlow
        self.estados.append(Slow(porcentajeSlow, tiempo_slow))

    def to_dict(self):
        return {
            "x": self.center_x,
            "y": self.center_y,
            "vida": self.vida,
            "max_vida": self.max_vida,
            "stamina": self.stamina,
            "indice_activo": self.indice_activo,
            "direccion": self.direccion,
            "inventario": [
                item.__class__.__name__ if item else None
                for item in self.inventory
            ]
        }