import arcade
from vista.textos import * 


class BaseInventoryUI:
    # Constants
    COLUMNS = 4
    
    def __init__(self, capacity: int, box_size: int = 80, padding: int = 20):
        self.capacity = capacity
        self.box_size = box_size
        self.padding = padding
        
        # Colors
        self.background_color = (20, 20, 20, 180) 
        self.box_color = (40, 40, 40, 100)
        self.box_color_hover = (60, 60, 60, 150)
        self.box_color_drag_source = (100, 80, 40, 200)
        self.border_color = arcade.color.WHITE
        self.border_color_hover = arcade.color.CYAN
        self.border_color_drag_target = arcade.color.GOLD
        
        # Drag state
        self._drag_source = None
        self._hover_index = None

    def _get_grid_metrics(self):
        """Calculate grid metrics - returns (start_x, start_y)."""
        window = arcade.get_window()
        grid_width = (self.COLUMNS * self.box_size) + ((self.COLUMNS - 1) * self.padding)
        start_x = (window.width - grid_width) / 2 + (self.box_size / 2)
        start_y = (window.height / 2) + (self.box_size / 2) + (self.padding / 2)
        return start_x, start_y

    def get_slot_at_pointer(self, mouse_x, mouse_y):
        start_x, start_y = self._get_grid_metrics()

        for i in range(self.capacity):
            col = i % self.COLUMNS
            row = i // self.COLUMNS
            
            cx = start_x + (col * (self.box_size + self.padding))
            cy = start_y - (row * (self.box_size + self.padding))

            if abs(mouse_x - cx) < self.box_size / 2 and abs(mouse_y - cy) < self.box_size / 2:
                return i 
                
        return None

    def set_hover(self, idx):
        self._hover_index = idx

    def draw(self, items: list, drag_source: int = None, mouse_pos: tuple = None):
        window = arcade.get_window()
        
        # Fondo
        arcade.draw_rect_filled(
            arcade.rect.XYWH(window.width/2, window.height/2, window.width, window.height),
            self.background_color
        )

        start_x, start_y = self._get_grid_metrics()

        for i in range(self.capacity):
            col = i % self.COLUMNS
            row = i // self.COLUMNS

            current_x = start_x + (col * (self.box_size + self.padding))
            current_y = start_y - (row * (self.box_size + self.padding))
            
            is_hover = (i == self._hover_index)
            is_drag_source = (i == drag_source)
            is_drag_target = (is_hover and drag_source is not None and i != drag_source)

            # Colors
            if is_drag_source:
                bg = self.box_color_drag_source
            elif is_hover:
                bg = self.box_color_hover
            else:
                bg = self.box_color

            if is_drag_target:
                border = self.border_color_drag_target
                border_w = 3
            elif is_hover or is_drag_source:
                border = self.border_color_hover
                border_w = 2
            else:
                border = self.border_color
                border_w = 1

            slot_rect = arcade.rect.XYWH(current_x, current_y, self.box_size, self.box_size)
            arcade.draw_rect_filled(slot_rect, bg)
            arcade.draw_rect_outline(slot_rect, border, border_width=border_w)

            # Item
            if i < len(items) and items[i] is not None:
                if i != drag_source:
                    item = items[i]
                    if hasattr(item, 'texture') and item.texture:
                        item_rect = arcade.rect.XYWH(current_x, current_y, self.box_size * 0.7, self.box_size * 0.7)
                        arcade.draw_texture_rect(texture=item.texture, rect=item_rect)
                
                if is_hover:
                    nombre = items[i].name if hasattr(items[i], 'name') else "Item"
                    arcade.draw_text(nombre.upper(), current_x, current_y - (self.box_size / 2) - 25,
                                arcade.color.CYAN, font_size=10, anchor_x="center", bold=True)

        # Draw dragged item
        if drag_source is not None and mouse_pos is not None and drag_source < len(items):
            item = items[drag_source]
            if item and hasattr(item, 'texture') and item.texture:
                mx, my = mouse_pos
                item_rect = arcade.rect.XYWH(mx, my, self.box_size * 0.7, self.box_size * 0.7)
                arcade.draw_texture_rect(texture=item.texture, rect=item_rect, alpha=200)