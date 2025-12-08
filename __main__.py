import Libraries.nsys as nsys
import json, hashlib, time, threading;
from permissions import PermissionSubsystem
from Drivers.surfaceDriverpygOnly import SurfaceDriver as sd
from Libraries.autofont import getfont as getfontmap
from Fonts.PY.mdi import getfont as geticons
import numpy as np
from Libraries.nsys import AppSession, windows
from Libraries.nsys import sysUI
from Libraries.nsys import id
from Drivers.surfaceDriverpygOnly import overlayfb
systemVersion = "0.0.1"
nsys.log(f"NovaOS {systemVersion} booting on " + nsys.getsysinfo())
nsys.sysState.set(nsys.sysState.Booting)
nsys.log("state set to Booting")
nsys.log("Loading permissions subsystem")
permissions = PermissionSubsystem()
nsys.log("Permissions subsystem loaded")
CHARACTER_MAP = getfontmap()
nsys.log("Loaded system font")
icons = geticons()
nsys.log("Loaded Icon Font")

cursorchar = [
    "01111000000000000000",
    "10001100000000000000",
    "10100110000000000000",
    "10110011000000000000",
    "10111001100000000000",
    "10111100110000000000",
    "10111110011000000000",
    "10111111001100000000",
    "10111111100110000000",
    "10111111110011000000",
    "10111111111001100000",
    "10111111111100110000",
    "10111111111110011000",
    "10111111111111001100",
    "10111111111111100110",
    "10111111111111110010",
    "10111111111111111010",
    "10111111111111110010",
    "10111111111100000110",
    "10111111111100111100",
    "10111110011110110000",
    "10111000011110010000",
    "10010011001111010000",
    "11000111101111010000",
    "01111100100110010000",
    "00000000110000110000",
    "00000000011111100000",
]
cursorchar = np.array([[c == '1' for c in line] for line in cursorchar], dtype=bool)

winthread = []
mouse_was_pressed = False
mouse_pressed = (False, False, False)
cDragWin = None
dragging = False
hasStartedId = False
drag_offset = (0, 0)
dragged_element_index = None
def overlay_image(base, overlay, pos_x, pos_y):
    overlay_np = np.array(overlay)
    try:
        if overlay_np.ndim == 3 and overlay_np.shape[2] == 3:
            mask = np.any(overlay_np != 0, axis=-1)
        else:
            raise ValueError
    except Exception:
        try:
            overlay_arr = np.array(overlay, dtype=np.uint8)
            if overlay_arr.ndim == 3 and overlay_arr.shape[2] == 3:
                overlay_np = overlay_arr
                mask = np.any(overlay_np != 0, axis=-1)
            else:
                # Unexpected shape: no-op
                return base
        except Exception:
            # If conversion fails, give up gracefully
            return base

    # Get the dimensions of the base and overlay images
    base_height, base_width, _ = base.shape
    overlay_height, overlay_width, _ = overlay_np.shape

    # Calculate ROI in the base image
    y_start = max(0, pos_y)
    y_end = min(base_height, pos_y + overlay_height)
    x_start = max(0, pos_x)
    x_end = min(base_width, pos_x + overlay_width)

    # Corresponding region in the overlay
    overlay_y_start = max(0, -pos_y)
    overlay_y_end = overlay_y_start + (y_end - y_start)
    overlay_x_start = max(0, -pos_x)
    overlay_x_end = overlay_x_start + (x_end - x_start)

    # Extract ROIs
    base_roi = base[y_start:y_end, x_start:x_end]
    overlay_roi = overlay_np[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]
    mask_roi = mask[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]

    # Apply mask: copy overlay pixels where mask is True
    base_roi[mask_roi] = overlay_roi[mask_roi]

    # Write back the modified ROI into the base and return
    base[y_start:y_end, x_start:x_end] = base_roi
    return base

focus = (None, "Unset")

