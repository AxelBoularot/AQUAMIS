BASE_WIDTH = 1500
BASE_HEIGHT = 750


def _compute_transform(
    current_size,
    *,
    menu_height: int = 0,
    max_width_crop_ratio: float = 0.15,
):
       
    current_w, current_h = current_size
    available_h = current_h - menu_height
    if available_h <= 0:
        return 0.0, 0, menu_height, 0, 0

    sx = current_w / BASE_WIDTH
    sy = available_h / BASE_HEIGHT

    base_aspect = BASE_WIDTH / BASE_HEIGHT
    area_aspect = current_w / available_h

                                                                                                
                                                                                            
                                       
    portrait_threshold = base_aspect * 0.80
    if area_aspect < portrait_threshold:
        cover = max(sx, sy)
        contain = min(sx, sy)
        new_w_cover = int(BASE_WIDTH * cover)
        if current_w > 0:
            crop_ratio = max(0.0, (new_w_cover - current_w) / current_w)
        else:
            crop_ratio = 1.0
        scale = cover if crop_ratio <= float(max_width_crop_ratio) else contain
    else:
        scale = min(sx, sy)

    new_width = int(BASE_WIDTH * scale)
    new_height = int(BASE_HEIGHT * scale)

    x_offset = (current_w - new_width) // 2
    y_offset = menu_height + (available_h - new_height) // 2
    return scale, x_offset, y_offset, new_width, new_height


def compute_transform_with_menu(screen, menu_height: int, *, max_width_crop_ratio: float = 0.15):
                                                                         
    return _compute_transform(screen.get_size(), menu_height=menu_height, max_width_crop_ratio=max_width_crop_ratio)

def get_scaling_factors(screen):
    current_width, current_height = screen.get_size()
    scale_x = current_width / BASE_WIDTH
    scale_y = current_height / BASE_HEIGHT
    return scale_x, scale_y

def scale_pos(x, y, scale_x, scale_y):
    return int(x * scale_x), int(y * scale_y)

def scale_size(width, height, scale_x, scale_y):
    return int(width * scale_x), int(height * scale_y)

def convert_mouse_pos_with_menu(
    mouse_pos,
    screen,
    menu_height,
    *,
    max_width_crop_ratio: float = 0.15,
):
    current_size = screen.get_size()
    scale, x_offset, y_offset, _, _ = _compute_transform(
        current_size,
        menu_height=menu_height,
        max_width_crop_ratio=max_width_crop_ratio,
    )
    if scale == 0:
        return (0, 0)
    
    virtual_x = int((mouse_pos[0] - x_offset) / scale)
    virtual_y = int((mouse_pos[1] - y_offset) / scale)
    
    virtual_x = max(0, min(BASE_WIDTH - 1, virtual_x))
    virtual_y = max(0, min(BASE_HEIGHT - 1, virtual_y))
    
    return (virtual_x, virtual_y)