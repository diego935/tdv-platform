import arcade

class FloatingMessage:
    def __init__(self, text, x, y, color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color  # RGB tuple
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
            # Creamos el color con la transparencia actual
            r, g, b = self.color
            color = (r, g, b, self.alpha)
            arcade.draw_text(
                self.text, 
                self.x, 
                self.y, 
                color, 
                font_size=12, 
                anchor_x="center",
                font_name="Arial"
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

    def show_message(self, text, x, y, color=(255, 255, 255)):
        from vista.inventory import FloatingMessage 
        nuevo = FloatingMessage(text, x, y, color)
        self.floating_messages.append(nuevo)

    def update(self):
        for m in self.floating_messages:
            m.update()
        self.floating_messages = [m for m in self.floating_messages if m.active]

    def draw(self):
        for m in self.floating_messages:
            m.draw()