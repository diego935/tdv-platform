import json
import os
from typing import Callable, Optional


class DialogSystem:
    _instance = None

    def __init__(self):
        self.acciones: dict[str, Callable] = {}
        self.dialogo_actual: Optional[dict] = None
        self.nodo_actual: Optional[str] = None
        self.opciones: dict[str, str] = {}
        self.dialogo_activo: bool = False
        self.nodo_texto: str = ""
        self.nodo_accion: str = ""
        self._listeners: list[Callable] = []
        self._vista = None
        self._nombre_dialogo: str = ""

    @classmethod
    def get_instance(cls) -> "DialogSystem":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    def set_vista(self, vista):
        self._vista = vista

    def cargar_dialogo(self, nombre: str) -> bool:
        self._nombre_dialogo = nombre
        ruta = f"assets/dialogs/{nombre}.json"
        if not os.path.exists(ruta):
            print(f"[DialogSystem] Archivo no encontrado: {ruta}")
            return False
        with open(ruta, "r", encoding="utf-8") as f:
            self.dialogo_actual = json.load(f)
        return True

    def iniciar(self, nodo_inicial: str) -> bool:
        if self.dialogo_actual is None:
            return False
        if nodo_inicial not in self.dialogo_actual:
            print(f"[DialogSystem] Nodo no encontrado: {nodo_inicial}")
            return False
        self.dialogo_activo = True
        self.mostrar_nodo(nodo_inicial)
        self.ejecutar_accion_actual()
        return True

    def mostrar_nodo(self, nodo_id: str) -> None:
        if self.dialogo_actual is None:
            return
        nodo = self.dialogo_actual.get(nodo_id)
        if nodo is None:
            return
        self.nodo_actual = nodo_id
        self.nodo_texto = nodo.get("texto", "")
        self.nodo_accion = nodo.get("accion") or ""
        self.opciones = nodo.get("opciones", {})
        self._notificar_cambio()

    def ejecutar_accion_actual(self) -> None:
        if not self.nodo_accion or not self._vista:
            return
        
        from dialog.acciones import obtener_accion, ejecutar_accion
        accion = obtener_accion(self._nombre_dialogo, self.nodo_accion)
        if accion:
            ejecutar_accion(accion, self._vista)

    def seleccionar_opcion(self, numero: str) -> bool:
        if numero not in self.opciones:
            return False
        siguiente_nodo = self.opciones[numero]
        self.mostrar_nodo(siguiente_nodo)
        self.ejecutar_accion_actual()
        return True

    def cerrar(self) -> None:
        self.dialogo_activo = False
        self.dialogo_actual = None
        self.nodo_actual = None
        self.opciones = {}
        self._notificar_cambio()

    def registrar_accion(self, nombre: str, callback: Callable) -> None:
        self.acciones[nombre] = callback

    def obtener_opciones(self) -> list[tuple[str, str]]:
        resultado = []
        for i in range(1, len(self.opciones) + 1):
            clave = str(i)
            if clave in self.opciones:
                resultado.append((clave, self.opciones[clave]))
        return resultado

    def tiene_opciones(self) -> bool:
        return len(self.opciones) > 0

    def agregar_listener(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def quitar_listener(self, callback: Callable) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notificar_cambio(self) -> None:
        for listener in self._listeners:
            listener()

    @classmethod
    def get(cls):
        return cls._instance


DialogManager = DialogSystem.get_instance