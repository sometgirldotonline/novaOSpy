import os
import sys
import platform
import pathlib
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont
import subprocess
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
    descenders = set('gjpqy')
    fh = FONT_SIZE
    if char.lower() in descenders:
        fh += 2
    img = Image.new("1", (FONT_SIZE, fh), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), char, 1, font=font)
    arr =  [
        ''.join(['1' if pixel else '0' for pixel in img.crop((0, y, FONT_SIZE, y+1)).getdata()])
        for y in range(fh)
    ]
    if char.lower() not in descenders:
        arr.append("0"*FONT_SIZE)
        arr.append("0"*FONT_SIZE)
    return arr

def getfont():
    font_path = None
    if platform.system() == "Linux":
        print("Using system font.")
        # todo: rely on DE settings, GNOME Tweaks etc don't update fontcache becauase fuck you?
        font_path = subprocess.check_output(['fc-match', '-f', '%{file}\n', 'mono']).decode().strip()
    else:
        print("Your current platform has not been implemented for using your default font. Defaulting to bundled comicsans")
        font_path = os.path.join(pathlib.Path(__file__).parent.parent.absolute(), "TTF", "comic.ttf")
    base = os.path.splitext(os.path.basename(font_path))[0]
    font = ImageFont.truetype(font_path, FONT_SIZE)
    glyph_map = glyph_names(font_path)

    # Reference character for "normal height" (no tail)
    ref_char = 'H'
    ref_bitmap = render_char(ref_char, font)
    ref_top = next((i for i, line in enumerate(ref_bitmap) if '1' in line), 0)
    ref_bottom = next((i for i, line in enumerate(reversed(ref_bitmap)) if '1' in line), 0)
    normal_height = FONT_SIZE - ref_top - ref_bottom

    # Lowercase letters with descenders
    descenders = set('gjpqy')

    charmap = {}
    for name, char in glyph_map.items():
        try:
            bitmap = render_char(char, font)
            top = next((i for i, line in enumerate(bitmap) if '1' in line), 0)
            bottom = next((i for i, line in enumerate(reversed(bitmap)) if '1' in line), 0)
            char_height = FONT_SIZE - top - bottom + 20

            # Only pad top for lowercase letters without descenders
            if char.islower() and char not in descenders and char_height < normal_height:
                pad = normal_height - char_height
                bitmap = ['0' * len(bitmap[0])] * pad + bitmap
                # If bitmap is now longer than FONT_SIZE, trim from the top only
                if len(bitmap) > FONT_SIZE:
                    bitmap = bitmap[len(bitmap) - FONT_SIZE:]
                elif len(bitmap) < FONT_SIZE:
                    bitmap += ['0' * len(bitmap[0])] * (FONT_SIZE - len(bitmap))

            # Ensure all bitmaps are FONT_SIZE rows
            if len(bitmap) < FONT_SIZE:
                bitmap += ['0' * len(bitmap[0])] * (FONT_SIZE - len(bitmap))


            # Find the last column index that contains any pixel
            max_width = 0
            for line in bitmap:
                for i, pixel in enumerate(line):
                    if pixel == '1':
                        max_width = max(max_width, i + 1)
            bitmap = [line[:max_width] for line in bitmap]

            charmap[name] = bitmap
        except Exception as e:
            print(f"Error rendering {name}: {e}")
    return charmap