def getTopWinForPos(x, y):
    canidates = []
    sysUICanidates = []
    for win in windows:
        wx = parseSmartVar(win["pos"][0])
        wy = parseSmartVar(win["pos"][1])
        ww = parseSmartVar(win["geo"][0])
        wh = parseSmartVar(win["geo"][1])
        if wx <= x <= wx + ww:
            if wy <= y <= wy + wh:
                canidates.append(win)
    for win in sysUI:
        sys_x = parseSmartVar(win["pos"][0])
        sys_y = parseSmartVar(win["pos"][1])
        sys_w = parseSmartVar(win["geo"][0])
        sys_h = parseSmartVar(win["geo"][1])
        if sys_x <= x <= sys_x + sys_w:
            if sys_y <= y <= sys_y + sys_h:
                sysUICanidates.append(win)
    if len(canidates) > 0:
        if len(sysUICanidates) > 0:
            return sysUICanidates[len(sysUICanidates)-1], "sysui"
        else:
            return canidates[len(canidates)-1], "window"
    else: 
        if len(sysUICanidates) > 0:
            return sysUICanidates[len(sysUICanidates)-1], "sysui"
        else:
            return None, None

def handleInputs(event):
    hasReturned = False
    if len(windows) == 0:
        if len(sysUI) == 0:
            return
    if (len(windows) > 0 and ("focus" in  windows[-1] and ((event.type == id.events.KEYDOWN and windows[-1]["focus"] is not None) and windows[-1]["components"][windows[-1]["focus"]]["type"] == "input"))) or (len(sysUI) > 0 and "focus" in  sysUI[-1] and ((event.type == id.events.KEYDOWN and sysUI[-1]["focus"] is not None) and sysUI[-1]["components"][sysUI[-1]["focus"]]["type"] == "input")):
        input = windows[-1]["components"][windows[-1]["focus"]]
        fwin = windows[-1]
        if input is None or ("type" in input and input["type"] != "input"):
            input = sysUI[-1]["components"][sysUI[-1]["focus"]]
            fwin = sysUI[-1]
        if event.key == id.keys.BACKSPACE:
            if "value" in input:
                if "cursor" in input:
                    pos = input["cursor"]
                    if pos >= len(input["value"]):
                        pos = len(input["value"]) -1
                    if pos < 0:
                        pos = 1
                    if pos < len(input["value"]): 
                        strarray = list(input["value"])
                        strarray.__delitem__(pos)
                        input["value"] = ''.join(strarray)
                        input["cursor"] -=1;
                else:
                    input["value"] = input["value"][:-1]
        elif event.key == id.keys.DELETE:
            if "value" in input:
                if "cursor" in input:
                    pos = input["cursor"]+1
                    if pos < len(input["value"]):
                        strarray = list(input["value"])
                        strarray.__delitem__(pos)
                        input["value"] = ''.join(strarray)
        elif event.key == id.keys.RETURN:
            if "on_return" in input:
                input["on_return"](input["value"], windows[-1], windows[-1]["components"].index(input))
            hasReturned = True
        elif event.key == id.keys.LEFT:
            if "cursor" in input and (input["cursor"] > -1):
                input["cursor"] -=1;
        elif event.key == id.keys.RIGHT:
            if "cursor" in input and (input["cursor"] < len(input["value"])-1):
                input["cursor"] +=1;
        else:
            if "value" in input:
                if "cursor" in input:
                    pos = input["cursor"]+1
                    strarray = list(input["value"])
                    strarray.insert(pos, event.unicode)
                    input["value"] = ''.join(strarray)
                    input["cursor"] +=1;
                else:
                    input["value"] += event.unicode
            else:
                input["value"] = event.unicode
        # Pass the window along with the value to the on_change handler
        if "on_change" in input and not hasReturned:
                input["on_change"](input["value"], fwin, fwin["components"].index(input))
        fwin["cbak"] = None
        fwin["fbak"] = None


