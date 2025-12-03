import pygame
import numpy as np
import math
from threading import Thread
from Drivers import sdl
from Drivers import shapeDriver
from scipy.ndimage import label, find_objects
import os
overlayfb = np.zeros((768, 1366,3), dtype=np.uint8)
os.environ["SDL_RENDER_VSYNC"] = "0"
# from systemfont import charmap as CHARACTER_MAP
# Charecter to ttf glyph map for special chars like hyphen, letters are to be ignored for this list, do not include normal letters- its just the ones that you shift for or use accents on
cgmap = {
    "-": "hyphen",
    "_": "underscore",
    " ": "space",
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "!": "exclam",
    "@": "at",
    "#": "numbersign",
    "$": "dollar",
    "%": "percent",
    "^": "caret",
    "&": "ampersand",
    "*": "asterisk",
    "(": "parenleft",
    ")": "parenright",
    "-": "hyphen",
    "=": "equal",
    "+": "plus",
    "{": "braceleft",
    "}": "braceright",
    "[": "bracketleft",
    "]": "bracketright",
    "\\": "backslash",
    "|": "pipe",
    ":": "colon",
    ";": "semicolon",
    "'": "quotesingle",
    '"': "quotedbl",
    "<": "less",
    ">": "greater",
    ",": "comma",
    ".": "period",
    "?": "question",
    "/": "slash",
    "`": "grave",
    "~": "tilde",
    "£": "pound",
    "€": "euro"
}
def overlay_image(base, overlay, pos_x, pos_y):
    """
    Overlays the `overlay` image onto the `base` image at position (pos_x, pos_y),
    copying only non-black pixels using NumPy masking.
    """
    result = base

    h, w, _ = overlay.shape

    # Define the region of interest on the base image
    end_x = min(pos_x + h, base.shape[0])
    end_y = min(pos_y + w, base.shape[1])

    roi = result[pos_x:end_x, pos_y:end_y]
    overlay_crop = overlay[:end_x - pos_x, :end_y - pos_y]

    # Create a mask for non-black pixels
    mask = np.any(overlay_crop != [0, 0, 0], axis=-1)

    # Apply the overlay using the mask
    roi[mask] = overlay_crop[mask]

    return result



