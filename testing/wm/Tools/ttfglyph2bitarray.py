import os
import sys
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont

FONT_SIZE = 20  # change as needed

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

def main(font_path):
    base = os.path.splitext(os.path.basename(font_path))[0]
    output_path = f"Fonts/PY/{base}.py"
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

    with open(output_path, "w") as f:
        f.write("charmap = {\n")
        for name, bitmap in charmap.items():
            f.write(f"    \"{name}\": [\n")
            for line in bitmap:
                f.write(f"        \"{line}\",\n")
            f.write("    ],\n")
        f.write("}\n")

    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ttf2bitmap.py fontfile.ttf")
        sys.exit(1)
    main(sys.argv[1])
