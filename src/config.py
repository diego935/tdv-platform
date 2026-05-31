ANCHO_VENTANA = 1280
ALTO_VENTANA = 720
TITULO_VENTANA = "Pill of Silence"

COLOR_FONDO_MENU = (20, 20, 20)
COLOR_FONDO_JUEGO = (47, 79, 79)


CELL_SIZE = 64
DISTANCIA_ACTUALIZACION = 1500
# CONFIGURACIÓN DE LA LINTERNA (EFECTO FOV)
LINTERNA_APERTURA_GRADOS = 30  # Esto es por cada lado

# Distancia en píxeles que alcanza a iluminar el haz de luz frontal
LINTERNA_ALCANCE = 1200         

# Radio en píxeles del hueco central para que el sprite del jugador se vea completo
LINTERNA_RADIO_JUGADOR = 70    

# Tamaño del escudo exterior de oscuridad (debe ser muy grande para tapar toda la pantalla)
LINTERNA_RADIO_MAX_MAPA = 4500 

# Color y opacidad de la noche/oscuridad (R, G, B, Alpha). 255 es oscuridad ciega absoluta.
LINTERNA_COLOR_OSCURIDAD = (0, 0, 0, 242)

# Ciclo dia noche
DURACION_DIA_SEGUNDOS = 120.0  

# Opacidad mínima en el mediodía (0 = sol radiante y luz invisible, 20 = sombra muy tenue)
ALPHA_MIN_MEDIODIA = 0         

# Opacidad máxima en la medianoche (245 = casi a oscuras por completo)
ALPHA_MAX_MEDIANOCHE = 245