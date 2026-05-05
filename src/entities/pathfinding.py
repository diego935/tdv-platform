import heapq
import threading
import time
from typing import List, Tuple, Optional, Set, Callable
import arcade


class Nodo:
    def __init__(self, x: int, y: int, transitable: bool = True):
        self.x = x
        self.y = y
        self.transitable = transitable
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.padre = None
        self._version = 0

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        if isinstance(other, Nodo):
            return self.x == other.x and self.y == other.y
        return False

    def __hash__(self):
        return hash((self.x, self.y))

    def reiniciar(self):
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.padre = None


class GridPathfinder:
    def __init__(self, cell_size: int = 32):
        self.cell_size = cell_size
        self.grid: dict = {}
        self.world_bounds = None
        self._grid_actualizado = False
        self._version_nodos = 0

        self.direcciones = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        self.costo_cardinal = 1.0
        self.costo_diagonal = 1.414

        self._hilo_actualizacion = None
        self._actualizando = False
        self._callback_completado: Optional[Callable] = None
        self._bloques_pendientes = None
        self.bloques_referencia = None

    def _mundo_a_grid(self, x: float, y: float) -> Tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))

    def _grid_a_mundo(self, gx: int, gy: int) -> Tuple[float, float]:
        return (gx * self.cell_size + self.cell_size / 2,
                gy * self.cell_size + self.cell_size / 2)

    def actualizar_desde_bloques(self, bloques, padding: int = 0):
        if self._actualizando:
            return
        self._actualizar_grid_sync(bloques, padding)

    def actualizar_grafo_async(self, bloques=None, callback: Optional[Callable] = None, padding: int = 0):
        if bloques is None:
            bloques = self.bloques_referencia
        if not bloques:
            return
        self.bloques_referencia = list(bloques)
        self._bloques_pendientes = list(bloques)
        self._callback_completado = callback
        self._hilo_actualizacion = threading.Thread(
            target=self._worker_actualizar,
            args=(padding,),
            daemon=True
        )
        self._actualizando = True
        self._hilo_actualizacion.start()

    def _worker_actualizar(self, padding: int):
        try:
            inicio = time.time()
            self._actualizar_grid_sync(self._bloques_pendientes, padding)
            duracion = time.time() - inicio
        except Exception as e:
            print(f"[GridPathfinder] Error en actualización: {e}")
        finally:
            self._actualizando = False
            if self._callback_completado:
                try:
                    self._callback_completado()
                except Exception as e:
                    print(f"[GridPathfinder] Error en callback: {e}")

    def _actualizar_grid_sync(self, bloques, padding: int = 2):
        self.grid.clear()

        if not bloques:
            self._grid_actualizado = True
            return

        x_min = min(b.left for b in bloques)
        x_max = max(b.right for b in bloques)
        y_min = min(b.bottom for b in bloques)
        y_max = max(b.top for b in bloques)

        margen_celdas = 20
        x_min -= margen_celdas * self.cell_size
        x_max += margen_celdas * self.cell_size
        y_min -= margen_celdas * self.cell_size
        y_max += margen_celdas * self.cell_size

        self.world_bounds = (x_min, y_min, x_max, y_max)

        celdas_bloqueadas: Set[Tuple[int, int]] = set()

        for bloque in bloques:
            bx_min, by_min = self._mundo_a_grid(bloque.left, bloque.bottom)
            bx_max, by_max = self._mundo_a_grid(bloque.right - 1, bloque.top - 1)

            bx_min -= padding
            by_min -= padding
            bx_max += padding
            by_max += padding

            for gx in range(bx_min, bx_max + 1):
                for gy in range(by_min, by_max + 1):
                    celdas_bloqueadas.add((gx, gy))

        gx_min, gy_min = self._mundo_a_grid(x_min, y_min)
        gx_max, gy_max = self._mundo_a_grid(x_max, y_max)

        for gx in range(gx_min, gx_max + 1):
            for gy in range(gy_min, gy_max + 1):
                transitable = (gx, gy) not in celdas_bloqueadas
                self.grid[(gx, gy)] = Nodo(gx, gy, transitable)

        self._grid_actualizado = True

    def esta_actualizando(self) -> bool:
        return self._actualizando

    def _heuristica(self, nodo: Nodo, objetivo: Nodo) -> float:
        dx = abs(nodo.x - objetivo.x)
        dy = abs(nodo.y - objetivo.y)
        return self.costo_cardinal * (dx + dy) + (self.costo_diagonal - 2 * self.costo_cardinal) * min(dx, dy)

    def _vecinos(self, nodo: Nodo) -> List[Tuple[Nodo, float]]:
        vecinos = []

        for dx, dy in self.direcciones:
            nx, ny = nodo.x + dx, nodo.y + dy

            vecino = self.grid.get((nx, ny))
            if vecino and vecino.transitable:
                if dx != 0 and dy != 0:
                    adj1 = self.grid.get((nodo.x + dx, nodo.y))
                    adj2 = self.grid.get((nodo.x, nodo.y + dy))
                    if not (adj1 and adj1.transitable and adj2 and adj2.transitable):
                        continue

                costo = self.costo_diagonal if dx != 0 and dy != 0 else self.costo_cardinal
                vecinos.append((vecino, costo))

        return vecinos

    MAX_DISTANCIA_BUSQUEDA = 100
    MAX_ITERACIONES = 5000

    def encontrar_ruta(self, inicio: Tuple[float, float],
                      fin: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        if not self._grid_actualizado:
            return None

        inicio_grid = self._mundo_a_grid(inicio[0], inicio[1])
        fin_grid = self._mundo_a_grid(fin[0], fin[1])

        nodo_inicio = self.grid.get(inicio_grid)
        nodo_fin = self.grid.get(fin_grid)

        if not nodo_inicio or not nodo_fin:
            return None

        if not nodo_fin.transitable:
            nodo_fin = self._encontrar_celda_cercana(fin_grid)
            if not nodo_fin:
                return None

        distancia_grid = abs(fin_grid[0] - inicio_grid[0]) + abs(fin_grid[1] - inicio_grid[1])
        max_distancia = min(distancia_grid * 2, self.MAX_DISTANCIA_BUSQUEDA)

        self._version_nodos += 1

        def _es_nodo_fresco(nodo):
            return nodo._version == self._version_nodos

        def _marcar_fresco(nodo):
            nodo._version = self._version_nodos
            nodo.g = float('inf')
            nodo.h = 0
            nodo.f = float('inf')
            nodo.padre = None

        _marcar_fresco(nodo_inicio)
        nodo_inicio.g = 0
        nodo_inicio.h = self._heuristica(nodo_inicio, nodo_fin)
        nodo_inicio.f = nodo_inicio.h

        abierta = []
        heapq.heappush(abierta, nodo_inicio)

        cerrada: Set[Nodo] = set()

        iteraciones = 0

        while abierta and iteraciones < self.MAX_ITERACIONES:
            iteraciones += 1
            nodo_actual = heapq.heappop(abierta)

            distancia_actual = abs(nodo_actual.x - nodo_inicio.x) + abs(nodo_actual.y - nodo_inicio.y)
            if distancia_actual > max_distancia:
                continue

            if nodo_actual == nodo_fin:
                return self._reconstruir_ruta(nodo_fin)

            cerrada.add(nodo_actual)

            for vecino, costo_movimiento in self._vecinos(nodo_actual):
                if vecino in cerrada:
                    continue

                if not _es_nodo_fresco(vecino):
                    _marcar_fresco(vecino)

                nuevo_g = nodo_actual.g + costo_movimiento

                if nuevo_g < vecino.g:
                    vecino.padre = nodo_actual
                    vecino.g = nuevo_g
                    vecino.h = self._heuristica(vecino, nodo_fin)
                    vecino.f = vecino.g + vecino.h

                if vecino not in abierta:
                    heapq.heappush(abierta, vecino)

        if iteraciones >= self.MAX_ITERACIONES:
            print(f"[GridPathfinder] A* alcanzó límite de iteraciones ({self.MAX_ITERACIONES})")
        return None

    def _encontrar_celda_cercana(self, grid_pos: Tuple[int, int]) -> Optional[Nodo]:
        for radio in range(1, 20):
            for dx in range(-radio, radio + 1):
                for dy in range(-radio, radio + 1):
                    if abs(dx) == radio or abs(dy) == radio:
                        pos = (grid_pos[0] + dx, grid_pos[1] + dy)
                        nodo = self.grid.get(pos)
                        if nodo and nodo.transitable:
                            return nodo
        return None

    def _reconstruir_ruta(self, nodo_fin: Nodo) -> List[Tuple[float, float]]:
        ruta = []
        nodo = nodo_fin

        while nodo:
            mundo_x, mundo_y = self._grid_a_mundo(nodo.x, nodo.y)
            ruta.append((mundo_x, mundo_y))
            nodo = nodo.padre

        return ruta[::-1]

    def tiene_linea_de_vision(self, pos1: Tuple[float, float],
                             pos2: Tuple[float, float]) -> bool:
        g1 = self._mundo_a_grid(pos1[0], pos1[1])
        g2 = self._mundo_a_grid(pos2[0], pos2[1])

        x1, y1 = g1
        x2, y2 = g2

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        x, y = x1, y1

        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1

        error = dx - dy

        while True:
            nodo = self.grid.get((x, y))
            if nodo and not nodo.transitable:
                return False

            if x == x2 and y == y2:
                break

            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc

        return True

    def obtener_celdas_transitables(self) -> List[Tuple[int, int]]:
        return [(nodo.x, nodo.y) for nodo in self.grid.values() if nodo.transitable]

    def obtener_celdas_bloqueadas(self) -> List[Tuple[int, int]]:
        return [(nodo.x, nodo.y) for nodo in self.grid.values() if not nodo.transitable]

    def debug_dibujar_grid(self, color_transitable=arcade.color.GREEN, color_bloqueado=arcade.color.RED, alpha=50):
        for (gx, gy), nodo in self.grid.items():
            x, y = self._grid_a_mundo(gx, gy)
            color = color_transitable if nodo.transitable else color_bloqueado
            arcade.draw_rect_filled(
                arcade.rect.XYWH(x, y, self.cell_size - 2, self.cell_size - 2),
                (*color[:3], alpha)
            )

    def debug_dibujar_ruta(self, ruta: List[Tuple[float, float]], color=arcade.color.YELLOW, grosor=2):
        if len(ruta) < 2:
            return
        arcade.draw_line_strip(ruta, color, grosor)

    def debug_dibujar_punto(self, pos: Tuple[float, float], color=arcade.color.CYAN, radio=5):
        arcade.draw_circle_filled(pos[0], pos[1], radio, color)


class SistemaNavegacion:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SistemaNavegacion, cls).__new__(cls)
        return cls._instance

    def __init__(self, lista_bloques=None, cell_size=32):
        if not hasattr(self, 'inicializado'):
            self.cell_size = cell_size
            self.bloques_referencia = lista_bloques
            self.grid_pathfinder = GridPathfinder(cell_size=cell_size)
            self.inicializado = True

            if self.bloques_referencia:
                self.grid_pathfinder.bloques_referencia = lista_bloques
                self.grid_pathfinder.actualizar_desde_bloques(lista_bloques)

    def actualizar_desde_bloques(self, bloques):
        if bloques:
            self.bloques_referencia = bloques
        self.grid_pathfinder.actualizar_desde_bloques(bloques, 0)

    def actualizar_grafo_async(self, bloques=None, callback: Optional[Callable] = None, padding: int = 0):
        if bloques is None:
            bloques = self.bloques_referencia
        if bloques:
            self.bloques_referencia = bloques
            self.grid_pathfinder.bloques_referencia = bloques
            self.grid_pathfinder.actualizar_grafo_async(bloques, callback, padding)

    def encontrar_ruta(self, inicio, destino):
        return self.grid_pathfinder.encontrar_ruta(inicio, destino)

    def tiene_linea_de_vision(self, pos1, pos2):
        return self.grid_pathfinder.tiene_linea_de_vision(pos1, pos2)

    def debug_dibujar_grid(self, color_transitable=arcade.color.GREEN, color_bloqueado=arcade.color.RED, alpha=50):
        self.grid_pathfinder.debug_dibujar_grid(color_transitable, color_bloqueado, alpha)

    @property
    def grafo(self):
        return self.grid_pathfinder

    @property
    def esta_actualizando(self):
        return self.grid_pathfinder.esta_actualizando()