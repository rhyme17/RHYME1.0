class ButtonStyleManager:
    BUTTON_ROLES = {
        "primary": {
            "background": "#2f7bff",
            "border_color": "#2f7bff",
            "color": "#ffffff",
            "font_weight": "700",
            "hover_background": "#2468dc",
        },
        "danger": {
            "background": "#ff5b69",
            "border_color": "#ff5b69",
            "color": "#ffffff",
            "font_weight": "700",
            "hover_background": "#ea4a58",
        },
        "secondary": {
            "background": "#ffffff",
            "border_color": "#b9d2ff",
            "color": "#24457d",
            "font_weight": "500",
            "hover_background": "#e9f2ff",
        },
    }

    def __init__(self):
        self._button_configs = {}

    def set_button_role(self, button, role):
        if button is None:
            return
        button.setProperty("btnRole", role)
        button.style().unpolish(button)
        button.style().polish(button)

    def apply_button_roles(self, button_role_mapping):
        for button, role in button_role_mapping.items():
            if button is not None:
                self.set_button_role(button, role)

    def apply_minimum_height(self, buttons, height=28):
        for button in buttons:
            if button is not None:
                button.setMinimumHeight(height)