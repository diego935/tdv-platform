import arcade

class Estado:
    def __init__(self, duracion: float = None):
        self.duracion = duracion
        self.tiempo_restante = duracion
    
    def aplicar(self, jugador):
        pass
    
    def actualizar(self, jugador, delta_time: float):
        if self.duracion is not None:
            self.tiempo_restante -= delta_time
            return self.tiempo_restante > 0
        return True
    
    def remover(self, jugador):
        pass

class Veneno(Estado):
    def __init__(self, dano_por_segundo: float, duracion: float):
        super().__init__(duracion)
        self.dano_por_segundo = dano_por_segundo
    
    def actualizar(self, jugador, delta_time: float) -> bool:
        jugador.recibir_dano(self.dano_por_segundo * delta_time)
        return super().actualizar(jugador, delta_time)

class Slow(Estado):
    def __init__(self, factor_velocidad: float, duracion: float):
        super().__init__(duracion)
        self.factor = factor_velocidad

    def actualizar(self, jugador, delta_time: float) -> bool:
            self.tiempo_restante -= delta_time
            if self.tiempo_restante > 0: return True 
            else: 
                jugador.slowed/= self.factor
                return False 



class Sanacion(Estado):
    def __init__(self, cantidad_total: float, tiempo: float):
        super().__init__(tiempo)
        self.cantidad_total = cantidad_total
        self.cantidad_restante = cantidad_total
        self.velocidad = cantidad_total / tiempo
    
    def actualizar(self, jugador, delta_time: float) -> bool:
        cura = min(self.velocidad * delta_time, self.cantidad_restante)
        jugador.vida = min(jugador.vida + cura, jugador.max_vida)
        self.cantidad_restante -= cura
        return self.cantidad_restante > 0


class BendicionDelBosque(Estado):
    def __init__(self, regeneracion_por_segundo: float = 1.5):
        super().__init__(None)  # Duración infinita
        self.regeneracion_por_segundo = regeneracion_por_segundo
    
    def actualizar(self, jugador, delta_time: float) -> bool:
        if jugador.vida < jugador.max_vida and jugador.vida > 0:
            jugador.vida = min(jugador.vida + self.regeneracion_por_segundo * delta_time, jugador.max_vida)
        return True

