from Libraries.nsys import sysUI
from __main__ import launcher, systemSession, surface
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
nsys = module_from_spec(spec := spec_from_file_location(
    "nsys", Path(__file__).parent.parent / "Libraries" / "nsys.py"
))
spec.loader.exec_module(nsys)

taskbarId = -1

    
def showTaskbar(session: nsys.Session):
    global taskbarId
    ccfg = session.get_config().get("colours").get("taskbar")
    if taskbarId != -1:
        sysUI.pop(taskbarId)
    taskbar = sysUI.append({
        "title": "Taskbar",
        "pos": (0, {"op": "-", "left":"sH", "right": 30}),
        "geo": ("sW", 30),
        "colour": ccfg.get("bg"),
        "fixed": True,  # This window will not be draggable and has no title or border
        "components": [
            {"type": "button", "text": "Start", "colour":  ccfg.get("label"), "bg": ccfg.get("buttons"), "border": ccfg.get("label"), 
            "on_click": lambda: launcher(systemSession, "")},
            {"type": "label", "text": "User", "colour":  systemSession.user},
        ],
        "showOnlyLoggedIn": True,  # Only show this taskbar if the user is logged in
    })
    taskbarId = len(sysUI) - 1