from PIL import Image, ImageDraw, ImageFont

def generate_font_array(ttf_path, font_size, characters, output_name="font_array.py"):
    """
    Generates a Python array for a font from a TTF file.

    Args:
        ttf_path (str): Path to the TTF file.
        font_size (int): Size of the font to render.
        characters (str): Characters to include in the font array.
        output_name (str): Name of the output Python file.
    """
    # Load the font
    font = ImageFont.truetype(ttf_path, font_size)

    # Dictionary to store the font arrays
    font_dict = {}

    for char in characters:
        # Get the bounding box of the character
        bbox = font.getbbox(char)
        char_width = bbox[2] - bbox[0]
        char_height = bbox[3] - bbox[1]

        # Create a blank image for the character
        img = Image.new("1", (char_width, char_height), color=1)  # White background
        draw = ImageDraw.Draw(img)

        # Draw the character
        draw.text((-bbox[0], -bbox[1]), char, font=font, fill=0)  # Black text

        # Extract pixel data
        pixels = img.load()
        char_array = []
        for y in range(img.height):
            row = ""
            for x in range(img.width):
                row += "1" if pixels[x, y] == 0 else "0"  # Black = 1, White = 0
            char_array.append(row)

        # Add to the dictionary
        font_dict[char] = char_array
    font_dict[" "] = [
        "0",
        "0",
        "0",
        "0",
        "0"
    ]
    font_dict["cursor"] = [
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "11111000000000000000",
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
    "00000000000000000000",
    "00000000000000000000",
    "00000000000000000000",
]
    font_dict["missing"] =[
        "11111",
        "10001",
        "10001",
        "10001",
        "11111",
        ]

    # Write the font dictionary to a Python file
    with open(output_name, "w") as f:
        f.write("charmap = {\n")
        for char, char_array in font_dict.items():
            f.write(f"    '{char}': [\n")
            for row in char_array:
                f.write(f"        \"{row}\",\n")
            f.write("    ],\n")
        f.write("}\n")

    print(f"Font array saved to {output_name}")


# Example usage
import sys
ttf_path = sys.argv[1]  # Path to your Micro 5 TTF file
font_size = 20 # Set the font size (adjust based on the font)
characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:).,.1234567890"  # Characters to include
generate_font_array(ttf_path, font_size, characters)