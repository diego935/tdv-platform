import sys
import os
from datetime import datetime

class Log:
    NIVEL_DEBUG = 0
    NIVEL_INFO = 1
    NIVEL_WARNING = 2
    NIVEL_ERROR = 3
    
    _nivel = NIVEL_DEBUG
    _log_file = None
    
    @classmethod
    def init(cls, log_file: str = "game.log"):
        cls._log_file = open(log_file, "a", encoding="utf-8")
    
    @classmethod
    def close(cls):
        if cls._log_file:
            cls._log_file.close()
            cls._log_file = None
    
    @classmethod
    def _formatear(cls, nivel: str, fuente: str, mensaje: str, params: str) -> str:
        return f"[{datetime.now().strftime('%H:%M:%S')}][{nivel}][{fuente}] {mensaje} {params}"
    
    @classmethod
    def _escribir(cls, texto: str):
        print(texto)
        if cls._log_file:
            cls._log_file.write(texto + "\n")
            cls._log_file.flush()
    
    @classmethod
    def debug(cls, fuente: str, mensaje: str, **kwargs):
        if cls._nivel <= cls.NIVEL_DEBUG:
            params = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
            cls._escribir(cls._formatear("DEBUG", fuente, mensaje, params))
    
    @classmethod
    def info(cls, fuente: str, mensaje: str, **kwargs):
        if cls._nivel <= cls.NIVEL_INFO:
            params = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
            cls._escribir(cls._formatear("INFO", fuente, mensaje, params))
    
    @classmethod
    def warning(cls, fuente: str, mensaje: str, **kwargs):
        if cls._nivel <= cls.NIVEL_WARNING:
            params = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
            cls._escribir(cls._formatear("WARN", fuente, mensaje, params))
    
    @classmethod
    def error(cls, fuente: str, mensaje: str, **kwargs):
        if cls._nivel <= cls.NIVEL_ERROR:
            params = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
            cls._escribir(cls._formatear("ERROR", fuente, mensaje, params))