import arcade

class FloatingMessage:
    def __init__(self, text, x, y):
        self.text = text
        self.x = x
        self.y = y
        self.alpha = 255  # Opacidad total al inicio
        self.speed = 0.5  # Qué tan rápido sube
        self.fade_rate = 2 # Qué tan rápido desaparece
        self.active = True

    def update(self):
        # Mueve el texto hacia arriba lentamente
        self.y += self.speed
        # Reduce la opacidad
        self.alpha -= self.fade_rate
        
        if self.alpha <= 0:
            self.alpha = 0
            self.active = False

    def draw(self):
        if self.active:
            # Creamos el color blanco con la transparencia actual
            color = (255, 255, 255, self.alpha)
            arcade.draw_text(
                self.text, 
                self.x, 
                self.y, 
                color, 
                font_size=12, 
                anchor_x="center",
                font_name="Arial" # O tu fuente por defecto
            )



class TextManager:
    _instance = None  # Aquí guardamos la instancia única

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TextManager, cls).__new__(cls)
            # Inicializamos la lista solo la primera vez
            cls._instance.floating_messages = []
        return cls._instance 
        ## NOTE: Esto es un singleton, es una clase que solo es instanciada una vez, las siguientes veces que se intenta devuelve la clase ya instanciada.

    def show_message(self, text, x, y):
        # Import local para evitar errores de importación circular
        from vista.inventory import FloatingMessage 
        nuevo = FloatingMessage(text, x, y)
        self.floating_messages.append(nuevo)

    def update(self):
        for m in self.floating_messages:
            m.update()
        self.floating_messages = [m for m in self.floating_messages if m.active]

    def draw(self):
        for m in self.floating_messages:
            m.draw()