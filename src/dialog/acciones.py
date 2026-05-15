import json
import os
from items.items import Botiquin
from items.items import BaseItem
from utils.log import Log


_acciones_cache = {}

_ITEM_FACTORY = {}


def _get_vista():
    """Get vista safely."""
    from dialog.dialog_system import DialogManager
    dm = DialogManager()
    return dm.get_vista() if dm else None


def _init_item_factory():
    """Inicializa la factory de items."""
    global _ITEM_FACTORY
    if _ITEM_FACTORY:
        return
    _ITEM_FACTORY = {
        "Botiquin": Botiquin,
    }


def _safe_call(method_name, *args):
    """Safe method call."""
    vista = _get_vista()
    if vista and hasattr(vista, method_name):
        getattr(vista, method_name)(*args)


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
    """Ejecuta una acción del diálogo."""
    if not accion:
        return
    
    if ":" in accion:
        tipo, param = accion.split(":", 1)
    else:
        tipo = accion
        param = ""
    
    vista = vista or _get_vista()
    if not vista:
        return
    
    if tipo == "quitar-vida":
        cantidad = int(param) if param.isdigit() else 10
        vista.sprite_jugador.recibir_dano(cantidad)
    elif tipo == "curar":
        cantidad = int(param) if param.isdigit() else 10
        vista.sprite_jugador.iniciar_curacion(cantidad)
    elif tipo == "dar-item":
        _init_item_factory()
        param = param.strip()
        if param in _ITEM_FACTORY:
            ItemClass = _ITEM_FACTORY[param]
            item = ItemClass()
        else:
            item = BaseItem(1, param, "assets/items/Flint.png")
        
        px = vista.sprite_jugador.center_x
        py = vista.sprite_jugador.center_y
        
        npc = vista.lista_npcs[0]
        npc_shape = npc.shape
        nx = (npc_shape[0][0] + npc_shape[2][0]) / 2
        ny = (npc_shape[0][1] + npc_shape[2][1]) / 2        
        offset = 80
        if px > nx:
            item.center_x = px + offset
        else:
            item.center_x = px - offset
            
        if py > ny:
            item.center_y = py + offset
        else:
            item.center_y = py - offset
        
        _safe_call('item_manager_add_item', item)
    elif tipo == "cerrar":
        _safe_call('cerrar_dialogo')
    elif tipo == "debug":
        from utils.log import Log
        Log.debug("DialogAcciones", "Debug action", param=param)


def obtener_accion(nombre_dialogo: str, clave_accion: str) -> str:
    acciones = cargar_acciones(nombre_dialogo)
    return acciones.get(clave_accion, "")