# Ensure no duplicate enumeration of applications
registered_apps = permissions.list_applications()
if len(registered_apps) == 0:
    for af in nsys.listapplications():
        if not af.startswith("__"):
            try:
                with open(f"applications/{af}/meta.json") as f:
                    data = json.load(f)
                    permissions.add_application(af, data["name"], data["description"], data["version"], data["developer"], data["developer_website"], data["developer_email"])
            except Exception as e:
                nsys.log(f"Error reading meta.json in {af}: {e}")
                continue

nsys.log("Permissions subsystem initialized")   
def picker(applications):
    try:
        aid = int(input("Choose app to execute (number): "))
        return aid        
    except:
        nsys.log('Please enter a number')
        return picker(applications)
global applications;
applications = [];
systemSession = nsys.Session();

def launcher(session, args):
    global surface
    shouldExitOnClose = True

    # do not run if already running
    if "Launcher" in [w["title"] for w in windows]:
        nsys.log("Launcher already running, not starting again.")
        return "Launcher already running"
    windows.append({"title":"Launcher", "pos": (0, surface.height - 530), "geo": (300,500), "colour":(220,220,220), "components":[], "drawAlways":False, "clearFrames": False, "waitFirstDraw": True})
    launcherWin = windows[-1]
    # detect click outside launcher and close it
    def onCloseLauncher():
        nsys.log("Closing launcher")
        if launcherWin in windows:
            windows.remove(launcherWin)
        return "Launcher closed"
    # Create the launcher window
    # Hook the mousedown event to check if the click is outside the launcher window
    def onMouseDown(event):
        mp = id.get_mouse_position()
        if launcherWin in windows and not (launcherWin["pos"][0] <= mp[0] <= launcherWin["pos"][0] + launcherWin["geo"][0] and launcherWin["pos"][1] <= mp[1] <= launcherWin["pos"][1] + launcherWin["geo"][1]):
            nsys.log(f"Mouse down outside launcher at {mp}, closing launcher",2)
            onCloseLauncher()
    id.hook_event(id.events.MOUSEBUTTONDOWN, onMouseDown)
    # Main apps frame
    launcherWin["components"].append({"type":"text", "text": "Apps"})
    registered_apps = permissions.list_applications()
    for app in registered_apps:
        app_id = app['id']
        app_name = app['name']

        
        def launch_app(app_id=app_id):
            app_ses = nsys.AppSession(app_id, session)
            onCloseLauncher()
            app_ses.exec()

        # Create button based on app type
        launcherWin['components'].append({"type": "button", "text":app_name, "on_click": launch_app, "border":(0,0,0), "bg":(250,250,250),"colour":(0,0,0)})

    # tkinter.ttk.Button(root, text="Reauthenticate Session", command=systemSession.showAuthPopup).pack()
    arg = args.split(", ")
    if(arg[0] == "test"):
        app_id = arg[1]
        # Launch basic apps normally
        app_ses = nsys.AppSession(app_id, session)
        app_ses.exec()
    launcherWin["indexbak"] = "balls"
    return "Done"
    # root.mainloop()



def parseSmartVar(v):
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        if v.lower().strip() == "sw":
            v = surface.width
        elif v.lower().strip() == "sh":
            v = surface.height 
    elif isinstance(v, dict):
        op = v["op"]
        l = parseSmartVar(v["left"])    
        r = parseSmartVar(v["right"])

        match op:
            case "+":
                v =  l + r
            case "-":
                v =  l - r
            case "*":
                v = l * r
            case "/":
                v = l / r
            case __:
                raise ValueError("Unknown expr: "+ str(l) + " " + str(op) + " " + str(r))
    return int(v)


