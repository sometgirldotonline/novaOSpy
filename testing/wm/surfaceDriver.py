import pygame
import numpy as np
import math
import os
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
    "#": "hash",
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
class SurfaceDriver:
    class Bitmap:
        def __init__(self, width=1280, height=720, title="NovaOS BMP SurfaceDriver Window", callback=None, font=None):
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
            self.rate = 60  # Default refresh rate
            self.callback = callback
            pygame.mouse.set_visible(False)  # Hide the mouse cursor            # Set up the display
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE,  pygame.DOUBLEBUF | pygame.HWSURFACE)
            pygame.display.set_caption(self.title)
            # Create a numpy array for raw pixel data (RGB format) with shape (height, width, 3)
            # This matches the conventional NumPy [y, x] indexing
            self.pixel_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)

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
            self.pixel_data[:, :] = colour

        # --- Optimized drawing helper methods ---
        @staticmethod
        def draw_rect(framebuf, x, y, w, h, colour):
            """
            Draw a filled rectangle using slicing.
            Note: framebuf is assumed to have shape (height, width, 3)
            and (x,y) corresponds to (row, col) indices.
            """
            framebuf[y:y+h, x:x+w] = colour

        @staticmethod
        def draw_border(framebuf, x, y, w, h, border_colour=(255, 255, 255), thickness=3):
            """
            Draw a border for a rectangle using slicing.
            """
            # Top border
            framebuf[y:y+thickness, x:x+w] = border_colour
            # Bottom border
            framebuf[y+h-thickness:y+h, x:x+w] = border_colour
            # Left border
            framebuf[y:y+h, x:x+thickness] = border_colour
            # Right border
            framebuf[y:y+h, x+w-thickness:x+w] = border_colour

        @staticmethod
        def draw_title_bar(framebuf, x, y, w, title_height=50, title_colour=(255, 255, 255)):
            """
            Draw a title bar at the top of the rectangle.
            """
            framebuf[y:y+title_height, x:x+w] = title_colour
        def draw_text(self, pixel_data, text, x, y, colour=(255, 255, 255), spacing=2, pixel_multiplier=1.0, font=None, width=None, height=None, curpos="balls"):
            """
            Draw text on the screen with automatic top padding for shorter characters.
            Supports '\n' for line breaks.
            Characters that are shorter than the tallest in the text are padded at the top.
            pixel_multiplier can be a float for finer scaling, including values less than 1.0.
            If width is provided, text will wrap at that width (character-based line wrapping).
            """
            if font is None:
                font = self.font
            lines = text.split('\n')
            max_letter_height = max(
            [len(font[c]) if c in font else len(font['missing']) for c in text if c != '\n']
            ) if any(c != '\n' or c != ' ' for c in text) else 1
            text_max_height = int(math.ceil(max_letter_height * pixel_multiplier))
            font[' '] = ["0" * 3 for x in range(max_letter_height)]
            cursor_x = x
            cursor_y = y

            max_x_position = x
            max_y_position = y
            oci = 0
            cursorAtStart = False
            if curpos == -1:
                curpos = None;
                cursorAtStart=True
            for line in lines:
                line_cursor_x = cursor_x
                for char in line:
                    if char in font:
                        char_pixels = font[char]
                    else:
                        if char in cgmap and cgmap[char] in font:
                            char_pixels = font[cgmap[char]]
                        else:
                            char_pixels = font['missing']


                    # Add cursor to the character if curpos matches oci
                    # if curpos is not None and curpos == oci:
                    #     char_pixels_with_cursor = [row + "11" for row in char_pixels]
                    # elif cursorAtStart and oci == 0:
                    #     char_pixels_with_cursor = ["11" + row for row in char_pixels]
                    # else:
                    char_pixels_with_cursor = char_pixels

                    char_width = int(math.ceil(len(char_pixels_with_cursor[0]) * pixel_multiplier + spacing * pixel_multiplier))
                    
                    wrap_width = width if width is not None else pixel_data.shape[1]
                    if line_cursor_x + char_width > x + wrap_width or line_cursor_x + char_width > pixel_data.shape[1]:
                        line_cursor_x = x
                        cursor_y += text_max_height

                    char_height_scaled = int(math.ceil(len(char_pixels_with_cursor) * pixel_multiplier))
                    top_padding = text_max_height - char_height_scaled

                    # Draw the character (with or without cursor)
                    if pixel_multiplier >= 1.0:
                        for row_index, row in enumerate(char_pixels_with_cursor):
                            for col_index, pixel in enumerate(row):
                                if pixel == "1":
                                    for dy in range(int(math.ceil(pixel_multiplier))):
                                        for dx in range(int(math.ceil(pixel_multiplier))):
                                            px = int(line_cursor_x + col_index * pixel_multiplier + dx)
                                            py = int(cursor_y + top_padding + row_index * pixel_multiplier + dy)
                                            if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                                pixel_data[py, px] = colour
                    else:
                        skip_factor = 1.0 / pixel_multiplier
                        scaled_width = max(1, int(len(char_pixels_with_cursor[0]) * pixel_multiplier))
                        scaled_height = max(1, int(len(char_pixels_with_cursor) * pixel_multiplier))
                        for scaled_y in range(scaled_height):
                            for scaled_x in range(scaled_width):
                                source_y = int(scaled_y / pixel_multiplier)
                                source_x = int(scaled_x / pixel_multiplier)
                                if source_y < len(char_pixels_with_cursor) and source_x < len(char_pixels_with_cursor[0]):
                                    if char_pixels_with_cursor[source_y][source_x] == "1":
                                        px = int(line_cursor_x + scaled_x)
                                        py = int(cursor_y + top_padding + scaled_y)
                                        if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                            pixel_data[py, px] = colour
                    # draww the cursor ( a 2px wide line with the height as the max height of any charecters) if curpos matches oci
                    if curpos is not None and curpos == oci:
                        cursor_x = line_cursor_x + char_width
                        cursor_y = cursor_y + top_padding
                        # Draw the cursor as a vertical line
                        cursor_height = text_max_height
                        if pixel_multiplier >= 1.0:
                            for dy in range(int(math.ceil(cursor_height))):
                                for dx in range(2):
                                    px = int(cursor_x + dx)
                                    py = int(cursor_y + dy)
                                    if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                        pixel_data[py, px] = colour
                    elif cursorAtStart and oci == 0:
                        print("Drawing cursor at start")
                        # Draw the cursor at the start of the text, before the first character
                        cursor_x = line_cursor_x
                        cursor_y = y
                        # Draw the cursor as a vertical line, default height to 20px if the text_max_height is less than 5
                        cursor_height = text_max_height if text_max_height >= 5 else 20
                        if pixel_multiplier >= 1.0:
                            for dy in range(int(math.ceil(cursor_height))):
                                for dx in range(2):
                                    px = int(cursor_x + dx)
                                    py = int(cursor_y + dy)
                                    if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                        pixel_data[py, px] = colour
                                    
                    line_cursor_x += char_width
                    max_x_position = max(max_x_position, line_cursor_x)
                    max_y_position = max(max_y_position, cursor_y + text_max_height)
                    oci += 1
                # After each line, move cursor_y down and reset line_cursor_x
                cursor_y += text_max_height
                line_cursor_x = x
            text_width = max_x_position - x
            text_height = max_y_position - y
            return text_height, text_width
        def draw_fchar(self, pixel_data, char, x, y, colour=(255, 255, 255), pixel_multiplier=1.0, font=None):
            """
            Draw a single character on the screen with scaling do not look up based on charecters, char is the name of character in the font/charmap.
            pixel_multiplier can be a float for finer scaling, including values less than 1.0.
            """
            if font == None:
                font=self.font
            # Get the pixel data for the character
            if char in font:
                char_pixels = font[char]
            else:
                char_pixels = font['missing']            # Support for subpixel rendering
            if pixel_multiplier >= 1.0:
                # Draw the character pixel-by-pixel with scaling
                for row_index, row in enumerate(char_pixels):
                    for col_index, pixel in enumerate(row):
                        if pixel == "1":
                            for dy in range(int(math.ceil(pixel_multiplier))):
                                for dx in range(int(math.ceil(pixel_multiplier))):
                                    # Correct pixel calculation
                                    px = int(x + col_index * pixel_multiplier + dx)
                                    py = int(y + row_index * pixel_multiplier + dy)
                                    
                                    # Check boundaries before writing (corrected order)
                                    if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                        # Correct NumPy indexing: [y, x]
                                        pixel_data[py, px] = colour
            else:
                # For subpixel rendering (pixel_multiplier < 1.0)
                # Use float-based sampling to properly handle any scale factor
                skip_factor = 1.0 / pixel_multiplier
                
                # Calculate dimensions of scaled character
                scaled_width = max(1, int(len(char_pixels[0]) * pixel_multiplier))
                scaled_height = max(1, int(len(char_pixels) * pixel_multiplier))
                
                # For each pixel in the scaled output
                for scaled_y in range(scaled_height):
                    for scaled_x in range(scaled_width):
                        # Map back to source character
                        source_y = int(scaled_y / pixel_multiplier)
                        source_x = int(scaled_x / pixel_multiplier)
                        
                        # Make sure we're within bounds of the source character
                        if source_y < len(char_pixels) and source_x < len(char_pixels[0]):
                            # If this pixel is set in the source
                            if char_pixels[source_y][source_x] == "1":
                                # Calculate destination coordinates
                                px = int(x + scaled_x)
                                py = int(y + scaled_y)
                                
                                # Draw if in bounds
                                if py < pixel_data.shape[0] and px < pixel_data.shape[1]:
                                    pixel_data[py, px] = colour
        def draw_line(self, pixel_data, x1, y1, x2, y2, colour=(255, 255, 255)):
            # Bresenham's line algorithm
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy

            while True:
                # Draw the pixel using correct NumPy indexing [y, x]
                if 0 <= y1 < pixel_data.shape[0] and 0 <= x1 < pixel_data.shape[1]:
                    pixel_data[y1, x1] = colour  # This is already correct: [y, x]
                if x1 == x2 and y1 == y2:
                    break
                err2 = err * 2
                if err2 > -dy:
                    err -= dy
                    x1 += sx
                if err2 < dx:
                    err += dx
                    y1 += sy
        def draw_circle(self, pixel_data, x0, y0, radius, colour=(255, 255, 255)):
            # Midpoint circle algorithm
            x = radius
            y = 0
            radius_error = 1 - x

            while x >= y:
                # Draw the circle in all octants using correct NumPy indexing [y, x]
                # With boundary checks
                points = [
                    (y0 + y, x0 + x), (y0 + x, x0 + y), 
                    (y0 + x, x0 - y), (y0 + y, x0 - x),
                    (y0 - y, x0 - x), (y0 - x, x0 - y), 
                    (y0 - x, x0 + y), (y0 - y, x0 + x)
                ]
                
                for py, px in points:
                    if 0 <= py < pixel_data.shape[0] and 0 <= px < pixel_data.shape[1]:
                        pixel_data[py, px] = colour

                if radius_error < 0:
                    radius_error += 2 * (y + 1)
                else:
                    x -= 1
                    radius_error += 2 * (y - x + 1)
                y += 1
        def run(self):
            """
            Main loop for the SurfaceDriver.
            """
            frame = 0  # Frame counter for animation
            while self.running:
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
                if self.callback:
                    # Pass width and height in the conventional order (width first, then height)
                    self.callback(self.pixel_data, frame, self.width, self.height, eventgetter=eventgetter)# Create a surface from the pixel data
                # Note: Pygame expects pixel data in a certain format - they might be transposing
                # the array internally which could contribute to rotation issues
                surface = pygame.surfarray.make_surface(self.pixel_data.swapaxes(0, 1))
                # Blit the surface to the screen and update the display
                self.screen.blit(surface, (0, 0))
                pygame.display.flip()

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