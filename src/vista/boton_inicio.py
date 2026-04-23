import arcade

class Boton:
    def __init__(self, x: int, y: int, texto):
        self.x = x
        self.y = y
        self.texto = texto
        self.ancho = 220
        self.alto = 60

    def dibujar (self, fuente):
            arcade.draw_rectangle_filled(self.x, self.y, self.ancho, self.alto, arcade.color.DARK_RED)

            arcade.draw_text(

                self.texto,
                self.x, self.y,
                arcade.color.WHITE,
                18,
                anchor_x= "center",
                anchor_y= "center",
                font_name = fuente
            )
    def esta_pulsado(self, x, y):
            return (self.x - self.ancho/2 < x < self.x + self.ancho/2 and self.y - self.alto/2 < y < self.y + self.alto/2)
