import arcade
from vista.inventory import *
from vista.textos import *

class Jugador(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(32, 32, arcade.color.AQUAMARINE)
        
        self.vida = 100
        self.municion = 30
        self.velocidad = 5
        self.capacidad = 8 # NOTE: Está hardcodeada la capacidad del invetario.  
        self.inventory = [None] * self.capacidad
        self.vistaInventario = BaseInventoryUI(self.capacidad) 
        self.indice_seleccionado = None

    def draw_inventory(self): 
        self.vistaInventario.draw(self.inventory, self.indice_seleccionado )


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