def drawAppWin(elem):
    # check if element has a frameCount
    if "frameCount" not in elem:
        elem["frameCount"] = 0
    # if we have onFrameStart, call it
    if "onFrameStart" in elem:
        elem["onFrameStart"](elem["frameCount"])
    colour = elem["colour"]
    wo, ho = elem["geo"]
    xo, yo = elem["pos"]
    w = parseSmartVar(wo)
    h = parseSmartVar(ho)
    x = parseSmartVar(xo)
    y = parseSmartVar(yo)
    if("clearFrames" in elem and elem["clearFrames"]):
        elem["fbuf"][0:h, 0:w] = colour
    type = "window"
    if elem in sysUI:
        type = "sysui"

    if "components" in elem:
        for comp in elem["components"]:
            comp_xo = x if "pos" in comp else 0
            comp_yo = y if "pos" in comp else 0
            comp_w = None
            comp_h = None
            if "geo" in comp:
                comp_w = w
                comp_h = h
            if "fixed" in elem and elem["fixed"]:
                comp_x = comp_xo
                comp_y = comp_yo
            else:
                comp_x = 5 + comp_xo
                comp_y =  30 + comp_yo
            i = None
            compi = None
            if type == "window":
                if elem not in windows:
                    windows.append(elem)
                i = windows.index(elem)
                compi = windows[i]["components"].index(comp)
                if (compi > 0 and "bbox" in windows[i]["components"][compi-1]) and "pos" not in comp:
                    prev_bbox = windows[i]["components"][compi-1]["bbox"]
                    comp_y = prev_bbox[1] + prev_bbox[3] + 5
            elif type == "sysui":
                i = sysUI.index(elem)
                compi = sysUI[i]["components"].index(comp)
                if (compi > 0 and "bbox" in sysUI[i]["components"][compi-1]) and "pos" not in comp:
                    prev_bbox = sysUI[i]["components"][compi-1]["bbox"]
                    comp_y = prev_bbox[1] + prev_bbox[3] + 5
            # use the previous component's bbox if it exists
            if "colour" not in comp:
                comp["colour"] = (0,0,0)
            if(comp["type"] == "text"):
                if "pixel_multiplier" not in comp:
                    comp["pixel_multiplier"] = 1
                comp_w = min(comp_w, w-25) if comp_w is not None else w-25
                comp_h = min(comp_h, h-25) if comp_h is not None else h-25
                t= surface.draw_text(elem["fbuf"], comp["text"], comp_x, comp_y, width=comp_w+comp_xo+20, height=comp_h, colour=comp["colour"], pixel_multiplier=comp["pixel_multiplier"])
                comp["bbox"] = (comp_x, comp_y, t[1], t[0])  # Store the bounding box of the text
            elif(comp["type"] == "button"):
                # use the previous components bbox for positioning offset if it exists, and if this element did not specify a position, so we can autmolatically position elements vertically, downwards
                print(w)
                t = surface.draw_text(elem["fbuf"], comp["text"], comp_x+5,comp_y,width=w)
                if "geo" in comp:
                    cw = w
                    ch = h
                else:
                    cw = t[1]+ 10
                    ch = t[0]+ 10
                                # Top Border
                ch += 10
                ch -=  (len(comp["text"].split(" ")) - 1)
                cb=comp["border"]
                #border
                elem["fbuf"][comp_y-2:comp_y+ch+2, comp_x-2:comp_x+cw+2] = cb
                #bg
                elem["fbuf"][comp_y:comp_y+ch, comp_x:comp_x+cw] = comp["bg"]
                t = surface.draw_text(elem["fbuf"], comp["text"], comp_x+5,comp_y +5, colour=comp["colour"])
                comp["bbox"] = (comp_x, comp_y, cw, ch)
            elif(comp["type"] == "input"):
                t = surface.draw_text(elem["fbuf"], comp["value"], comp_x+5,comp_y)
                crs = len(comp["value"]) - 1
                if "cursor" in comp:
                    crs = comp["cursor"]
                else:
                    comp["cursor"] = crs
                if "geo" in comp:
                    cw = comp["geo"][0]
                    ch = comp["geo"][1]
                else:
                    cw = t[1]+ 10
                    ch = t[0]+ 10
                cb = comp["border"] if "border" in comp else (0, 0, 0)
                if "focus" in elem:
                    if elem["focus"] == compi:
                        cb = (255, 255, 0)
                    else:
                        crs = None # if not focused, cursor is not shown
                #border
                cw -= 10
                surface.draw_border(elem["fbuf"],comp_x-2, comp_y-2, cw+4, ch+4, cb, 2)
                #bg
                surface.draw_rect(elem["fbuf"],comp_x, comp_y, cw, ch, comp["bg"])
                colour = comp["colour"] if "colour" in comp else (0, 0, 0)
                t = surface.draw_text(elem["fbuf"], comp["value"], comp_x+5,comp_y, curpos=crs, colour=colour)
                comp["bbox"] = (comp_x, comp_y, cw, ch)
                if "on_change" in comp:
                    if hasattr(comp, "input_text"):
                        if comp["input_text"] != comp["value"]:
                            comp["on_change"](comp["value"])
                            comp["input_text"] = comp["value"]
                    else:
                        comp["input_text"] = comp["value"]
                # if the input text is not set, set it to the value
            elif(comp["type"] == "image"):
                if "image" in comp:
                    img = comp["image"]
                    if isinstance(img, str):
                        img = read_bmp_rgb_array(img, target_height=comp_h, target_width=comp_w)
                    if img is not None:
                        # Ensure the image fits within the component's geometry
                        img_h, img_w = len(img), len(img[0])
                        overlay_image(elem["fbuf"], img, comp_x, comp_y)
                        comp["bbox"] = (comp_x, comp_y, img_w, img_h)  
    elem["renderthread"] = None
    elem["cbak"] = elem["components"]
    if "focus" in elem:
        elem["fbak"] = elem["focus"]
    else:
        elem["fbak"] = None
    elem["frameCount"] += 1
    return "Done"

