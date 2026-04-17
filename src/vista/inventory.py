import arcade
from vista.textos import * 



class BaseInventoryUI:
    def __init__(self, capacity: int, box_size: int = 80, padding: int = 20):
        self.capacity = capacity
        self.box_size = box_size
        self.padding = padding
        
        # Estética estilo SCP
        self.background_color = (20, 20, 20, 180) 
        self.box_color = (40, 40, 40, 100)             
        self.border_color = arcade.color.WHITE    
        self.text_color = arcade.color.WHITE

    def draw(self, items: list, selected_index: int = None):
        window = arcade.get_window()
        
        # 1. Fondo Oscuro
        arcade.draw_rect_filled(
            arcade.rect.XYWH(window.width/2, window.height/2, window.width, window.height),
            self.background_color
        )

        # --- AJUSTE DE CENTRADO ---
        columns = 4
        grid_width = (columns * self.box_size) + ((columns - 1) * self.padding)
        start_x = (window.width - grid_width) / 2 + (self.box_size / 2)
        start_y = (window.height / 2) + (self.box_size / 2) + (self.padding / 2)

        for i in range(self.capacity):
            col = i % columns
            row = i // columns

            current_x = start_x + (col * (self.box_size + self.padding))
            current_y = start_y - (row * (self.box_size + self.padding))
            
            is_selected = (i == selected_index)
            current_border = arcade.color.CYAN if is_selected else self.border_color
            slot_rect = arcade.rect.XYWH(current_x, current_y, self.box_size, self.box_size)
            
            arcade.draw_rect_filled(slot_rect, self.box_color)
            arcade.draw_rect_outline(slot_rect, current_border, border_width=2 if is_selected else 1)

            if i < len(items):
                item = items[i]
                if hasattr(item, 'texture') and item.texture:
                    item_rect = arcade.rect.XYWH(
                        current_x, 
                        current_y, 
                        self.box_size * 0.7, 
                        self.box_size * 0.7
                    )
                    arcade.draw_texture_rect(texture=item.texture, rect=item_rect)
                
                if is_selected:
                    nombre = item.name if hasattr(item, 'name') else "Slot Vacio"
                    arcade.draw_text(
                        nombre.upper(), 
                        current_x, 
                        current_y - (self.box_size / 2) - 25,
                        arcade.color.CYAN, 
                        font_size=10, 
                        anchor_x="center", 
                        bold=True
                    )

    def get_slot_at_pointer(self, mouse_x, mouse_y):
        window = arcade.get_window()
        
        columns = 4
        grid_width = (columns * self.box_size) + ((columns - 1) * self.padding)
        start_x = (window.width - grid_width) / 2 + (self.box_size / 2)
        start_y = (window.height / 2) + (self.box_size / 2) + (self.padding / 2)

        for i in range(self.capacity):
            col = i % columns
            row = i // columns
            
            cx = start_x + (col * (self.box_size + self.padding))
            cy = start_y - (row * (self.box_size + self.padding))

            if (abs(mouse_x - cx) < self.box_size / 2 and 
                abs(mouse_y - cy) < self.box_size / 2):
                return i 
                
        return None
