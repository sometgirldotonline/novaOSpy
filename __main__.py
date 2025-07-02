import Libraries.nsys as nsys
import json, hashlib, time, threading;
from permissions import PermissionSubsystem
from Drivers.surfaceDriverSdlPyg import SurfaceDriver as sd
from Fonts.PY.vt323 import charmap as CHARACTER_MAP
from Fonts.PY.mdi import charmap as icons
import numpy as np
from Libraries.nsys import AppSession, windows
from Libraries.nsys import sysUI
from Libraries.nsys import id
from Drivers.surfaceDriverSdlPyg import overlayfb
systemVersion = "0.0.1"
nsys.log(f"NovaOS {systemVersion} booting on " + nsys.getsysinfo())
nsys.sysState.set(nsys.sysState.Booting)
nsys.log("state set to Booting")
nsys.log("Loading permissions subsystem")
permissions = PermissionSubsystem()
nsys.log("Permissions subsystem loaded")
winthread = []
mouse_was_pressed = False
mouse_pressed = (False, False, False)
cDragWin = None
dragging = False
hasStartedId = False
drag_offset = (0, 0)
dragged_element_index = None
def overlay_image(base, overlay, pos_x, pos_y):
    # Convert the overlay to a NumPy array if it's not already
    overlay_np = np.array(overlay, dtype=object)

    # Create a mask to identify valid pixels (tuples that are not (0, 0, 0))
    valid_mask = np.vectorize(lambda pixel: isinstance(pixel, tuple) and pixel != (0, 0, 0))(overlay_np)

    # Get the dimensions of the base and overlay images
    base_height, base_width, _ = base.shape
    overlay_height, overlay_width,_ = overlay_np.shape

    # Calculate the region of interest (ROI) in the base image
    y_start = max(0, pos_y)
    y_end = min(base_height, pos_y + overlay_height)
    x_start = max(0, pos_x)
    x_end = min(base_width, pos_x + overlay_width)

    # Calculate the corresponding region in the overlay
    overlay_y_start = max(0, -pos_y)
    overlay_y_end = overlay_y_start + (y_end - y_start)
    overlay_x_start = max(0, -pos_x)
    overlay_x_end = overlay_x_start + (x_end - x_start)

    # Extract the regions of interest
    base_roi = base[y_start:y_end, x_start:x_end]
    overlay_roi = overlay_np[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]
    valid_mask_roi = valid_mask[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]

    # Apply the valid mask to copy only valid pixels from the overlay to the base
    base_roi[valid_mask_roi] = overlay_roi[valid_mask_roi]
    return base_roi

focus = (None, "Unset")

def getTopWinForPos(x, y):
    canidates = []
    sysUICanidates = []
    for win in windows:
        wx = int(eval(str(win["pos"][0])))
        wy = int(eval(str(win["pos"][1])))
        ww = int(eval(str(win["geo"][0])))
        wh = int(eval(str(win["geo"][1])))
        if wx <= x <= wx + ww:
            if wy <= y <= wy + wh:
                canidates.append(win)
    for win in sysUI:
        sys_x = int(eval(str(win["pos"][0])))
        sys_y = int(eval(str(win["pos"][1])))
        sys_w = int(eval(str(win["geo"][0])))
        sys_h = int(eval(str(win["geo"][1])))
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
                    # print(pos, input["value"], len(input["value"]))
                    if pos < len(input["value"]):
                        strarray = list(input["value"])
                        strarray.__delitem__(pos)
                        input["value"] = ''.join(strarray)
        elif event.key == id.keys.RETURN:
            #print(f"Return pressed, value: {input['value']}")
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
            #print(f"Key pressed: {event.key}, unicode: {event.unicode}")
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
        # print(af)
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
        # print(focus)
        mp = id.get_mouse_position()
        if launcherWin in windows and not (launcherWin["pos"][0] <= mp[0] <= launcherWin["pos"][0] + launcherWin["geo"][0] and launcherWin["pos"][1] <= mp[1] <= launcherWin["pos"][1] + launcherWin["geo"][1]):
            print(f"Mouse down outside launcher at {mp}, closing launcher")
            onCloseLauncher()
    id.hook_event(id.events.MOUSEBUTTONDOWN, onMouseDown)
    # Main apps frame
    launcherWin["components"].append({"type":"text", "text": "Apps"})
    registered_apps = permissions.list_applications()
    for app in registered_apps:
        # print(app)
        app_id = app['id']
        app_name = app['name']
        # print(f'{app_id}: {app_name}')

        
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





