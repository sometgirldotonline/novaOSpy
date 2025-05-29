from Libraries import nsys
from Libraries.nsys import sysUI
from Drivers.surfaceDriver import SurfaceDriver
from __main__ import launcher, systemSession, surface
print(surface.width, surface.height)  
sysUI.append({
    "title": "Taskbar",
    "pos": (0, "surface.height - 30"),
    "geo": ("surface.width", 30),
    "colour": (50, 50, 50),
    "fixed": True,  # This window will not be draggable and has no title or border
    "components": [
        {"type": "button", "text": "Start", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), 
         "on_click": lambda: launcher(systemSession, "")}
    ],
    "showOnlyLoggedIn": True,  # Only show this taskbar if the user is logged in
})