class SurfaceDriver:
    class Bitmap:
        def __init__(self, width=1280, height=720, title="NovaOS BMP SurfaceDriver Window", callback=None, font=None, shapeDrawer=shapeDriver.Bitmap):
            """
            Initialise the SurfaceDriver.

            :param width: Width of the window.
            :param height: Height of the window.
            :param title: Title of the window.
            :param callback: A function to update the pixel data.
            """
            pygame.init()
            self.width = width
            self.height = height
            self.title = title
            self.rate = 30  # Default refresh rate
            self.callback = callback
            pygame.mouse.set_visible(False)  # Hide the mouse cursor            # Set up the display
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE,  pygame.DOUBLEBUF | pygame.HWSURFACE)
            pygame.display.set_caption(self.title)
            # Create a numpy array for raw pixel data (RGB format) with shape (height, width, 3)
            # This matches the conventional NumPy [y, x] indexing
            self.pixel_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            self.shapeDrawer = shapeDrawer
            # Running state
            self.running = True
            self.font = font
            if not hasattr(self.font,'cursor'):
                self.font['cursor'] = [
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
            if not hasattr(self.font,'missing'):
                self.font['missing'] = [
        "11111111111111111111",
        "10000000000000000001",
        "10000000000000000001",
        "10000000000000000001",
        "10000000000000000001",
        "10000000000000000001",
        "10000000000000000001",
        "11111111111111111111",
    ]
            # if not hasattr(self.font,' '):

            # Clock for limiting frame rate
            self.clock = pygame.time.Clock()
            
        def setRefreshRate(self, rate):
            """
            Set the refresh rate of the display.

            :param rate: Refresh rate in Hz.
            """
            self.rate = rate
            
        def fill_screen(self, colour=(255, 255, 255)):
            """
            Overwrite the entire screen with a specific colour.

            :param colour: A tuple representing the RGB colour (e.g., (255, 0, 0) for red).
            """
            self.shapeDrawer.fill_screen(self.pixel_data,colour=colour)
        def draw_rect(self, framebuf, x, y, w, h, colour=(255, 255, 255)):
            return self.shapeDrawer.draw_rect(framebuf,x,y,w,h,colour)
        def draw_border(self,x, y, w, h, border_colour=(255, 255, 255), thickness=3):
            return self.shapeDrawer.draw_border(self.pixel_data, x,y,w,h,border_colour, thickness)
        def draw_text(self,pixel_data, text, x, y, colour=(255, 255, 255), spacing=2, pixel_multiplier=1.0, font=None, width=None, height=None, curpos="balls"):
            if font == None:
                font = self.font
            return self.shapeDrawer.draw_text(pixel_data, text, x, y, colour, spacing,pixel_multiplier, font, width, height, curpos)
        def draw_fchar(self,pixel_data, char, x, y, colour=(255, 255, 255), pixel_multiplier=1.0, font=None):
            if font == None:
                font = self.font
            return self.shapeDrawer.draw_fchar(pixel_data, char, x, y, colour,pixel_multiplier, font)
        def draw_line(self,pixel_data, x1, y1, x2, y2, colour=(255, 255, 255)):
            return self.shapeDrawer.draw_line(pixel_data,x1,x2,y1,y2,colour)
        def draw_circle(self, pixel_data, x0, y0, radius, colour=(255, 255, 255)):
            return self.shapeDrawer.draw_circle(pixel_data,x0,y0,radius,colour)
        def draw_title_bar(self,framebuf, x, y, w, title_height=50, title_colour=(255, 255, 255)):
            """
            Draw a title bar at the top of the rectangle.
            """
            framebuf[y:y+title_height, x:x+w] = title_colour
        def run(self):
            """
            Main loop for the SurfaceDriver.
            """
            frame = 0  # Frame counter for animation
            self.surface = pygame.Surface((self.width, self.height))
            while self.running:
                if not(hasattr(self, 'oldPD')):
                    self.oldPD = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                eventgetter = pygame.event.get()
                for event in eventgetter:
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.width, self.height = event.w, event.h
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                        # Always allocate pixel_data as (height, width, 3)
                        pygame.display.update()
                        self.pixel_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)  # Correct NumPy order: (height, width, 3)
                        # If a callback is provided, use it to update the pixel data
                        if self.callback:
                            # Note: we pass width and height in the conventional order (width first, then height)
                            self.callback(self.pixel_data, frame, self.width, self.height)                # If a callback is provided, use it to update the pixel data
                            # Get events from the sdl.py - call only once per loop
                event = sdl.get_event()
                if event is not None:
                    print(f"Processing event: {event}")
                    
                    if event.get("event") == "resize":
                        print("Socket resize event:", event["width"], "x", event["height"])
                        self.width, self.height = event["width"], event["height"]
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                        # Fix: correct dimensions for pygame
                        pygame.display.update()
                        self.surface = pygame.Surface((self.width, self.height))
                        self.pixel_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                        # On resize event:

                    
                    # Clear the event after processing
                    sdl.clear_event()
                # pygame.mouse.set_visible(True)
                if self.callback:
                    # Pass width and height in the conventional order (width first, then height)
                    self.callback(self.pixel_data, frame, self.width, self.height, eventgetter=eventgetter)# Create a surface from the pixel data
                    # pygame.mouse.set_visible(False)
                # diff = self.oldPD != self.pixel_data
                # labeled, _ = label(diff)
                # rects = find_objects(labeled)
                # if len(rects) > 15:  # threshold = e.g. 10
                #     surface = pygame.surfarray.make_surface(self.pixel_data.swapaxes(0,1))
                #     self.screen.blit(surface, (0, 0))
                # else:
                #     for slices in rects:
                #         ys, xs = slices[:2]
                #         x = xs.start
                #         y = ys.start
                #         w = xs.stop - xs.start
                #         h = ys.stop - ys.start
                #         subarray = self.pixel_data[y:y+h, x:x+w]
                #         surface = pygame.surfarray.make_surface(subarray.swapaxes(0,1))
                #         self.screen.blit(surface, (x, y))
                # pygame.display.flip()
                # # Note: Pygame expects pixel data in a certain format - they might be transposing
                # # the array internally which could contribute to rotation issues
                Thread(target=overlay_image,args=[self.pixel_data, overlayfb, 0,0],daemon=True).start()
                pygame.surfarray.blit_array(self.surface, self.pixel_data.swapaxes(0, 1))
                self.screen.blit(self.surface, (0, 0))
                pygame.display.flip()
                # Thread(target=sdl.send_frame,args=[self.pixel_data.copy()],daemon=True).start()
                self.oldPD = self.pixel_data.copy()
                # Increment the frame counter
                frame += 1
                # Limit the frame rate to 60 FPS    
                self.clock.tick(self.rate)
            pygame.quit()