def handleMouseInput(e):
    global windows, dragging, drag_offset, dragged_element_index, mouse_was_pressed, mouse_pressed, cDragWin, id, hasStartedId, focus, fbw, fbh
    height = fbh
    width =fbw
    mouse_buttons = id.get_mouse_buttons()
    mouse_x, mouse_y = id.get_mouse_position()
    if mouse_buttons[0]:
        if not dragging:
            for i, elem in enumerate(windows + sysUI):
                gtwfp, wt = getTopWinForPos(mouse_x, mouse_y)
                if gtwfp != None:
                    elem = gtwfp
                    if wt == "window":
                        i = windows.index(gtwfp)
                    elif wt == "sysui":
                        i = sysUI.index(gtwfp)
                else: 
                    break
                wo, ho = elem["geo"]
                xo, yo = elem["pos"]
                w = parseSmartVar(wo)
                h = parseSmartVar(ho)
                x = parseSmartVar(xo)
                y = parseSmartVar(yo)
                if x <= mouse_x <= x + w and y <= mouse_y <= y + h:
                    if wt == "window":
                        windows.append(windows.pop(windows.index(gtwfp)))
                        focus = (windows[-1], "window") 
                    elif wt == "sysui":
                        sysUI.append(sysUI.pop(sysUI.index(gtwfp)))
                        focus = (sysUI[-1], "sysui")
                if x <= mouse_x <= x + w and y <= mouse_y <= y + h:
                    mouse_pressed = id.get_mouse_buttons()
                    # Check if the left mouse button is pressed
                    if mouse_pressed[0]:  # Index 0 corresponds to the left mouse button
                        if not mouse_was_pressed:
                            # This block runs only when the button is pressed for the first time
                            is_within_close_x = (x+w)-23 <= mouse_x < (x+w)-3
                            is_within_close_y = y+3 <= mouse_y < y+19

                            if is_within_close_x & is_within_close_y:
                                if gtwfp != None and wt == "window":
                                    windows.remove(gtwfp)
                                    if "onCloseFunc" in gtwfp:
                                        gtwfp["onCloseFunc"]()
                            else:
                                # we didnt click close, so we probably clicked an element in the window
                                button_clicked = False
                                if "components" in elem:
                                    for comp in elem["components"]:
                                        if "bbox" in comp:
                                            comp_x = comp["bbox"][0] + x
                                            comp_y = comp["bbox"][1] + y
                                            cw = comp["bbox"][2]
                                            ch = comp["bbox"][3]
                                        else:
                                            comp_x = x
                                            comp_y = y
                                            cw = 0
                                            ch = 0
                                        if comp_x <= mouse_x <= comp_x + cw and comp_y <= mouse_y <= comp_y + ch:
                                            elem["focus"] = elem["components"].index(comp) if "components" in elem else None
                                            if(comp["type"] == "button"):
                                                # Handle button click here
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                button_clicked = True
                                                break
                                            elif(comp["type"] == "input"):
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                break
                                        else:
                                            elem["focus"] = None
                                # Only start dragging if not clicking a button and we are within the top 25px of the window
                                if not button_clicked and y <= mouse_y <= y + 25:
                                    dragging = True
                                    dragged_element_index = i
                                    drag_offset = (mouse_x - x, mouse_y - y)
                                    # clear opos of window if exists
                                    if "opos" in elem:
                                        windows[windows.index(elem)]["opos"] = None                                                

                        # Update the flag to indicate the button is now pressed
                        mouse_was_pressed = True
                else: 
                    if 'opos' in elem:
                        windows[windows.index(elem)]["opos"] = None
                    dragging = True
                    dragged_element_index = i
                    drag_offset = (mouse_x - x, mouse_y - y)
                break
        else:
            gw, wt = focus
            if gw != None or cDragWin != None and wt == "window":
                if cDragWin == None:
                    cDragWin = gw
                dx, dy = drag_offset
                new_x = max(0, min(mouse_x - dx, width - cDragWin["geo"][0]))
                new_y = max(0, min(mouse_y - dy, height - cDragWin["geo"][1]))
                cDragWin["geo"] = (
                    cDragWin["geo"][0],
                    cDragWin["geo"][1]
                )
                cDragWin["pos"] = (new_x, new_y)
    else:
        dragging = False
        dragged_element_index = None
        mouse_was_pressed = False
        cDragWin = None    # Draw windows using correct NumPy indexing [y, x]
    

