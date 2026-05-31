import arcade
import json
import os
from utils.log import Log
from items.items import item_from_dict
from entities.estados import estado_from_dict

SAVE_FILE = "savegame.json"


def guardar_partida(vista_juego):
    datos = _ensamblar_datos(vista_juego)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, default=str)
    Log.info("SaveSystem", "Partida guardada", archivo=SAVE_FILE)


def _ensamblar_datos(vista_juego):
    jugador = vista_juego.sprite_jugador
    from dialog.quest_manager import QM

    return {
        "version": 2, ## Lo evita que el sistema anterior cargue partidas. 
        "player": jugador.to_dict(),
        "misiones": QM.to_dict(),
        "enemigos": [e.to_dict() for e in vista_juego.lista_enemigos],
        "enemigos_muertos": _get_muertos_map_enemigos(vista_juego),
        "puertas": [p.to_dict() for p in vista_juego.lista_puertas],
        "rejas": {
            "trial_activas": vista_juego.rejas_trial_activas,
            "segura_activas": vista_juego.rejas_segura_activas,
            "final_activas": vista_juego.rejas_final_activas,
            "barrera_final_activas": vista_juego.barrera_final_activas,
            "barrera_jefe_activas": vista_juego.barrera_jefe_activas,
            "jefe_derrotado": vista_juego.jefe_derrotado,
        },
        "oleadas": {
            "activas": vista_juego.oleadas_activas,
            "completadas": vista_juego.oleadas_completadas,
            "actual": vista_juego.oleada_actual,
            "timer_entre_oleadas": vista_juego.timer_entre_oleadas,
            "max_oleadas": vista_juego.max_oleadas,
        },
        "interactions": {
            "stats": _serializar_stats_interaction(vista_juego),
        },
        "items_suelo": [
            item.to_dict() for item in vista_juego.item_manager.items_on_ground
        ],
        "dia_noche_timer": vista_juego.timer_dia_noche,
        "esbirros_jefe": [e.to_dict() for e in getattr(vista_juego, "lista_esbirros_jefe", [])],
        "timer_spawn_nido": vista_juego.timer_spawn_nido,
    }


def _discretize(pos):
    return (round(pos[0] / 64) * 64, round(pos[1] / 64) * 64)


def _get_muertos_map_enemigos(vista_juego):
    posiciones_vivas = {_discretize((e.center_x, e.center_y)) for e in vista_juego.lista_enemigos}
    posiciones_muertas = []
    if hasattr(vista_juego, '_map_enemy_positions'):
        for pos in vista_juego._map_enemy_positions:
            dpos = _discretize(pos)
            if dpos not in posiciones_vivas:
                posiciones_muertas.append(list(pos))
    return posiciones_muertas


def _serializar_stats_interaction(vista_juego):
    from items.colections import InteractionManager
    im = InteractionManager()
    stats = {}
    for cat, datos in im.stats.items():
        stats[cat] = {"actual": datos["actual"], "total": datos["total"]}
    return stats


def cargar_partida(vista_juego):
    if not os.path.exists(SAVE_FILE):
        Log.warning("SaveSystem", "No se encontró archivo de guardado")
        return False

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("version", 1) < 2:
            Log.warning("SaveSystem", "Versión de guardado antigua, ignorando")
            return False

        _restaurar_player(vista_juego, data["player"])
        _restaurar_misiones(data)
        _restaurar_puertas(vista_juego, data.get("puertas", []))
        _restaurar_enemigos(vista_juego, data.get("enemigos", []))
        _restaurar_muertos(vista_juego, data.get("enemigos_muertos", []))
        _restaurar_rejas(vista_juego, data.get("rejas", {}))
        _restaurar_oleadas(vista_juego, data.get("oleadas", {}))
        _restaurar_interactions(vista_juego, data.get("interactions", {}))
        _restaurar_items_suelo(vista_juego, data.get("items_suelo", []))
        _restaurar_esbirros_jefe(vista_juego, data.get("esbirros_jefe", []))
        vista_juego.timer_dia_noche = data.get("dia_noche_timer", 0.0)
        vista_juego.timer_spawn_nido = data.get("timer_spawn_nido", 6.0)

        Log.info("SaveSystem", "Partida cargada correctamente")
        return True
    except Exception as e:
        Log.error("SaveSystem", "Error cargando partida", error=str(e))
        return False


def _restaurar_player(vista_juego, player_data):
    p = vista_juego.sprite_jugador
    p.center_x = player_data["x"]
    p.center_y = player_data["y"]
    p.vida = player_data["vida"]
    p.max_vida = player_data["max_vida"]
    p.stamina = player_data["stamina"]
    p.max_stamina = player_data.get("max_stamina", 100.0)
    p.stamina_cooldown_timer = player_data.get("stamina_cooldown_timer", 0.0)
    p.indice_activo = player_data.get("indice_activo", 0)
    p.direccion = player_data.get("direccion", "down")
    p.bateria_linterna = player_data.get("bateria_linterna", 100.0)
    p.linterna_encendida = player_data.get("linterna_encendida", True)
    p.slowed = player_data.get("slowed", 1.0)

    inventario = []
    for item_data in player_data.get("inventario", []):
        if item_data is None:
            inventario.append(None)
        else:
            inventario.append(item_from_dict(item_data))
    while len(inventario) < p.capacidad:
        inventario.append(None)
    p.inventory = inventario[:p.capacidad]

    p.estados = []
    for ed in player_data.get("estados", []):
        e = estado_from_dict(ed)
        if e:
            p.estados.append(e)

    p.texture = p.texturas.get(p.direccion, p.texturas["down"])


