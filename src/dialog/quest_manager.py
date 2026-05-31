import json
import os
from typing import Optional, Callable, Any
from utils.log import Log


class QuestObjective:
    def __init__(
        self,
        obj_id: str,
        tipo: str,
        target: str,
        cantidad: int,
        descripcion: str = "",
        progreso: int = 0
    ):
        self.id = obj_id
        self.tipo = tipo
        self.target = target
        self.cantidad = cantidad
        self.descripcion = descripcion
        self.progreso = progreso

    def is_completed(self) -> bool:
        return self.progreso >= self.cantidad

    def actualizar(self, cantidad: int = 1) -> bool:
        self.progreso = min(self.progreso + cantidad, self.cantidad)
        return self.is_completed()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "target": self.target,
            "cantidad": self.cantidad,
            "descripcion": self.descripcion,
            "progreso": self.progreso
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestObjective":
        return cls(
            data["id"],
            data["tipo"],
            data["target"],
            data["cantidad"],
            data.get("descripcion", ""),
            data.get("progreso", 0)
        )


class Quest:
    TIPO_KILL = "kill"
    TIPO_COLLECT = "collect"
    TIPO_TALK = "talk"
    TIPO_REACH = "reach"
    TIPO_CUSTOM = "custom"

    ESTADO_BLOQUEADA = "bloqueada"
    ESTADO_DISPONIBLE = "disponible"
    ESTADO_EN_PROGRESO = "en_progreso"
    ESTADO_COMPLETADA = "completada"

    def __init__(
        self,
        quest_id: str,
        nombre: str,
        descripcion: str,
        objetivos: list[dict],
        recompensas: dict,
        estado: str = ESTADO_DISPONIBLE,
        requisitos: dict = None,
        dialogo_inicio: str = None,
        dialogo_completado: str = None
    ):
        self.id = quest_id
        self.nombre = nombre
        self.descripcion = descripcion
        self._objetivos: list[QuestObjective] = [
            QuestObjective.from_dict(o) for o in objetivos
        ]
        self.recompensas = recompensas
        self.estado = estado
        self.requisitos = requisitos or {}
        self.dialogo_inicio = dialogo_inicio
        self.dialogo_completado = dialogo_completado
        self._callbacks_completado: list[Callable] = []
        self.recompensa_entregada: bool = False

    def get_objetivos(self) -> list[QuestObjective]:
        return self._objetivos

    def get_objetivo(self, obj_id: str) -> Optional[QuestObjective]:
        for obj in self._objetivos:
            if obj.id == obj_id:
                return obj
        return None

    def objetivos_completados(self) -> bool:
        return all(obj.is_completed() for obj in self._objetivos)

    def progreso_total(self) -> tuple[int, int]:
        completados = sum(1 for o in self._objetivos if o.is_completed())
        return (completados, len(self._objetivos))

    def actualizar_objetivo(self, obj_id: str, cantidad: int = 1) -> bool:
        objetivo = self.get_objetivo(obj_id)
        if objetivo:
            return objetivo.actualizar(cantidad)
        return False

    def iniciar(self) -> bool:
        if self.estado != self.ESTADO_DISPONIBLE:
            return False
        self.estado = self.ESTADO_EN_PROGRESO
        return True

    def completar(self) -> bool:
        if self.estado != self.ESTADO_EN_PROGRESO:
            return False
        if not self.objetivos_completados():
            return False
        self.estado = self.ESTADO_COMPLETADA
        for callback in self._callbacks_completado:
            callback(self)
        return True

    def registrar_callback(self, callback: Callable) -> None:
        self._callbacks_completado.append(callback)

    def entregar_recompensa(self) -> bool:
        if self.recompensa_entregada:
            return False
        self.recompensa_entregada = True
        return True

    def recompra_entregada(self) -> bool:
        return self.recompensa_entregada

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "objetivos": [o.to_dict() for o in self._objetivos],
            "recompensas": self.recompensas,
            "estado": self.estado,
            "requisitos": self.requisitos,
            "dialogo_inicio": self.dialogo_inicio,
            "dialogo_completado": self.dialogo_completado,
            "recompensa_entregada": self.recompensa_entregada
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        quest = cls(
            data["id"],
            data["nombre"],
            data["descripcion"],
            data["objetivos"],
            data["recompensas"],
            data.get("estado", cls.ESTADO_DISPONIBLE),
            data.get("requisitos"),
            data.get("dialogo_inicio"),
            data.get("dialogo_completado")
        )
        quest.recompensa_entregada = data.get("recompensa_entregada", False)
        return quest


