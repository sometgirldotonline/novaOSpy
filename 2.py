from surfaceDriver import SurfaceDriver as sd
from inputDriver import InputDriver as id
from surfaceDriver import render_animated_gradient as rag
from Fonts.PY.vt323 import charmap as CHARACTER_MAP
from Fonts.PY.mdi import charmap as icons
# CHARACTER_MAP = icons
import time
import numpy as np
import sys
def rgb(r, g, b):
    """Convert RGB values to a tuple."""
    return (r, g, b)
mouse_was_pressed = False
mouse_pressed = (False, False, False)
windows = []
sysUI = []
cDragWin = None
dragging = False
hasStartedId = False
drag_offset = (0, 0)
dragged_element_index = None
def overlay_image(base, overlay, pos_x, pos_y):
    for y in range(len(overlay)):
        if pos_y + y >= len(base):
            continue
        for x in range(len(overlay[0])):
            if pos_x + x >= len(base[0]):
                continue
            base[pos_y + y][pos_x + x] = overlay[y][x]
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
    if "focus" in  windows[-1] and ((event.type == id.events.KEYDOWN and windows[-1]["focus"] is not None) and windows[-1]["components"][windows[-1]["focus"]]["type"] == "input"):
        print(f"Key pressed: {event.key}, unicode: {event.unicode}")
        input = windows[-1]["components"][windows[-1]["focus"]]
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

def renderFunction(framebuf, frame, width, height, eventgetter=None):
    global windows, dragging, drag_offset, dragged_element_index, mouse_was_pressed, mouse_pressed, cDragWin, id, hasStartedId, focus
    id.poll(eventgetter)
    # rag(framebuf, frame, width, height)
    surface.fill_screen(rgb(138, 207, 0))

    mouse_buttons = id.get_mouse_buttons()
    mouse_x, mouse_y = id.get_mouse_position()

    if mouse_buttons[0]:
        if not dragging:
            for i, elem in enumerate(windows):
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
                                        comp_x = comp["bbox"][0] + elem["pos"][0]
                                        comp_y = comp["bbox"][1] + elem["pos"][1]
                                        cw = comp["bbox"][2]
                                        ch = comp["bbox"][3]
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
        if type == "window":
            if x > surface.width or x < 0:
                windows[windows.index(elem)]["opos"] = elem["pos"]
                windows[windows.index(elem)]["pos"] = (0, y)
            if y > surface.height or y < 0:
                windows[windows.index(elem)]["opos"] = elem["pos"]
                windows[windows.index(elem)]["pos"] = (x, 0)
            # if we have an opos (original position) and its within the screen bounds, set pos to opos, and clear the opos
            if "opos" in elem and elem["opos"] is not None:
                opos_x, opos_y = elem["opos"]
                if 0 <= opos_x <= width - w and 0 <= opos_y <= height - h:
                    windows[windows.index(elem)]["pos"] = (opos_x, opos_y)
                    windows[windows.index(elem)]["opos"] = None   
        
        colour = elem["colour"]

        if type == "window":
            # Draw title using draw_text function
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
                    t = surface.draw_text(elem["fbuf"], comp["text"], comp_x+5,comp_y)
                    # for the bbox here we will use the borders geometry
                    comp["bbox"] = (comp_x, comp_y, cw, ch)
                elif(comp["type"] == "input"):
                    # use the previous components bbox for positioning offset if it exists, and if this element did not specify a position, so we can autmolatically position elements vertically, downwards
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
                    # if we are focusing this input, we should brighten the border
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
                    # for the bbox here we will use the borders geometry
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
            # Fixed windows do not have a titlebar or borders
            framebuf[y:y+h, x:x+w] = elem["fbuf"]
        else:
            framebuf[y:y+elem["fbuf"].shape[0], x:x+elem["fbuf"].shape[1]] = elem["fbuf"]  # Draw the component buffer onto the main frame buffer
                # Main body

                # Titlebar
        if "fixed" not in elem or not elem["fixed"]:
            framebuf[y:y+25, x:x+w] = (255, 255, 255)
            surface.draw_text(framebuf, title, title_x, title_y-5, (0, 0, 0), pixel_multiplier=1.2)
            # Borders
            framebuf[y:y+h, x:x+3] = (255, 255, 255)             # Left
            framebuf[y:y+h, x+w-3:x+w] = (255, 255, 255)         # Right
            framebuf[y+h-3:y+h, x:x+w] = (255, 255, 255)         # Bottom
            # Close Button
            # Close button background - brighter if mouse is hovering
            close_button_x = (x+w)-23
            close_button_y = y+3
            close_button_w = 20
            close_button_h = 19
            # Check if mouse is within close button bounds
            if (close_button_x <= mouse_x <= close_button_x + close_button_w and 
                close_button_y <= mouse_y <= close_button_y + close_button_h):
                framebuf[y+3:y+22,(x+w)-23:(x+w)-3] = (255,100,100)  # Brighter red when hovering
            else:
                framebuf[y+3:y+22,(x+w)-23:(x+w)-3] = (255,0,0)      # Normal red
            surface.draw_fchar(framebuf, "close", (x+w)-23, y+7, (0,0,0), font=icons, pixel_multiplier=0.95)    # Cursor (white square)
    size = 20
    cx = max(0, min(mouse_x, width - size))  # Width is for x-coordinate bounds
    cy = max(0, min(mouse_y, height - size)) # Height is for y-coordinate bounds
    # framebuf[cy:cy+size, cx:cx+size] = (255, 255, 255)  # Correct NumPy indexing: [y, x]
    # surface.draw_text(framebuf, "M", cx, cy, (0, 0, 0), pixel_multiplier=1)
    surface.draw_fchar(framebuf, "cursor", cx, cy, (0, 0, 255), pixel_multiplier=1, font=CHARACTER_MAP)
    # surface.draw_circle(framebuf, 10, 10, 50,50)

