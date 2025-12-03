import os
import sys
import platform
import pathlib
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont

FONT_SIZE = 12  # change as needed

def glyph_names(font_path):
    font = TTFont(font_path)
    cmap = font['cmap'].getBestCmap()
    reverse_map = {v: k for k, v in cmap.items()}
    glyph_order = font.getGlyphOrder()
    return {
        name: chr(reverse_map[name])
        for name in glyph_order
        if name in reverse_map
    }

def render_char(char, font):
    img = Image.new("1", (FONT_SIZE, FONT_SIZE), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), char, 1, font=font)
    return [
        ''.join(['1' if pixel else '0' for pixel in img.crop((0, y, FONT_SIZE, y+1)).getdata()])
        for y in range(FONT_SIZE)
    ]

def getfont():
    font_path = None
    if platform.system() == "Linux":
        print("Using system font.")
        font_path = subprocess.check_output(['fc-match', '-f', '%{file}\n', 'sans']).decode().strip()
    else:
        print("Your current platform has not been implemented for using your default font. Defaulting to bundled comicsans")
        font_path = os.path.join(Path(__file__).parent.parent.absolute(), "TTF", "comic.ttf")
    base = os.path.splitext(os.path.basename(font_path))[0]
    font = ImageFont.truetype(font_path, FONT_SIZE)
    glyph_map = glyph_names(font_path)

    charmap = {}
    for name, char in glyph_map.items():
        try:
            bitmap = render_char(char, font)
            # loop over each line of the bitmap and remove any lines that are all zeros
            # bitmap = [line for line in bitmap if '1' in line]
            
            # Find the last column that has any '1' in it
            if bitmap:
                # Find the last column index that contains any pixel
                max_width = 0
                for line in bitmap:
                    # Find the rightmost '1' in the line
                    for i, pixel in enumerate(line):
                        if pixel == '1':
                            max_width = max(max_width, i + 1)
                
                # Trim each line to the max_width
                bitmap = [line[:max_width] for line in bitmap]
            
            # if not bitmap:
                # continue  # Skip empty bitmaps
            charmap[name] = bitmap
        except Exception as e:
            print(f"Error rendering {name}: {e}")
    return charmap