from PyQt5.QtWidgets import QApplication

def move_window_to_screen(window, screen_number=0, center=False):
    app = QApplication.instance()
    screens = app.screens()
    if screen_number < len(screens):
        geometry = screens[screen_number].geometry()
        if center:
            frame_geom = window.frameGeometry()
            frame_geom.moveCenter(geometry.center())
            window.move(frame_geom.topLeft())
        else:
            window.move(geometry.left(), geometry.top())
    else:
        window.move(100, 100)

def move_window_to_screen_center(window, screen_number=0, width=None, height=None):
    app = QApplication.instance()
    screens = app.screens()
    if screen_number < len(screens):
        geometry = screens[screen_number].geometry()
        if width and height:
            window.resize(width, height)
        frame_geom = window.frameGeometry()
        frame_geom.setWidth(width or frame_geom.width())
        frame_geom.setHeight(height or frame_geom.height())
        frame_geom.moveCenter(geometry.center())
        window.move(frame_geom.topLeft())
    else:
        if width and height:
            window.resize(width, height)
        window.move(100, 100)

def move_window_to_screen_right_of(window, reference_window, screen_number=0, width=None, height=None):
    app = QApplication.instance()
    screens = app.screens()
    if screen_number < len(screens):
        geometry = screens[screen_number].geometry()
        ref_geom = reference_window.frameGeometry()
        if width and height:
            window.resize(width, height)
        # Place to the right of the reference window, but within the screen
        x = ref_geom.right() + 10
        y = ref_geom.top()
        # If it would go off the screen, clamp to screen
        if x + (width or window.width()) > geometry.right():
            x = geometry.right() - (width or window.width())
        if y + (height or window.height()) > geometry.bottom():
            y = geometry.bottom() - (height or window.height())
        window.move(max(x, geometry.left()), max(y, geometry.top()))
    else:
        if width and height:
            window.resize(width, height)
        window.move(100, 100)

def move_window_according_to_preferences(window, app_config, width=None, height=None, window_type="data_entry"):
    """
    Position window according to user preferences stored in app_config.
    
    Args:
        window: The window to position
        app_config: AppConfig instance containing positioning preferences
        width: Optional width to resize window to
        height: Optional height to resize window to
        window_type: Type of window ("data_entry" or "svg_display")
    """
    app = QApplication.instance()
    screens = app.screens()
    
    if window_type == "data_entry":
        screen_number = app_config.general.data_entry_screen
        position = app_config.general.data_entry_position
        custom_x = app_config.general.data_entry_x
        custom_y = app_config.general.data_entry_y
    elif window_type == "svg_display":
        screen_number = app_config.general.svg_display_screen
        position = app_config.general.svg_display_position
        custom_x = app_config.general.svg_display_x
        custom_y = app_config.general.svg_display_y
    else:
        # Fallback to data entry settings
        screen_number = app_config.general.data_entry_screen
        position = app_config.general.data_entry_position
        custom_x = app_config.general.data_entry_x
        custom_y = app_config.general.data_entry_y
    
    # Ensure screen number is valid
    if screen_number >= len(screens):
        screen_number = 0
    
    geometry = screens[screen_number].geometry()
    
    # Resize window if dimensions provided
    if width and height:
        window.resize(width, height)
    
    # Calculate position based on preference
    if position == "center":
        frame_geom = window.frameGeometry()
        frame_geom.setWidth(width or frame_geom.width())
        frame_geom.setHeight(height or frame_geom.height())
        frame_geom.moveCenter(geometry.center())
        window.move(frame_geom.topLeft())
    
    elif position == "top_left":
        window.move(geometry.left(), geometry.top())
    
    elif position == "top_right":
        x = geometry.right() - (width or window.width())
        window.move(x, geometry.top())
    
    elif position == "bottom_left":
        y = geometry.bottom() - (height or window.height())
        window.move(geometry.left(), y)
    
    elif position == "bottom_right":
        x = geometry.right() - (width or window.width())
        y = geometry.bottom() - (height or window.height())
        window.move(x, y)
    
    elif position == "custom":
        # Use custom coordinates, but ensure window stays within screen bounds
        x = custom_x
        y = custom_y
        
        # Clamp to screen bounds
        max_x = geometry.right() - (width or window.width())
        max_y = geometry.bottom() - (height or window.height())
        x = max(geometry.left(), min(x, max_x))
        y = max(geometry.top(), min(y, max_y))
        
        window.move(x, y)
    
    else:
        # Fallback to center
        frame_geom = window.frameGeometry()
        frame_geom.setWidth(width or frame_geom.width())
        frame_geom.setHeight(height or frame_geom.height())
        frame_geom.moveCenter(geometry.center())
        window.move(frame_geom.topLeft())