surface = sd.Bitmap(1366, 768, "", callback=renderFunction, font=CHARACTER_MAP)
id = id()
id.hook_event(id.events.KEYDOWN, handleInputs)
# make a new window into onscreenelements, with a button that on click will print "Hello World"
windows.append({
    "title": "Hello World",
    "pos": (69, 180),
    "geo": (300, 200),
    "colour": (220, 220, 220),
    "components": [
        {"type": "text", "text": 'Click the button below to print "Hello World"', "colour": (100, 100, 150)},
        {"type": "button", "text": "Click Me",  "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), "on_click": lambda: print("Hello World")}
    ]
})
windows.append({
    "title": "Death window",
    "pos": (50, 80),
    "geo": (300, 200),
    "colour": (220, 220, 220),
    "components": [
        {"type": "text", "text": "press to make the script die\n\n\nBALLS", "geo":(280, 20), "colour": (100, 100, 150), "pixel_multiplier": 1.2},
        {"type": "button", "text": "i dare you", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), "on_click": lambda: exit()},
        {"type": "text", "text": "press to make the script die\n\n\nBALLS","colour": (100, 100, 150), "pixel_multiplier": 1.2},
    ]
})
def input_change_handler(value, window, index):
    print(f"Input changed to: {value}")
    # Update the text component below the input with the new value
    if index + 1 < len(window["components"]):
        window["components"][index + 1]["text"] = f"{value}"
def trmnl(command, window, index):
    """Eval python code and write it to the text after the input box."""
    try:
        result = exec(command)
        print(f"Command result: {result}")
        if index + 1 < len(window["components"]):
            prev_text = window["components"][index + 1]["text"]
            if prev_text == "":
                window["components"][index + 1]["text"] = f"{result}"
            else:
                window["components"][index + 1]["text"] = f"{prev_text}\n{result}"
    except Exception as e:
        print(f"Error occurred: {e}")
        # Update the text component below the input with the error message
        if index + 1 < len(window["components"]):
            prev_text = window["components"][index + 1]["text"]
            if prev_text == "":
                window["components"][index + 1]["text"] = f"Err:{e}"
            else:
                window["components"][index + 1]["text"] = f"{prev_text}\nErr:{e}"
    
windows.append({
    "title": "Terminal Window",
    "pos": (100, 100),
    "geo": (500, 500),
    "colour": (0, 0, 0),
    "components": [
        {"type":"input", "value": "A Value", "colour": (0, 255, 0), "bg": (0, 0, 0), "border": (0, 0, 0),"on_return": trmnl, "geo": (490, 20)},
        {"type": "text", "text": "", "colour": (0, 255, 0)},
        {"type": "button", "text": "Start", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), }
    ]
})
# Taskbar window
sysUI.append({
    "title": "Taskbar",
    "pos": (0, 768-30),
    "geo": (1366, 30),
    "colour": (50, 50, 50),
    "fixed": True,  # This window will not be draggable and has no title or border
    "components": [
        {"type": "button", "text": "Start", "colour": (100, 100, 150), "bg": (190, 190, 190), "border": (0, 0, 0), 
         "on_click": lambda: print("Start button clicked!")}
    ]
})
# Image window
windows.append({
    "title": "Image Window",
    "pos": (100, 100),
    "geo": (500, 500),
    "colour": (220, 220, 220),
    "components": [
        {"type": "image", "image": read_bmp_rgb_array("luke.bmp", target_height=50, target_width=50), "pos": (0, 0)}
    ]
})
try:
    surface.run()
except KeyboardInterrupt:
    print("Stopping bitch!")
    exit()