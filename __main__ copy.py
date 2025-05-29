import Libraries.nsys as nsys, json, importlib.util, hashlib, tkinter, tkinter.ttk, time;
from permissions import PermissionSubsystem
from Drivers.surfaceDriver import SurfaceDriver as sd
from Fonts.PY.vt323 import charmap as CHARACTER_MAP
from Fonts.PY.mdi import charmap as icons
import numpy as np
from Libraries.nsys import windows
from Libraries.nsys import sysUI
from Libraries.nsys import id
systemVersion = "0.0.1"
nsys.log(f"NovaOS {systemVersion} booting on " + nsys.getsysinfo())
nsys.sysState.set(nsys.sysState.Booting)
nsys.log("state set to Booting")
nsys.log("Loading permissions subsystem")
permissions = PermissionSubsystem()
nsys.log("Permissions subsystem loaded")

mouse_was_pressed = False
mouse_pressed = (False, False, False)
cDragWin = None
dragging = False
hasStartedId = False
drag_offset = (0, 0)
dragged_element_index = None
def overlay_image(base, overlay, pos_x, pos_y):
    # Get the dimensions of the base and overlay images
    base_height = len(base)
    base_width = len(base[0])
    overlay_height = len(overlay)
    overlay_width = len(overlay[0])

    # Iterate over the overlay image
    for y in range(overlay_height):
        for x in range(overlay_width):
            # Calculate the position in the base image
            base_y = pos_y + y
            base_x = pos_x + x

            # Check if the position is within the bounds of the base image
            if 0 <= base_y < base_height and 0 <= base_x < base_width:
                # Copy the pixel from the overlay to the base
                base[base_y][base_x] = overlay[y][x]
previous_bmps = {}
def read_bmp_rgb_array(filename, target_width=None, target_height=None):
    cache_key = (filename, target_width, target_height)
    if cache_key in previous_bmps:
        return previous_bmps[cache_key]

    with open(filename, "rb") as f:
        f.seek(10)
        pixel_offset = int.from_bytes(f.read(4), "little")

        f.seek(18)
        width = int.from_bytes(f.read(4), "little")
        height = int.from_bytes(f.read(4), "little")

        f.seek(28)
        bpp = int.from_bytes(f.read(2), "little")
        if bpp != 24:
            raise ValueError("Only 24-bit BMPs are supported.")

        row_size = (width * 3 + 3) & ~3
        f.seek(pixel_offset)

        raw_pixels = [None] * height
        for y in reversed(range(height)):
            row = [tuple(f.read(3)[::-1]) for _ in range(width)]
            padding = row_size - width * 3
            if padding:
                f.read(padding)
            raw_pixels[y] = row

    # Skip resize if dimensions match or are not provided
    if not target_width or not target_height or (target_width == width and target_height == height):
        previous_bmps[cache_key] = raw_pixels
        return raw_pixels

    # Nearest-neighbor resize
    resized = []
    for y in range(target_height):
        src_y = int(y * height / target_height)
        row = []
        for x in range(target_width):
            src_x = int(x * width / target_width)
            row.append(raw_pixels[src_y][src_x])
        resized.append(row)

    previous_bmps[cache_key] = resized
    return resized

focus = (None, "Unset")

def getTopWinForPos(x, y):
    canidates = []
    sysUICanidates = []
    for win in windows:
        if win["pos"][0] <= x <= win["pos"][0]+win["geo"][0]:
            if win["pos"][1] <= y <= win["pos"][1]+win["geo"][1]:
                canidates.append(win)
    for win in sysUI:
        if win["pos"][0] <= x <= win["pos"][0]+win["geo"][0]:
            if win["pos"][1] <= y <= win["pos"][1]+win["geo"][1]:
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

def wait_until(somepredicate, timeout, period=0.25, *args, **kwargs):
  mustend = time.time() + timeout
  while time.time() < mustend:
    if somepredicate: return True
    time.sleep(period)
  return False

