import arcade

class Jugador(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(32, 32, arcade.color.AQUAMARINE)
        
        self.vida = 100
        self.municion = 30
        self.velocidad = 5