def _restaurar_misiones(data):
    from dialog.quest_manager import QM
    misiones_data = data.get("misiones", {})
    if misiones_data:
        QM.from_dict(misiones_data)


def _restaurar_puertas(vista_juego, puertas_data):
    from entities.blocks import Puerta
    for pd in puertas_data:
        for puerta in vista_juego.lista_puertas:
            if abs(puerta.center_x - pd["x"]) < 5 and abs(puerta.center_y - pd["y"]) < 5:
                puerta.estado = pd.get("estado", "cerrada")
                puerta.activa_colision = pd.get("activa_colision", True)
                puerta.tiempo_estado = pd.get("tiempo_estado", 0.0)
                frame_idx = 0 if puerta.estado in ("cerrada", "cerrando") else len(puerta.frames) - 1
                puerta.texture = puerta.frames[frame_idx]
                break


def _restaurar_enemigos(vista_juego, enemigos_data):
    from entities.enemy import EnemigoIA, EnemigoRanged, Jefe

    vista_juego._map_enemy_positions = set()

    for saved in enemigos_data:
        ex, ey = saved.get("x", 0), saved.get("y", 0)
        d_saved = _discretize((ex, ey))
        etype = saved.get("enemy_type", "")
        matched = False

        if etype == "Jefe":
            for e in vista_juego.lista_enemigos:
                if isinstance(e, Jefe):
                    e.vida = saved.get("vida", e.vida)
                    e.combate_iniciado = saved.get("combate_iniciado", False)
                    matched = True
                    break
            if not matched:
                from entities.enemy import Jefe
                w = saved.get("width", 736)
                h = saved.get("height", 448)
                jefe = Jefe(ex, ey, w, h)
                jefe.vida = saved.get("vida", 1000)
                jefe.combate_iniciado = saved.get("combate_iniciado", False)
                vista_juego.lista_enemigos.append(jefe)
            continue

        for e in vista_juego.lista_enemigos:
            d_current = _discretize((e.center_x, e.center_y))
            if d_current == d_saved:
                e.vida = saved.get("vida", e.vida)
                if hasattr(e, 'estado') and "estado_fsm" in saved:
                    e.estado = saved["estado_fsm"]
                if etype == "EnemigoRanged" and isinstance(e, EnemigoRanged):
                    e._timer_ataque_ranged = saved.get("_timer_ataque_ranged", 0.0)
                vista_juego._map_enemy_positions.add(d_saved)
                matched = True
                break

        if not matched:
            if etype == "EnemigoRanged":
                from entities.enemy import EnemigoRanged
                enemigo = EnemigoRanged(
                    x=ex, y=ey,
                    tipo_patrulla=saved.get("tipo_patrulla", EnemigoIA.TIPO_AREA),
                    area_center=(ex, ey),
                    area_radio=saved.get("area_radio", 500),
                    dano_ataque=saved.get("dano_ataque", 5.0),
                    vista_rango=saved.get("vista_rango", 800),
                    radio_R=saved.get("radio_R", 450),
                    radio_r=saved.get("radio_r", 200),
                    intervalo_ataque=saved.get("intervalo_ataque", 2.0),
                    inteligencia=saved.get("inteligencia", False),
                    rango_ataque=saved.get("rango_ataque", 300),
                    velocidad=saved.get("velocidad", 300),
                    velocidad_proyectil=saved.get("velocidad_proyectil", 400),
                )
            else:
                from entities.enemy import EnemigoIA
                enemigo = EnemigoIA(
                    x=ex, y=ey,
                    tipo_patrulla=saved.get("tipo_patrulla", EnemigoIA.TIPO_AREA),
                    area_center=(ex, ey),
                    area_radio=saved.get("area_radio", 500),
                    dano_ataque=saved.get("dano_ataque", 15.0),
                    vista_rango=saved.get("vista_rango", 800),
                    velocidad=saved.get("velocidad", 320),
                    velocidad_patrulla=saved.get("velocidad_patrulla", 120),
                )
            enemigo.enemy_id = saved.get("enemy_id", "bandido")
            enemigo.vida = saved.get("vida", 100)
            if "estado_fsm" in saved:
                enemigo.estado = saved["estado_fsm"]
            if etype == "EnemigoRanged" and isinstance(enemigo, EnemigoRanged):
                enemigo._timer_ataque_ranged = saved.get("_timer_ataque_ranged", 0.0)
            vista_juego.lista_enemigos.append(enemigo)


