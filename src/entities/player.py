import arcade
from vista.inventory import *
from vista.textos import *


class Jugador(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(32, 32, arcade.color.AQUAMARINE)
        
        self.vida = 100
        self.municion = 30
        self.vel_caminar = 5
        self.velocidad = self.vel_caminar
        self.vel_correr = 10
        self.esta_corriendo = False
        self.stamina_agotada = False
        self.capacidad = 8 # NOTE: Está hardcodeada la capacidad del invetario.  
        self.inventory = [None] * self.capacidad
        self.vistaInventario = BaseInventoryUI(self.capacidad) 
        self.indice_seleccionado = None
        self.indice_activo = 0
        self.stamina = 100; 
        self.max_stamina = 100.0
        self.stamina_cooldown_timer = 0.0
        self.stamina_delay= 1.5 
        self.stamina_exhausted_delay = 3.0
        self.tasa_consumo_stamina = 25
        self.tasa_regen_stamina = 25
        

    def draw_inventory(self, mouse_pos=None): 
        self.vistaInventario.draw(self.inventory, self.vistaInventario._drag_source if hasattr(self.vistaInventario, '_drag_source') else None, mouse_pos)


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
        elif abajo and not arriba:
            self.change_y = -self.velocidad_actual

        if izq and not der:
            self.change_x = -self.velocidad_actual
        elif der and not izq:
            self.change_x = self.velocidad_actual


    def cambiar_slot(self, indice):
        if 0 <= indice < 4:
            self.indice_activo = indice
            ## TODO: Añadir sonidos 