class QuestEventBus:
    _instance = None

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    @classmethod
    def get_instance(cls) -> "QuestEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: dict = None) -> None:
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data or {})
                except Exception as e:
                    Log.error("QuestEventBus", f"Error en callback: {e}")

    @classmethod
    def clear_bus(cls) -> None:
        """Vacía todos los suscriptores y destruye la instancia del EventBus."""
        if cls._instance:
            cls._instance._subscribers.clear()
        cls._instance = None
        Log.info("QuestEventBus", "EventBus reiniciado a cero.")


class QuestManager:
    _instance = None
    _default_callbacks: dict[str, Callable] = {}

    def __init__(self):
        self.misiones: dict[str, Quest] = {}
        self.misiones_activas: list[str] = []
        self.misiones_completadas: list[str] = []
        self.event_bus = QuestEventBus.get_instance()
        self._on_progress_callback: Optional[Callable] = None
        self._on_complete_callback: Optional[Callable] = None

    @classmethod
    def get_instance(cls) -> "QuestManager":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.cargar_misiones_defecto()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def set_progress_callback(self, callback: Callable[[str, Quest, QuestObjective], None]) -> None:
        self._on_progress_callback = callback

    def set_complete_callback(self, callback: Callable[[str, Quest], None]) -> None:
        self._on_complete_callback = callback

    def cargar_misiones_defecto(self) -> None:
        ruta = "assets/misiones.json"
        if not os.path.exists(ruta):
            Log.warning("QuestManager", "Archivo de misiones no encontrado", ruta=ruta)
            return

        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)

        for quest_data in data.get("misiones", []):
            quest = Quest.from_dict(quest_data)
            self.misiones[quest.id] = quest
            if quest.estado == Quest.ESTADO_EN_PROGRESO:
                if quest.id not in self.misiones_activas:
                    self.misiones_activas.append(quest.id)
            elif quest.estado == Quest.ESTADO_COMPLETADA:
                if quest.id not in self.misiones_completadas:
                    self.misiones_completadas.append(quest.id)
            Log.debug("QuestManager", "Misión cargada", quest_id=quest.id, nombre=quest.nombre)

    def get_mision(self, quest_id: str) -> Optional[Quest]:
        return self.misiones.get(quest_id)

    def get_misiones_bloqueadas(self) -> list[Quest]:
        return [q for q in self.misiones.values() if q.estado == Quest.ESTADO_BLOQUEADA]

    def get_misiones_disponibles(self) -> list[Quest]:
        return [q for q in self.misiones.values() if q.estado == Quest.ESTADO_DISPONIBLE]

    def get_misiones_activas(self) -> list[Quest]:
        return [q for q in self.misiones.values() if q.estado == Quest.ESTADO_EN_PROGRESO]

    def get_misiones_completadas(self) -> list[Quest]:
        return [q for q in self.misiones.values() if q.estado == Quest.ESTADO_COMPLETADA]

    def iniciar_mision(self, quest_id: str) -> bool:
        quest = self.get_mision(quest_id)
        if quest is None:
            Log.warning("QuestManager", "Misión no encontrada", quest_id=quest_id)
            return False

        if quest.estado == Quest.ESTADO_BLOQUEADA:
            Log.warning("QuestManager", "Misión bloqueada", quest_id=quest_id)
            return False

        if quest.estado not in [Quest.ESTADO_DISPONIBLE]:
            Log.warning("QuestManager", "Misión no disponible", quest_id=quest_id, estado=quest.estado)
            return False

        if not quest.iniciar():
            return False

        if quest_id not in self.misiones_activas:
            self.misiones_activas.append(quest_id)

        Log.info("QuestManager", "Misión iniciada", quest_id=quest_id, nombre=quest.nombre)
        self.event_bus.publish("quest_started", {"quest_id": quest_id, "quest": quest})
        return True

    def completar_mision(self, quest_id: str, aplicar_recompensas: bool = True) -> bool:
        quest = self.get_mision(quest_id)
        if quest is None:
            Log.warning("QuestManager", "Misión no encontrada", quest_id=quest_id)
            return False

        if quest.estado != Quest.ESTADO_EN_PROGRESO:
            Log.warning("QuestManager", "Misión no está en progreso", quest_id=quest_id, estado=quest.estado)
            return False

        if not quest.objetivos_completados():
            progreso = quest.progreso_total()
            Log.warning("QuestManager", "Objetivos incompletos", quest_id=quest_id, progreso=progreso)
            return False

        quest.completar()

        if quest_id in self.misiones_activas:
            self.misiones_activas.remove(quest_id)

        if quest_id not in self.misiones_completadas:
            self.misiones_completadas.append(quest_id)

        Log.info("QuestManager", "Misión completada", quest_id=quest_id, nombre=quest.nombre)

        if aplicar_recompensas:
            self._aplicar_recompensas(quest)

        self.event_bus.publish("quest_completed", {"quest_id": quest_id, "quest": quest})

        if self._on_complete_callback:
            self._on_complete_callback(quest_id, quest)

        self._desbloquear_siguientes(quest_id)
        return True

    def actualizar_objetivo(
        self,
        quest_id: str,
        obj_id: str,
        cantidad: int = 1
    ) -> bool:
        quest = self.get_mision(quest_id)
        if quest is None or quest.estado != Quest.ESTADO_EN_PROGRESO:
            return False

        if not quest.actualizar_objetivo(obj_id, cantidad):
            return False

        objetivo = quest.get_objetivo(obj_id)

        if self._on_progress_callback:
            self._on_progress_callback(quest_id, quest, objetivo)

        self.event_bus.publish("objective_updated", {
            "quest_id": quest_id,
            "objetivo": objetivo.to_dict()
        })

        if quest.objetivos_completados():
            self.completar_mision(quest_id)

        return True

    def _on_enemy_killed(self, data: dict) -> None:
        enemy_id = data.get("enemy_id")
        for quest in self.get_misiones_activas():
            for objetivo in quest.get_objetivos():
                if objetivo.tipo == Quest.TIPO_KILL and objetivo.target == enemy_id:
                    self.actualizar_objetivo(quest.id, objetivo.id)

    def _on_item_collected(self, data: dict) -> None:
        item_id = data.get("item_id")
        cantidad = data.get("cantidad", 1)
        for quest in self.get_misiones_activas():
            for objetivo in quest.get_objetivos():
                if objetivo.tipo == Quest.TIPO_COLLECT and objetivo.target == item_id:
                    self.actualizar_objetivo(quest.id, objetivo.id, cantidad)

    def _on_npc_talked(self, data: dict) -> None:
        npc_id = data.get("npc_id")
        for quest in self.get_misiones_activas():
            for objetivo in quest.get_objetivos():
                if objetivo.tipo == Quest.TIPO_TALK and objetivo.target == npc_id:
                    self.actualizar_objetivo(quest.id, objetivo.id)

    def _on_location_reached(self, data: dict) -> None:
        location_id = data.get("location_id")
        for quest in self.get_misiones_activas():
            for objetivo in quest.get_objetivos():
                if objetivo.tipo == Quest.TIPO_REACH and objetivo.target == location_id:
                    self.actualizar_objetivo(quest.id, objetivo.id)

    def suscripcion_automatica(self) -> None:
        self.event_bus.subscribe("enemy_killed", self._on_enemy_killed)
        self.event_bus.subscribe("item_collected", self._on_item_collected)
        self.event_bus.subscribe("npc_talked", self._on_npc_talked)
        self.event_bus.subscribe("location_reached", self._on_location_reached)

    def _aplicar_recompensas(self, quest: Quest) -> None:
        recompensas = quest.recompensas
        Log.info("QuestManager", "Aplicando recompensas", quest_id=quest.id, recompensas=recompensas)
        self.event_bus.publish("quest_reward", {"quest_id": quest.id, "recompensas": recompensas})

    def _desbloquear_siguientes(self, quest_id: str) -> None:
        for quest in self.misiones.values():
            if quest.estado == Quest.ESTADO_BLOQUEADA:
                requisitos = quest.requisitos
                if requisitos.get("mision_anterior") == quest_id:
                    quest.estado = Quest.ESTADO_DISPONIBLE
                    Log.info("QuestManager", "Misión desbloqueada", quest_id=quest.id)

    def esta_completada(self, quest_id: str) -> bool:
        quest = self.get_mision(quest_id)
        return quest is not None and quest.estado == Quest.ESTADO_COMPLETADA

    def esta_activa(self, quest_id: str) -> bool:
        quest = self.get_mision(quest_id)
        return quest is not None and quest.estado == Quest.ESTADO_EN_PROGRESO

    def recompensa_entregada(self, quest_id: str) -> bool:
        quest = self.get_mision(quest_id)
        return quest is not None and quest.recompensa_entregada

    def to_dict(self) -> dict:
        return {
            "misiones_activas": self.misiones_activas,
            "misiones_completadas": self.misiones_completadas,
            "estados": {
                qid: self.misiones[qid].estado
                for qid in self.misiones
                if qid in self.misiones_activas or qid in self.misiones_completadas
            },
            "progreso": {
                qid: [o.to_dict() for o in self.misiones[qid].get_objetivos()]
                for qid in self.misiones_activas
            }
        }

    def from_dict(self, data: dict) -> None:
        self.misiones_activas = data.get("misiones_activas", [])
        self.misiones_completadas = data.get("misiones_completadas", [])
        estados = data.get("estados", {})
        progreso = data.get("progreso", {})

        for quest_id, estado in estados.items():
            if quest_id in self.misiones:
                self.misiones[quest_id].estado = estado
                if estado == Quest.ESTADO_COMPLETADA and quest_id not in self.misiones_completadas:
                    self.misiones_completadas.append(quest_id)
                elif estado == Quest.ESTADO_EN_PROGRESO and quest_id not in self.misiones_activas:
                    self.misiones_activas.append(quest_id)

        # Misión del trial en la zona spawn se fuerza a estar en progreso si no está completada
        if "mision_trial" in self.misiones:
            if self.misiones["mision_trial"].estado != Quest.ESTADO_COMPLETADA:
                self.misiones["mision_trial"].estado = Quest.ESTADO_EN_PROGRESO
                if "mision_trial" not in self.misiones_activas:
                    self.misiones_activas.append("mision_trial")

        for quest_id, objetivos_data in progreso.items():
            if quest_id in self.misiones:
                objetivos_quest = self.misiones[quest_id].get_objetivos()
                for i, obj_data in enumerate(objetivos_data):
                    if i < len(objetivos_quest):
                        objetivos_quest[i].progreso = obj_data.get("progreso", 0)
                        
    def clear_manager(self, default: bool = True) -> None:
        """Vacía por completo el progreso de las misiones y las restablece a su estado inicial."""
        Log.info("QuestManager", "Vaciando datos lógicos de misiones...")
        
        # Limpiar diccionarios y listas de progreso
        self.misiones.clear()
        self.misiones_activas.clear()
        self.misiones_completadas.clear()
        
        # Quitar los callbacks globales de la interfaz
        self._on_progress_callback = None
        self._on_complete_callback = None
        
        # Limpiar los suscriptores del EventBus propio
        if self.event_bus:
            self.event_bus.clear_bus()
            
        # ¡CRÍTICO!: Volvemos a cargar las misiones por defecto aquí
        # Esto asegura que el diccionario misiones no esté vacío y que "verificar_condicion" no falle
        if default: self.cargar_misiones_defecto()
            
        Log.info("QuestManager", "QuestManager restablecido con misiones base limpias.")



QM = QuestManager.get_instance()
EB = QuestEventBus.get_instance()