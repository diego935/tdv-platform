import arcade
from vista.inventory import *
from vista.textos import *
from vista.asset_manager import AssetManager


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
        self.indice_seleccionado = None
        self.indice_activo = 0
        self.stamina = 100; 
        self.max_stamina = 100.0
        self.stamina_cooldown_timer = 0.0
        self.stamina_delay= 1.5 
        self.stamina_exhausted_delay = 3.0
        self.tasa_consumo_stamina = 25
        self.tasa_regen_stamina = 25
        #Curacion
        self.tasa_regen_hp = 15
        self.direccion = "down"
        assets = AssetManager()
        self.texturas = {
            "up": assets.get_texture("assets/Jugador/Soldado hacia arriba.png"),
            "down": assets.get_texture("assets/Jugador/Soldado hacia abajo.png"),
            "left": assets.get_texture("assets/Jugador/Soldado hacia izquierda.png"),
            "right": assets.get_texture("assets/Jugador/Soldado hacia derecha.png"),
        }
        self.texture = self.texturas[self.direccion]
        self.scale = 0.025


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
        

        if self.curacion_pendiente > 0:
            cura_frame = self.velocidad_curacion * delta_time
            cura_frame = min(cura_frame, self.curacion_pendiente) # Evita pasarse
            
            self.vida += cura_frame
            self.curacion_pendiente -= cura_frame
            
            # Tope máximo
            if self.vida >= self.max_vida:
                self.vida = self.max_vida
                self.curacion_pendiente = 0.0

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

        self.texture = self.texturas[self.direccion]


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
            return arma.usar(self, target_x, target_y, proyectiles_list)
        return False 
    

    def iniciar_curacion(self, cantidad, tiempo):
        """ Inicia un proceso de curación gradual """
        if self.vida >= self.max_vida:
            return False
        self.curacion_pendiente += float(cantidad)
        self.velocidad_curacion = float(cantidad) / float(tiempo)
        return True

    def destruir_item_activo(self):
        """ Elimina el item actual del inventario (cuando se gasta) """
        if 0 <= self.indice_activo < len(self.inventory):
            self.inventory[self.indice_activo] = None