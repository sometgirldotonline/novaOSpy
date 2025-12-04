from Libraries.nsys import sysUI
from __main__ import launcher, systemSession, surface
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
nsys = module_from_spec(spec := spec_from_file_location(
    "nsys", Path(__file__).parent.parent / "Libraries" / "nsys.py"
))
spec.loader.exec_module(nsys)

print(surface.width, surface.height)  
taskbarId = -1

    
def showTaskbar(session: nsys.Session):
    global taskbarId
    if taskbarId != -1:
        sysUI.pop(taskbarId)
    taskbar = sysUI.append({
        "title": "Taskbar",
        "pos": (0, "surface.height - 30"),
        "geo": ("surface.width", 30),
        "colour": session.get,
        "fixed": True,  # This window will not be draggable and has no title or border
        "components": [
            {"type": "button", "text": "Start", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), 
            "on_click": lambda: launcher(systemSession, "")},
            {"type": "button", "text": "dEFENSETRATE TASKBARM", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), "pos": (200,0),
            "on_click": lambda: sysUI.pop(taskbarId)},
        ],
        "showOnlyLoggedIn": True,  # Only show this taskbar if the user is logged in
    })
    taskbarId = len(sysUI) - 1