fbw = None
fbh = None
fbc = None
fbuf = None


def renderFunction(framebuf, frame, width, height, eventgetter=None):
    global fbc, fbuf, windows, dragging, drag_offset, dragged_element_index, mouse_was_pressed, mouse_pressed, cDragWin, id, hasStartedId, focus, fbw, fbh, overlayfb, dmRunning
    fbw = width
    fbh = height
    nsys.fbgeo = [width, height]
    fbc = frame
    fbuf = framebuf
    id.poll(eventgetter)
    
    surface.fill_screen((113, 135, 199))
    mouse_x, mouse_y = id.get_mouse_position()
    if dmRunning == False:
        threading.Thread(target=drawMouse, daemon=True).start()
    
    # Cache parsed values once
    parsed_elems = []
    for elem in windows + sysUI:
        w = parseSmartVar(elem["geo"][0])
        h = parseSmartVar(elem["geo"][1])
        x = parseSmartVar(elem["pos"][0])
        y = parseSmartVar(elem["pos"][1])
        parsed_elems.append((elem, x, y, w, h))
    
    # Single pass through all elements
    for elem, x, y, w, h in parsed_elems:
        elem_type = "sysui" if elem in sysUI else "window"
        
        # Skip if not authenticated
        if nsys.sysState.get() == nsys.sysState.awaitLogin:
            if elem.get("showOnlyLoggedIn", False):
                continue
        
        # Create/update framebuffer once
        if "fbuf" not in elem or elem["fbuf"].shape != (h, w, 3):
            elem["fbuf"] = np.zeros((h, w, 3), dtype=np.uint8)
            elem["fbuf"][:] = elem["colour"]
            elem["cbak"] = None
        
        # Draw if needed
        if (not elem.get("cbak") or elem["cbak"] != elem.get("components") or 
            elem.get("drawAlways")):
            drawAppWin(elem)
        
        # Blit to screen
        if elem_type == "window":
            framebuf[y:y+h, x:x+w] = elem["fbuf"][:h, :w]
        else:
            framebuf[y:y+h, x:x+w] = elem["fbuf"][:h, :w]
        title = "Unknown Window"
        title_x = x + 5
        title_y = y + 5
        if "title" in elem:
            title = elem["title"]

        if "fixed" not in elem or not elem["fixed"]:
            framebuf[y:y+25, x:x+w] = (255, 255, 255)
            surface.draw_text(framebuf, title, title_x, title_y-5, (0, 0, 0), pixel_multiplier=2, width=w-30, height=25)
            framebuf[y:y+h, x:x+3] = (255, 255, 255)             # Left
            framebuf[y:y+h, x+w-3:x+w] = (255, 255, 255)         # Right
            framebuf[y+h-3:y+h, x:x+w] = (255, 255, 255)         # Bottom
            close_button_x = (x+w)-23
            close_button_y = y+3
            close_button_w = 20
            close_button_h = 19
            if (close_button_x <= mouse_x <= close_button_x + close_button_w and 
                close_button_y <= mouse_y <= close_button_y + close_button_h):
                framebuf[y+3:y+22,(x+w)-23:(x+w)-3] = (255,100,100)  # Brighter red when hovering
            else:
                framebuf[y+3:y+22,(x+w)-23:(x+w)-3] = (255,0,0)      # Normal red
            surface.draw_fchar(framebuf, icons["close"], (x+w)-23, y+7, (0,0,0), pixel_multiplier=1)    # Cursor (white square)