def drawAppWin(elem):
    # check if element has a frameCount
    if "frameCount" not in elem:
        elem["frameCount"] = 0
    # if we have onFrameStart, call it
    if "onFrameStart" in elem:
        elem["onFrameStart"](elem["frameCount"])
    colour = elem["colour"]
    w, h = elem["geo"]
    w = int(eval(str(w)))
    h = int(eval(str(h)))
    # elem["fbuf"] = np.zeros((elem['geo'][1], elem["geo"][0], 3), dtype=np.uint8)
    if("clearFrames" in elem and elem["clearFrames"]):
        elem["fbuf"][0:h, 0:w] = colour
    type = "window"
    if elem in sysUI:
        type = "sysui"
    x, y = elem["pos"]
    x = int(eval(str(x)))
    y = int(eval(str(y)))
    if "components" in elem:
        for comp in elem["components"]:
            comp_xo = int(eval(str(comp["pos"][0]))) if "pos" in comp else 0
            comp_yo = int(eval(str(comp["pos"][1]))) if "pos" in comp else 0
            comp_w = None
            comp_h = None
            if "geo" in comp:
                comp_w = int(eval(str(comp["geo"][0])))
                comp_h = int(eval(str(comp["geo"][1])))
            if "fixed" in elem and elem["fixed"]:
                comp_x = int(eval(str(comp_xo)))
                comp_y = int(eval(str(comp_yo)))
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
                if not hasattr(comp, "pixel_multiplier"):
                    comp["pixel_multiplier"] = 1
                comp_w = min(comp_w, w-25) if comp_w is not None else w-25
                comp_h = min(comp_h, h-25) if comp_h is not None else h-25
                t= surface.draw_text(elem["fbuf"], comp["text"], comp_x, comp_y-5, width=comp_w+comp_xo+20, height=comp_h, colour=comp["colour"], pixel_multiplier=comp["pixel_multiplier"])
                comp["bbox"] = (comp_x, comp_y, t[1], t[0])  # Store the bounding box of the text
            elif(comp["type"] == "button"):
                # use the previous components bbox for positioning offset if it exists, and if this element did not specify a position, so we can autmolatically position elements vertically, downwards

                t = surface.draw_text(elem["fbuf"], comp["text"], comp_x+5,comp_y)
                if "geo" in comp:
                    cw = int(eval(str(comp["geo"][0])))
                    ch = int(eval(str(comp["geo"][1])))
                else:
                    cw = t[1]+ 10
                    ch = t[0]+ 10
                                # Top Border
                cb=comp["border"]
                elem["fbuf"][comp_y:comp_y+ch, comp_x:comp_x+cw] = comp["bg"]
                elem["fbuf"][comp_y-2:comp_y, comp_x-2:comp_x+cw+2] = cb
                # bottom border
                elem["fbuf"][comp_y+ch:comp_y+ch+2, comp_x-2:comp_x+cw+2] = cb
                # Left Border
                elem["fbuf"][comp_y:comp_y+ch, comp_x-2:comp_x] = cb
                # Right Border
                elem["fbuf"][comp_y:comp_y+ch, comp_x+cw:comp_x+cw+2] = cb
                t = surface.draw_text(elem["fbuf"], comp["text"], comp_x+5,comp_y, colour=comp["colour"])
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
                # Top Border
                elem["fbuf"][comp_y-2:comp_y, comp_x-2:comp_x+cw+2] = cb
                # bottom border
                elem["fbuf"][comp_y+ch:comp_y+ch+2, comp_x-2:comp_x+cw+2] = cb
                # Left Border
                elem["fbuf"][comp_y:comp_y+ch, comp_x-2:comp_x+2] = cb
                # Right Border
                elem["fbuf"][comp_y:comp_y+ch, comp_x+cw:comp_x+cw+2] = cb
                # 
                elem["fbuf"][comp_y:comp_y+ch, comp_x:comp_x+cw] = comp["bg"]
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
                w, h = elem["geo"]
                w = int(eval(str(w)))
                h = int(eval(str(h)))
                x, y = elem["pos"]
                x = int(eval(str(x)))
                y = int(eval(str(y)))
                if x <= mouse_x <= x + w and y <= mouse_y <= y + h:
                    if wt == "window":
                        windows.append(windows.pop(windows.index(gtwfp)))
                        focus = (windows[-1], "window") 
                    elif wt == "sysui":
                        sysUI.append(sysUI.pop(sysUI.index(gtwfp)))
                        focus = (sysUI[-1], "sysui")
                if x <= mouse_x <= x + w and y <= mouse_y <= y + h:
                    # print(f"mouse_pressed: {mouse_pressed}, mouse_was_pressed: {mouse_was_pressed}")
                    mouse_pressed = id.get_mouse_buttons()
                    # Check if the left mouse button is pressed
                    if mouse_pressed[0]:  # Index 0 corresponds to the left mouse button
                        if not mouse_was_pressed:
                            # This block runs only when the button is pressed for the first time
                            #print("Mouse clicked!")
                            is_within_close_x = (x+w)-23 <= mouse_x < (x+w)-3
                            is_within_close_y = y+3 <= mouse_y < y+19

                            if is_within_close_x & is_within_close_y:
                                # print(f"mouse_pressed: {mouse_pressed}, mouse_was_pressed: {mouse_was_pressed}")
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
                                            comp_x = comp["bbox"][0] + int(eval(str(elem["pos"][0])))
                                            comp_y = comp["bbox"][1] + int(eval(str(elem["pos"][1])))
                                            cw = int(eval(str(comp["bbox"][2])))
                                            ch = int(eval(str(comp["bbox"][3])))
                                        else:
                                            # print(comp)
                                            comp_x = int(eval(str(elem["pos"][0])))
                                            comp_y = int(eval(str(elem["pos"][1])))
                                            cw = 0
                                            ch = 0
                                        if comp_x <= mouse_x <= comp_x + cw and comp_y <= mouse_y <= comp_y + ch:
                                            #print(f"Mouse clicked in a component")
                                            elem["focus"] = elem["components"].index(comp) if "components" in elem else None
                                            if(comp["type"] == "button"):
                                                #print(f"Button {comp['text']} clicked!")
                                                # Handle button click here
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                button_clicked = True
                                                break
                                            elif(comp["type"] == "input"):
                                                #print(f"Input clicked!")
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                break
                                        else:
                                            #print(f"Mouse clicked outside of components")
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
def frameDrawNew():
    global fbc, fbuf, fbw, fbh
    width = fbw 
    height = fbh
    frame = fbc
    framebuf = fbuf