def handleInputs(event):
    hasReturned = False
    if ("focus" in  windows[-1] and ((event.type == id.events.KEYDOWN and windows[-1]["focus"] is not None) and windows[-1]["components"][windows[-1]["focus"]]["type"] == "input")) or (len(sysUI) > 0 and "focus" in  sysUI[-1] and ((event.type == id.events.KEYDOWN and sysUI[-1]["focus"] is not None) and sysUI[-1]["components"][sysUI[-1]["focus"]]["type"] == "input")):
        input = windows[-1]["components"][windows[-1]["focus"]]
        if input is None or ("type" in input and input["type"] != "input"):
            input = sysUI[-1]["components"][sysUI[-1]["focus"]]
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
                    print(pos, input["value"], len(input["value"]))
                    if pos < len(input["value"]):
                        strarray = list(input["value"])
                        strarray.__delitem__(pos)
                        input["value"] = ''.join(strarray)
        elif event.key == id.keys.RETURN:
            print(f"Return pressed, value: {input['value']}")
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
            print(f"Key pressed: {event.key}, unicode: {event.unicode}")
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
            input["on_change"](input["value"], windows[-1], windows[-1]["components"].index(input))


# Ensure no duplicate enumeration of applications
registered_apps = permissions.list_applications()
if len(registered_apps) == 0:
    for af in nsys.listapplications():
        print(af)
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
    shouldExitOnClose = True
    windows.append({"title":"Launcher", "pos": (69, 180), "geo": (300,500), "colour":(220,220,220), "components":[]})
    launcherWin = windows[-1]
    # Main apps frame
    launcherWin["components"].append({"type":"text", "text": "Apps"})
    registered_apps = permissions.list_applications()
    for app in registered_apps:
        print(app)
        app_id = app['id']
        app_name = app['name']
        print(f'{app_id}: {app_name}')
        
        # Create new frame for the app and buttons
        def load_app_info(app_id):
            try:
                app_spec = importlib.util.spec_from_file_location(
                    name=app_id.replace(".", ""),
                    location=f"./applications/{app_id}/__init__.py"
                )
                app_module = importlib.util.module_from_spec(app_spec)
                app_spec.loader.exec_module(app_module)
                return app_module.self
            except Exception as e:
                nsys.log(f"Error loading app info for {app_id}: {e}")
                return None
        
        app_instance = load_app_info(app_id)
        
        def launch_app(app_id=app_id):
            # Only launch basic apps via AppSession
            app_instance = load_app_info(app_id)
            # Launch basic apps normally
            app_ses = nsys.AppSession(app_id, session)
            app_ses.exec()

        # Create button based on app type
        launcherWin['components'].append({"type": "button", "text":app_name, "on_click": launch_app, "border":(0,0,0), "bg":(250,250,250),"colour":(0,0,0)})

    # tkinter.ttk.Button(root, text="Reauthenticate Session", command=systemSession.showAuthPopup).pack()
    arg = args.split(", ")
    if(arg[0] == "test"):
        app_id = arg[1]
        app_instance = load_app_info(app_id)
        # Launch basic apps normally
        app_ses = nsys.AppSession(app_id, session)
        app_ses.exec()
    
    # root.mainloop()



def authloop():
    try:
        nsys.sysState.set(nsys.sysState.awaitLogin)
        try:
            # systemSession.Authenticate("system", passhash=hashlib.md5(b"password").hexdigest(), sessionType=3)
            # time.sleep(1)
            systemSession.showAuthPopup(callback=lambda x: systemSession.exec(launcher, appfolder=""), appfolder="")
            print("salty")
            
        except Exception as e:
            nsys.log(e.args)
            # authloop()
    except(KeyboardInterrupt):
        nsys.log()
        nsys.log("Exiting.")
# check for arguments
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
        systemSession.exec(launcher, appfolder="", arguments="test, "+nsys.args[2])
    else:
        authloop()
else:
    authloop()