# Example additional rendering functions using the new methods:
def render_animated_gradient(pixel_data, frame, width, height):
    Y, X = np.indices((height, width))
    red   = ((X + frame) % 256).astype(np.uint8)
    green = ((Y + frame) % 256).astype(np.uint8)
    blue  = (((X + Y) // 2 + frame) % 256).astype(np.uint8)
    pixel_data[:, :, 0] = red
    pixel_data[:, :, 1] = green
    pixel_data[:, :, 2] = blue

def draw_hello(pixel_data, frame, width, height):
    """
    Draw "Hello" as pixels on the screen, with line wrapping and support for missing characters.
    """
    # Clear the screen
    pixel_data[:, :] = (0, 0, 0)
    render_animated_gradient(pixel_data=pixel_data, frame=frame)
    # Define the character map
    # Text to draw
    pixel_multiplier = 1 # Scale factor for each pixel
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    x, y = 10, 10  # Starting position
    spacing = 2  # Spacing between characters
    colour = (255, 255, 255)  # Colour of the text
    max_char_height = 5
    for char in CHARACTER_MAP:
        if len(char) > max_char_height:
            max_char_height = len(char)*pixel_multiplier
    max_char_height+=max_char_height+5;
    # Starting cursor position
    cursor_x = x
    cursor_y = y

    # Iterate through each character in the text
    for char in text:
        if char in CHARACTER_MAP:
            char_pixels = CHARACTER_MAP[char]
        else:
            char_pixels = CHARACTER_MAP['missing']        # Check if the character will exceed the screen width
        char_width = len(char_pixels[0]) * pixel_multiplier + spacing * pixel_multiplier
        if cursor_x + char_width > pixel_data.shape[1]:  # Use shape[1] for width (columns)
            # Wrap to the next line
            cursor_x = x
            cursor_y += max_char_height * pixel_multiplier  # Move down by the height of a character# Draw the character
        for row_index, row in enumerate(char_pixels):
            for col_index, pixel in enumerate(row):
                if pixel == "1":
                    # Scale the pixel horizontally and vertically
                    for dy in range(pixel_multiplier):
                        for dx in range(pixel_multiplier):
                            # Calculate pixel coordinates
                            py = cursor_y + row_index * pixel_multiplier + dy
                            px = cursor_x + col_index * pixel_multiplier + dx
                            # Check boundaries before writing - use correct order for shape checks
                            if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                # Correct NumPy indexing: [y, x]
                                pixel_data[py, px] = colour

        # Move the cursor to the right for the next character
        cursor_x += len(char_pixels[0]) * pixel_multiplier + spacing * pixel_multiplier
# Example usage
def draw_hello2(pixel_data, frame, width, height):
        render_animated_gradient(pixel_data, frame, width, height)
        driver.draw_text(pixel_data, "Hello", 10, 10, colour=(255, 255, 255), pixel_multiplier=10)
  
if __name__ == "__main__":
    # Create and run the SurfaceDriver using draw_hello callback
    driver = SurfaceDriver.Bitmap(callback=draw_hello2)
    driver.run()