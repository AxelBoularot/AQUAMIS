BASE_WIDTH = 1500
BASE_HEIGHT = 750

def get_scaling_factors(screen):
    current_width, current_height = screen.get_size()
    scale_x = current_width / BASE_WIDTH
    scale_y = current_height / BASE_HEIGHT
    return scale_x, scale_y

def scale_pos(x, y, scale_x, scale_y):
    return int(x * scale_x), int(y * scale_y)

def scale_size(width, height, scale_x, scale_y):
    return int(width * scale_x), int(height * scale_y)

def convert_mouse_pos(mouse_pos, screen):
    current_size = screen.get_size()
    if current_size == (BASE_WIDTH, BASE_HEIGHT):
        return mouse_pos
    
    scale_x = current_size[0] / BASE_WIDTH
    scale_y = current_size[1] / BASE_HEIGHT
    scale = min(scale_x, scale_y)
    
    new_width = int(BASE_WIDTH * scale)
    new_height = int(BASE_HEIGHT * scale)
    
    x_offset = (current_size[0] - new_width) // 2
    y_offset = (current_size[1] - new_height) // 2
    
    virtual_x = int((mouse_pos[0] - x_offset) / scale)
    virtual_y = int((mouse_pos[1] - y_offset) / scale)
    
    virtual_x = max(0, min(BASE_WIDTH - 1, virtual_x))
    virtual_y = max(0, min(BASE_HEIGHT - 1, virtual_y))
    
    return (virtual_x, virtual_y)

def convert_mouse_pos_with_menu(mouse_pos, screen, menu_height):
    current_size = screen.get_size()
    
    available_h = current_size[1] - menu_height
    scale = min(current_size[0] / BASE_WIDTH, available_h / BASE_HEIGHT)
    
    new_width = int(BASE_WIDTH * scale)
    new_height = int(BASE_HEIGHT * scale)
    
    x_offset = (current_size[0] - new_width) // 2
    y_offset = menu_height + (available_h - new_height) // 2
    
    if scale == 0: return (0, 0)
    
    virtual_x = int((mouse_pos[0] - x_offset) / scale)
    virtual_y = int((mouse_pos[1] - y_offset) / scale)
    
    virtual_x = max(0, min(BASE_WIDTH - 1, virtual_x))
    virtual_y = max(0, min(BASE_HEIGHT - 1, virtual_y))
    
    return (virtual_x, virtual_y)