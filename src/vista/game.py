import arcade
from config import ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO_JUEGO
from entities.player import Jugador
from entities.enemy import Enemigo
from entities.blocks import *


class VistaJuego(arcade.View):
    def __init__(self):
        super().__init__()
        self.sprite_jugador = None
        self.lista_jugadores = None
        self.lista_enemigos = None
        self.lista_puertas = None
        self.lista_bloques = None
        

        self.izquierda_presionado = False
        self.derecha_presionado = False
        self.arriba_presionado = False
        self.abajo_presionado = False

    def setup(self):
        self.window.background_color = COLOR_FONDO_JUEGO

        self.lista_jugadores = arcade.SpriteList()
        self.lista_enemigos = arcade.SpriteList()
        self.lista_puertas = arcade.SpriteList()
        self.lista_bloques= arcade.SpriteList()

        self.sprite_jugador = Jugador()
        self.sprite_jugador.center_x = ANCHO_VENTANA // 2
        self.sprite_jugador.center_y = ALTO_VENTANA // 2
        self.lista_jugadores.append(self.sprite_jugador)
        
        """puerta = Puerta(ANCHO_VENTANA // 2 + 300, ALTO_VENTANA // 2, width=100, height=300, tiempo_apertura=1.5, tiempo_cierre=1.0)
        self.lista_puertas.append(puerta)
        self.lista_bloques.append(puerta)"""

        puertas, bloques = crear_casa(
            x=ANCHO_VENTANA // 2,
            y=ALTO_VENTANA // 2,
            ancho_habitable=500,
            alto_habitable=500,
            grosor=32,
            direcciones_puerta=["NORTE", "ESTE"],
            ancho_puerta=100
        )
        self.lista_puertas.extend(puertas)
        self.lista_bloques.extend(bloques)




        self.physics_engine = arcade.PhysicsEngineSimple(self.sprite_jugador, self.lista_bloques)


    def on_draw(self):
        self.clear()
        self.lista_bloques.draw()
        self.lista_puertas.draw()
        self.lista_enemigos.draw()
        self.lista_jugadores.draw()

    def cerca_con_margen(self, sprite1, sprite2, margen=10):
        dx = abs(sprite1.center_x - sprite2.center_x)
        dy = abs(sprite1.center_y - sprite2.center_y)

        return (
            dx < (sprite1.width / 2 + sprite2.width / 2 + margen) and
            dy < (sprite1.height / 2 + sprite2.height / 2 + margen)
        )

    def on_update(self, delta_time):
        self.sprite_jugador.change_x = 0
        self.sprite_jugador.change_y = 0

        if self.arriba_presionado and not self.abajo_presionado:
            self.sprite_jugador.change_y = self.sprite_jugador.velocidad
        elif self.abajo_presionado and not self.arriba_presionado:
            self.sprite_jugador.change_y = -self.sprite_jugador.velocidad

        if self.izquierda_presionado and not self.derecha_presionado:
            self.sprite_jugador.change_x = -self.sprite_jugador.velocidad
        elif self.derecha_presionado and not self.izquierda_presionado:
            self.sprite_jugador.change_x = self.sprite_jugador.velocidad


        self.lista_puertas.update(delta_time)
        self.lista_jugadores.update()
        self.lista_enemigos.update()

        ## Sincroniza el estado de las puerts
        for puerta in self.lista_puertas:
            if puerta.activa_colision and puerta not in self.lista_bloques:
                self.lista_bloques.append(puerta)
            elif not puerta.activa_colision and puerta in self.lista_bloques:
                self.lista_bloques.remove(puerta)

        self.physics_engine.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = True
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = True
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = True
        elif key == arcade.key.E:
            for puerta in self.lista_puertas:
                if self.cerca_con_margen(self.sprite_jugador, puerta, margen=10):
                    puerta.interactuar()
                    break ## Se asume que solo se interactua con una puerta a la vez

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.arriba_presionado = False
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.abajo_presionado = False
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.izquierda_presionado = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.derecha_presionado = False