def _restaurar_muertos(vista_juego, muertos_data):
    mapa_posiciones = set()
    for pos in muertos_data:
        if len(pos) == 2:
            mapa_posiciones.add(_discretize((pos[0], pos[1])))

    vivos_a_quitar = []
    for e in vista_juego.lista_enemigos:
        dpos = _discretize((e.center_x, e.center_y))
        if dpos in mapa_posiciones:
            vivos_a_quitar.append(e)

    for e in vivos_a_quitar:
        e.kill()
        if e in vista_juego.lista_enemigos:
            vista_juego.lista_enemigos.remove(e)
        if e in vista_juego.lista_bloques:
            vista_juego.lista_bloques.remove(e)


def _restaurar_rejas(vista_juego, rejas_data):
    from entities.blocks import Puerta

    vista_juego.rejas_trial_activas = rejas_data.get("trial_activas", False)
    vista_juego.rejas_segura_activas = rejas_data.get("segura_activas", False)
    vista_juego.rejas_final_activas = rejas_data.get("final_activas", True)
    vista_juego.barrera_final_activas = rejas_data.get("barrera_final_activas", False)
    vista_juego.barrera_jefe_activas = rejas_data.get("barrera_jefe_activas", False)
    vista_juego.jefe_derrotado = rejas_data.get("jefe_derrotado", False)

    if vista_juego.rejas_trial_sprites:
        for reja in vista_juego.rejas_trial_sprites:
            if vista_juego.rejas_trial_activas:
                reja.visible = True
                if reja not in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.append(reja)
            else:
                reja.visible = False
                if reja in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.remove(reja)

    if vista_juego.rejas_segura_sprites:
        for reja in vista_juego.rejas_segura_sprites:
            if vista_juego.rejas_segura_activas:
                reja.visible = True
                if reja not in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.append(reja)
            else:
                reja.visible = False
                if reja in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.remove(reja)

    if vista_juego.rejas_final_sprites:
        for reja in vista_juego.rejas_final_sprites:
            if vista_juego.rejas_final_activas:
                reja.visible = True
                if reja not in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.append(reja)
            else:
                reja.visible = False
                if reja in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.remove(reja)

    if vista_juego.barrera_final_sprites:
        for muro in vista_juego.barrera_final_sprites:
            muro.visible = vista_juego.barrera_final_activas
            if vista_juego.barrera_final_activas:
                if muro not in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.append(muro)
            else:
                if muro in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.remove(muro)

    if vista_juego.barrera_jefe_sprites:
        for muro in vista_juego.barrera_jefe_sprites:
            muro.visible = vista_juego.barrera_jefe_activas
            if vista_juego.barrera_jefe_activas:
                if muro not in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.append(muro)
            else:
                if muro in vista_juego.lista_bloques:
                    vista_juego.lista_bloques.remove(muro)

    if vista_juego.rejas_trial_activas or vista_juego.rejas_segura_activas or vista_juego.barrera_final_activas or vista_juego.barrera_jefe_activas:
        vista_juego.physics_engine = arcade.PhysicsEngineSimple(
            vista_juego.sprite_jugador, vista_juego.lista_bloques
        )
        vista_juego.nav_manager.actualizar_desde_bloques(vista_juego.lista_bloques)


def _restaurar_oleadas(vista_juego, oleadas_data):
    vista_juego.oleadas_activas = oleadas_data.get("activas", False)
    vista_juego.oleadas_completadas = oleadas_data.get("completadas", False)
    vista_juego.oleada_actual = oleadas_data.get("actual", 0)
    vista_juego.timer_entre_oleadas = oleadas_data.get("timer_entre_oleadas", 0.0)
    vista_juego.max_oleadas = oleadas_data.get("max_oleadas", 3)


def _restaurar_interactions(vista_juego, interactions_data):
    from items.colections import InteractionManager
    im = InteractionManager()
    im.set_player(vista_juego.sprite_jugador)
    stats_data = interactions_data.get("stats", {})
    for cat, datos in stats_data.items():
        if cat in im.stats:
            im.stats[cat]["actual"] = datos.get("actual", 0)
            im.stats[cat]["total"] = datos.get("total", 0)


def _restaurar_items_suelo(vista_juego, items_data):
    vista_juego.item_manager.clear()
    for item_data in items_data:
        item = item_from_dict(item_data)
        if item:
            item.is_dropped = True
            vista_juego.item_manager.add_to_world(item)


def _restaurar_esbirros_jefe(vista_juego, esbirros_data):
    from entities.enemy import EnemigoIA
    vista_juego.lista_esbirros_jefe = []
    for ed in esbirros_data:
        ex, ey = ed.get("x", 0), ed.get("y", 0)
        enemigo = EnemigoIA(
            x=ex, y=ey,
            tipo_patrulla=EnemigoIA.TIPO_AREA,
            area_center=(ex, ey),
            area_radio=400,
            dano_ataque=15.0,
            vista_rango=800,
            velocidad=320,
            velocidad_patrulla=120,
        )
        enemigo.enemy_id = "bandido"
        enemigo.vida = ed.get("vida", 100)
        vista_juego.lista_enemigos.append(enemigo)
        vista_juego.lista_esbirros_jefe.append(enemigo)


def hay_partida_guardada():
    return os.path.exists(SAVE_FILE)


def borrar_partida():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