def renderFunction(framebuf, frame, width, height, eventgetter=None):
    global windows, dragging, drag_offset, dragged_element_index, mouse_was_pressed, mouse_pressed, cDragWin, id, hasStartedId, focus
    id.poll(eventgetter)
    # rag(framebuf, frame, width, height)
    surface.fill_screen((138, 207, 0))

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
                x, y = elem["pos"]
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
                            print("Mouse clicked!")
                            is_within_close_x = (x+w)-23 <= mouse_x < (x+w)-3
                            is_within_close_y = y+3 <= mouse_y < y+19

                            if is_within_close_x & is_within_close_y:
                                # print(f"mouse_pressed: {mouse_pressed}, mouse_was_pressed: {mouse_was_pressed}")
                                if gtwfp != None and wt == "window":
                                    windows.remove(gtwfp)
                            else:
                                # we didnt click close, so we probably clicked an element in the window
                                button_clicked = False
                                if "components" in elem:
                                    for comp in elem["components"]:
                                        if "bbox" in comp:
                                            comp_x = comp["bbox"][0] + elem["pos"][0]
                                            comp_y = comp["bbox"][1] + elem["pos"][1]
                                            cw = comp["bbox"][2]
                                            ch = comp["bbox"][3]
                                        else:
                                            print(comp)
                                            comp_x = 0 + elem["pos"][0]
                                            comp_y = 0 + elem["pos"][1]
                                            cw = 0
                                            ch = 0
                                        if comp_x <= mouse_x <= comp_x + cw and comp_y <= mouse_y <= comp_y + ch:
                                            print(f"Mouse clicked in a component")
                                            elem["focus"] = elem["components"].index(comp) if "components" in elem else None
                                            if(comp["type"] == "button"):
                                                print(f"Button {comp['text']} clicked!")
                                                # Handle button click here
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                button_clicked = True
                                                break
                                            elif(comp["type"] == "input"):
                                                print(f"Input clicked!")
                                                if "on_click" in comp:
                                                    comp["on_click"]()
                                                break
                                        else:
                                            print(f"Mouse clicked outside of components")
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
    # keyboard event handling
    wsysui = windows + sysUI
    for elem in wsysui:
        type = "window"
        if elem in sysUI:
            type = "sysui"
        w, h = elem["geo"]
        x, y = elem["pos"]
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
        elem["fbuf"] = np.zeros((elem['geo'][1], elem["geo"][0], 3), dtype=np.uint8)
        elem["fbuf"][0:h, 0:w] = colour
        if "components" in elem:
            for comp in elem["components"]:


                comp_xo = comp["pos"][0] if "pos" in comp else 0
                comp_yo = comp["pos"][1] if "pos" in comp else 0
                comp_w = None
                comp_h = None
                if "geo" in comp:
                    comp_w = comp["geo"][0]
                    comp_h = comp["geo"][1]
                if "fixed" in elem and elem["fixed"]:
                    comp_x = comp_xo
                    comp_y = comp_yo
                else:
                    comp_x = 5 + comp_xo
                    comp_y =  30 + comp_yo
                i = None
                compi = None
                if type == "window":
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
                        cw = comp["geo"][0]
                        ch = comp["geo"][1]
                    else:
                        cw = t[1]+ 10
                        ch = t[0]+ 10
                    elem["fbuf"][comp_y-2:comp_y+ch+2, comp_x-2:comp_x+cw+2] = comp["border"]
                    elem["fbuf"][comp_y:comp_y+ch, comp_x:comp_x+cw] = comp["bg"]
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
                    elem["fbuf"][comp_y-2:comp_y+ch+2, comp_x-2:comp_x+cw+2] = cb
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
        if "fixed" in elem and elem["fixed"]:
            framebuf[y:y+h, x:x+w] = elem["fbuf"]
        else:
            framebuf[y:y+elem["fbuf"].shape[0], x:x+elem["fbuf"].shape[1]] = elem["fbuf"]  # Draw the component buffer onto the main frame buffer
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
    for i in range (5):
        surface.draw_circle(framebuf, cx, cy, i*10,i*10)
    surface.draw_fchar(framebuf, "cursor", cx, cy, (0, 0, 255), pixel_multiplier=1, font=CHARACTER_MAP)


surface = sd.Bitmap(1366, 768, "", callback=renderFunction, font=CHARACTER_MAP)
id.hook_event(id.events.KEYDOWN, handleInputs)
try:
    surface.run()
except KeyboardInterrupt:
    print("Stopping bitch!")
    exit()