def renderFunction(framebuf, frame, width, height, eventgetter=None):
    global fbc, fbuf, windows, dragging, drag_offset, dragged_element_index, mouse_was_pressed, mouse_pressed, cDragWin, id, hasStartedId, focus, fbw, fbh, overlayfb
    fbw = width
    fbh = height
    fbc = frame
    fbuf = framebuf
    id.poll(eventgetter)
    # rag(framebuf, frame, width, height)
    surface.fill_screen((138, 207, 0))

    mouse_x, mouse_y = id.get_mouse_position()


    wsysui = windows + sysUI
    for elem in wsysui:
        type = "window"
        if elem in sysUI:
            type = "sysui"
        # check if systems state is authenticated
        # print(nsys.sysState.get() == nsys.sysState.awaitLogin)
        if nsys.sysState.get() == nsys.sysState.awaitLogin:
            if "showOnlyLoggedIn" in elem and elem["showOnlyLoggedIn"]:
                break
        w, h = elem["geo"]
        w = int(eval(str(w)))
        h = int(eval(str(h)))
        x, y = elem["pos"]
        x = int(eval(str(x)))
        y = int(eval(str(y)))
        if "stamp" not in elem:
            elem["stamp"] = time.time()
        if type == "window":
            if x > surface.width or x < 0:
                windows[windows.index(elem)]["opos"] = elem["pos"]
                windows[windows.index(elem)]["pos"] = (0, y)
            if y > surface.height or y < 0:
                windows[windows.index(elem)]["opos"] = elem["pos"]
                windows[windows.index(elem)]["pos"] = (x, 0)
            if "opos" in elem and elem["opos"] is not None:
                opos_x, opos_y = elem["opos"]
                if 0 <= opos_x <= width - w and 0 <= opos_y <= height - h:
                    windows[windows.index(elem)]["pos"] = (opos_x, opos_y)
                    windows[windows.index(elem)]["opos"] = None   
        
        colour = elem["colour"]

        if type == "window":
            title = elem["title"]
            title_x = x + 5
            title_y = y + 5
        # if we dont have Fbuf or its bigger than our screen, create a new one or if our h/w is not the expected h/w 
        if "fbuf" not in elem or elem["fbuf"].shape[0] > surface.height or elem["fbuf"].shape[1] > surface.width or elem["fbuf"].shape[0] != h or elem["fbuf"].shape[1] != w:
            elem["fbuf"] = np.zeros((int(eval(str(elem['geo'][1]))), int(eval(str(elem["geo"][0]))), 3), dtype=np.uint8)
            elem["fbuf"][0:int(eval(str(h))), 0:int(eval(str(w)))] = colour
            elem["indexbak"] = None
        if "renderthread" not in elem or ("renderthread" in elem and elem["renderthread"] == None):
            if (("cbak" in elem and elem["cbak"] != elem ["components"]) or "cbak" not in elem) or (("fbak" in elem and "focus" in elem and elem["fbak"] != elem ["focus"]) or "fbak" not in elem) or (("indexbak" in elem and elem["indexbak"] != wsysui.index(elem)) or "indexbak" not in elem) or ("drawAlways" in elem and elem["drawAlways"]):
                elem["indexbak"] = wsysui.index(elem)
                elem["renderthread"] = threading.Thread(target=lambda: drawAppWin(elem), daemon=True)
                elem["renderthread"].start()
                if "firstFrameComplete" not in elem:
                    if "waitFirstDraw" in elem and elem["waitFirstDraw"]:
                        if elem["renderthread"] != None:
                            elem["renderthread"].join()
                        else:
                            elem["renderthread"] = threading.Thread(target=lambda: drawAppWin(elem), daemon=True)
                            elem["renderthread"].start()
                            if elem["renderthread"] != None:
                                elem["renderthread"].join()
                    elem["firstFrameComplete"] = True
                
        if "fixed" in elem and elem["fixed"]:
            framebuf[y:y+h, x:x+w] = elem["fbuf"]
        else:
            # framebuf[y:y+elem["fbuf"].shape[0], x:x+elem["fbuf"].shape[1]] = elem["fbuf"][:y+elem["fbuf"].shape[0], :x+elem["fbuf"].shape[1]]  # Draw the component buffer onto the main frame buffer
            # Sizes
            fh, fw = (height, width)  # framebuf height & width
            eh, ew = (int(eval(str(elem["fbuf"].shape[0]))), int(eval(str(elem["fbuf"].shape[1]))))  # element height & width

            # Compute the actual height and width we can draw without overflow
            h2 = min(eh, fh - y)
            # print(h2, eh, fh)
            w2 = min(ew, fw - x)
            # print(w2, ew, fw)

            # Clip only if within framebuf bounds
            if h2 > 0 and w2 > 0:
                framebuf[y:y+h2, x:x+w2] = elem["fbuf"][:h2, :w2]
        if "fixed" not in elem or not elem["fixed"]:
            framebuf[y:y+25, x:x+w] = (255, 255, 255)
            surface.draw_text(framebuf, title, title_x, title_y-5, (0, 0, 0), pixel_multiplier=1.2, width=w-30, height=25)
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
            surface.draw_fchar(framebuf, "close", (x+w)-23, y+7, (0,0,0), font=icons, pixel_multiplier=0.95)    # Cursor (white square)
    size = 20
    cx = max(0, min(mouse_x, width - size))  # Width is for x-coordinate bounds
    cy = max(0, min(mouse_y, height - size)) # Height is for y-coordinate bounds
    # for i in range (5):
    #     surface.draw_circle(framebuf, cx, cy, i*10,i*10)
    surface.draw_fchar(framebuf, "cursor", cx, cy, (0,0,0), pixel_multiplier=1, font=CHARACTER_MAP)


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
            systemSession.showAuthPopup(callback=onAuthenticate, appfolder="")
            print("salty")
            
        except Exception as e:
            nsys.log(e.args)
            # authloop()
    except(KeyboardInterrupt):
        nsys.log()
        nsys.log("Exiting.")
# check for arguments
#nsys.args = ["b","test","com.example.helloworld"]
print(nsys.args)

if len(nsys.args) > 1:
    if nsys.args[1] == "test":
        nsys.log("Starting test mode. Module: " + nsys.args[2])
        
        # Set the system state to Test Mode (6)
        nsys.sysState.set(nsys.sysState.testMode)
        # Log in automatically as "test" user, password "test", session type 3
        systemSession.Authenticate("test", passhash=hashlib.md5(b"test").hexdigest(), sessionType=3)
        print(systemSession)
        time.sleep(1)
        #systemSession.exec(print(), appfolder=nsys.args[2], arguments="test, "+nsys.args[2])
        testAppSession = AppSession(nsys.args[2],systemSession)
        testAppSession.exec("test")
    else:
        authloop()
else:
    authloop()
try:
    surface.run()
except KeyboardInterrupt:
    print("Stopping bitch!")
    exit()