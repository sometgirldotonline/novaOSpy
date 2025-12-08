import math
import numpy as np
import cv2
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
def wrap_text(text, font, spacing, pixel_multiplier, wrap_width):
    # Returns a list of wrapped lines
    lines = []
    for raw_line in text.split('\n'):
        line = ""
        line_cursor_x = 0
        for word in raw_line.split(" "):
            wordWidth = 0
            for char in word:
                if char in font:
                    char_pixels = font[char]
                elif char in cgmap and cgmap[char] in font:
                    char_pixels = font[cgmap[char]]
                else:
                    char_pixels = font['missing']
                scaled = resizeFC(char_pixels, pixel_multiplier)
                char_width = scaled.shape[1] + int(spacing * pixel_multiplier)
                wordWidth += char_width
            wordWidth += 4
            if line_cursor_x + wordWidth > wrap_width and line:
                lines.append(line.rstrip())
                line = ""
                line_cursor_x = 0
            line += word + " "
            line_cursor_x += wordWidth
        lines.append(line.rstrip())
    return lines
def resizeFC(char_pixels, scale):
    char_pixels = char_pixels
    if scale == 1.0:
        return char_pixels
    elif math.floor(scale) == scale and scale > 1:
        
        return char_pixels.repeat(scale, axis=0).repeat(scale, axis=1)
    else:
        if not char_pixels.any() or len(char_pixels) == 0 or len(char_pixels[0]) == 0:
            return np.zeros((1, 1), dtype=bool)
        return cv2.resize(char_pixels.astype(np.uint8), None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST).astype(bool)
        
# ShapeDriver- Draws Shapes (duh)
class Bitmap:
    @staticmethod
    def fill_screen(framebuf, colour=(255, 255, 255)):
        """
        Overwrite the entire screen with a specific colour.

        :param colour: A tuple representing the RGB colour (e.g., (255, 0, 0) for red).
        """
        framebuf[:, :] = colour

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
    def draw_text(pixel_data, text, x, y, colour=(255, 255, 255), spacing=2, pixel_multiplier=1.0, font=None, width=None, height=None, curpos="balls", wrap=True):
        if font is None:
            raise ValueError("Provide a font")
        wrap_width = width if width is not None else pixel_data.shape[1] - x
        wrapped_lines = wrap_text(text, font, spacing, pixel_multiplier, wrap_width)
        if wrap == False:
            wrapped_lines = [wrapped_lines[0]]
        max_letter_height = max(
            [len(font[c]) if c in font else len(font['missing']) for c in text if c != '\n']
        ) if any(c != '\n' for c in text) else 1
        text_max_height = int(math.ceil(max_letter_height * pixel_multiplier))
        cursor_x = x
        cursor_y = y
        max_x_position = x
        max_y_position = y
        oci = 0
        cursorAtStart = False
        if curpos == -1:
            curpos = None
            cursorAtStart = True
        for line in wrapped_lines:
            line_cursor_x = cursor_x
            if not line:
                continue
            for char in line:
                if char in font:
                    char_pixels = font[char]
                else:
                    if char in cgmap and cgmap[char] in font:
                        char_pixels = font[cgmap[char]]
                    else:
                        char_pixels = font['missing']
                char_pixels_with_cursor = char_pixels

                char_width = int(math.ceil(len(char_pixels_with_cursor[0]) * pixel_multiplier + spacing * pixel_multiplier))
                char_height_scaled = int(math.ceil(len(char_pixels_with_cursor) * pixel_multiplier))
                top_padding = text_max_height - char_height_scaled

                if isinstance(char_pixels, list):
                        char_pixels = np.array([[c == '1' for c in line] for line in char_pixels], dtype=bool)
                if isinstance(char_pixels, list):
                    char_pixels = np.array([[c == '1' for c in line] for line in char_pixels], dtype=bool)
                scaled = resizeFC(char_pixels, pixel_multiplier)
                h, w = scaled.shape
                dest_y = int(cursor_y + top_padding)
                y1 = max(0, dest_y)
                y2 = min(pixel_data.shape[0], dest_y+h)
                dest_x = line_cursor_x
                x1 = max(0, dest_x)
                x2 = min(pixel_data.shape[1], dest_x + w)
                mask_y_start = y1 - dest_y
                mask_x_start = x1 - dest_x
                if y2 > y1 and x2 > x1:
                    sliced = scaled[mask_y_start: mask_y_start + (y2 - y1), mask_x_start: mask_x_start + (x2 - x1)]
                    region = pixel_data[y1:y2, x1:x2]
                    region[sliced] = (0,0,0)
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
                    cursor_x = line_cursor_x
                    cursor_y = y
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
            cursor_y += text_max_height
        if height is not None:
            pixel_data = pixel_data[0:height, 0:max_x_position-x]
        text_width = max_x_position - x
        text_height = (max_y_position - y)
        return text_height, text_width

    @staticmethod
    def draw_fchar(pixel_data, char, x, y, colour=(255, 255, 255), pixel_multiplier=1.0):
        """
        Draw a single character on the screen with scaling do not look up based on charecters, char is the name of character in the font/charmap.
        pixel_multiplier can be a float for finer scaling, including values less than 1.0.
        """
        char_pixels = char
        if isinstance(char_pixels, list):
            char_pixels = np.array([[c == '1' for c in line] for line in char_pixels], dtype=bool)
        scaled = resizeFC(char_pixels, pixel_multiplier)
        h, w = scaled.shape
        y1 = max(0, y)
        y2 = min(pixel_data.shape[0], y+h)
        x1 = max(0, x)
        x2 = min(pixel_data.shape[1], x + w)
        mask_y_start = y1 - y
        mask_x_start = x1 - x
        if y2 > y1 and x2 > x1:
            sliced = scaled[mask_y_start: mask_y_start + (y2 - y1), mask_x_start: mask_x_start + (x2 - x1)]
            region = pixel_data[y1:y2, x1:x2]
            region[sliced] = (0,0,0)
    @staticmethod
    def draw_line(pixel_data, x1, y1, x2, y2, colour=(255, 255, 255)):
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
    @staticmethod
    def draw_circle(pixel_data, x0, y0, radius, colour=(255, 255, 255)):
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