dmRunning = False
def drawMouse():
    global id, fbw, fbh, dmRunning, fbuf
    dmRunning = True
    width = fbw
    height = fbh
    size = 20
    while True:
        mouse_x, mouse_y = id.get_mouse_position()
        cx = max(0, min(mouse_x, fbuf.shape[1] - size))  # Width is for x-coordinate bounds
        cy = max(0, min(mouse_y, fbuf.shape[0] - size)) # Height is for y-coordinate bounds
        surface.draw_fchar(fbuf, cursorchar, cx, cy, (0,0,0), pixel_multiplier=1)

surface = sd.Bitmap(1366, 768, "", callback=renderFunction, font=CHARACTER_MAP)
id.hook_event(id.events.KEYDOWN, handleInputs)
def loopIS():
    while True:
        handleMouseInput(None)

threading.Thread(target=loopIS, daemon=True).start()
from sysApps import taskbar
def authloop():
    try:
        nsys.sysState.set(nsys.sysState.awaitLogin)
        try:
            # systemSession.Authenticate("system", passhash=hashlib.md5(b"password").hexdigest(), sessionType=3)
            # time.sleep(1)
            def onAuthenticate(x):
                nsys.log("Authentication successful")
                nsys.sysState.set(nsys.sysState.sysAuthenticated)
                # Start the launcher
                launcher(systemSession, "")
                taskbar.showTaskbar(systemSession)
            systemSession.showAuthPopup(callback=onAuthenticate, appfolder="")
            
        except Exception as e:
            nsys.log(e.args)
            # authloop()
    except(KeyboardInterrupt):
        nsys.log()
        nsys.log("Exiting.")
# check for arguments
# nsys.args = ["b","test","online.sometgirl.readmereader"]

if len(nsys.args) > 1:
    if nsys.args[1] == "test":
        nsys.log("Starting test mode. Module: " + nsys.args[2])
        
        # Set the system state to Test Mode (6)
        nsys.sysState.set(nsys.sysState.testMode)
        # Log in automatically as "test" user, password "test", session type 3
        systemSession.Authenticate("test", passhash=hashlib.md5(b"test").hexdigest(), sessionType=3)
        taskbar.showTaskbar(systemSession)
        time.sleep(1)
        testAppSession = AppSession(nsys.args[2],systemSession)
        testAppSession.exec("test")
    else:
        authloop()
else:
    authloop()
try:
    surface.run()
except KeyboardInterrupt:
    exit()