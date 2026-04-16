import arcade

class Enemigo(arcade.SpriteSolidColor):
    def __init__(self):
        super().__init__(width=32, height=32, color=arcade.color.BLOOD_RED)
        self.vida = 50
