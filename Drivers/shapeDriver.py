import numpy,math
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
    def draw_text(pixel_data, text, x, y, colour=(255, 255, 255), spacing=2, pixel_multiplier=1.0, font=None, width=None, height=None, curpos="balls"):
        """
        Draw text on the screen with automatic top padding for shorter characters.
        Supports '\n' for line breaks.
        Characters that are shorter than the tallest in the text are padded at the top.
        pixel_multiplier can be a float for finer scaling, including values less than 1.0.
        If width is provided, text will wrap at that width (character-based line wrapping).
        """
        if font is None:
            raise ValueError("Provide a font")
        lines = text.split('\n')
        max_letter_height = max(
        [len(font[c]) if c in font else len(font['missing']) for c in text if c != '\n']
        ) if any(c != '\n' for c in text) else 1
        font[' '] = ["0" * 3 for x in range(max_letter_height)]
        text_max_height = int(math.ceil(max_letter_height * pixel_multiplier))

        cursor_x = x
        cursor_y = y

        max_x_position = x
        max_y_position = y
        oci = 0
        cursorAtStart = False
        newstring = ""
        wrap_width = width if width is not None else 200  # define a reasonable default

        for line in lines:
            line_cursor_x = cursor_x
            line = line.split(" ")
            for word in line:
                wordWidth = 0
                for char in word:
                    if char in font:
                        char_pixels = font[char]
                    elif char in cgmap and cgmap[char] in font:
                        char_pixels = font[cgmap[char]]
                    else:
                        char_pixels = font['missing']

                    char_width = int(math.ceil(len(char_pixels[0]) * pixel_multiplier + spacing * pixel_multiplier))
                    wordWidth += char_width
                    if line_cursor_x + wordWidth > x + wrap_width:
                        line_cursor_x = 0
                        newstring += "\n"
                wordWidth += 4
                newstring += word + " "

                line_cursor_x += wordWidth  # update cursor after adding word

                
        if curpos == -1:
            curpos = None;
            cursorAtStart=True
        for line in newstring.split("\n"):
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
                # if line_cursor_x + char_width > x + wrap_width or line_cursor_x + char_width > pixel_data.shape[1]:
                #     line_cursor_x = x
                #     cursor_y += text_max_height

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
        if height != None:
            pixel_data=pixel_data[0:height, 0:max_x_position-x]
        text_width = max_x_position - x
        text_height = max_y_position - y
        return text_height, text_width
    @staticmethod
    def draw_fchar(pixel_data, char, x, y, colour=(255, 255, 255), pixel_multiplier=1.0, font=None):
        """
        Draw a single character on the screen with scaling do not look up based on charecters, char is the name of character in the font/charmap.
        pixel_multiplier can be a float for finer scaling, including values less than 1.0.
        """
        if font == None:
            raise ValueError("Provide a font")
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
