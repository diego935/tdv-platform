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

    def to_dict(self):
        return {
            "__type__": self.__class__.__name__,
            "duracion": self.duracion,
            "tiempo_restante": self.tiempo_restante,
        }


def estado_from_dict(data):
    tipo = data.get("__type__", "")
    if tipo == "Veneno":
        e = Veneno.__new__(Veneno)
    elif tipo == "Slow":
        e = Slow.__new__(Slow)
    elif tipo == "Sanacion":
        e = Sanacion.__new__(Sanacion)
    elif tipo == "BendicionDelBosque":
        e = BendicionDelBosque.__new__(BendicionDelBosque)
    else:
        return None
    e.__dict__.update({k: v for k, v in data.items() if k != "__type__"})
    return e


class Veneno(Estado):
    def __init__(self, dano_por_segundo: float, duracion: float):
        super().__init__(duracion)
        self.dano_por_segundo = dano_por_segundo
    
    def actualizar(self, jugador, delta_time: float) -> bool:
        jugador.recibir_dano(self.dano_por_segundo * delta_time)
        return super().actualizar(jugador, delta_time)

    def to_dict(self):
        d = super().to_dict()
        d["dano_por_segundo"] = self.dano_por_segundo
        return d


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

    def to_dict(self):
        d = super().to_dict()
        d["factor"] = self.factor
        return d


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

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "cantidad_total": self.cantidad_total,
            "cantidad_restante": self.cantidad_restante,
            "velocidad": self.velocidad,
        })
        return d


class BendicionDelBosque(Estado):
    def __init__(self, regeneracion_por_segundo: float = 3.0):
        super().__init__(None)
        self.regeneracion_por_segundo = regeneracion_por_segundo
    
    def actualizar(self, jugador, delta_time: float) -> bool:
        if jugador.vida < jugador.max_vida and jugador.vida > 0:
            jugador.vida = min(jugador.vida + self.regeneracion_por_segundo * delta_time, jugador.max_vida)
        return True

    def to_dict(self):
        d = super().to_dict()
        d["regeneracion_por_segundo"] = self.regeneracion_por_segundo
        return d
