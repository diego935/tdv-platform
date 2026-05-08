import json
import os


_acciones_cache = {}

_ITEM_FACTORY = {}


def _init_item_factory():
    """Inicializa la factory de items."""
    global _ITEM_FACTORY
    if _ITEM_FACTORY:
        return
    try:
        from items.items import Botiquin
        _ITEM_FACTORY = {
            "Botiquin": Botiquin,
        }
    except ImportError:
        pass


def cargar_acciones(nombre_dialogo: str) -> dict:
    if nombre_dialogo in _acciones_cache:
        return _acciones_cache[nombre_dialogo]
    
    ruta = f"assets/dialogs/{nombre_dialogo}.json"
    if not os.path.exists(ruta):
        return {}
    
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    acciones = data.get("_acciones", {})
    _acciones_cache[nombre_dialogo] = acciones
    return acciones


def ejecutar_accion(accion: str, vista) -> None:
    if not accion:
        return
    
    if ":" in accion:
        tipo, param = accion.split(":", 1)
    else:
        tipo = accion
        param = ""
    
    if tipo == "quitar-vida":
        cantidad = int(param) if param.isdigit() else 10
        vista.quitar_vida(cantidad)
    elif tipo == "curar":
        cantidad = int(param) if param.isdigit() else 10
        vista.curar(cantidad)
    elif tipo == "dar-item":
        _init_item_factory()
        param = param.strip()
        if param in _ITEM_FACTORY:
            ItemClass = _ITEM_FACTORY[param]
            item = ItemClass()
        else:
            from items.items import BaseItem
            item = BaseItem(1, param, "assets/items/Flint.png")
        
        # Position item near player
        item.center_x = vista.sprite_jugador.center_x + 32
        item.center_y = vista.sprite_jugador.center_y
        vista.item_manager.add_to_world(item)
        print(f"[Dialog] Has recibido: {param}")
    elif tipo == "cerrar":
        vista.cerrar_dialogo()
    elif tipo == "debug":
        print(f"[Dialog] {param}")


def obtener_accion(nombre_dialogo: str, clave_accion: str) -> str:
    acciones = cargar_acciones(nombre_dialogo)
    return acciones.get(clave_accion, "")