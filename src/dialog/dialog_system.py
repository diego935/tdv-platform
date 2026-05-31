import json
import os
import arcade
from typing import Callable, Optional
from utils.log import Log


def verificar_condicion(condicion: dict) -> bool:
    if not condicion:
        return True

    from dialog.quest_manager import QM

    for clave, valor in condicion.items():
        if clave == "mision_completada":
            return QM.esta_completada(valor)
        elif clave == "mision_activa":
            return QM.esta_activa(valor)
        elif clave == "mision_no_activa":
            quest = QM.get_mision(valor)
            return quest is not None and quest.estado not in ["en_progreso", "completada"]
        elif clave == "flag":
            return QM.esta_completada(valor) or QM.esta_activa(valor)
        elif clave == "recompensa_no_recibida":
            return QM.esta_completada(valor) and not QM.recompensa_entregada(valor)

    return True


class DialogSystem:
    _instance = None

    def __init__(self):
        self.acciones: dict[str, Callable] = {}
        self.dialogo_actual: Optional[dict] = None
        self.nodo_actual: Optional[str] = None
        self.opciones: dict[str, str] = {}
        self._opciones_filtradas: dict = {}
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
            Log.warning("DialogSystem", "Archivo de diálogo no encontrado", ruta=ruta)
            return False
        with open(ruta, "r", encoding="utf-8") as f:
            self.dialogo_actual = json.load(f)
        return True

    def iniciar(self, nodo_inicial: str) -> bool:
        if self.dialogo_actual is None:
            return False
        if nodo_inicial not in self.dialogo_actual:
            Log.warning("DialogSystem", "Nodo de diálogo no encontrado", nodo=nodo_inicial)
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
        self.obtener_opciones()
        self._notificar_cambio()

    def ejecutar_accion_actual(self) -> None:
        if not self.nodo_accion or not self._vista:
            return
        
        from dialog.acciones import ejecutar_accion
        accion = self.nodo_accion
        
        if ":" in accion or accion in ["cerrar", "debug"]:
            ejecutar_accion(accion, self._vista)
        else:
            from dialog.acciones import obtener_accion
            accion_real = obtener_accion(self._nombre_dialogo, accion)
            if accion_real:
                ejecutar_accion(accion_real, self._vista)

    def seleccionar_opcion(self, numero: str) -> bool:
        if numero not in self._opciones_filtradas:
            return False

        opcion = self._opciones_filtradas[numero]
        siguiente_nodo = opcion.get("nodo") if isinstance(opcion, dict) else opcion

        if not siguiente_nodo:
            return False

        self.mostrar_nodo(siguiente_nodo)

        if self.nodo_accion:
            self.ejecutar_accion_actual()

        return True

    def cerrar(self) -> None:
        self.dialogo_activo = False
        self.dialogo_actual = None
        self.nodo_actual = None
        self.opciones = {}
        self._opciones_filtradas = {}
        self._notificar_cambio()

    def on_key_press(self, key) -> bool:
        """Maneja input del jugador. Returns True si el diálogo debe cerrar."""
        if not self.dialogo_activo:
            return True
        
        if key == arcade.key.E:
            self.cerrar()
            return True
        elif key in [arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3, 
                     arcade.key.KEY_4, arcade.key.KEY_5]:
            num = str(key - arcade.key.KEY_1 + 1)
            self.seleccionar_opcion(num)
            return False
        return False

    def get_vista(self):
        return self._vista

    def registrar_accion(self, nombre: str, callback: Callable) -> None:
        self.acciones[nombre] = callback

    def obtener_opciones(self) -> list[tuple[str, str, str]]:
        resultado = []
        opciones_filtradas = {}
        
        # Este contador llevará el número visible real de la opción (1, 2, 3...)
        contador_opcion_visible = 1

        for i in range(1, 10):
            clave_json = str(i)
            if clave_json not in self.opciones:
                continue

            opcion_raw = self.opciones[clave_json]

            if isinstance(opcion_raw, str):
                condicion = None
                siguiente_nodo = opcion_raw
                texto_mostrar = opcion_raw
            elif isinstance(opcion_raw, dict):
                siguiente_nodo = opcion_raw.get("nodo", "")
                condicion = opcion_raw.get("condicion")
                texto_mostrar = opcion_raw.get("texto", siguiente_nodo)
            else:
                continue

            if not verificar_condicion(condicion):
                continue

            # Convertimos el contador actual a string ('1', '2', '3'...)
            clave_visible = str(contador_opcion_visible)

            # Guardamos la opción mapeada a su NUEVO número dinámico de teclado
            opciones_filtradas[clave_visible] = opcion_raw
            
            # Añadimos a la lista que renderiza la UI con el número correcto
            resultado.append((clave_visible, siguiente_nodo, texto_mostrar))
            
            # Incrementamos solo porque esta opción SÍ es válida y se va a mostrar
            contador_opcion_visible += 1

        self._opciones_filtradas = opciones_filtradas
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


    def clear_manager(self) -> None:
        """Fuerza el cierre del diálogo y limpia todas las variables y listeners de la UI."""
        Log.info("DialogSystem", "Limpiando el sistema de diálogos...")
        
        # Forzar el estado lúdico a cerrado
        self.dialogo_activo = False
        self.dialogo_actual = None
        self.nodo_actual = None
        self.nodo_texto = ""
        self.nodo_accion = ""
        self._nombre_dialogo = ""
        
        # Limpiar diccionarios de opciones
        self.opciones.clear()
        self._opciones_filtradas.clear()
        self.acciones.clear()
        
        # Desvincular la vista gráfica anterior y limpiar observadores de interfaz
        self._vista = None
        self._listeners.clear()
        
        Log.info("DialogSystem", "Sistema de diálogos reseteado por completo.")

DialogManager = DialogSystem.get_instance